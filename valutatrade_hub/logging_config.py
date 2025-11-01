import logging
import logging.handlers
import json
import os

from valutatrade_hub.infra.settings import settings


def setup_logging() -> None:
    """Настройка конфигурации логирования на основе SettingsLoader."""
    log_config = settings.get_log_config()
    log_file = log_config["log_file"]

    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

    log_format = log_config["log_format"]
    if log_format == "JSON":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=log_config["max_bytes"],
            backupCount=log_config["backup_count"],
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    log_level = getattr(
        logging, log_config["log_level"].upper(), logging.INFO
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Очищаем существующие обработчики
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    if log_file:
        root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.info("Система логирования инициализирована")


class JSONFormatter(logging.Formatter):
    """Форматтер для JSON логов."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Добавляем дополнительные поля если они есть
        if hasattr(record, 'action'):
            log_entry['action'] = record.action
        if hasattr(record, 'username'):
            log_entry['username'] = record.username
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'currency_code'):
            log_entry['currency_code'] = record.currency_code
        if hasattr(record, 'amount'):
            log_entry['amount'] = record.amount
        if hasattr(record, 'rate'):
            log_entry['rate'] = record.rate
        if hasattr(record, 'base'):
            log_entry['base'] = record.base
        if hasattr(record, 'result'):
            log_entry['result'] = record.result
        if hasattr(record, 'error_type'):
            log_entry['error_type'] = record.error_type
        if hasattr(record, 'error_message'):
            log_entry['error_message'] = record.error_message
        if hasattr(record, 'from_currency'):
            log_entry['from_currency'] = record.from_currency
        if hasattr(record, 'to_currency'):
            log_entry['to_currency'] = record.to_currency
        if hasattr(record, 'wallet_state'):
            log_entry['wallet_state'] = record.wallet_state
        if hasattr(record, 'portfolio_user_id'):
            log_entry['portfolio_user_id'] = record.portfolio_user_id
        if hasattr(record, 'user_info'):
            log_entry['user_info'] = record.user_info
        if hasattr(record, 'final_balance'):
            log_entry['final_balance'] = record.final_balance

        return json.dumps(log_entry, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """
    Получение логгера с заданным именем.

    Args:
        name: Имя логгера

    Returns:
        Настроенный логгер
    """
    return logging.getLogger(name)


def set_log_level(level: str) -> None:
    """
    Установка уровня логирования для корневого логгера.

    Args:
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.getLogger().setLevel(log_level)


def add_file_handler(file_path: str, level: str = None) -> None:
    """
    Добавление файлового обработчика для логирования.

    Args:
        file_path: Путь к файлу лога
        level: Уровень логирования (опционально)
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    file_handler = logging.handlers.RotatingFileHandler(
        file_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )

    log_config = settings.get_log_config()
    log_format = log_config["log_format"]

    if log_format == "JSON":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    file_handler.setFormatter(formatter)

    if level:
        file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))

    logging.getLogger().addHandler(file_handler)


def configure_actions_logger() -> logging.Logger:
    """
    Настройка специального логгера для действий.

    Returns:
        Логгер для действий
    """
    actions_logger = logging.getLogger('actions')
    actions_logger.setLevel(logging.INFO)

    # Удаляем существующие обработчики
    for handler in actions_logger.handlers[:]:
        actions_logger.removeHandler(handler)

    # Создаем обработчик для файла действий
    log_config = settings.get_log_config()
    actions_file = 'data/actions.log'

    os.makedirs(os.path.dirname(actions_file), exist_ok=True)

    file_handler = logging.handlers.RotatingFileHandler(
        actions_file,
        maxBytes=log_config["max_bytes"],
        backupCount=log_config["backup_count"],
        encoding='utf-8'
    )

    # Используем JSON формат для действий
    file_handler.setFormatter(JSONFormatter())
    actions_logger.addHandler(file_handler)

    # Добавляем консольный обработчик для действий
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    actions_logger.addHandler(console_handler)

    return actions_logger


def configure_debug_logger() -> logging.Logger:
    """
    Настройка логгера для отладки.

    Returns:
        Логгер для отладки
    """
    debug_logger = logging.getLogger('debug')
    debug_logger.setLevel(logging.DEBUG)

    # Удаляем существующие обработчики
    for handler in debug_logger.handlers[:]:
        debug_logger.removeHandler(handler)

    # Создаем обработчик для файла отладки
    debug_file = 'data/debug.log'
    os.makedirs(os.path.dirname(debug_file), exist_ok=True)

    file_handler = logging.handlers.RotatingFileHandler(
        debug_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding='utf-8'
    )

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    debug_logger.addHandler(file_handler)

    return debug_logger


# Глобальные логгеры для удобного использования
actions_logger = configure_actions_logger()
debug_logger = configure_debug_logger()

__all__ = [
    'setup_logging',
    'get_logger',
    'set_log_level',
    'add_file_handler',
    'configure_actions_logger',
    'configure_debug_logger',
    'JSONFormatter',
    'actions_logger',
    'debug_logger'
]