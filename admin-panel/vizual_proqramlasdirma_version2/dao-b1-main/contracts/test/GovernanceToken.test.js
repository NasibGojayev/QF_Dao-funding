const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("GovernanceToken", function () {
    let governanceToken;
    let owner;
    let addr1;
    let addr2;
    let addrs;

    beforeEach(async function () {
        // Get signers
        [owner, addr1, addr2, ...addrs] = await ethers.getSigners();

        // Deploy GovernanceToken
        const GovernanceToken = await ethers.getContractFactory("GovernanceToken");
        governanceToken = await GovernanceToken.deploy("DAO Token", "DAO", ethers.parseEther("1000000"));
        await governanceToken.waitForDeployment();
    });

    describe("Deployment", function () {
        it("Should set the right owner", async function () {
            expect(await governanceToken.owner()).to.equal(owner.address);
        });

        it("Should assign the total supply to the owner", async function () {
            const ownerBalance = await governanceToken.balanceOf(owner.address);
            expect(await governanceToken.totalSupply()).to.equal(ownerBalance);
        });

        it("Should have correct name and symbol", async function () {
            expect(await governanceToken.name()).to.equal("DAO Token");
            expect(await governanceToken.symbol()).to.equal("DAO");
        });

        it("Should mint initial supply if provided", async function () {
            const balance = await governanceToken.balanceOf(owner.address);
            expect(balance).to.equal(ethers.parseEther("1000000"));
        });

        it("Should not mint if initial supply is zero", async function () {
            const GovernanceToken = await ethers.getContractFactory("GovernanceToken");
            const token = await GovernanceToken.deploy("Test", "TST", 0);
            await token.waitForDeployment();

            expect(await token.totalSupply()).to.equal(0);
        });
    });

    describe("Minting", function () {
        it("Should allow owner to mint tokens", async function () {
            await governanceToken.mint(addr1.address, ethers.parseEther("100"));
            expect(await governanceToken.balanceOf(addr1.address)).to.equal(ethers.parseEther("100"));
        });

        it("Should increase total supply when minting", async function () {
            const initialSupply = await governanceToken.totalSupply();
            await governanceToken.mint(addr1.address, ethers.parseEther("100"));
            expect(await governanceToken.totalSupply()).to.equal(initialSupply + ethers.parseEther("100"));
        });

        it("Should fail if non-owner tries to mint", async function () {
            await expect(
                governanceToken.connect(addr1).mint(addr2.address, ethers.parseEther("100"))
            ).to.be.revertedWithCustomError(governanceToken, "OwnableUnauthorizedAccount");
        });

        it("Should allow minting to multiple addresses", async function () {
            await governanceToken.mint(addr1.address, ethers.parseEther("100"));
            await governanceToken.mint(addr2.address, ethers.parseEther("200"));

            expect(await governanceToken.balanceOf(addr1.address)).to.equal(ethers.parseEther("100"));
            expect(await governanceToken.balanceOf(addr2.address)).to.equal(ethers.parseEther("200"));
        });
    });

    describe("Transfers", function () {
        beforeEach(async function () {
            // Mint some tokens to addr1
            await governanceToken.mint(addr1.address, ethers.parseEther("1000"));
        });

        it("Should transfer tokens between accounts", async function () {
            await governanceToken.connect(addr1).transfer(addr2.address, ethers.parseEther("50"));
            expect(await governanceToken.balanceOf(addr2.address)).to.equal(ethers.parseEther("50"));
        });

        it("Should fail if sender doesn't have enough tokens", async function () {
            const initialBalance = await governanceToken.balanceOf(addr1.address);
            await expect(
                governanceToken.connect(addr1).transfer(addr2.address, initialBalance + ethers.parseEther("1"))
            ).to.be.revertedWithCustomError(governanceToken, "ERC20InsufficientBalance");
        });

        it("Should update balances after transfers", async function () {
            const initialBalance1 = await governanceToken.balanceOf(addr1.address);
            const initialBalance2 = await governanceToken.balanceOf(addr2.address);

            await governanceToken.connect(addr1).transfer(addr2.address, ethers.parseEther("100"));

            expect(await governanceToken.balanceOf(addr1.address)).to.equal(initialBalance1 - ethers.parseEther("100"));
            expect(await governanceToken.balanceOf(addr2.address)).to.equal(initialBalance2 + ethers.parseEther("100"));
        });

        it("Should emit Transfer event", async function () {
            await expect(governanceToken.connect(addr1).transfer(addr2.address, ethers.parseEther("50")))
                .to.emit(governanceToken, "Transfer")
                .withArgs(addr1.address, addr2.address, ethers.parseEther("50"));
        });
    });

    describe("Allowances", function () {
        beforeEach(async function () {
            await governanceToken.mint(addr1.address, ethers.parseEther("1000"));
        });

        it("Should approve tokens for delegated transfer", async function () {
            await governanceToken.connect(addr1).approve(addr2.address, ethers.parseEther("100"));
            expect(await governanceToken.allowance(addr1.address, addr2.address)).to.equal(ethers.parseEther("100"));
        });

        it("Should allow transferFrom with proper allowance", async function () {
            await governanceToken.connect(addr1).approve(addr2.address, ethers.parseEther("100"));
            await governanceToken.connect(addr2).transferFrom(addr1.address, addr2.address, ethers.parseEther("50"));

            expect(await governanceToken.balanceOf(addr2.address)).to.equal(ethers.parseEther("50"));
            expect(await governanceToken.allowance(addr1.address, addr2.address)).to.equal(ethers.parseEther("50"));
        });

        it("Should fail transferFrom without allowance", async function () {
            await expect(
                governanceToken.connect(addr2).transferFrom(addr1.address, addr2.address, ethers.parseEther("50"))
            ).to.be.revertedWithCustomError(governanceToken, "ERC20InsufficientAllowance");
        });

        it("Should emit Approval event", async function () {
            await expect(governanceToken.connect(addr1).approve(addr2.address, ethers.parseEther("100")))
                .to.emit(governanceToken, "Approval")
                .withArgs(addr1.address, addr2.address, ethers.parseEther("100"));
        });
    });

    describe("Ownership", function () {
        it("Should transfer ownership", async function () {
            await governanceToken.transferOwnership(addr1.address);
            expect(await governanceToken.owner()).to.equal(addr1.address);
        });

        it("Should prevent non-owners from transferring ownership", async function () {
            await expect(
                governanceToken.connect(addr1).transferOwnership(addr2.address)
            ).to.be.revertedWithCustomError(governanceToken, "OwnableUnauthorizedAccount");
        });

        it("Should allow new owner to mint", async function () {
            await governanceToken.transferOwnership(addr1.address);
            await governanceToken.connect(addr1).mint(addr2.address, ethers.parseEther("100"));
            expect(await governanceToken.balanceOf(addr2.address)).to.equal(ethers.parseEther("100"));
        });

        it("Should prevent old owner from minting after transfer", async function () {
            await governanceToken.transferOwnership(addr1.address);
            await expect(
                governanceToken.mint(addr2.address, ethers.parseEther("100"))
            ).to.be.revertedWithCustomError(governanceToken, "OwnableUnauthorizedAccount");
        });
    });

    describe("Edge Cases", function () {
        it("Should handle zero amount transfers", async function () {
            await governanceToken.mint(addr1.address, ethers.parseEther("100"));
            await expect(governanceToken.connect(addr1).transfer(addr2.address, 0))
                .to.emit(governanceToken, "Transfer")
                .withArgs(addr1.address, addr2.address, 0);
        });

        it("Should handle minting zero tokens", async function () {
            const initialSupply = await governanceToken.totalSupply();
            await governanceToken.mint(addr1.address, 0);
            expect(await governanceToken.totalSupply()).to.equal(initialSupply);
        });

        it("Should handle maximum uint256 values", async function () {
            const maxUint256 = ethers.MaxUint256;
            // This should work without overflow
            await governanceToken.approve(addr1.address, maxUint256);
            expect(await governanceToken.allowance(owner.address, addr1.address)).to.equal(maxUint256);
        });
    });
});
