import csv
import json
import os
from pathlib import Path

import pandas as pd

FILE_NAME = "file_util.py"


class FileUtil:
    @staticmethod
    def get_project_root() -> Path:
        """
        Get the root directory of the project.
        {repo}/backend
        file_util.py is located in {repo}/backend/src/utils/file_util.py
        """
        path = Path(__file__).resolve().parent.parent.parent
        if path.name != "backend":
            raise Exception(
                f"Expected project root to be 'backend', but got '{path.name}'"
            )

        return path

    @staticmethod
    def get_data_dir() -> Path:
        """
        Get the data directory of the project.
        {repo}/backend/data
        """
        path = FileUtil.get_project_root() / "data"
        if not path.exists():
            print(f"{FILE_NAME}: Data directory not found: {path}. Creating it.")
            os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def get_models_dir() -> Path:
        """
        Get the models directory of the project.
        {repo}/backend/models
        """
        path = FileUtil.get_project_root() / "models"
        if not path.exists():
            print(f"{FILE_NAME}: Models directory not found: {path}. Creating it.")
            os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def load_json_file(file_path: Path) -> list[dict]:
        """
        Load JSON data from a file.
        """
        if not Path(file_path).exists():
            print(f"{FILE_NAME}: File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data

    @staticmethod
    def save_json_file(data: list[dict], dir: Path, file_name: str) -> Path:
        """
        Save JSON data to a file.
        """
        # Create the directory if it doesn't exist
        os.makedirs(dir, exist_ok=True)

        file_path = dir / file_name
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"{FILE_NAME}: Data saved to {file_path}")
        return file_path

    # Jsonl
    @staticmethod
    def save_jsonl_file(data: list[dict], dir: Path, file_name: str) -> Path:
        """
        Save JSONL data to a file.
        """
        # Create the directory if it doesn't exist
        os.makedirs(dir, exist_ok=True)

        file_path = dir / file_name
        with open(file_path, "w", encoding="utf-8") as f:
            for item in data:
                json_line = json.dumps(item, ensure_ascii=False)
                f.write(json_line + "\n")

        print(f"{FILE_NAME}: Data saved to {file_path}")

        return file_path

    @staticmethod
    def load_jsonl_file(file_path: Path) -> list[dict]:
        records = []

        with open(file_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                if not line.strip():
                    continue

                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"{FILE_NAME}: Invalid JSON at line {line_no}: {e}")

        print(f"{FILE_NAME}: Loaded {len(records)} records from {file_path}")

        return records

    # Lưu cả json và csv: trả về đường dẫn file json và csv
    @staticmethod
    def save_json_and_csv(
        data: list[dict], dir: Path, file_name: str = "data"
    ) -> tuple[Path, Path]:
        """
        Save JSON and CSV data to files.
        """
        # Xóa extension nếu có trong file_name
        file_name = file_name.replace(".json", "").replace(".csv", "")

        # Save JSON
        json_path = FileUtil.save_json_file(data, dir, file_name + ".json")
        print(f"{FILE_NAME}: Data saved to {json_path}")

        # Save CSV
        csv_path = dir / (file_name + ".csv")
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")

        print(f"{FILE_NAME}: Data saved to {csv_path}")

        return json_path, csv_path

    @staticmethod
    def write_csv(path: Path, rows, columns=None):
        rows = list(rows)

        if columns is None:
            columns = list(dict.fromkeys(key for row in rows for key in row))

        Path(path).parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()

            for row in rows:
                writer.writerow(
                    {
                        key: json.dumps(row.get(key), ensure_ascii=False)
                        for key in columns
                    }
                )

    @staticmethod
    def read_csv(path: Path) -> list[dict]:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)

            return [
                {key: json.loads(value) for key, value in row.items()} for row in reader
            ]
