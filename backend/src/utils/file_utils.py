import json
import os
from pathlib import Path

from src.utils.logger import setup_logger
 

class FileUtils:
    @staticmethod
                  
    def load_json_file(file_path: Path) -> list[dict]:
        """
        Load JSON data from a file.
        """
        if not Path(file_path).exists():
            print(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
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
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        print(f"Data saved to {file_path}")
            
        return file_path
            