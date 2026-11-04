import csv
import json
from pathlib import Path


class FileUtils:
    @staticmethod
    def write_csv(path: Path, rows: list[dict], columns: list[str]):
        if not rows:
            return
        print("THỰC TẾ FIELDNAMES TRONG UTILS:", columns)
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=columns)
            w.writeheader()
            w.writerows(rows)

    # read CSV file and return list of dict
    @staticmethod
    def read_csv(path: Path) -> list[dict]:
        with path.open("r", newline="", encoding="utf-8-sig") as f:
            r = csv.DictReader(f)
            return list(r)

    @staticmethod
    def write_jsonl(path: Path, rows: list[dict]):
        with path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # read JSONL file and return list of dict
    @staticmethod
    def read_jsonl(path: Path) -> list[dict]:
        with path.open("r", encoding="utf-8") as f:
            return [json.loads(line) for line in f]
