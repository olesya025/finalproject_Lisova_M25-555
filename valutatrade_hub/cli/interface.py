from getpass import getpass
import logging
from typing import Optional

from prettytable import PrettyTable

from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.core.usecases import PortfolioManager, UserManager
from valutatrade_hub.core.utils import load_json_data
from valutatrade_hub.core.currencies import get_currency, get_all_currencies
from valutatrade_hub.core.currencies import CurrencyNotFoundError
from valutatrade_hub.core.exceptions import InsufficientFundsError, ApiRequestError

# Parser Service imports
from valutatrade_hub.parser_service.updater import RatesUpdater
from valutatrade_hub.parser_service.storage import RatesStorage

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/operations.log'),
        logging.StreamHandler()
    ]
)

def log_operation(func):
    """Decorator for operation logging."""
    def wrapper(*args, **kwargs):
        logging.info(f"Executing operation: {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logging.info(f"Operation {func.__name__} completed successfully")
            return result
        except Exception as e:
            logging.error(f"Error in operation {func.__name__}: {e}")
            raise
    return wrapper

def get_exchange_rates():
    """Closure for caching exchange rates."""
    cache = {}
    
    def fetch_rates():
        if not cache:
            try:
                rates_data = load_json_data("data/rates.json")
                if rates_data and 'pairs' in rates_data:
                    # Convert pairs format to simple currency: rate
                    for pair, info in rates_data['pairs'].items():
                        from_curr, to_curr = pair.split('_')
                        if to_curr == 'USD':
                            cache[from_curr] = info['rate']
                        elif from_curr == 'USD':
                            cache[to_curr] = 1.0 / info['rate']
                else:
                    # Fallback to default rates
                    currencies = get_all_currencies()
                    default_rates = {
                        "USD": 1.0,
                        "EUR": 0.85,
                        "RUB": 0.011,
                        "BTC": 50000.0,
                        "ETH": 3000.0
                    }
                    cache.update({
                        code: rate for code, rate in default_rates.items()
                        if code in currencies
                    })
            except Exception as e:
                if not cache:
                    raise ApiRequestError(
                        f"failed to load rates: {str(e)}"
                    )
        return cache
    
    return fetch_rates

# Initialize rates cache
get_rates = get_exchange_rates()

class WalletCLI:
    """CLI interface class for wallet management."""
    
    def __init__(self):
        self.user_manager = UserManager()
        self.portfolio_manager = PortfolioManager()
        self.current_user: Optional[User] = None
        self.current_portfolio: Optional[Portfolio] = None

    @log_operation
    def create_user(self):
        """Create new user."""
        print("\n=== CREATE USER ===")
        while True:
            username = input("Enter username: ").strip()
            if not username:
                print("Username cannot be empty")
                continue
            
            password = getpass("Enter password (min 4 characters): ")
            if len(password) < 4:
                print("Password must be at least 4 characters")
                continue
            
            confirm_password = getpass("Confirm password: ")
            if password != confirm_password:
                print("Passwords do not match")
                continue
            
            try:
                user = self.user_manager.create_user(username, password)
                print(f"✅ User {username} created successfully!")
                return user
            except ValueError as e:
                print(f"❌ Error: {e}")
                return None

    @log_operation
    def authenticate_user(self):
        """Authenticate user."""
        print("\n=== LOGIN ===")
        username = input("Username: ").strip()
        password = getpass("Password: ")
        
        user = self.user_manager.authenticate_user(username, password)
        if user:
            self.current_user = user
            self.current_portfolio = self.portfolio_manager.get_user_portfolio(
                user.user_id
            )
            print(f"✅ Login successful! Welcome, {username}!")
            return True
        else:
            print("❌ Invalid username or password")
            return False

    def display_balance(self):
        """Display balance with formatted output."""
        if not self.current_portfolio:
            print("Portfolio not loaded")
            return
        
        print("\n=== YOUR BALANCE ===")
        table = PrettyTable()
        table.field_names = ["Currency", "Type", "Balance", "USD Equivalent"]
        
        try:
            rates = get_rates()
        except ApiRequestError as e:
            print(f"⚠️ Warning: {e}")
            print("💡 Showing balance without USD conversion")
            rates = {}
        
        total_usd = 0
        
        for currency_code, wallet in self.current_portfolio.wallets.items():
            balance = wallet.balance
            currency_display = wallet.currency.get_display_info()
            currency_type = "FIAT" if "FIAT" in currency_display else "CRYPTO"
            
            if currency_code in rates:
                usd_value = balance * rates[currency_code]
                total_usd += usd_value
                balance_str = (
                    f"{balance:.8f}" if currency_type == "CRYPTO"
                    else f"{balance:.2f}"
                )
                table.add_row([
                    currency_code,
                    currency_type,
                    balance_str,
                    f"${usd_value:.2f}"
                ])
            else:
                balance_str = (
                    f"{balance:.8f}" if currency_type == "CRYPTO"
                    else f"{balance:.2f}"
                )
                table.add_row([
                    currency_code,
                    currency_type,
                    balance_str,
                    "N/A"
                ])
        
        print(table)
        if rates:
            print(f"💰 Total portfolio value: ${total_usd:.2f}")

    def _confirm_action(self, message: str) -> bool:
        """Confirm action with user."""
        confirmation = input(f"{message} (y/n): ").strip().lower()
        return confirmation in ['y', 'yes', 'д', 'да']

    @log_operation
    def deposit_funds(self):
        """Deposit funds."""
        if not self.current_portfolio:
            print("Portfolio not loaded")
            return
        
        print("\n=== DEPOSIT FUNDS ===")
        self._show_available_currencies()
        
        currency = input("Select currency: ").strip().upper()
        try:
            get_currency(currency)
            
            if currency not in self.current_portfolio.wallets:
                print(f"❌ You don't have a wallet for {currency}")
                return
            
            amount = float(input("Deposit amount: "))
            if not self._confirm_action(f"Deposit {amount} {currency}?"):
                print("❌ Operation cancelled")
                return
            
            self.portfolio_manager.deposit_funds(
                self.current_user.user_id, currency, amount
            )
            
            # Refresh portfolio after operation
            self.current_portfolio = self.portfolio_manager.get_user_portfolio(
                self.current_user.user_id
            )
            print(f"✅ Deposited {amount} {currency}")
            
        except CurrencyNotFoundError as e:
            print(f"❌ {e}")
            print("💡 Use 'Currency Info' command to see available currencies")
        except ValueError as e:
            print(f"❌ Error: {e}")
        except Exception as e:
            print(f"❌ An error occurred: {e}")

    @log_operation
    def add_currency(self):
        """Add new currency to portfolio."""
        if not self.current_portfolio:
            print("Portfolio not loaded")
            return
        
        print("\n=== ADD CURRENCY ===")
        all_currencies = get_all_currencies()
        available_currencies = [
            curr for curr in all_currencies.keys()
            if curr not in self.current_portfolio.wallets
        ]
        
        if not available_currencies:
            print("❌ All available currencies already in portfolio")
            return
        
        print("Available currencies to add:")
        for code in available_currencies:
            currency = all_currencies[code]
            print(f" {code}: {currency.get_display_info()}")
        
        currency = input("Enter currency code: ").strip().upper()
        try:
            get_currency(currency)
            
            if currency not in available_currencies:
                print(f"❌ Currency {currency} already in portfolio or unavailable")
                return
            
            if not self._confirm_action(f"Add currency {currency} to portfolio?"):
                print("❌ Operation cancelled")
                return
            
            self.portfolio_manager.add_currency_to_portfolio(
                self.current_user.user_id, currency
            )
            
            # Refresh portfolio after operation
            self.current_portfolio = self.portfolio_manager.get_user_portfolio(
                self.current_user.user_id
            )
            print(f"✅ Currency {currency} added to portfolio")
            
        except CurrencyNotFoundError as e:
            print(f"❌ {e}")
            print("💡 Use 'Currency Info' command to see available currencies")
        except ValueError as e:
            print(f"❌ Error: {e}")
        except Exception as e:
            print(f"❌ An error occurred: {e}")

    @log_operation
    def buy_currency(self):
        """Buy currency with USD."""
        if not self.current_portfolio:
            print("Portfolio not loaded")
            return
        
        print("\n=== BUY CURRENCY ===")
        all_currencies = get_all_currencies()
        available_currencies = [
            curr for curr in all_currencies.keys()
            if curr != "USD"
        ]
        
        if not available_currencies:
            print("❌ No currencies available for purchase")
            return
        
        print("Available currencies to buy:")
        for code in available_currencies:
            currency = all_currencies[code]
            print(f" {code}: {currency.get_display_info()}")
        
        currency = input("Enter currency code to buy: ").strip().upper()
        if currency not in available_currencies:
            print("❌ Unsupported currency")
            return
        
        try:
            amount = float(input(f"How much {currency} to buy: "))
            if amount <= 0:
                print("❌ Amount must be positive")
                return
            
            # Get rate through portfolio_manager
            rate_info = self.portfolio_manager.get_rate("USD", currency)
            rate = rate_info['rate']
            price = 1.0 / rate  # Price in USD per currency unit
            total_cost = amount * price
            
            print("\nOperation details:")
            print(f"Purchase: {amount} {currency}")
            print(f"Rate: 1 {currency} = ${price:.6f} USD")
            print(f"Total cost: ${total_cost:.6f} USD")
            
            if not self._confirm_action("Confirm purchase?"):
                print("❌ Operation cancelled")
                return
            
            # Execute purchase through portfolio_manager
            self.portfolio_manager.buy_currency(
                self.current_user.user_id, currency, amount, price
            )
            
            # Refresh portfolio after operation
            self.current_portfolio = self.portfolio_manager.get_user_portfolio(
                self.current_user.user_id
            )
            print(
                f"✅ Successfully bought {amount} {currency} "
                f"for ${total_cost:.6f} USD"
            )
            
        except InsufficientFundsError as e:
            print(f"❌ {e}")
        except CurrencyNotFoundError as e:
            print(f"❌ {e}")
            print("💡 Use 'Currency Info' command to see available currencies")
        except ApiRequestError as e:
            print(f"❌ {e}")
            print("💡 Please try again later or check network connection")
        except ValueError as e:
            print(f"❌ Error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

    @log_operation
    def sell_currency(self):
        """Sell currency for USD."""
        if not self.current_portfolio:
            print("Portfolio not loaded")
            return
        
        print("\n=== SELL CURRENCY ===")
        user_currencies = [
            curr for curr in self.current_portfolio.wallets.keys()
            if curr != "USD" and self.current_portfolio.wallets[curr].balance > 0
        ]
        
        if not user_currencies:
            print("❌ You have no currencies to sell")
            return
        
        print("Your currencies available for sale:")
        for curr in user_currencies:
            wallet = self.current_portfolio.wallets[curr]
            balance = wallet.balance
            print(f" {curr}: {balance:.8f} ({wallet.currency.name})")
        
        currency = input("Enter currency code to sell: ").strip().upper()
        if currency not in user_currencies:
            print(f"❌ You don't have '{currency}' or balance is zero")
            return
        
        try:
            wallet = self.current_portfolio.get_wallet(currency)
            print(f"Your current {currency} balance: {wallet.balance:.8f}")
            
            amount = float(input(f"How much {currency} to sell: "))
            if amount <= 0:
                print("❌ Amount must be positive")
                return
            
            if amount > wallet.balance:
                print(
                    f"❌ Not enough {currency}. "
                    f"Available: {wallet.balance:.8f}"
                )
                return
            
            # Get rate through portfolio_manager
            rate_info = self.portfolio_manager.get_rate(currency, "USD")
            rate = rate_info['rate']
            price = rate  # Price in USD per currency unit
            total_revenue = amount * price
            
            print("\nOperation details:")
            print(f"Sale: {amount} {currency}")
            print(f"Rate: 1 {currency} = ${price:.6f} USD")
            print(f"Total revenue: ${total_revenue:.6f} USD")
            
            if not self._confirm_action("Confirm sale?"):
                print("❌ Operation cancelled")
                return
            
            # Execute sale through portfolio_manager
            self.portfolio_manager.sell_currency(
                self.current_user.user_id, currency, amount, price
            )
            
            # Refresh portfolio after operation
            self.current_portfolio = self.portfolio_manager.get_user_portfolio(
                self.current_user.user_id
            )
            print(
                f"✅ Successfully sold {amount} {currency} "
                f"for ${total_revenue:.6f} USD"
            )
            
        except InsufficientFundsError as e:
            print(f"❌ {e}")
        except CurrencyNotFoundError as e:
            print(f"❌ {e}")
            print("💡 Use 'Currency Info' command to see available currencies")
        except ApiRequestError as e:
            print(f"❌ {e}")
            print("💡 Please try again later or check network connection")
        except ValueError as e:
            print(f"❌ Error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

    def show_currency_info(self):
        """Show information about all available currencies."""
        print("\n=== CURRENCY INFORMATION ===")
        try:
            all_currencies = get_all_currencies()
            table = PrettyTable()
            table.field_names = ["Code", "Description"]
            
            for code, currency in all_currencies.items():
                table.add_row([code, currency.get_display_info()])
            
            print(table)
            
            try:
                rates = get_rates()
                if rates:
                    print("\n📈 CURRENT EXCHANGE RATES TO USD:")
                    rates_table = PrettyTable()
                    rates_table.field_names = ["Currency", "Rate to USD"]
                    
                    for code, rate in rates.items():
                        if code != "USD":
                            rates_table.add_row([code, f"${rate:.6f}"])
                    
                    print(rates_table)
            except ApiRequestError as e:
                print(f"\n⚠️ Exchange rates temporarily unavailable: {e}")
                
        except Exception as e:
            print(f"❌ Error loading currency information: {e}")

    def update_rates(self):
        """Update exchange rates manually."""
        print("\n=== UPDATE EXCHANGE RATES ===")
        print("Updating rates from external APIs...")
        
        try:
            updater = RatesUpdater()
            success = updater.run_update()
            
            if success:
                print("✅ Rates updated successfully!")
                print(f"   Sources: {updater.successful_sources}/2")
                print(f"   Total rates: {updater.total_rates}")
            else:
                print("❌ Rates update failed")
                print("💡 Check logs for details")
                
        except Exception as e:
            print(f"❌ Error updating rates: {e}")

    def show_current_rates(self):
        """Show current rates from cache."""
        print("\n=== CURRENT EXCHANGE RATES ===")
        try:
            storage = RatesStorage()
            rates_data = storage.read_current_rates()
            
            if rates_data and 'pairs' in rates_data:
                table = PrettyTable()
                table.field_names = ["Pair", "Rate", "Source", "Updated"]
                
                for pair, info in rates_data['pairs'].items():
                    table.add_row([
                        pair,
                        f"{info['rate']:.6f}",
                        info['source'],
                        info['updated_at'][:19]  # Show only date and time
                    ])
                
                print(table)
                print(f"Last refresh: {rates_data.get('last_refresh', 'Unknown')}")
            else:
                print("No rates data available. Use 'Update Exchange Rates' first.")
                
        except Exception as e:
            print(f"❌ Error loading rates: {e}")

    def _show_available_currencies(self):
        """Show available currencies in portfolio."""
        if self.current_portfolio.wallets:
            print(
                "Your currencies:",
                ", ".join(self.current_portfolio.wallets.keys())
            )
        else:
            print("You have no currencies in your portfolio yet")

    def portfolio_menu(self):
        """Portfolio management menu after login."""
        while True:
            print("\n=== PORTFOLIO MANAGEMENT ===")
            print("1. View Balance")
            print("2. Deposit Funds")
            print("3. Add Currency")
            print("4. Buy Currency")
            print("5. Sell Currency")
            print("6. Currency Information")
            print("7. Update Exchange Rates")
            print("8. Show Current Rates")
            print("9. Logout")
            
            try:
                choice = input("Select action (1-9): ").strip()
                
                if choice == "1":
                    self.display_balance()
                elif choice == "2":
                    self.deposit_funds()
                elif choice == "3":
                    self.add_currency()
                elif choice == "4":
                    self.buy_currency()
                elif choice == "5":
                    self.sell_currency()
                elif choice == "6":
                    self.show_currency_info()
                elif choice == "7":
                    self.update_rates()
                elif choice == "8":
                    self.show_current_rates()
                elif choice == "9":
                    self.current_user = None
                    self.current_portfolio = None
                    print("✅ Logout successful")
                    break
                else:
                    print("❌ Invalid choice")
                    
            except KeyboardInterrupt:
                print("\nReturning to main menu...")
                break
            except Exception as e:
                print(f"❌ An error occurred: {e}")

    def run(self):
        """Main application menu."""
        print("=" * 50)
        print(" CURRENCY WALLET APPLICATION")
        print("=" * 50)
        print("Project: finalproject_lisova_m25_555")
        
        while True:
            print("\n=== MAIN MENU ===")
            print("1. Create User")
            print("2. Login")
            print("3. Currency Information")
            print("4. Exit")
            
            try:
                choice = input("\nSelect command (1-4): ").strip()
                
                if choice == "1":
                    self.create_user()
                elif choice == "2":
                    if self.authenticate_user():
                        self.portfolio_menu()
                elif choice == "3":
                    self.show_currency_info()
                elif choice == "4":
                    print("👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid command. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n👋 Exiting application...")
                break
            except Exception as e:
                print(f"❌ An error occurred: {e}")


def main():
    """Application entry point."""
    cli = WalletCLI()
    cli.run()


if __name__ == "__main__":
    main()