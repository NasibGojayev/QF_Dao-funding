// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract MatchingPool {
    uint256 public poolBalance;

    event Funded(address indexed from, uint256 amount);
    event Distributed(uint256 proposalId, uint256 amount);

    function fund() external payable {
        require(msg.value > 0, "Zero value");
        poolBalance += msg.value;
        emit Funded(msg.sender, msg.value);
    }

    function distribute(address payable to, uint256 proposalId, uint256 amount) external {
        require(amount <= poolBalance, "Not enough pool balance");

        poolBalance -= amount;
        to.transfer(amount);

        emit Distributed(proposalId, amount);
    }
}
