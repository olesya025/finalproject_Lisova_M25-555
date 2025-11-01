import hashlib
from datetime import datetime
from typing import Dict, Optional

from .currencies import Currency, get_currency
from .exceptions import InsufficientFundsError


class User:
    """Класс пользователя системы."""

    def __init__(
        self,
        user_id: int,
        username: str,
        password: str,
        salt: Optional[str] = None,
        registration_date: Optional[datetime] = None,
    ):
        self._user_id = user_id
        self._username = username
        self._salt = salt or self._generate_salt()
        self._hashed_password = self._hash_password(password)
        self._registration_date = registration_date or datetime.now()

    def _generate_salt(self) -> str:
        """Генерация соли для хеширования пароля."""
        import secrets

        return secrets.token_hex(8)

    def _hash_password(self, password: str) -> str:
        """Хеширование пароля с солью."""
        return hashlib.sha256((password + self._salt).encode()).hexdigest()

    def get_user_info(self) -> Dict:
        """Получение информации о пользователе (без пароля)."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }

    def change_password(self, new_password: str) -> None:
        """Изменение пароля пользователя."""
        if len(new_password) < 4:
            raise ValueError("Пароль должен содержать не менее 4 символов")
        self._hashed_password = self._hash_password(new_password)

    def verify_password(self, password: str) -> bool:
        """Проверка пароля."""
        return self._hashed_password == self._hash_password(password)

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value

    @property
    def registration_date(self) -> datetime:
        return self._registration_date


class Wallet:
    """Класс кошелька для конкретной валюты."""

    def __init__(self, currency_code: str, balance: float = 0.0):
        self._currency = get_currency(currency_code)  # Валидация валюты
        self._balance = balance

    @property
    def currency_code(self) -> str:
        return self._currency.code

    @property
    def currency(self) -> Currency:
        return self._currency

    def deposit(self, amount: float) -> None:
        """Пополнение баланса."""
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")
        self.balance += amount

    def withdraw(self, amount: float) -> None:
        """Снятие средств."""
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной")

        if amount > self._balance:
            raise InsufficientFundsError(self.currency_code, self._balance, amount)

        self.balance -= amount

    def get_balance_info(self) -> Dict:
        """Информация о балансе."""
        return {
            "currency_code": self.currency_code,
            "currency_info": self._currency.get_display_info(),
            "balance": self._balance,
        }

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        if not isinstance(value, (int, float)):
            raise ValueError("Баланс должен быть числом")
        self._balance = value


class Portfolio:
    """Класс портфеля пользователя (управление всеми кошельками)."""

    def __init__(self, user_id: int, wallets: Optional[Dict[str, Wallet]] = None):
        self._user_id = user_id
        self._wallets = wallets or {}

    def buy_currency(self, currency_code: str, amount: float, price: float) -> None:
        """Покупка валюты за USD."""
        if amount <= 0:
            raise ValueError("Сумма покупки должна быть положительной")
        if price <= 0:
            raise ValueError("Цена должна быть положительной")

        # Получаем или создаем кошелек для покупаемой валюты
        if currency_code not in self._wallets:
            self.add_currency(currency_code)

        # Получаем USD кошелек
        usd_wallet = self.get_wallet("USD")

        # Расчет общей стоимости покупки
        total_cost = amount * price

        # Проверяем достаточно ли USD
        if total_cost > usd_wallet.balance:
            error_msg = (
                f"Недостаточно USD для покупки. "
                f"Нужно: ${total_cost:.2f}, доступно: ${usd_wallet.balance:.2f}"
            )
            raise ValueError(error_msg)

        # Выполняем операцию: списываем USD, добавляем валюту
        usd_wallet.withdraw(total_cost)
        target_wallet = self.get_wallet(currency_code)
        target_wallet.deposit(amount)

    def sell_currency(self, currency_code: str, amount: float, price: float) -> None:
        """Продажа валюты за USD."""
        if amount <= 0:
            raise ValueError("Сумма продажи должна быть положительной")

        if price <= 0:
            raise ValueError("Цена должна быть положительной")

        # Получаем кошелек продаваемой валюты
        if currency_code not in self._wallets:
            raise ValueError(f"У вас нет валюты {currency_code} для продажи")

        source_wallet = self.get_wallet(currency_code)

        # Проверяем достаточно ли валюты для продажи
        if amount > source_wallet.balance:
            raise InsufficientFundsError(currency_code, source_wallet.balance, amount)

        # Получаем USD кошелек
        usd_wallet = self.get_wallet("USD")

        # Расчет выручки от продажи
        total_revenue = amount * price

        # Выполняем операцию: списываем валюту, добавляем USD
        source_wallet.withdraw(amount)
        usd_wallet.deposit(total_revenue)

    def add_currency(self, currency_code: str) -> None:
        """Добавление новой валюты в портфель."""
        if currency_code in self._wallets:
            raise ValueError(f"Валюта {currency_code} уже есть в портфеле")
        self._wallets[currency_code] = Wallet(currency_code)

    def get_total_value(self, base_currency: str = "USD") -> float:
        """Расчет общей стоимости портфеля в базовой валюте."""
        exchange_rates = {
            "USD": 1.0,
            "EUR": 0.85,
            "RUB": 0.011,
            "BTC": 50000.0,
        }
        total_value = 0.0
        for currency_code, wallet in self._wallets.items():
            if currency_code in exchange_rates and base_currency in exchange_rates:
                rate_to_base = (
                    exchange_rates[currency_code] / exchange_rates[base_currency]
                )
                total_value += wallet.balance * rate_to_base
        return total_value

    def get_wallet(self, currency_code: str) -> Wallet:
        """Получение кошелька по коду валюты."""
        if currency_code not in self._wallets:
            raise ValueError(f"Валюта {currency_code} не найдена в портфеле")
        return self._wallets[currency_code]

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def wallets(self) -> Dict[str, Wallet]:
        return self._wallets.copy()
