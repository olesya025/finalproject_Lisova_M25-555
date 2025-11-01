import logging
import functools
from typing import Any, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


def log_action(action: str = None, verbose: bool = False):
    """
    Декоратор для логирования доменных операций.

    Args:
        action: Название действия (BUY/SELL/REGISTER/LOGIN и т.д.)
        verbose: Расширенное логирование с контекстом

    Логирует:
        - timestamp (ISO format)
        - action (BUY/SELL/REGISTER/LOGIN)
        - username или user_id
        - currency_code, amount
        - rate и base (если применимо)
        - result (OK/ERROR)
        - error_type/error_message при исключениях
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Определяем действие
            operation_action = action or func.__name__.upper()

            # Базовый контекст логирования
            log_context = {
                'timestamp': datetime.now().isoformat(),
                'action': operation_action,
                'result': 'OK'
            }

            try:
                # Извлекаем контекст из аргументов
                _extract_logging_context(args, kwargs, log_context)

                # Логируем начало операции в verbose режиме
                if verbose:
                    logger.info(
                        f"Начало операции {operation_action}",
                        extra=log_context
                    )

                # Выполняем функцию
                result = func(*args, **kwargs)

                # Добавляем расширенный контекст после успешного выполнения
                if verbose:
                    _add_verbose_context(result, log_context)

                # Логируем успешное завершение
                logger.info("Операция выполнена", extra=log_context)
                return result

            except Exception as e:
                # Логируем ошибку
                log_context.update({
                    'result': 'ERROR',
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                })
                logger.error(
                    "Ошибка операции", extra=log_context, exc_info=True
                )
                # Пробрасываем исключение дальше
                raise

        return wrapper
    return decorator


def _extract_logging_context(args: tuple, kwargs: dict, context: dict) -> None:
    """
    Извлечение контекста для логирования из аргументов функции.

    Args:
        args: Позиционные аргументы
        kwargs: Именованные аргументы
        context: Словарь для сохранения контекста
    """
    # Обрабатываем позиционные аргументы
    for arg in args:
        if hasattr(arg, '__dict__'):
            # Если это объект User
            if hasattr(arg, 'user_id') and hasattr(arg, 'username'):
                context['user_id'] = arg.user_id
                context['username'] = arg.username
            # Если это объект Portfolio
            elif hasattr(arg, 'user_id'):
                context['user_id'] = arg.user_id
            # Если это Wallet или другой объект с валютой
            if hasattr(arg, 'currency_code'):
                context['currency_code'] = arg.currency_code
            elif hasattr(arg, 'currency') and hasattr(arg.currency, 'code'):
                context['currency_code'] = arg.currency.code

    # Обрабатываем именованные аргументы
    for key, value in kwargs.items():
        if key in ['username', 'user']:
            context['username'] = value
        elif key == 'user_id':
            context['user_id'] = value
        elif key == 'currency_code':
            context['currency_code'] = value
        elif key in ['amount', 'quantity']:
            context['amount'] = value
        elif key == 'rate':
            context['rate'] = value
        elif key in ['base', 'base_currency']:
            context['base'] = value
        elif key == 'from_currency':
            context['from_currency'] = value
        elif key == 'to_currency':
            context['to_currency'] = value

    # Если не нашли username, но есть user_id, используем его
    if 'username' not in context and 'user_id' in context:
        context['username'] = f"user_{context['user_id']}"


def _add_verbose_context(result: Any, context: dict) -> None:
    """
    Добавление расширенного контекста для verbose режима.

    Args:
        result: Результат выполнения функции
        context: Словарь контекста для обновления
    """
    try:
        if hasattr(result, '__dict__'):
            # Для объектов Portfolio
            if hasattr(result, 'wallets'):
                wallet_state = {}
                for currency_code, wallet in result.wallets.items():
                    wallet_state[currency_code] = {
                        'balance': wallet.balance,
                        'currency_type': type(wallet.currency).__name__
                    }
                context['wallet_state'] = wallet_state
                context['portfolio_user_id'] = result.user_id

            # Для объектов User
            elif hasattr(result, 'user_id') and hasattr(result, 'username'):
                context['user_info'] = {
                    'user_id': result.user_id,
                    'username': result.username,
                    'registration_date': (
                        result.registration_date.isoformat()
                        if hasattr(result, 'registration_date')
                        else None
                    )
                }

            # Для операций с балансом
            if hasattr(result, 'balance'):
                context['final_balance'] = result.balance
            if hasattr(result, 'currency_code'):
                context['currency_code'] = result.currency_code

    except Exception as e:
        # В случае ошибки при получении verbose контекста логируем без него
        logger.debug(f"Не удалось получить verbose контекст: {e}")


def confirm_operation(message: str = None):
    """
    Декоратор для подтверждения операций.

    Args:
        message: Сообщение для подтверждения
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Получаем описание операции
            operation_message = message or func.__doc__
            if operation_message:
                # Берем первую строку из docstring
                operation_message = operation_message.strip().split('\n')[0]
            else:
                operation_message = f"операцию {func.__name__}"

            print(f"\n⚠️  Вы собираетесь выполнить: {operation_message}")
            confirmation = input(
                "Подтвердите операцию (y/д - да, n/н - нет): "
            ).strip().lower()

            if confirmation in ['y', 'yes', 'д', 'да', 'y']:
                return func(*args, **kwargs)
            else:
                print("❌ Операция отменена пользователем")
                return None

        return wrapper
    return decorator


def log_simple(func: Callable) -> Callable:
    """
    Упрощенная версия декоратора логирования без параметров.

    Используется для быстрого добавления базового логирования.
    """
    return log_action()(func)


# Специализированные декораторы для конкретных операций
def log_buy_operation(verbose: bool = True):
    """Специализированный декоратор для операций покупки."""
    return log_action(action="BUY", verbose=verbose)


def log_sell_operation(verbose: bool = True):
    """Специализированный декоратор для операций продажи."""
    return log_action(action="SELL", verbose=verbose)


def log_auth_operation(verbose: bool = False):
    """Специализированный декоратор для операций аутентификации."""
    return log_action(action="AUTH", verbose=verbose)


def log_currency_operation(verbose: bool = False):
    """Специализированный декоратор для операций с валютами."""
    return log_action(action="CURRENCY_OP", verbose=verbose)


# Декоратор для измерения времени выполнения
def timing(log_level: str = "DEBUG"):
    """
    Декоратор для измерения времени выполнения функций.

    Args:
        log_level: Уровень логирования для временных метрик
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            import time
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                duration = end_time - start_time

                # Логируем время выполнения
                log_message = (
                    f"Функция {func.__name__} выполнена за {duration:.4f} секунд"
                )

                if log_level.upper() == "INFO":
                    logger.info(log_message)
                elif log_level.upper() == "WARNING":
                    logger.warning(log_message)
                elif log_level.upper() == "ERROR":
                    logger.error(log_message)
                else:
                    logger.debug(log_message)

        return wrapper
    return decorator


# Экспортируемые декораторы для удобного импорта
__all__ = [
    'log_action',
    'log_simple',
    'confirm_operation',
    'log_buy_operation',
    'log_sell_operation',
    'log_auth_operation',
    'log_currency_operation',
    'timing'
]