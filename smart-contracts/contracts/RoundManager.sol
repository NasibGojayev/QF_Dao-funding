// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

contract RoundManager is Ownable {
    struct Round {
        uint256 id;
        uint256 startTime;
        uint256 endTime;
        string metaPtr;
    }

    uint256 private _currentRoundId;
    mapping(uint256 => Round) public rounds;

    event RoundCreated(uint256 indexed id, uint256 startTime, uint256 endTime);

    constructor(address initialOwner) Ownable(initialOwner) {}

    function createRound(uint256 startTime, uint256 endTime, string memory metaPtr) public onlyOwner returns (uint256) {
        require(endTime > startTime, "End time must be after start time");
        
        _currentRoundId++;
        uint256 newId = _currentRoundId;

        rounds[newId] = Round({
            id: newId,
            startTime: startTime,
            endTime: endTime,
            metaPtr: metaPtr
        });

        emit RoundCreated(newId, startTime, endTime);
        return newId;
    }

    function isRoundActive(uint256 roundId) public view returns (bool) {
        Round memory r = rounds[roundId];
        return block.timestamp >= r.startTime && block.timestamp <= r.endTime;
    }
}
