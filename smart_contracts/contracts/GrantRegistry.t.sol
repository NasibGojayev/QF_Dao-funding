// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./GrantRegistry.sol";

contract GrantRegistryTest {
    GrantRegistry registry;

    function setUp() public {
        registry = new GrantRegistry();
    }

    function testCreateProposal() public {
        uint256 id = registry.createProposal("ipfs://example");

        require(id == 1, "ID mismatch");
        (uint256 pid, address owner, , bool active) = registry.proposals(1);

        require(pid == 1, "Wrong id");
        require(owner == address(this), "Wrong owner");
        require(active == true, "Should be active");
    }
}
