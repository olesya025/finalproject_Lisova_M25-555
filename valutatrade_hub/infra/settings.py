import json
import os
from typing import Any, Dict, Optional

import toml


class SettingsLoader:
    """
    Singleton класс для загрузки и управления конфигурацией приложения.
    """
    _instance: Optional['SettingsLoader'] = None
    _initialized: bool = False

    def __new__(cls) -> 'SettingsLoader':
        """
        Реализация Singleton через __new__.
        Выбран этот способ для простоты и читабельности.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """
        Инициализация конфигурации. Гарантирует однократную инициализацию.
        """
        if self._initialized:
            return

        self._config: Dict[str, Any] = {}
        self._load_configuration()
        self._initialized = True

    def _load_configuration(self) -> None:
        """Загрузка конфигурации из pyproject.toml или config.json"""
        # Пытаемся загрузить из pyproject.toml
        if os.path.exists("pyproject.toml"):
            try:
                with open("pyproject.toml", "r", encoding="utf-8") as f:
                    pyproject_data = toml.load(f)
                    tool_config = pyproject_data.get("tool", {}).get("valutatrade", {})
                    if tool_config:
                        self._config.update(tool_config)
                        return
            except Exception as e:
                print(f"Warning: Could not load pyproject.toml: {e}")

        # Пытаемся загрузить из config.json
        config_json_path = "config.json"
        if os.path.exists(config_json_path):
            try:
                with open(config_json_path, "r", encoding="utf-8") as f:
                    json_config = json.load(f)
                    self._config.update(json_config)
                    return
            except Exception as e:
                print(f"Warning: Could not load config.json: {e}")

        # Значения по умолчанию
        self._set_defaults()

    def _set_defaults(self) -> None:
        """Установка значений по умолчанию"""
        default_config = {
            "data_dir": "data/",
            "rates_ttl_seconds": 300,
            "default_base_currency": "USD",
            "log_file": "data/valutatrade.log",
            "log_format": "TEXT",  # TEXT или JSON
            "log_level": "INFO",
            "max_log_size_mb": 10,
            "log_backup_count": 5
        }
        self._config.update(default_config)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Получение значения конфигурации по ключу.

        Args:
            key: Ключ конфигурации
            default: Значение по умолчанию если ключ не найден

        Returns:
            Значение конфигурации или default
        """
        return self._config.get(key, default)

    def reload(self) -> None:
        """Перезагрузка конфигурации из файлов"""
        self._config.clear()
        self._load_configuration()

    def get_data_dir(self) -> str:
        """Получить путь к директории данных"""
        return self.get("data_dir", "data/")

    def get_rates_ttl(self) -> int:
        """Получить TTL для кеша курсов валют"""
        return self.get("rates_ttl_seconds", 300)

    def get_default_base_currency(self) -> str:
        """Получить базовую валюту по умолчанию"""
        return self.get("default_base_currency", "USD")

    def get_log_config(self) -> Dict[str, Any]:
        """Получить конфигурацию логирования"""
        return {
            "log_file": self.get("log_file", "data/valutatrade.log"),
            "log_format": self.get("log_format", "TEXT"),
            "log_level": self.get("log_level", "INFO"),
            "max_bytes": self.get("max_log_size_mb", 10) * 1024 * 1024,
            "backup_count": self.get("log_backup_count", 5)
        }


# Глобальный экземпляр для импорта
settings = SettingsLoader()
