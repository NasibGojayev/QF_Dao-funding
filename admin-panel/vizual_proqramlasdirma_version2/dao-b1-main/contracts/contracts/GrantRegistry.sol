// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract GrantRegistry {
    struct Project {
        address owner;
        string metadataURI;
        bool exists;
    }

    mapping(uint256 => Project) public projects;
    uint256 public nextId;

    event ProjectRegistered(uint256 indexed projectId, address owner, string metadataURI);

    function registerProject(string calldata metadataURI) external returns (uint256) {
        uint256 id = nextId++;
        projects[id] = Project({owner: msg.sender, metadataURI: metadataURI, exists: true});
        emit ProjectRegistered(id, msg.sender, metadataURI);
        return id;
    }

    function getProject(uint256 id) external view returns (address, string memory) {
        require(projects[id].exists, "Project not found");
        Project storage p = projects[id];
        return (p.owner, p.metadataURI);
    }
}
