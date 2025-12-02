// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract GrantRegistry {
    struct Proposal {
        uint256 id;
        address owner;
        string metadataURI;
        bool active;
    }

    uint256 public proposalCount;
    mapping(uint256 => Proposal) public proposals;

    event ProposalCreated(uint256 indexed id, address indexed owner, string metadataURI);
    event ProposalStatusChanged(uint256 indexed id, bool active);

    function createProposal(string calldata metadataURI) external returns (uint256) {
        proposalCount++;
        proposals[proposalCount] = Proposal({
            id: proposalCount,
            owner: msg.sender,
            metadataURI: metadataURI,
            active: true
        });

        emit ProposalCreated(proposalCount, msg.sender, metadataURI);
        return proposalCount;
    }

    function setProposalStatus(uint256 id, bool active) external {
        Proposal storage p = proposals[id];
        require(msg.sender == p.owner, "Not owner");
        p.active = active;
        emit ProposalStatusChanged(id, active);
    }
}
