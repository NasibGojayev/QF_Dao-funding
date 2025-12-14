// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract DonationVault {
    // Track ETH donations per project id
    mapping(uint256 => uint256) public projectBalances;
    
    // Track project owners for access control
    mapping(uint256 => address) public projectOwners;

    event Donated(uint256 indexed projectId, address indexed donor, uint256 amount);
    event Withdrawn(uint256 indexed projectId, address indexed to, uint256 amount);
    event ProjectOwnerSet(uint256 indexed projectId, address indexed owner);

    receive() external payable {}

    /// @notice Set the owner of a project (should be called by GrantRegistry or governance)
    /// @dev In production, this should be restricted to a trusted contract/role
    function setProjectOwner(uint256 projectId, address owner) external {
        require(projectOwners[projectId] == address(0), "Owner already set");
        require(owner != address(0), "Invalid owner address");
        projectOwners[projectId] = owner;
        emit ProjectOwnerSet(projectId, owner);
    }

    function donate(uint256 projectId) external payable {
        require(msg.value > 0, "Must send ETH");
        projectBalances[projectId] += msg.value;
        emit Donated(projectId, msg.sender, msg.value);
    }

    /// @notice Withdraw funds - restricted to project owner only
    function withdraw(uint256 projectId, address payable to, uint256 amount) external {
        require(msg.sender == projectOwners[projectId], "Only project owner can withdraw");
        require(projectBalances[projectId] >= amount, "Insufficient balance");
        projectBalances[projectId] -= amount;
        to.transfer(amount);
        emit Withdrawn(projectId, to, amount);
    }
}
