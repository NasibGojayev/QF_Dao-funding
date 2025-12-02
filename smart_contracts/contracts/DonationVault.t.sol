// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./DonationVault.sol";

contract DonationVaultTest {
    DonationVault vault;

    function setUp() public {
        vault = new DonationVault();
    }

    function testDonate() public {
        uint256 before = address(vault).balance;

        vault.donate{value: 1 ether}(10);
        require(address(vault).balance == before + 1 ether, "Balance incorrect");

        (uint256 pid, address donor, uint256 amount) = vault.donations(1);
        require(pid == 10, "Wrong proposal id");
        require(donor == address(this), "Wrong donor");
        require(amount == 1 ether, "Wrong amount");
    }
}
