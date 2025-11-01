import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, List
import logging
import tempfile

from .config import config

logger = logging.getLogger(__name__)


class RatesStorage:
    """Storage manager for rates data."""
    
    def __init__(self):
        self._ensure_data_directory()
    
    def _ensure_data_directory(self):
        """Ensure data directory exists."""
        os.makedirs(os.path.dirname(config.RATES_FILE_PATH), exist_ok=True)
        os.makedirs(os.path.dirname(config.HISTORY_FILE_PATH), exist_ok=True)
    
    def _atomic_write(self, file_path: str, data: Any):
        """Write data atomically using temporary file."""
        try:
            with tempfile.NamedTemporaryFile(
                mode='w', 
                encoding='utf-8',
                dir=os.path.dirname(file_path),
                delete=False
            ) as tmp_file:
                json.dump(data, tmp_file, indent=2, ensure_ascii=False)
                tmp_path = tmp_file.name
            
            os.replace(tmp_path, file_path)
            logger.debug(f"Successfully wrote data to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to write data to {file_path}: {e}")
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
    
    def save_current_rates(self, rates_data: Dict[str, Any]):
        """Save current rates snapshot to rates.json."""
        try:
            self._atomic_write(config.RATES_FILE_PATH, rates_data)
            logger.info(f"Saved {len(rates_data.get('pairs', {}))} rates to {config.RATES_FILE_PATH}")
        except Exception as e:
            logger.error(f"Failed to save current rates: {e}")
            raise
    
    def save_historical_record(self, record: Dict[str, Any]):
        """Save historical record to exchange_rates.json."""
        try:
            # Load existing history
            history = self._load_history()
            
            # Add new record
            history.append(record)
            
            # Save updated history
            self._atomic_write(config.HISTORY_FILE_PATH, history)
            logger.debug(f"Added historical record {record.get('id')}")
            
        except Exception as e:
            logger.error(f"Failed to save historical record: {e}")
            raise
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load historical data from file."""
        if not os.path.exists(config.HISTORY_FILE_PATH):
            return []
        
        try:
            with open(config.HISTORY_FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to load history file, creating new: {e}")
            return []
    
    def read_current_rates(self) -> Dict[str, Any]:
        """Read current rates from cache file."""
        if not os.path.exists(config.RATES_FILE_PATH):
            return {}
        
        try:
            with open(config.RATES_FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to read rates file: {e}")
            return {}


def create_historical_record(
    from_currency: str,
    to_currency: str, 
    rate: float,
    source: str,
    meta: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Create a historical record entry."""
    timestamp = datetime.now(timezone.utc)
    record_id = f"{from_currency}_{to_currency}_{timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    
    return {
        "id": record_id,
        "from_currency": from_currency.upper(),
        "to_currency": to_currency.upper(),
        "rate": rate,
        "timestamp": timestamp.isoformat(),
        "source": source,
        "meta": meta or {}
    }