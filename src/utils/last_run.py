"""Last run tracking utilities"""
import os
from datetime import datetime, timedelta
import pytz
import logging
from ..config import config

logger = logging.getLogger(__name__)

def ensure_data_dir():
    """Ensure data directory exists"""
    os.makedirs(config.PATHS["data_dir"], exist_ok=True)

def get_last_run_date() -> datetime:
    """Get the date of the last digest run"""
    ensure_data_dir()
    current_time = datetime.now(pytz.UTC)
    
    try:
        if os.path.exists(config.PATHS["last_run_file"]):
            with open(config.PATHS["last_run_file"], 'r') as f:
                last_run = datetime.fromisoformat(f.read().strip())
                logger.info(f"Last run was at: {last_run}")
                return last_run
    except Exception as e:
        logger.warning(f"Error reading last run date: {e}")
    
    # Default to 1 day ago if no valid date found
    default_date = current_time - timedelta(days=config.ARXIV_CONFIG["default_lookback_days"])
    logger.info(f"Using default date: {default_date}")
    return default_date

def save_last_run_date():
    """Save the current time as last run"""
    ensure_data_dir()
    try:
        current_time = datetime.now(pytz.UTC)
        with open(config.PATHS["last_run_file"], 'w') as f:
            f.write(current_time.isoformat())
        logger.info(f"Saved current run date: {current_time}")
    except Exception as e:
        logger.error(f"Error saving last run date: {e}") 