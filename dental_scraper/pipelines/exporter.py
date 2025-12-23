import json
from datetime import datetime
from pathlib import Path

from scrapy import signals
from scrapy.exporters import JsonItemExporter

from dental_scraper.items import NormalizedProductItem


class JsonExporterPipeline:
    def __init__(self):
        self.files: dict[str, any] = {}
        self.exporters: dict[str, JsonItemExporter] = {}
        self.item_counts: dict[str, int] = {}

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signal=signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        output_dir = Path(spider.settings.get("OUTPUT_DIR", "./output"))
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = output_dir / f"{spider.name}_{timestamp}.json"

        self.files[spider.name] = open(filename, "wb")
        self.exporters[spider.name] = JsonItemExporter(
            self.files[spider.name],
            encoding="utf-8",
            indent=2,
        )
        self.exporters[spider.name].start_exporting()
        self.item_counts[spider.name] = 0

        spider.logger.info(f"Exporting to: {filename}")

    def spider_closed(self, spider):
        if spider.name in self.exporters:
            self.exporters[spider.name].finish_exporting()
            self.files[spider.name].close()

            count = self.item_counts.get(spider.name, 0)
            spider.logger.info(f"Exported {count} items for {spider.name}")

    def process_item(self, item: NormalizedProductItem, spider) -> NormalizedProductItem:
        if spider.name in self.exporters:
            self.exporters[spider.name].export_item(item)
            self.item_counts[spider.name] = self.item_counts.get(spider.name, 0) + 1
        return item


class CsvExporterPipeline:
    def __init__(self):
        self.files: dict[str, any] = {}
        self.writers: dict[str, any] = {}
        self.headers_written: dict[str, bool] = {}

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signal=signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        import csv

        output_dir = Path(spider.settings.get("OUTPUT_DIR", "./output"))
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = output_dir / f"{spider.name}_{timestamp}.csv"

        self.files[spider.name] = open(filename, "w", newline="", encoding="utf-8")
        self.writers[spider.name] = csv.writer(self.files[spider.name])
        self.headers_written[spider.name] = False

        spider.logger.info(f"Exporting CSV to: {filename}")

    def spider_closed(self, spider):
        if spider.name in self.files:
            self.files[spider.name].close()

    def process_item(self, item: NormalizedProductItem, spider) -> NormalizedProductItem:
        if spider.name not in self.writers:
            return item

        item_dict = dict(item)

        if not self.headers_written.get(spider.name, False):
            self.writers[spider.name].writerow(item_dict.keys())
            self.headers_written[spider.name] = True

        self.writers[spider.name].writerow(item_dict.values())
        return item
