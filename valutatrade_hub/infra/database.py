"""
Singleton DatabaseManager - абстракция над JSON-хранилищем.
"""
import json
import os
from typing import Any, Dict, List, Optional
from .settings import settings


class DatabaseManager:
    """
    Singleton класс для управления JSON-хранилищем данных.
    """
    _instance: Optional['DatabaseManager'] = None
    _initialized: bool = False

    def __new__(cls) -> 'DatabaseManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
            
        self.data_dir = settings.get_data_dir()
        self._ensure_data_directory()
        self._initialized = True

    def _ensure_data_directory(self) -> None:
        """Создание директории данных если её нет."""
        os.makedirs(self.data_dir, exist_ok=True)

    def load_data(self, filename: str) -> List[Dict[str, Any]]:
        """Загрузка данных из JSON файла."""
        file_path = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(file_path):
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, Exception):
            return []

    def save_data(self, filename: str, data: List[Dict[str, Any]]) -> None:
        """Сохранение данных в JSON файл."""
        file_path = os.path.join(self.data_dir, filename)
        
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка при сохранении данных: {e}")

    def get_file_path(self, filename: str) -> str:
        """Получение полного пути к файлу данных."""
        return os.path.join(self.data_dir, filename)


# Глобальный экземпляр для импорта
database = DatabaseManager()
