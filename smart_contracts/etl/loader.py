from db import Session, ProposalEvent
from logger import setup_logger

logger = setup_logger(__name__)

def save_proposal_event(event_data):
    """Save proposal event to database with duplicate checking"""
    session = Session()
    try:
        # Check for duplicates
        existing = session.query(ProposalEvent).filter_by(tx_hash=event_data["tx_hash"]).first()
        if existing:
            logger.debug(f"Event already exists: {event_data['tx_hash']}")
            return
        
        # Create and save new record
        record = ProposalEvent(**event_data)
        session.add(record)
        session.commit()
        logger.info(f"Saved proposal {event_data['proposal_id']} from tx {event_data['tx_hash']}")
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving event: {e}")
        raise
    finally:
        session.close()

def save_proposal_events_batch(events_data):
    """Save multiple proposal events in a single transaction"""
    session = Session()
    try:
        saved_count = 0
        for event_data in events_data:
            # Check for duplicates
            if session.query(ProposalEvent).filter_by(tx_hash=event_data["tx_hash"]).first():
                continue
            
            record = ProposalEvent(**event_data)
            session.add(record)
            saved_count += 1
        
        session.commit()
        logger.info(f"Batch saved {saved_count} proposal events")
        return saved_count
    except Exception as e:
        session.rollback()
        logger.error(f"Error in batch save: {e}")
        raise
    finally:
        session.close()

