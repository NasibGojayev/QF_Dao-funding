// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./RoundManager.sol";

contract RoundManagerTest {
    RoundManager rm;

    function setUp() public {
        rm = new RoundManager();
    }

    function testCreateRound() public {
        uint256 id = rm.createRound(100, 200);
        require(id == 1, "Wrong ID");

        (, uint256 s, uint256 e, bool f) = rm.rounds(1);
        require(s == 100, "Wrong start");
        require(e == 200, "Wrong end");
        require(f == false, "Should not be finalized");
    }
}
