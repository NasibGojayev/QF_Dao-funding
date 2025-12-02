from web3 import Web3
from config import NODE_URL

w3 = Web3(Web3.HTTPProvider(NODE_URL))

def get_contract_events(contract, event_name, from_block, to_block):
    return contract.events[event_name].get_logs(from_block=from_block, to_block=to_block)

def create_event_filter(contract, event_name, from_block=0):
    return contract.events[event_name].create_filter(from_block=from_block)
