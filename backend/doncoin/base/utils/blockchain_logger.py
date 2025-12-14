"""
Blockchain Logger Utility
Provides structured logging for all Web3/blockchain interactions.
"""
import logging
import json
import time
from functools import wraps
from typing import Any, Dict, Optional

# Get the dedicated blockchain logger from Django settings
logger = logging.getLogger('blockchain')


class BlockchainLogger:
    """
    Logger for all blockchain/smart contract interactions.
    Logs Web3 calls, contract methods, and transaction details.
    """
    
    @staticmethod
    def log_web3_call(method: str, params: Optional[Dict] = None, result: Any = None, 
                      duration_ms: float = 0, error: Optional[str] = None):
        """Log a Web3 RPC call"""
        log_data = {
            "type": "WEB3_CALL",
            "method": method,
            "params": params or {},
            "duration_ms": round(duration_ms, 2),
        }
        
        if error:
            log_data["error"] = str(error)
            logger.error(f"Web3 call failed: {method} | {json.dumps(log_data)}")
        else:
            log_data["result_preview"] = str(result)[:200] if result else None
            logger.info(f"Web3 call: {method} | {json.dumps(log_data)}")
    
    @staticmethod
    def log_contract_call(contract_name: str, method: str, args: tuple = (), 
                          tx_hash: Optional[str] = None, duration_ms: float = 0,
                          error: Optional[str] = None):
        """Log a smart contract method call"""
        log_data = {
            "type": "CONTRACT_CALL",
            "contract": contract_name,
            "method": method,
            "args": [str(a)[:100] for a in args],  # Truncate long args
            "duration_ms": round(duration_ms, 2),
        }
        
        if tx_hash:
            log_data["tx_hash"] = tx_hash
            
        if error:
            log_data["error"] = str(error)
            logger.error(f"Contract call failed: {contract_name}.{method} | {json.dumps(log_data)}")
        else:
            logger.info(f"Contract call: {contract_name}.{method} | {json.dumps(log_data)}")
    
    @staticmethod
    def log_event(contract_name: str, event_name: str, event_data: Dict,
                  block_number: int, tx_hash: str):
        """Log a blockchain event detection"""
        log_data = {
            "type": "EVENT",
            "contract": contract_name,
            "event": event_name,
            "block": block_number,
            "tx_hash": tx_hash,
            "data": {k: str(v)[:100] for k, v in event_data.items()},  # Truncate
        }
        logger.info(f"Event detected: {contract_name}.{event_name} at block {block_number} | {json.dumps(log_data)}")
    
    @staticmethod
    def log_transaction(tx_hash: str, from_addr: str, to_addr: str, 
                        value: str, status: str = "pending"):
        """Log a blockchain transaction"""
        log_data = {
            "type": "TRANSACTION",
            "tx_hash": tx_hash,
            "from": from_addr,
            "to": to_addr,
            "value": value,
            "status": status,
        }
        logger.info(f"Transaction {status}: {tx_hash[:16]}... | {json.dumps(log_data)}")
    
    @staticmethod
    def log_indexer_event(action: str, details: Dict, duration_ms: float = 0):
        """Log indexer-specific events"""
        log_data = {
            "type": "INDEXER",
            "action": action,
            "details": details,
            "duration_ms": round(duration_ms, 2),
        }
        logger.info(f"Indexer: {action} | {json.dumps(log_data)}")


def log_blockchain_call(func):
    """Decorator to automatically log blockchain function calls"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            duration = (time.time() - start) * 1000
            BlockchainLogger.log_web3_call(
                method=func.__name__,
                params={"args": str(args)[:200], "kwargs": str(kwargs)[:200]},
                result=result,
                duration_ms=duration
            )
            return result
        except Exception as e:
            duration = (time.time() - start) * 1000
            BlockchainLogger.log_web3_call(
                method=func.__name__,
                params={"args": str(args)[:200], "kwargs": str(kwargs)[:200]},
                duration_ms=duration,
                error=str(e)
            )
            raise
    return wrapper


# Singleton instance for easy import
blockchain_logger = BlockchainLogger()
