import logging
from datetime import datetime, timezone
from typing import Dict, Any

from .api_clients import CoinGeckoClient, ExchangeRateApiClient
from .storage import RatesStorage, create_historical_record
from .exceptions import ApiRequestError

logger = logging.getLogger(__name__)


class RatesUpdater:
    """Main coordinator for rates updating process."""
    
    def __init__(self):
        self.coingecko_client = CoinGeckoClient()
        self.exchangerate_client = ExchangeRateApiClient()
        self.storage = RatesStorage()
        
        self.successful_sources = 0
        self.total_rates = 0
    
    def run_update(self) -> bool:
        """Run complete rates update process."""
        logger.info("Starting rates update process...")
        
        all_rates = {}
        self.successful_sources = 0
        self.total_rates = 0
        
        try:
            # Fetch from CoinGecko
            crypto_rates = self._fetch_from_coingecko()
            if crypto_rates:
                all_rates.update(crypto_rates)
                self.successful_sources += 1
            
            # Fetch from ExchangeRate-API
            fiat_rates = self._fetch_from_exchangerate()
            if fiat_rates:
                all_rates.update(fiat_rates)
                self.successful_sources += 1
            
            if not all_rates:
                logger.error("No rates were fetched from any source")
                return False
            
            # Prepare and save data
            rates_data = self._prepare_rates_data(all_rates)
            self.storage.save_current_rates(rates_data)
            
            # Save historical records
            self._save_historical_records(all_rates)
            
            logger.info(
                f"Update completed successfully. "
                f"Rates: {self.total_rates}, Sources: {self.successful_sources}/2"
            )
            return True
            
        except Exception as e:
            logger.error(f"Rates update failed: {e}")
            return False
    
    def _fetch_from_coingecko(self) -> Dict[str, float]:
        """Fetch rates from CoinGecko with error handling."""
        try:
            rates = self.coingecko_client.fetch_rates()
            self.total_rates += len(rates)
            return rates
        except ApiRequestError as e:
            logger.error(f"Failed to fetch from CoinGecko: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error with CoinGecko: {e}")
            return {}
    
    def _fetch_from_exchangerate(self) -> Dict[str, float]:
        """Fetch rates from ExchangeRate-API with error handling."""
        try:
            rates = self.exchangerate_client.fetch_rates()
            self.total_rates += len(rates)
            return rates
        except ApiRequestError as e:
            logger.error(f"Failed to fetch from ExchangeRate-API: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error with ExchangeRate-API: {e}")
            return {}
    
    def _prepare_rates_data(self, all_rates: Dict[str, float]) -> Dict[str, Any]:
        """Prepare rates data for storage."""
        pairs = {}
        
        for pair_key, rate in all_rates.items():
            from_currency, to_currency = pair_key.split('_')
            pairs[pair_key] = {
                "rate": rate,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "source": "CoinGecko" if from_currency in [
                    c.upper() for c in self.coingecko_client.config.CRYPTO_CURRENCIES
                ] else "ExchangeRate-API"
            }
        
        return {
            "pairs": pairs,
            "last_refresh": datetime.now(timezone.utc).isoformat()
        }
    
    def _save_historical_records(self, all_rates: Dict[str, float]):
        """Save historical records for all rates."""
        for pair_key, rate in all_rates.items():
            from_currency, to_currency = pair_key.split('_')
            source = "CoinGecko" if from_currency in [
                c.upper() for c in self.coingecko_client.config.CRYPTO_CURRENCIES
            ] else "ExchangeRate-API"
            
            record = create_historical_record(
                from_currency=from_currency,
                to_currency=to_currency,
                rate=rate,
                source=source,
                meta={"raw_pair": pair_key}
            )
            
            try:
                self.storage.save_historical_record(record)
            except Exception as e:
                logger.warning(f"Failed to save historical record for {pair_key}: {e}")