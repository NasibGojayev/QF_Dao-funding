from extractor import get_contract_events
from transformer import map_proposal_event
from loader import save_proposal_event
from logger import setup_logger

logger = setup_logger(__name__)

def run_backfill(contract, event_name, start_block, end_block, batch_size):
    """Backfill historical events from the blockchain"""
    logger.info(f"Starting backfill for {event_name} from block {start_block} to {end_block}")
    total_events = 0
    
    for i in range(start_block, end_block + 1, batch_size):
        batch_end = min(i + batch_size - 1, end_block)
        logger.info(f"Processing blocks {i} to {batch_end}")
        
        logs = get_contract_events(contract, event_name, i, batch_end)
        logger.info(f"Found {len(logs)} events in this batch")
        
        for log in logs:
            save_proposal_event(map_proposal_event(log))
            total_events += 1
    
    logger.info(f"Backfill complete. Processed {total_events} total events")

