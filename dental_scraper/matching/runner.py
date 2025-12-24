import argparse
import json
from datetime import datetime
from pathlib import Path

from .engine import MatchingEngine
from .models import Product


def load_products_from_json(file_path: Path) -> list[Product]:
    with open(file_path, encoding="utf-8") as f:
        content = f.read()
        if not content.rstrip().endswith("]"):
            last_brace = content.rfind("}")
            content = content[: last_brace + 1] + "]"
        data = json.loads(content)

    return [Product.from_dict(item) for item in data]


def find_latest_json_files(output_dir: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}

    for json_file in output_dir.glob("*.json"):
        if json_file.name == "suppliers_metadata.json":
            continue

        name = json_file.stem
        if name.startswith("dental_cremer"):
            if "dental_cremer" not in files or json_file.stat().st_mtime > files["dental_cremer"].stat().st_mtime:
                files["dental_cremer"] = json_file
        elif name.startswith("dental_speed"):
            if "dental_speed" not in files or json_file.stat().st_mtime > files["dental_speed"].stat().st_mtime:
                files["dental_speed"] = json_file

    return files


def run_matching(
    output_dir: Path,
    threshold: float = 0.70,
    output_file: Path | None = None,
) -> None:
    files = find_latest_json_files(output_dir)

    if len(files) < 2:
        print(f"Need at least 2 supplier files. Found: {list(files.keys())}")
        return

    print(f"Loading products from {len(files)} suppliers...")
    all_products: list[Product] = []

    for supplier, file_path in files.items():
        products = load_products_from_json(file_path)
        print(f"  {supplier}: {len(products)} products")
        all_products.extend(products)

    print(f"\nTotal products: {len(all_products)}")
    print(f"Running matching with threshold: {threshold}...")

    engine = MatchingEngine(fuzzy_threshold=threshold)
    result = engine.match_all_pairs(all_products)

    print(f"\n{'='*60}")
    print("MATCHING RESULTS")
    print(f"{'='*60}")
    print(f"Total matches: {len(result.matches)}")
    print(f"By method: {result.stats['by_method']}")
    print(f"Unmatched (supplier A): {len(result.unmatched_a)}")
    print(f"Unmatched (supplier B): {len(result.unmatched_b)}")

    if result.matches:
        print(f"\n{'='*60}")
        print("TOP 10 MATCHES")
        print(f"{'='*60}")

        for i, match in enumerate(result.matches[:10], 1):
            print(f"\n{i}. [{match.method}] Confidence: {match.confidence:.1%}")
            print(f"   A: {match.product_a.name}")
            print(f"      {match.product_a.supplier} - R${match.product_a.price}")
            print(f"   B: {match.product_b.name}")
            print(f"      {match.product_b.supplier} - R${match.product_b.price}")
            if match.price_diff_percent:
                diff = match.price_diff_percent
                cheaper = match.cheaper_supplier
                print(f"   -> Price diff: {diff:+.1f}% (cheaper at {cheaper})")

    if result.matches:
        print(f"\n{'='*60}")
        print("PRICE COMPARISON SUMMARY")
        print(f"{'='*60}")

        suppliers = set()
        for m in result.matches:
            suppliers.add(m.product_a.supplier)
            suppliers.add(m.product_b.supplier)
        suppliers = list(suppliers)

        cheaper_count = {s: 0 for s in suppliers}
        total_savings = {s: 0.0 for s in suppliers}

        for match in result.matches:
            if match.cheaper_supplier:
                cheaper_count[match.cheaper_supplier] += 1
                if match.product_a.price and match.product_b.price:
                    diff = abs(float(match.product_a.price) - float(match.product_b.price))
                    total_savings[match.cheaper_supplier] += diff

        for supplier in suppliers:
            count = cheaper_count[supplier]
            savings = total_savings[supplier]
            print(f"{supplier}: cheaper in {count} products (potential savings: R${savings:.2f})")

    if output_file:
        output_data = result.to_dict()
        output_data["generated_at"] = datetime.now().isoformat()
        output_data["files_used"] = {k: str(v) for k, v in files.items()}

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\nResults saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Match products across suppliers")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory containing scraped JSON files",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.70,
        help="Minimum confidence threshold for fuzzy matching",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output file for match results (JSON)",
    )

    args = parser.parse_args()
    run_matching(args.output_dir, args.threshold, args.output)


if __name__ == "__main__":
    main()
