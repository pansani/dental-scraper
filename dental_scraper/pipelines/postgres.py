import psycopg2
from itemadapter import ItemAdapter

SUPPLIER_MAPPING = {
    "dental_speed": ("Dental Speed", "dental-speed"),
    "dental_cremer": ("Dental Cremer", "dental-cremer"),
}


class PostgresPipeline:
    def __init__(self, db_config):
        self.db_config = db_config
        self.conn = None
        self.supplier_cache = {}

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            db_config={
                "host": crawler.settings.get("DB_HOST"),
                "port": crawler.settings.get("DB_PORT"),
                "dbname": crawler.settings.get("DB_NAME"),
                "user": crawler.settings.get("DB_USER"),
                "password": crawler.settings.get("DB_PASSWORD"),
            }
        )

    def open_spider(self, spider):
        self.conn = psycopg2.connect(**self.db_config)
        spider.logger.info(f"Connected to PostgreSQL: {self.db_config['dbname']}")

    def close_spider(self, spider):
        if self.conn:
            self.conn.close()
            spider.logger.info("PostgreSQL connection closed")

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        try:
            with self.conn.cursor() as cur:
                supplier_id = self._get_or_create_supplier(cur, spider.name)
                sp_id, old_price, product_id = self._upsert_supplier_product(
                    cur, supplier_id, adapter
                )

                new_price = adapter.get("price")
                if new_price and (
                    old_price is None or float(old_price) != float(new_price)
                ):
                    self._insert_price_history(cur, sp_id, adapter)

                if not product_id:
                    self._try_link_to_master(cur, sp_id, adapter)

                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            spider.logger.error(f"DB error for {adapter.get('external_id')}: {e}")

        return item

    def _get_or_create_supplier(self, cur, spider_name):
        if spider_name in self.supplier_cache:
            return self.supplier_cache[spider_name]

        name, slug = SUPPLIER_MAPPING.get(spider_name, (spider_name, spider_name))

        cur.execute("SELECT id FROM suppliers WHERE slug = %s", (slug,))
        row = cur.fetchone()

        if row:
            supplier_id = row[0]
        else:
            cur.execute(
                """
                INSERT INTO suppliers (name, slug, is_active, created_at, updated_at)
                VALUES (%s, %s, true, NOW(), NOW())
                RETURNING id
                """,
                (name, slug),
            )
            supplier_id = cur.fetchone()[0]

        self.supplier_cache[spider_name] = supplier_id
        return supplier_id

    def _upsert_supplier_product(self, cur, supplier_id, adapter):
        cur.execute(
            "SELECT id, current_price, product_id FROM supplier_products WHERE supplier_id = %s AND external_id = %s",
            (supplier_id, adapter.get("external_id")),
        )
        existing = cur.fetchone()
        old_price = existing[1] if existing else None
        old_product_id = existing[2] if existing else None

        cur.execute(
            """
            INSERT INTO supplier_products (
                supplier_id, external_id, external_url, name, normalized_name,
                brand, category, raw_category, unit, quantity, ean, anvisa_registration,
                manufacturer_code, image_url, in_stock, current_price, pix_price,
                original_price, discount_percent, last_scraped_at, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), NOW())
            ON CONFLICT (supplier_id, external_id) DO UPDATE SET
                name = EXCLUDED.name,
                normalized_name = EXCLUDED.normalized_name,
                brand = EXCLUDED.brand,
                category = EXCLUDED.category,
                raw_category = EXCLUDED.raw_category,
                unit = EXCLUDED.unit,
                quantity = EXCLUDED.quantity,
                ean = EXCLUDED.ean,
                anvisa_registration = EXCLUDED.anvisa_registration,
                manufacturer_code = EXCLUDED.manufacturer_code,
                image_url = EXCLUDED.image_url,
                in_stock = EXCLUDED.in_stock,
                current_price = EXCLUDED.current_price,
                pix_price = EXCLUDED.pix_price,
                original_price = EXCLUDED.original_price,
                discount_percent = EXCLUDED.discount_percent,
                last_scraped_at = NOW(),
                updated_at = NOW()
            RETURNING id, product_id
            """,
            (
                supplier_id,
                adapter.get("external_id"),
                adapter.get("external_url"),
                adapter.get("name"),
                adapter.get("normalized_name"),
                adapter.get("brand") or adapter.get("normalized_brand"),
                adapter.get("category"),
                adapter.get("raw_category"),
                adapter.get("unit", "unidade"),
                adapter.get("quantity", 1),
                adapter.get("ean"),
                adapter.get("anvisa_registration"),
                adapter.get("manufacturer_code"),
                adapter.get("image_url"),
                adapter.get("in_stock", True),
                adapter.get("price"),
                adapter.get("pix_price"),
                adapter.get("original_price"),
                adapter.get("discount_percent"),
            ),
        )
        result = cur.fetchone()
        sp_id = result[0]
        product_id = result[1] if result[1] else old_product_id

        return sp_id, old_price, product_id

    def _insert_price_history(self, cur, supplier_product_id, adapter):
        cur.execute(
            """
            INSERT INTO price_histories (
                supplier_product_id, price, pix_price, original_price, in_stock, recorded_at, created_at
            ) VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            """,
            (
                supplier_product_id,
                adapter.get("price"),
                adapter.get("pix_price"),
                adapter.get("original_price"),
                adapter.get("in_stock", True),
            ),
        )

    def _try_link_to_master(self, cur, supplier_product_id, adapter):
        ean = adapter.get("ean")
        anvisa = adapter.get("anvisa_registration")
        mfg_code = adapter.get("manufacturer_code")

        if not ean and not anvisa and not mfg_code:
            return

        master_id = None

        if ean:
            cur.execute("SELECT id FROM products WHERE ean = %s LIMIT 1", (ean,))
            row = cur.fetchone()
            if row:
                master_id = row[0]
            else:
                master_id = self._create_master_product(cur, adapter, "ean", ean)

        elif anvisa:
            cur.execute(
                "SELECT id FROM products WHERE anvisa_registration = %s LIMIT 1",
                (anvisa,),
            )
            row = cur.fetchone()
            if row:
                master_id = row[0]
            else:
                master_id = self._create_master_product(
                    cur, adapter, "anvisa_registration", anvisa
                )

        elif mfg_code:
            cur.execute(
                "SELECT id FROM products WHERE manufacturer_code = %s LIMIT 1",
                (mfg_code,),
            )
            row = cur.fetchone()
            if row:
                master_id = row[0]
            else:
                master_id = self._create_master_product(
                    cur, adapter, "manufacturer_code", mfg_code
                )

        if master_id:
            cur.execute(
                "UPDATE supplier_products SET product_id = %s WHERE id = %s",
                (master_id, supplier_product_id),
            )

    def _create_master_product(self, cur, adapter, field_name, field_value):
        columns = [
            "name",
            "normalized_name",
            "brand",
            "normalized_brand",
            field_name,
            "created_at",
            "updated_at",
        ]
        placeholders = ["%s", "%s", "%s", "%s", "%s", "NOW()", "NOW()"]

        cur.execute(
            f"""
            INSERT INTO products ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING id
            """,
            (
                adapter.get("name"),
                adapter.get("normalized_name"),
                adapter.get("brand") or adapter.get("normalized_brand"),
                adapter.get("normalized_brand"),
                field_value,
            ),
        )
        return cur.fetchone()[0]
