// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract MatchingPool is Ownable {
    event FundsDistributed(uint256 indexed roundId, address indexed recipient, uint256 amount);

    constructor(address initialOwner) Ownable(initialOwner) {}

    function allocateFunds(uint256 roundId, address token, address[] memory recipients, uint256[] memory amounts) public onlyOwner {
        require(recipients.length == amounts.length, "Arrays length mismatch");
        
        for (uint256 i = 0; i < recipients.length; i++) {
            // In a real scenario, this might interact with the vault or hold funds itself
            // taking funds from this contract
            if (amounts[i] > 0) {
                 IERC20(token).transfer(recipients[i], amounts[i]);
                 emit FundsDistributed(roundId, recipients[i], amounts[i]);
            }
        }
    }
}
