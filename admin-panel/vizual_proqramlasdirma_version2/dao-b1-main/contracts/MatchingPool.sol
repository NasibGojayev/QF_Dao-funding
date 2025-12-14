// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title MatchingPool
 * @notice Implements Quadratic Funding (QF) matching distribution
 * @dev Uses the formula: match = (√c₁ + √c₂ + ... + √cₙ)² - Σcᵢ
 */
contract MatchingPool is Ownable {
    // Pool balances per round
    mapping(uint256 => uint256) public poolBalances;
    
    // Track contributions: roundId => projectId => donor => amount
    mapping(uint256 => mapping(uint256 => mapping(address => uint256))) public contributions;
    
    // Track unique donors per project per round
    mapping(uint256 => mapping(uint256 => address[])) private projectDonors;
    
    // Track if donor already contributed (for efficient donor list management)
    mapping(uint256 => mapping(uint256 => mapping(address => bool))) private hasDonated;

    event Funded(uint256 indexed poolId, address indexed from, uint256 amount);
    event ContributionRecorded(uint256 indexed roundId, uint256 indexed projectId, address indexed donor, uint256 amount);
    event MatchingDistributed(uint256 indexed roundId, uint256 indexed projectId, uint256 matchAmount);

    constructor() Ownable() {}

    /// @notice Fund the matching pool for a specific round
    function fundPool(uint256 poolId) external payable {
        require(msg.value > 0, "Must send ETH");
        poolBalances[poolId] += msg.value;
        emit Funded(poolId, msg.sender, msg.value);
    }

    /// @notice Record a contribution for QF calculation
    /// @dev This should be called by the DonationVault or integrated donation system
    function recordContribution(uint256 roundId, uint256 projectId, address donor, uint256 amount) external {
        require(amount > 0, "Amount must be positive");
        
        // Track if this is a new donor for this project
        if (!hasDonated[roundId][projectId][donor]) {
            projectDonors[roundId][projectId].push(donor);
            hasDonated[roundId][projectId][donor] = true;
        }
        
        contributions[roundId][projectId][donor] += amount;
        emit ContributionRecorded(roundId, projectId, donor, amount);
    }

    /// @notice Calculate quadratic funding match for a project
    /// @dev Uses integer square root approximation (Babylonian method)
    /// @param roundId The funding round ID
    /// @param projectId The project ID
    /// @return The calculated match amount
    function calculateMatching(uint256 roundId, uint256 projectId) public view returns (uint256) {
        address[] memory donors = projectDonors[roundId][projectId];
        if (donors.length == 0) return 0;

        uint256 sumOfSqrts = 0;
        uint256 totalContributions = 0;

        // Calculate sum of square roots and total contributions
        for (uint256 i = 0; i < donors.length; i++) {
            address donor = donors[i];
            uint256 contribution = contributions[roundId][projectId][donor];
            
            if (contribution > 0) {
                sumOfSqrts += sqrt(contribution);
                totalContributions += contribution;
            }
        }

        // QF formula: (sum of square roots)² - total contributions
        uint256 sumOfSqrtsSquared = sumOfSqrts * sumOfSqrts;
        
        // Match amount is the difference (this is what gets matched from the pool)
        if (sumOfSqrtsSquared > totalContributions) {
            return sumOfSqrtsSquared - totalContributions;
        }
        
        return 0;
    }

    /// @notice Distribute matching funds to a project (admin only)
    /// @dev In production, this would be called by governance or automated distribution
    /// @param roundId The funding round ID
    /// @param projectId The project ID
    /// @param recipient The address to receive the matching funds
    function distributeMatching(uint256 roundId, uint256 projectId, address payable recipient) external onlyOwner {
        uint256 matchAmount = calculateMatching(roundId, projectId);
        require(matchAmount > 0, "No matching funds calculated");
        require(poolBalances[roundId] >= matchAmount, "Insufficient pool balance");
        
        poolBalances[roundId] -= matchAmount;
        
        (bool success, ) = recipient.call{value: matchAmount}("");
        require(success, "Transfer failed");
        
        emit MatchingDistributed(roundId, projectId, matchAmount);
    }

    /// @notice Get the number of unique donors for a project in a round
    function getDonorCount(uint256 roundId, uint256 projectId) external view returns (uint256) {
        return projectDonors[roundId][projectId].length;
    }

    /// @notice Get all donors for a project in a round
    function getDonors(uint256 roundId, uint256 projectId) external view returns (address[] memory) {
        return projectDonors[roundId][projectId];
    }

    /// @notice Integer square root using Babylonian method
    /// @dev Good enough approximation for QF calculations
    function sqrt(uint256 x) internal pure returns (uint256) {
        if (x == 0) return 0;
        
        // Initial guess
        uint256 z = (x + 1) / 2;
        uint256 y = x;
        
        // Iterate until convergence
        while (z < y) {
            y = z;
            z = (x / z + z) / 2;
        }
        
        return y;
    }

    /// @notice Allow contract to receive ETH
    receive() external payable {
        // Direct ETH sends go to pool 0 by default
        poolBalances[0] += msg.value;
        emit Funded(0, msg.sender, msg.value);
    }
}
