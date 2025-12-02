def map_proposal_event(log):
    """Transform ProposalCreated event log into database record format"""
    return {
        "tx_hash": log["transactionHash"].hex(),
        "block_number": log["blockNumber"],
        "proposal_id": log["args"]["id"],
        "owner": log["args"]["owner"],
        "metadata_uri": log["args"]["metadataURI"],
        "active": 1  # New proposals are active by default
    }

