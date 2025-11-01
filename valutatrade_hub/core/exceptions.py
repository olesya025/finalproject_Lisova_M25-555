"""Пользовательские исключения для приложения."""

class CurrencyNotFoundError(ValueError):
    """Исключение для случая, когда валюта не найдена."""
    def __init__(self, currency_code: str):
        super().__init__(f"Неизвестная валюта '{currency_code}'")
        self.currency_code = currency_code


class InsufficientFundsError(ValueError):
    """Исключение для случая недостаточных средств."""
    def __init__(self, currency_code: str, available: float, required: float):
        message = (
            f"Недостаточно средств: доступно {available} {currency_code}, "
            f"требуется {required} {currency_code}"
        )
        super().__init__(message)
        self.currency_code = currency_code
        self.available = available
        self.required = required


class InvalidCurrencyError(ValueError):
    """Исключение для невалидной валюты."""
    pass


class ApiRequestError(Exception):
    """Исключение для сбоев внешнего API."""
    def __init__(self, reason: str = "неизвестная ошибка"):
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")
        self.reason = reason
