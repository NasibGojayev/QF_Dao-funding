// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract DonationVault {
    struct Donation {
        uint256 proposalId;
        address donor;
        uint256 amount;
    }

    uint256 public donationCount;
    mapping(uint256 => Donation) public donations;
    mapping(uint256 => uint256) public proposalTotals;

    event Donated(uint256 indexed id, uint256 proposalId, address donor, uint256 amount);

    function donate(uint256 proposalId) external payable returns (uint256) {
        require(msg.value > 0, "Zero value");

        donationCount++;
        donations[donationCount] = Donation({
            proposalId: proposalId,
            donor: msg.sender,
            amount: msg.value
        });

        proposalTotals[proposalId] += msg.value;

        emit Donated(donationCount, proposalId, msg.sender, msg.value);
        return donationCount;
    }
}
