// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./MatchingPool.sol";

contract MatchingPoolTest {
    MatchingPool pool;

    function setUp() public {
        pool = new MatchingPool();
    }

    function testFund() public {
        pool.fund{value: 5 ether}();
        require(pool.poolBalance() == 5 ether, "Wrong balance");
    }

    function testDistribute() public {
        pool.fund{value: 3 ether}();

        uint256 before = address(this).balance;
        pool.distribute(payable(address(this)), 1, 2 ether);

        require(address(this).balance == before + 2 ether, "Wrong payout");
        require(pool.poolBalance() == 1 ether, "Pool incorrect");
    }

    receive() external payable {}
}
