import os
from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class ParserConfig:
    """Configuration for Parser Service."""
    
    # API Key 
    EXCHANGERATE_API_KEY: str = field(default="46756b26226a3a722cc8c74f")
    
    # Endpoints
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"
    
    # Currency lists
    BASE_CURRENCY: str = "USD"
    FIAT_CURRENCIES: Tuple[str, ...] = ("EUR", "GBP", "RUB")
    CRYPTO_CURRENCIES: Tuple[str, ...] = ("BTC", "ETH", "SOL")
    
    # Use field with default_factory for mutable defaults
    CRYPTO_ID_MAP: Dict[str, str] = field(default_factory=lambda: {
        "BTC": "bitcoin",
        "ETH": "ethereum", 
        "SOL": "solana",
    })
    
    # File paths
    RATES_FILE_PATH: str = "data/rates.json"
    HISTORY_FILE_PATH: str = "data/exchange_rates.json"
    
    # Network parameters
    REQUEST_TIMEOUT: int = 10
    
    def __post_init__(self):
        """Initialize after dataclass creation."""
        # Load API key from environment if not set
        if not self.EXCHANGERATE_API_KEY:
            self.EXCHANGERATE_API_KEY = os.getenv("EXCHANGERATE_API_KEY", "")
        
        # DEBUG: Print if API key is loaded
        if self.EXCHANGERATE_API_KEY:
            print(f"DEBUG: API Key loaded: {self.EXCHANGERATE_API_KEY[:10]}...")


# Global configuration instance
config = ParserConfig()