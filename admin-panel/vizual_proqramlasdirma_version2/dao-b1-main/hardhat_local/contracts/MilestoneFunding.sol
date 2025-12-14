// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

contract MilestoneFunding {
    address public owner;
    uint256 public projectCount;

    struct Project {
        address creator;
        string title;
        uint256 balance;
    }

    mapping(uint256 => Project) public projects;

    event ProjectCreated(uint256 indexed projectId, address indexed creator, string title);
    event TransactionCreated(uint256 indexed projectId, address indexed from, uint256 amount, string note);
    event MilestoneResolved(uint256 indexed projectId, uint256 indexed milestoneId, address resolver);
    event TagAssigned(uint256 indexed projectId, uint256 indexed tagId, string tag);

    modifier onlyOwner() {
        require(msg.sender == owner, "only owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function createProject(string calldata title) external returns (uint256) {
        projectCount += 1;
        projects[projectCount] = Project({creator: msg.sender, title: title, balance: 0});
        emit ProjectCreated(projectCount, msg.sender, title);
        return projectCount;
    }

    function contribute(uint256 projectId, string calldata note) external payable {
        require(projectId > 0 && projectId <= projectCount, "invalid project");
        require(msg.value > 0, "zero amount");
        projects[projectId].balance += msg.value;
        emit TransactionCreated(projectId, msg.sender, msg.value, note);
    }

    function resolveMilestone(uint256 projectId, uint256 milestoneId) external onlyOwner {
        emit MilestoneResolved(projectId, milestoneId, msg.sender);
    }

    function assignTag(uint256 projectId, uint256 tagId, string calldata tag) external onlyOwner {
        emit TagAssigned(projectId, tagId, tag);
    }

    function withdraw(uint256 projectId) external {
        Project storage p = projects[projectId];
        require(msg.sender == p.creator, "not creator");
        uint256 amount = p.balance;
        require(amount > 0, "no funds");
        p.balance = 0;
        payable(msg.sender).transfer(amount);
    }
}
