// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./GovernanceToken.sol";

contract GovernanceTokenTest {
    GovernanceToken token;

    function setUp() public {
        token = new GovernanceToken();
    }

    function testInitialSupply() public {
        uint256 supply = token.totalSupply();
        require(supply == 1_000_000 ether, "Wrong supply");
        require(token.balanceOf(address(this)) == supply, "Wrong owner balance");
    }
}
