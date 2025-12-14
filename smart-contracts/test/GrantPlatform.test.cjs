const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-toolbox/network-helpers");

describe("Grant Platform Contracts", function () {
    let govToken, grantRegistry, roundManager, donationVault, matchingPool;
    let owner, addr1, addr2;

    beforeEach(async function () {
        [owner, addr1, addr2] = await ethers.getSigners();

        const GovernanceToken = await ethers.getContractFactory("GovernanceToken");
        govToken = await GovernanceToken.deploy(owner.address);

        const GrantRegistry = await ethers.getContractFactory("GrantRegistry");
        grantRegistry = await GrantRegistry.deploy(owner.address);

        const RoundManager = await ethers.getContractFactory("RoundManager");
        roundManager = await RoundManager.deploy(owner.address);

        const DonationVault = await ethers.getContractFactory("DonationVault");
        donationVault = await DonationVault.deploy(owner.address);

        const MatchingPool = await ethers.getContractFactory("MatchingPool");
        matchingPool = await MatchingPool.deploy(owner.address);
    });

    describe("GovernanceToken", function () {
        it("Should mint initial supply to owner", async function () {
            const balance = await govToken.balanceOf(owner.address);
            expect(balance).to.be.gt(0);
        });

        it("Should allow owner to mint new tokens", async function () {
            await govToken.mint(addr1.address, 100);
            expect(await govToken.balanceOf(addr1.address)).to.equal(100);
        });

        it("Should fail if non-owner tries to mint", async function () {
            await expect(
                govToken.connect(addr1).mint(addr1.address, 100)
            ).to.be.revertedWithCustomError(govToken, "OwnableUnauthorizedAccount");
        });
    });

    describe("GrantRegistry", function () {
        it("Should create a grant and emit event", async function () {
            await expect(grantRegistry.createGrant("ipfs://metadata"))
                .to.emit(grantRegistry, "GrantCreated")
                .withArgs(1, owner.address, "ipfs://metadata");
        });

        it("Should update grant metadata", async function () {
            await grantRegistry.createGrant("ipfs://old");
            await grantRegistry.updateGrant(1, "ipfs://new");
            const grant = await grantRegistry.getGrant(1);
            expect(grant.metadata).to.equal("ipfs://new");
        });

        it("Should fail update if not owner", async function () {
            await grantRegistry.createGrant("ipfs://old");
            await expect(
                grantRegistry.connect(addr1).updateGrant(1, "ipfs://hack")
            ).to.be.revertedWith("Not grant owner");
        });
    });

    describe("RoundManager", function () {
        it("Should create a round", async function () {
            const now = await time.latest();
            await roundManager.createRound(now + 100, now + 1000, "meta");
            const isActive = await roundManager.isRoundActive(1);
            expect(isActive).to.be.false;
        });

        it("Should check active status correctly", async function () {
            const now = await time.latest();
            await roundManager.createRound(now + 100, now + 1000, "meta");

            await time.increaseTo(now + 150);
            expect(await roundManager.isRoundActive(1)).to.be.true;

            await time.increaseTo(now + 1001);
            expect(await roundManager.isRoundActive(1)).to.be.false;
        });

        it("Should fail if start time >= end time", async function () {
            const now = await time.latest();
            await expect(
                roundManager.createRound(now + 1000, now + 100, "meta")
            ).to.be.revertedWith("End time must be after start time");
        });
    });

    describe("DonationVault", function () {
        it("Should accept deposits", async function () {
            await govToken.mint(addr1.address, 1000);
            await govToken.connect(addr1).approve(donationVault.target, 500);

            await expect(donationVault.connect(addr1).deposit(govToken.target, 500, 1, 1))
                .to.emit(donationVault, "DonationReceived")
                .withArgs(addr1.address, govToken.target, 500, 1, 1);

            expect(await govToken.balanceOf(donationVault.target)).to.equal(500);
        });

        it("Should withdraw funds by owner", async function () {
            await govToken.mint(donationVault.target, 1000);

            await donationVault.withdraw(govToken.target, addr1.address, 400);
            expect(await govToken.balanceOf(addr1.address)).to.equal(400);
        });

        it("Should fail withdraw if not owner", async function () {
            await govToken.mint(donationVault.target, 1000);
            await expect(
                donationVault.connect(addr1).withdraw(govToken.target, addr1.address, 400)
            ).to.be.revertedWithCustomError(donationVault, "OwnableUnauthorizedAccount");
        });
    });

    describe("MatchingPool", function () {
        it("Should distribute funds", async function () {
            await govToken.mint(matchingPool.target, 1000);

            const recipients = [addr1.address, addr2.address];
            const amounts = [300, 200];

            await matchingPool.allocateFunds(1, govToken.target, recipients, amounts);

            expect(await govToken.balanceOf(addr1.address)).to.equal(300);
            expect(await govToken.balanceOf(addr2.address)).to.equal(200);
        });

        it("Should fail on array mismatch", async function () {
            await expect(
                matchingPool.allocateFunds(1, govToken.target, [addr1.address], [100, 200])
            ).to.be.revertedWith("Arrays length mismatch");
        });
    });
});
