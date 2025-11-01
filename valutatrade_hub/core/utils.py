import json
import os
from typing import Any, Dict, List


def load_json_data(file_path: str) -> List[Dict[str, Any]]:
    """Загрузка данных из JSON файла."""
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, Exception) as e:
        print(f"Warning: Could not load {file_path}: {e}")
        return []


def save_json_data(file_path: str, data: List[Dict[str, Any]]) -> None:
    """Сохранение данных в JSON файл"""
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Ошибка при сохранении данных: {e}")


def ensure_data_directory():
    """Создание папки data если её нет"""
    os.makedirs("data", exist_ok=True)
