// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

contract GrantRegistry is Ownable {
    struct Grant {
        uint256 id;
        address owner;
        string metadata; // IPFS hash or similar
        bool active;
    }

    uint256 private _currentGrantId;
    mapping(uint256 => Grant) public grants;

    event GrantCreated(uint256 indexed id, address indexed owner, string metadata);
    event GrantUpdated(uint256 indexed id, string metadata);
    event GrantStatusChanged(uint256 indexed id, bool active);

    constructor(address initialOwner) Ownable(initialOwner) {}

    function createGrant(string memory metadata) public returns (uint256) {
        _currentGrantId++;
        uint256 newId = _currentGrantId;
        
        grants[newId] = Grant({
            id: newId,
            owner: msg.sender,
            metadata: metadata,
            active: true
        });

        emit GrantCreated(newId, msg.sender, metadata);
        return newId;
    }

    function updateGrant(uint256 id, string memory metadata) public {
        require(grants[id].owner == msg.sender, "Not grant owner");
        grants[id].metadata = metadata;
        emit GrantUpdated(id, metadata);
    }

    function setGrantStatus(uint256 id, bool active) public {
        require(grants[id].owner == msg.sender || owner() == msg.sender, "Not authorized");
        grants[id].active = active;
        emit GrantStatusChanged(id, active);
    }
    
    function getGrant(uint256 id) public view returns (Grant memory) {
        return grants[id];
    }
}
