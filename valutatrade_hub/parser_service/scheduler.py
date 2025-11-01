import time
import threading
import logging
from typing import Optional

from .updater import RatesUpdater

logger = logging.getLogger(__name__)


class RatesScheduler:
    """Scheduler for periodic rates updates."""
    
    def __init__(self, interval_minutes: int = 30):
        self.interval = interval_minutes * 60  # Convert to seconds
        self.updater = RatesUpdater()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start the scheduler in a background thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("Scheduler is already running")
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(f"Scheduler started with {self.interval // 60} minute interval")
    
    def stop(self):
        """Stop the scheduler."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Scheduler stopped")
    
    def _run(self):
        """Main scheduler loop."""
        while not self._stop_event.is_set():
            try:
                logger.info("Scheduled rates update started...")
                success = self.updater.run_update()
                
                if success:
                    logger.info("Scheduled update completed successfully")
                else:
                    logger.warning("Scheduled update completed with errors")
                    
            except Exception as e:
                logger.error(f"Scheduled update failed: {e}")
            
            # Wait for interval or stop event
            wait_time = 0
            while wait_time < self.interval and not self._stop_event.is_set():
                time.sleep(1)
                wait_time += 1
    
    def run_once(self) -> bool:
        """Run update once (synchronous)."""
        try:
            return self.updater.run_update()
        except Exception as e:
            logger.error(f"One-time update failed: {e}")
            return False