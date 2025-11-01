from abc import ABC, abstractmethod
from typing import Dict

from .exceptions import CurrencyNotFoundError, InvalidCurrencyError


class Currency(ABC):
    """Абстрактный базовый класс для валют."""

    def __init__(self, name: str, code: str):
        self._validate_code(code)
        self._validate_name(name)

        self._name = name
        self._code = code.upper()

    def _validate_code(self, code: str) -> None:
        """Валидация кода валюты."""
        if not isinstance(code, str):
            raise InvalidCurrencyError("Код валюты должен быть строкой")
        if not 2 <= len(code) <= 5:
            raise InvalidCurrencyError("Код валюты должен содержать от 2 до 5 символов")
        if not code.isalnum() or " " in code:
            raise InvalidCurrencyError("Код валюты не должен содержать пробелов")

    def _validate_name(self, name: str) -> None:
        """Валидация названия валюты."""
        if not isinstance(name, str) or not name.strip():
            raise InvalidCurrencyError("Название валюты не может быть пустым")

    @abstractmethod
    def get_display_info(self) -> str:
        """Возвращает строковое представление валюты для UI/логов."""
        pass

    @property
    def name(self) -> str:
        return self._name

    @property
    def code(self) -> str:
        return self._code

    def __str__(self) -> str:
        return self.get_display_info()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', code='{self.code}')"


class FiatCurrency(Currency):
    """Класс для фиатных валют."""

    def __init__(self, name: str, code: str, issuing_country: str):
        super().__init__(name, code)
        self._issuing_country = issuing_country

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self._issuing_country})"

    @property
    def issuing_country(self) -> str:
        return self._issuing_country


class CryptoCurrency(Currency):
    """Класс для криптовалют."""

    def __init__(self, name: str, code: str, algorithm: str, market_cap: float = 0.0):
        super().__init__(name, code)
        self._algorithm = algorithm
        self._market_cap = market_cap

    def get_display_info(self) -> str:
        mcap_str = (
            f"{self._market_cap:.2e}"
            if self._market_cap > 1e6
            else f"{self._market_cap:.2f}"
        )
        return (
            f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self._algorithm}, MCAP: {mcap_str})"
        )

    @property
    def algorithm(self) -> str:
        return self._algorithm

    @property
    def market_cap(self) -> float:
        return self._market_cap

    @market_cap.setter
    def market_cap(self, value: float) -> None:
        if value < 0:
            raise ValueError("Рыночная капитализация не может быть отрицательной")
        self._market_cap = value


# Реестр валют и фабричный метод
_currency_registry: Dict[str, Currency] = {}


def _initialize_currencies():
    """Инициализация реестра валют."""
    global _currency_registry

    # Фиатные валюты
    fiats = [
        FiatCurrency("US Dollar", "USD", "United States"),
        FiatCurrency("Euro", "EUR", "Eurozone"),
        FiatCurrency("Russian Ruble", "RUB", "Russia"),
    ]

    # Криптовалюты
    cryptos = [
        CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
        CryptoCurrency("Ethereum", "ETH", "Ethash", 3.5e11),
    ]

    for currency in fiats + cryptos:
        _currency_registry[currency.code] = currency


def get_currency(code: str) -> Currency:
    """Фабричный метод для получения валюты по коду."""
    if not _currency_registry:
        _initialize_currencies()

    code_upper = code.upper()
    if code_upper not in _currency_registry:
        raise CurrencyNotFoundError(code_upper)

    return _currency_registry[code_upper]


def register_currency(currency: Currency) -> None:
    """Регистрация новой валюты в реестре."""
    _currency_registry[currency.code] = currency


def get_all_currencies() -> Dict[str, Currency]:
    """Получение всех зарегистрированных валют."""
    if not _currency_registry:
        _initialize_currencies()
    return _currency_registry.copy()
