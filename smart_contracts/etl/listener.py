import time
from extractor import create_event_filter
from transformer import map_proposal_event
from loader import save_proposal_event
from logger import setup_logger

logger = setup_logger(__name__)

def run_listener(contract, event_name, poll_interval):
    """Listen for new events in real-time"""
    logger.info(f"Starting listener for {event_name} with {poll_interval}s poll interval")
    event_filter = create_event_filter(contract, event_name)
    
    while True:
        try:
            new_events = event_filter.get_new_entries()
            if new_events:
                logger.info(f"Found {len(new_events)} new events")
                for event in new_events:
                    save_proposal_event(map_proposal_event(event))
            time.sleep(poll_interval)
        except KeyboardInterrupt:
            logger.info("Listener stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in listener: {e}")
            time.sleep(poll_interval)

