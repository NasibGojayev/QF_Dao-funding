// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract DonationVault is Ownable {
    event DonationReceived(address indexed donor, address indexed token, uint256 amount, uint256 roundId, uint256 grantId);
    event FundsWithdrawn(address indexed recipient, address indexed token, uint256 amount);

    constructor(address initialOwner) Ownable(initialOwner) {}

    function deposit(address token, uint256 amount, uint256 roundId, uint256 grantId) public {
        require(amount > 0, "Amount must be > 0");
        IERC20(token).transferFrom(msg.sender, address(this), amount);
        emit DonationReceived(msg.sender, token, amount, roundId, grantId);
    }

    function withdraw(address token, address recipient, uint256 amount) public onlyOwner {
        require(amount > 0, "Amount must be > 0");
        require(IERC20(token).balanceOf(address(this)) >= amount, "Insufficient balance");
        IERC20(token).transfer(recipient, amount);
        emit FundsWithdrawn(recipient, token, amount);
    }
}
