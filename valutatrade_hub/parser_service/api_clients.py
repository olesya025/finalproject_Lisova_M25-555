import requests
from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

from .config import config
from .exceptions import ApiRequestError

logger = logging.getLogger(__name__)


class BaseApiClient(ABC):
    """Abstract base class for API clients."""
    
    def __init__(self):
        self.config = config
    
    @abstractmethod
    def fetch_rates(self) -> Dict[str, float]:
        """Fetch rates from API and return standardized format."""
        pass
    
    def _make_request(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make HTTP request with error handling."""
        try:
            response = requests.get(
                url, 
                params=params, 
                timeout=self.config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise ApiRequestError(self.__class__.__name__, str(e))


class CoinGeckoClient(BaseApiClient):
    """Client for CoinGecko API."""
    
    def fetch_rates(self) -> Dict[str, float]:
        """Fetch cryptocurrency rates from CoinGecko."""
        logger.info("Fetching rates from CoinGecko...")
        
        # Prepare cryptocurrency IDs
        crypto_ids = [
            self.config.CRYPTO_ID_MAP[code] 
            for code in self.config.CRYPTO_CURRENCIES 
            if code in self.config.CRYPTO_ID_MAP
        ]
        
        if not crypto_ids:
            logger.warning("No valid cryptocurrency codes configured")
            return {}
        
        params = {
            'ids': ','.join(crypto_ids),
            'vs_currencies': 'usd'
        }
        
        try:
            data = self._make_request(self.config.COINGECKO_URL, params)
            return self._parse_response(data)
        except ApiRequestError as e:
            logger.error(f"CoinGecko API error: {e}")
            raise
    
    def _parse_response(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Parse CoinGecko response into standardized format."""
        rates = {}
        
        for crypto_code, gecko_id in self.config.CRYPTO_ID_MAP.items():
            if gecko_id in data and 'usd' in data[gecko_id]:
                rate = data[gecko_id]['usd']
                pair_key = f"{crypto_code}_{self.config.BASE_CURRENCY}"
                rates[pair_key] = float(rate)
                logger.debug(f"Parsed {pair_key}: {rate}")
        
        logger.info(f"Fetched {len(rates)} crypto rates from CoinGecko")
        return rates


class ExchangeRateApiClient(BaseApiClient):
    """Client for ExchangeRate-API."""
    
    def fetch_rates(self) -> Dict[str, float]:
        """Fetch fiat currency rates from ExchangeRate-API with fallback."""
        logger.info("Fetching rates from ExchangeRate-API...")
        
        if not self.config.EXCHANGERATE_API_KEY:
            logger.error("ExchangeRate-API key not configured")
            return self._get_fallback_rates()
        
        url = f"{self.config.EXCHANGERATE_API_URL}/{self.config.EXCHANGERATE_API_KEY}/latest/{self.config.BASE_CURRENCY}"
        
        try:
            data = self._make_request(url)
            
            # Check if we got valid rates
            rates_data = data.get('conversion_rates', {})
            if not rates_data:
                logger.warning("ExchangeRate-API returned empty rates, using fallback")
                return self._get_fallback_rates()
                
            return self._parse_response(data)
            
        except ApiRequestError as e:
            logger.error(f"ExchangeRate-API error: {e}, using fallback rates")
            return self._get_fallback_rates()
        except Exception as e:
            logger.error(f"Unexpected error with ExchangeRate-API: {e}, using fallback")
            return self._get_fallback_rates()
    
    def _parse_response(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Parse ExchangeRate-API response into standardized format."""
        if data.get('result') != 'success':
            error_msg = data.get('error-type', 'Unknown API error')
            logger.warning(f"ExchangeRate-API error: {error_msg}")
            return self._get_fallback_rates()
        
        rates = {}
        base_rates = data.get('conversion_rates', {})
        
        logger.debug(f"Found {len(base_rates)} rates in API response")
        
        for currency in self.config.FIAT_CURRENCIES:
            if currency in base_rates:
                rate = base_rates[currency]
                pair_key = f"{currency}_{self.config.BASE_CURRENCY}"
                rates[pair_key] = float(rate)
                logger.debug(f"Parsed {pair_key}: {rate}")
            else:
                logger.warning(f"Currency {currency} not found in API response")
        
        logger.info(f"Fetched {len(rates)} fiat rates from ExchangeRate-API")
        return rates
    
    def _get_fallback_rates(self) -> Dict[str, float]:
        """Provide fallback rates when API fails."""
        logger.info("Using fallback fiat rates")
        
        # Static fallback rates (примерные курсы)
        fallback_rates = {
            "EUR_USD": 0.93,    # 1 EUR = 0.93 USD
            "GBP_USD": 0.79,    # 1 GBP = 0.79 USD  
            "RUB_USD": 0.011,   # 1 RUB = 0.011 USD
        }
        
        rates = {}
        for currency in self.config.FIAT_CURRENCIES:
            pair_key = f"{currency}_{self.config.BASE_CURRENCY}"
            if pair_key in fallback_rates:
                rates[pair_key] = fallback_rates[pair_key]
                logger.debug(f"Using fallback rate for {pair_key}: {fallback_rates[pair_key]}")
        
        return rates