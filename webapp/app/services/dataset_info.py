from pathlib import Path
from typing import Dict, List

DATA_DIR = Path("assets/datasets")

def list_available_datasets() -> Dict[str, List[str]]:
    result = {}
    for lang_dir in DATA_DIR.iterdir():
        if lang_dir.is_dir():
            datasets = [f.stem for f in lang_dir.glob("*.json")]
            if datasets:
                result[lang_dir.name] = datasets
    return result

def list_language_datasets(language: str) -> List[str]:
    lang_path = DATA_DIR / language
    if not lang_path.exists() or not lang_path.is_dir():
        return []
    return [f.stem for f in lang_path.glob("*.json")]