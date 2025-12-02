// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract RoundManager {
    struct Round {
        uint256 id;
        uint256 start;
        uint256 end;
        bool finalized;
    }

    uint256 public roundCount;
    mapping(uint256 => Round) public rounds;

    event RoundCreated(uint256 indexed id, uint256 start, uint256 end);
    event RoundFinalized(uint256 indexed id);

    function createRound(uint256 start, uint256 end) external returns (uint256) {
        require(start < end, "Invalid timestamps");

        roundCount++;
        rounds[roundCount] = Round({
            id: roundCount,
            start: start,
            end: end,
            finalized: false
        });

        emit RoundCreated(roundCount, start, end);
        return roundCount;
    }

    function finalizeRound(uint256 id) external {
        Round storage r = rounds[id];
        require(block.timestamp > r.end, "Round not ended");
        require(!r.finalized, "Already finalized");

        r.finalized = true;

        emit RoundFinalized(id);
    }
}
