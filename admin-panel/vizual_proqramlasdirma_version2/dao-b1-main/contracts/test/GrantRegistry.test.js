const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("GrantRegistry", function () {
    let grantRegistry;
    let owner;
    let projectOwner1;
    let projectOwner2;
    let addrs;

    beforeEach(async function () {
        [owner, projectOwner1, projectOwner2, ...addrs] = await ethers.getSigners();

        const GrantRegistry = await ethers.getContractFactory("GrantRegistry");
        grantRegistry = await GrantRegistry.deploy();
        await grantRegistry.waitForDeployment();
    });

    describe("Deployment", function () {
        it("Should initialize with nextId as 0", async function () {
            expect(await grantRegistry.nextId()).to.equal(0);
        });
    });

    describe("Project Registration", function () {
        it("Should register a project", async function () {
            const metadataURI = "ipfs://QmTest123";
            await grantRegistry.connect(projectOwner1).registerProject(metadataURI);

            const [owner, uri] = await grantRegistry.getProject(0);
            expect(owner).to.equal(projectOwner1.address);
            expect(uri).to.equal(metadataURI);
        });

        it("Should increment project ID", async function () {
            await grantRegistry.connect(projectOwner1).registerProject("ipfs://QmTest1");
            expect(await grantRegistry.nextId()).to.equal(1);

            await grantRegistry.connect(projectOwner2).registerProject("ipfs://QmTest2");
            expect(await grantRegistry.nextId()).to.equal(2);
        });

        it("Should return correct project ID", async function () {
            const tx = await grantRegistry.connect(projectOwner1).registerProject("ipfs://QmTest1");
            const receipt = await tx.wait();

            // Find the ProjectRegistered event
            const event = receipt.logs.find(log => {
                try {
                    return grantRegistry.interface.parseLog(log).name === "ProjectRegistered";
                } catch (e) {
                    return false;
                }
            });

            const parsedEvent = grantRegistry.interface.parseLog(event);
            expect(parsedEvent.args.projectId).to.equal(0);
        });

        it("Should emit ProjectRegistered event", async function () {
            const metadataURI = "ipfs://QmTest123";
            await expect(grantRegistry.connect(projectOwner1).registerProject(metadataURI))
                .to.emit(grantRegistry, "ProjectRegistered")
                .withArgs(0, projectOwner1.address, metadataURI);
        });

        it("Should allow multiple projects from same owner", async function () {
            await grantRegistry.connect(projectOwner1).registerProject("ipfs://QmTest1");
            await grantRegistry.connect(projectOwner1).registerProject("ipfs://QmTest2");

            const [owner1] = await grantRegistry.getProject(0);
            const [owner2] = await grantRegistry.getProject(1);

            expect(owner1).to.equal(projectOwner1.address);
            expect(owner2).to.equal(projectOwner1.address);
        });

        it("Should allow different owners to register projects", async function () {
            await grantRegistry.connect(projectOwner1).registerProject("ipfs://QmTest1");
            await grantRegistry.connect(projectOwner2).registerProject("ipfs://QmTest2");

            const [owner1] = await grantRegistry.getProject(0);
            const [owner2] = await grantRegistry.getProject(1);

            expect(owner1).to.equal(projectOwner1.address);
            expect(owner2).to.equal(projectOwner2.address);
        });

        it("Should handle empty metadata URI", async function () {
            await grantRegistry.connect(projectOwner1).registerProject("");
            const [, uri] = await grantRegistry.getProject(0);
            expect(uri).to.equal("");
        });

        it("Should handle long metadata URI", async function () {
            const longURI = "ipfs://Qm" + "a".repeat(500);
            await grantRegistry.connect(projectOwner1).registerProject(longURI);
            const [, uri] = await grantRegistry.getProject(0);
            expect(uri).to.equal(longURI);
        });
    });

    describe("Project Retrieval", function () {
        beforeEach(async function () {
            await grantRegistry.connect(projectOwner1).registerProject("ipfs://QmTest1");
            await grantRegistry.connect(projectOwner2).registerProject("ipfs://QmTest2");
        });

        it("Should retrieve project by ID", async function () {
            const [owner, uri] = await grantRegistry.getProject(0);
            expect(owner).to.equal(projectOwner1.address);
            expect(uri).to.equal("ipfs://QmTest1");
        });

        it("Should retrieve correct project for each ID", async function () {
            const [owner1, uri1] = await grantRegistry.getProject(0);
            const [owner2, uri2] = await grantRegistry.getProject(1);

            expect(owner1).to.equal(projectOwner1.address);
            expect(uri1).to.equal("ipfs://QmTest1");
            expect(owner2).to.equal(projectOwner2.address);
            expect(uri2).to.equal("ipfs://QmTest2");
        });

        it("Should fail when retrieving non-existent project", async function () {
            await expect(
                grantRegistry.getProject(999)
            ).to.be.revertedWith("Project not found");
        });

        it("Should fail when retrieving project with ID >= nextId", async function () {
            const nextId = await grantRegistry.nextId();
            await expect(
                grantRegistry.getProject(nextId)
            ).to.be.revertedWith("Project not found");
        });
    });

    describe("Project Existence", function () {
        it("Should mark registered projects as existing", async function () {
            await grantRegistry.connect(projectOwner1).registerProject("ipfs://QmTest1");

            const project = await grantRegistry.projects(0);
            expect(project.exists).to.be.true;
        });

        it("Should not mark unregistered projects as existing", async function () {
            const project = await grantRegistry.projects(999);
            expect(project.exists).to.be.false;
        });
    });

    describe("Sequential ID Assignment", function () {
        it("Should assign IDs sequentially starting from 0", async function () {
            const tx1 = await grantRegistry.registerProject("ipfs://QmTest1");
            const receipt1 = await tx1.wait();
            const event1 = receipt1.logs.find(log => {
                try {
                    return grantRegistry.interface.parseLog(log).name === "ProjectRegistered";
                } catch (e) {
                    return false;
                }
            });

            const tx2 = await grantRegistry.registerProject("ipfs://QmTest2");
            const receipt2 = await tx2.wait();
            const event2 = receipt2.logs.find(log => {
                try {
                    return grantRegistry.interface.parseLog(log).name === "ProjectRegistered";
                } catch (e) {
                    return false;
                }
            });

            expect(grantRegistry.interface.parseLog(event1).args.projectId).to.equal(0);
            expect(grantRegistry.interface.parseLog(event2).args.projectId).to.equal(1);
        });

        it("Should maintain sequential IDs across different owners", async function () {
            await grantRegistry.connect(projectOwner1).registerProject("ipfs://QmTest1");
            await grantRegistry.connect(projectOwner2).registerProject("ipfs://QmTest2");
            await grantRegistry.connect(projectOwner1).registerProject("ipfs://QmTest3");

            expect(await grantRegistry.nextId()).to.equal(3);
        });
    });

    describe("Metadata URI Formats", function () {
        it("Should accept IPFS URIs", async function () {
            const ipfsURI = "ipfs://QmTest123abc";
            await grantRegistry.registerProject(ipfsURI);
            const [, uri] = await grantRegistry.getProject(0);
            expect(uri).to.equal(ipfsURI);
        });

        it("Should accept HTTP URIs", async function () {
            const httpURI = "https://example.com/metadata.json";
            await grantRegistry.registerProject(httpURI);
            const [, uri] = await grantRegistry.getProject(0);
            expect(uri).to.equal(httpURI);
        });

        it("Should accept Arweave URIs", async function () {
            const arweaveURI = "ar://abc123def456";
            await grantRegistry.registerProject(arweaveURI);
            const [, uri] = await grantRegistry.getProject(0);
            expect(uri).to.equal(arweaveURI);
        });

        it("Should accept arbitrary string URIs", async function () {
            const customURI = "custom-protocol://data";
            await grantRegistry.registerProject(customURI);
            const [, uri] = await grantRegistry.getProject(0);
            expect(uri).to.equal(customURI);
        });
    });

    describe("Gas Optimization", function () {
        it("Should use reasonable gas for registration", async function () {
            const tx = await grantRegistry.registerProject("ipfs://QmTest123");
            const receipt = await tx.wait();

            // Gas should be reasonable (less than 150k)
            expect(receipt.gasUsed).to.be.lt(150000);
        });

        it("Should use reasonable gas for retrieval", async function () {
            await grantRegistry.registerProject("ipfs://QmTest123");

            const tx = await grantRegistry.getProject.staticCall(0);
            // Static calls don't consume gas, but we can verify it works
            expect(tx).to.not.be.undefined;
        });
    });

    describe("Edge Cases", function () {
        it("Should handle registration of many projects", async function () {
            const numProjects = 10;
            for (let i = 0; i < numProjects; i++) {
                await grantRegistry.registerProject(`ipfs://QmTest${i}`);
            }

            expect(await grantRegistry.nextId()).to.equal(numProjects);
        });

        it("Should handle special characters in metadata URI", async function () {
            const specialURI = "ipfs://QmTest?param=value&other=123#fragment";
            await grantRegistry.registerProject(specialURI);
            const [, uri] = await grantRegistry.getProject(0);
            expect(uri).to.equal(specialURI);
        });

        it("Should handle unicode in metadata URI", async function () {
            const unicodeURI = "ipfs://QmTest你好世界";
            await grantRegistry.registerProject(unicodeURI);
            const [, uri] = await grantRegistry.getProject(0);
            expect(uri).to.equal(unicodeURI);
        });
    });

    describe("Storage Verification", function () {
        it("Should store all project data correctly", async function () {
            const metadataURI = "ipfs://QmTest123";
            await grantRegistry.connect(projectOwner1).registerProject(metadataURI);

            const project = await grantRegistry.projects(0);
            expect(project.owner).to.equal(projectOwner1.address);
            expect(project.metadataURI).to.equal(metadataURI);
            expect(project.exists).to.be.true;
        });

        it("Should maintain data integrity across multiple registrations", async function () {
            await grantRegistry.connect(projectOwner1).registerProject("ipfs://QmTest1");
            await grantRegistry.connect(projectOwner2).registerProject("ipfs://QmTest2");

            // Verify first project wasn't overwritten
            const project1 = await grantRegistry.projects(0);
            expect(project1.owner).to.equal(projectOwner1.address);
            expect(project1.metadataURI).to.equal("ipfs://QmTest1");

            // Verify second project is correct
            const project2 = await grantRegistry.projects(1);
            expect(project2.owner).to.equal(projectOwner2.address);
            expect(project2.metadataURI).to.equal("ipfs://QmTest2");
        });
    });
});
