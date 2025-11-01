import os
from datetime import datetime
from typing import Optional

from .models import Portfolio, User, Wallet
from .utils import load_json_data, save_json_data
from valutatrade_hub.infra.settings import settings
from valutatrade_hub.decorators import log_action
from .currencies import get_currency, CurrencyNotFoundError
from .exceptions import InsufficientFundsError, ApiRequestError


class UserManager:
    """User manager."""
    
    def __init__(self):
        data_dir = settings.get_data_dir()
        self.users_file = f"{data_dir}/users.json"
        self.portfolios_file = f"{data_dir}/portfolios.json"
        self._ensure_data_files()

    def _ensure_data_files(self):
        """Ensure data files exist."""
        os.makedirs(settings.get_data_dir(), exist_ok=True)
        if not os.path.exists(self.users_file):
            save_json_data(self.users_file, [])
        if not os.path.exists(self.portfolios_file):
            save_json_data(self.portfolios_file, [])

    @log_action(action="REGISTER", verbose=True)
    def create_user(self, username: str, password: str) -> User:
        """Create new user."""
        users_data = load_json_data(self.users_file)
        for user_data in users_data:
            if user_data["username"] == username:
                raise ValueError("User with this username already exists")

        user_id = len(users_data) + 1
        user = User(user_id, username, password)
        user_data = {
            "user_id": user.user_id,
            "username": user.username,
            "hashed_password": user._hashed_password,
            "salt": user._salt,
            "registration_date": user.registration_date.isoformat(),
        }
        users_data.append(user_data)
        save_json_data(self.users_file, users_data)
        self._create_user_portfolio(user_id)
        return user

    def _create_user_portfolio(self, user_id: int):
        """Create portfolio for user."""
        portfolios_data = load_json_data(self.portfolios_file)
        portfolio_data = {
            "user_id": user_id,
            "wallets": {
                "USD": {"balance": 1000.0},
            },
        }
        portfolios_data.append(portfolio_data)
        save_json_data(self.portfolios_file, portfolios_data)

    @log_action(action="LOGIN", verbose=False)
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user."""
        users_data = load_json_data(self.users_file)
        for user_data in users_data:
            if user_data["username"] == username:
                temp_user = User(
                    user_data["user_id"],
                    user_data["username"],
                    "temp_password",
                    user_data["salt"],
                    datetime.fromisoformat(user_data["registration_date"]),
                )
                temp_user._hashed_password = user_data["hashed_password"]
                if temp_user.verify_password(password):
                    return temp_user
        return None


class PortfolioManager:
    """Portfolio manager."""
    
    def __init__(self):
        data_dir = settings.get_data_dir()
        self.portfolios_file = f"{data_dir}/portfolios.json"

    def get_user_portfolio(self, user_id: int) -> Portfolio:
        """Get user portfolio."""
        portfolios_data = load_json_data(self.portfolios_file)
        for portfolio_data in portfolios_data:
            if portfolio_data["user_id"] == user_id:
                wallets = {}
                for currency_code, wallet_data in portfolio_data["wallets"].items():
                    wallets[currency_code] = Wallet(
                        currency_code, wallet_data["balance"]
                    )
                return Portfolio(user_id, wallets)
        return self._create_empty_portfolio(user_id)

    def _create_empty_portfolio(self, user_id: int) -> Portfolio:
        """Create empty portfolio."""
        portfolio = Portfolio(user_id)
        portfolio.add_currency("USD")
        self.save_portfolio(portfolio)
        return portfolio

    def save_portfolio(self, portfolio: Portfolio):
        """Save portfolio."""
        portfolios_data = load_json_data(self.portfolios_file)
        portfolio_found = False
        
        for i, portfolio_data in enumerate(portfolios_data):
            if portfolio_data["user_id"] == portfolio.user_id:
                wallets_data = {}
                for currency_code, wallet in portfolio.wallets.items():
                    wallets_data[currency_code] = {"balance": wallet.balance}
                portfolios_data[i]["wallets"] = wallets_data
                portfolio_found = True
                break
        
        if not portfolio_found:
            wallets_data = {}
            for currency_code, wallet in portfolio.wallets.items():
                wallets_data[currency_code] = {"balance": wallet.balance}
            portfolios_data.append({
                "user_id": portfolio.user_id,
                "wallets": wallets_data,
            })
        
        save_json_data(self.portfolios_file, portfolios_data)

    @log_action(action="BUY", verbose=True)
    def buy_currency(self, user_id: int, currency_code: str, amount: float, rate: float) -> Portfolio:
        """Buy currency with USD."""
        if amount <= 0:
            raise ValueError("Purchase amount must be positive")
        
        try:
            get_currency(currency_code)
        except CurrencyNotFoundError as e:
            raise e
        
        portfolio = self.get_user_portfolio(user_id)
        if currency_code not in portfolio.wallets:
            portfolio.add_currency(currency_code)
        
        portfolio.buy_currency(currency_code, amount, rate)
        self.save_portfolio(portfolio)
        return portfolio

    @log_action(action="SELL", verbose=True)
    def sell_currency(self, user_id: int, currency_code: str, amount: float, rate: float) -> Portfolio:
        """Sell currency for USD."""
        if amount <= 0:
            raise ValueError("Sale amount must be positive")
        
        try:
            get_currency(currency_code)
        except CurrencyNotFoundError as e:
            raise e
        
        portfolio = self.get_user_portfolio(user_id)
        if currency_code not in portfolio.wallets:
            raise ValueError(f"Wallet for currency {currency_code} not found")
        
        wallet = portfolio.get_wallet(currency_code)
        if amount > wallet.balance:
            raise InsufficientFundsError(currency_code, wallet.balance, amount)
        
        portfolio.sell_currency(currency_code, amount, rate)
        self.save_portfolio(portfolio)
        return portfolio

    @log_action(action="DEPOSIT", verbose=True)
    def deposit_funds(self, user_id: int, currency_code: str, amount: float) -> Portfolio:
        """Deposit funds."""
        portfolio = self.get_user_portfolio(user_id)
        if currency_code not in portfolio.wallets:
            portfolio.add_currency(currency_code)
        
        wallet = portfolio.get_wallet(currency_code)
        wallet.deposit(amount)
        self.save_portfolio(portfolio)
        return portfolio

    @log_action(action="ADD_CURRENCY", verbose=True)
    def add_currency_to_portfolio(self, user_id: int, currency_code: str) -> Portfolio:
        """Add currency to portfolio."""
        portfolio = self.get_user_portfolio(user_id)
        portfolio.add_currency(currency_code)
        self.save_portfolio(portfolio)
        return portfolio

    @log_action(action="GET_RATE", verbose=False)
    def get_rate(self, from_code: str, to_code: str) -> dict:
        """Get exchange rate using parser service data."""
        try:
            get_currency(from_code)
            get_currency(to_code)
        except CurrencyNotFoundError as e:
            raise e

        # Load rates from parser service cache
        try:
            from valutatrade_hub.parser_service.storage import RatesStorage
            storage = RatesStorage()
            rates_data = storage.read_current_rates()
            
            if not rates_data or 'pairs' not in rates_data:
                raise ApiRequestError("Rates data not available")
            
            # Same currency
            if from_code == to_code:
                return {'rate': 1.0, 'updated_at': rates_data.get('last_refresh')}
            
            # Try direct pair (both directions)
            direct_pair = f"{from_code}_{to_code}"
            reverse_pair = f"{to_code}_{from_code}"
            
            if direct_pair in rates_data['pairs']:
                return {
                    'rate': rates_data['pairs'][direct_pair]['rate'],
                    'updated_at': rates_data['pairs'][direct_pair]['updated_at']
                }
            elif reverse_pair in rates_data['pairs']:
                # Return inverse rate for reverse pair
                return {
                    'rate': 1.0 / rates_data['pairs'][reverse_pair]['rate'],
                    'updated_at': rates_data['pairs'][reverse_pair]['updated_at']
                }
            
            # Try through USD conversion
            from_usd_pair = f"{from_code}_USD"
            to_usd_pair = f"{to_code}_USD"
            usd_from_pair = f"USD_{from_code}"
            usd_to_pair = f"USD_{to_code}"
            
            from_rate = None
            to_rate = None
            
            # Get from_rate
            if from_usd_pair in rates_data['pairs']:
                from_rate = rates_data['pairs'][from_usd_pair]['rate']
            elif usd_from_pair in rates_data['pairs']:
                from_rate = 1.0 / rates_data['pairs'][usd_from_pair]['rate']
            
            # Get to_rate  
            if to_usd_pair in rates_data['pairs']:
                to_rate = rates_data['pairs'][to_usd_pair]['rate']
            elif usd_to_pair in rates_data['pairs']:
                to_rate = 1.0 / rates_data['pairs'][usd_to_pair]['rate']
            
            if from_rate and to_rate:
                calculated_rate = to_rate / from_rate
                return {
                    'rate': calculated_rate,
                    'updated_at': rates_data.get('last_refresh')
                }
            
            raise ApiRequestError(f"Rate for pair {from_code}/{to_code} not found")
            
        except Exception as e:
            raise ApiRequestError(f"Failed to get rate: {str(e)}")


# Global instances for app use
user_manager = UserManager()
portfolio_manager = PortfolioManager()