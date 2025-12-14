const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("MatchingPool", function () {
    let matchingPool;
    let owner;
    let donor1;
    let donor2;
    let donor3;
    let recipient;
    let addrs;

    beforeEach(async function () {
        [owner, donor1, donor2, donor3, recipient, ...addrs] = await ethers.getSigners();

        const MatchingPool = await ethers.getContractFactory("MatchingPool");
        matchingPool = await MatchingPool.deploy();
        await matchingPool.waitForDeployment();
    });

    describe("Deployment", function () {
        it("Should set the right owner", async function () {
            expect(await matchingPool.owner()).to.equal(owner.address);
        });

        it("Should initialize with zero balances", async function () {
            expect(await matchingPool.poolBalances(0)).to.equal(0);
            expect(await matchingPool.poolBalances(1)).to.equal(0);
        });
    });

    describe("Pool Funding", function () {
        it("Should accept pool funding", async function () {
            const fundAmount = ethers.parseEther("100");
            await matchingPool.connect(donor1).fundPool(1, { value: fundAmount });

            expect(await matchingPool.poolBalances(1)).to.equal(fundAmount);
        });

        it("Should emit Funded event", async function () {
            const fundAmount = ethers.parseEther("100");
            await expect(matchingPool.connect(donor1).fundPool(1, { value: fundAmount }))
                .to.emit(matchingPool, "Funded")
                .withArgs(1, donor1.address, fundAmount);
        });

        it("Should fail if funding with zero ETH", async function () {
            await expect(
                matchingPool.fundPool(1, { value: 0 })
            ).to.be.revertedWith("Must send ETH");
        });

        it("Should accumulate multiple fundings", async function () {
            await matchingPool.connect(donor1).fundPool(1, { value: ethers.parseEther("50") });
            await matchingPool.connect(donor2).fundPool(1, { value: ethers.parseEther("50") });

            expect(await matchingPool.poolBalances(1)).to.equal(ethers.parseEther("100"));
        });

        it("Should track different pools separately", async function () {
            await matchingPool.connect(donor1).fundPool(1, { value: ethers.parseEther("100") });
            await matchingPool.connect(donor1).fundPool(2, { value: ethers.parseEther("200") });

            expect(await matchingPool.poolBalances(1)).to.equal(ethers.parseEther("100"));
            expect(await matchingPool.poolBalances(2)).to.equal(ethers.parseEther("200"));
        });
    });

    describe("Contribution Recording", function () {
        it("Should record contributions", async function () {
            await matchingPool.recordContribution(1, 1, donor1.address, ethers.parseEther("10"));

            expect(await matchingPool.contributions(1, 1, donor1.address)).to.equal(ethers.parseEther("10"));
        });

        it("Should emit ContributionRecorded event", async function () {
            await expect(matchingPool.recordContribution(1, 1, donor1.address, ethers.parseEther("10")))
                .to.emit(matchingPool, "ContributionRecorded")
                .withArgs(1, 1, donor1.address, ethers.parseEther("10"));
        });

        it("Should fail if amount is zero", async function () {
            await expect(
                matchingPool.recordContribution(1, 1, donor1.address, 0)
            ).to.be.revertedWith("Amount must be positive");
        });

        it("Should accumulate multiple contributions from same donor", async function () {
            await matchingPool.recordContribution(1, 1, donor1.address, ethers.parseEther("10"));
            await matchingPool.recordContribution(1, 1, donor1.address, ethers.parseEther("5"));

            expect(await matchingPool.contributions(1, 1, donor1.address)).to.equal(ethers.parseEther("15"));
        });

        it("Should track unique donors", async function () {
            await matchingPool.recordContribution(1, 1, donor1.address, ethers.parseEther("10"));
            await matchingPool.recordContribution(1, 1, donor2.address, ethers.parseEther("10"));
            await matchingPool.recordContribution(1, 1, donor3.address, ethers.parseEther("10"));

            expect(await matchingPool.getDonorCount(1, 1)).to.equal(3);
        });

        it("Should not duplicate donors in list", async function () {
            await matchingPool.recordContribution(1, 1, donor1.address, ethers.parseEther("10"));
            await matchingPool.recordContribution(1, 1, donor1.address, ethers.parseEther("5"));

            expect(await matchingPool.getDonorCount(1, 1)).to.equal(1);
        });
    });

    describe("Quadratic Funding Calculation", function () {
        it("Should return zero for project with no contributions", async function () {
            const match = await matchingPool.calculateMatching(1, 1);
            expect(match).to.equal(0);
        });

        it("Should calculate QF for single donor", async function () {
            // Single donor: √1 = 1, squared = 1, minus contribution = 0
            await matchingPool.recordContribution(1, 1, donor1.address, ethers.parseEther("1"));

            const match = await matchingPool.calculateMatching(1, 1);
            // (√1)² - 1 = 1 - 1 = 0
            expect(match).to.equal(0);
        });

        it("Should calculate QF for two equal donors", async function () {
            // Two donors with 1 ETH each
            // (√1 + √1)² - 2 = 4 - 2 = 2
            await matchingPool.recordContribution(1, 1, donor1.address, ethers.parseEther("1"));
            await matchingPool.recordContribution(1, 1, donor2.address, ethers.parseEther("1"));

            const match = await matchingPool.calculateMatching(1, 1);
            // Note: Using integer sqrt, so results may vary slightly
            expect(match).to.be.closeTo(ethers.parseEther("2"), ethers.parseEther("0.1"));
        });

        it("Should calculate QF for three equal donors", async function () {
            // Three donors with 1 ETH each
            // (√1 + √1 + √1)² - 3 = 9 - 3 = 6
            await matchingPool.recordContribution(1, 1, donor1.address, ethers.parseEther("1"));
            await matchingPool.recordContribution(1, 1, donor2.address, ethers.parseEther("1"));
            await matchingPool.recordContribution(1, 1, donor3.address, ethers.parseEther("1"));

            const match = await matchingPool.calculateMatching(1, 1);
            expect(match).to.be.closeTo(ethers.parseEther("6"), ethers.parseEther("0.1"));
        });

        it("Should favor many small donors over few large donors", async function () {
            // Scenario A: 10 donors with 1 ETH each
            // (10 * √1)² - 10 = 100 - 10 = 90

            // Scenario B: 1 donor with 10 ETH
            // (√10)² - 10 = 10 - 10 = 0

            // Record scenario A
            for (let i = 0; i < 10; i++) {
                await matchingPool.recordContribution(1, 1, addrs[i].address, ethers.parseEther("1"));
            }

            const matchA = await matchingPool.calculateMatching(1, 1);

            // Record scenario B (different project)
            await matchingPool.recordContribution(1, 2, donor1.address, ethers.parseEther("10"));
            const matchB = await matchingPool.calculateMatching(1, 2);

            // Many small donors should get more matching
            expect(matchA).to.be.gt(matchB);
        });

        it("Should handle large contribution amounts", async function () {
            await matchingPool.recordContribution(1, 1, donor1.address, ethers.parseEther("1000"));
            await matchingPool.recordContribution(1, 1, donor2.address, ethers.parseEther("1000"));

            const match = await matchingPool.calculateMatching(1, 1);
            expect(match).to.be.gt(0);
        });

        it("Should calculate correctly for unequal contributions", async function () {
            await matchingPool.recordContribution(1, 1, donor1.address, ethers.parseEther("1"));
            await matchingPool.recordContribution(1, 1, donor2.address, ethers.parseEther("4"));
            await matchingPool.recordContribution(1, 1, donor3.address, ethers.parseEther("9"));

            // (√1 + √4 + √9)² - 14 = (1 + 2 + 3)² - 14 = 36 - 14 = 22
            const match = await matchingPool.calculateMatching(1, 1);
            expect(match).to.be.closeTo(ethers.parseEther("22"), ethers.parseEther("0.5"));
        });
    });

    describe("Matching Distribution", function () {
        beforeEach(async function () {
            // Fund the pool
            await matchingPool.fundPool(1, { value: ethers.parseEther("100") });

            // Record contributions
            await matchingPool.recordContribution(1, 1, donor1.address, ethers.parseEther("1"));
            await matchingPool.recordContribution(1, 1, donor2.address, ethers.parseEther("1"));
            await matchingPool.recordContribution(1, 1, donor3.address, ethers.parseEther("1"));
        });

        it("Should allow owner to distribute matching", async function () {
            const initialBalance = await ethers.provider.getBalance(recipient.address);

            await matchingPool.distributeMatching(1, 1, recipient.address);

            const finalBalance = await ethers.provider.getBalance(recipient.address);
            expect(finalBalance).to.be.gt(initialBalance);
        });

        it("Should emit MatchingDistributed event", async function () {
            const match = await matchingPool.calculateMatching(1, 1);

            await expect(matchingPool.distributeMatching(1, 1, recipient.address))
                .to.emit(matchingPool, "MatchingDistributed")
                .withArgs(1, 1, match);
        });

        it("Should fail if non-owner tries to distribute", async function () {
            await expect(
                matchingPool.connect(donor1).distributeMatching(1, 1, recipient.address)
            ).to.be.revertedWithCustomError(matchingPool, "OwnableUnauthorizedAccount");
        });

        it("Should fail if no matching funds calculated", async function () {
            await expect(
                matchingPool.distributeMatching(1, 99, recipient.address)
            ).to.be.revertedWith("No matching funds calculated");
        });

        it("Should fail if insufficient pool balance", async function () {
            // Create a project with huge matching requirement
            for (let i = 0; i < 20; i++) {
                await matchingPool.recordContribution(1, 2, addrs[i].address, ethers.parseEther("10"));
            }

            await expect(
                matchingPool.distributeMatching(1, 2, recipient.address)
            ).to.be.revertedWith("Insufficient pool balance");
        });

        it("Should decrease pool balance after distribution", async function () {
            const initialPoolBalance = await matchingPool.poolBalances(1);
            const match = await matchingPool.calculateMatching(1, 1);

            await matchingPool.distributeMatching(1, 1, recipient.address);

            const finalPoolBalance = await matchingPool.poolBalances(1);
            expect(finalPoolBalance).to.equal(initialPoolBalance - match);
        });
    });

    describe("Donor Management", function () {
        it("Should return donor list", async function () {
            await matchingPool.recordContribution(1, 1, donor1.address, ethers.parseEther("1"));
            await matchingPool.recordContribution(1, 1, donor2.address, ethers.parseEther("1"));

            const donors = await matchingPool.getDonors(1, 1);
            expect(donors).to.have.lengthOf(2);
            expect(donors).to.include(donor1.address);
            expect(donors).to.include(donor2.address);
        });

        it("Should return empty array for project with no donors", async function () {
            const donors = await matchingPool.getDonors(1, 1);
            expect(donors).to.have.lengthOf(0);
        });
    });

    describe("Square Root Function", function () {
        it("Should calculate sqrt correctly for perfect squares", async function () {
            // We can't directly test the internal sqrt function,
            // but we can verify through QF calculations

            // √4 = 2, so (√4)² - 4 = 4 - 4 = 0
            await matchingPool.recordContribution(1, 1, donor1.address, ethers.parseEther("4"));
            const match = await matchingPool.calculateMatching(1, 1);
            expect(match).to.equal(0);
        });

        it("Should handle sqrt of zero", async function () {
            // This is implicitly tested by projects with no contributions
            const match = await matchingPool.calculateMatching(1, 1);
            expect(match).to.equal(0);
        });
    });

    describe("Receive Function", function () {
        it("Should accept direct ETH transfers to pool 0", async function () {
            const amount = ethers.parseEther("10");
            await owner.sendTransaction({
                to: await matchingPool.getAddress(),
                value: amount
            });

            expect(await matchingPool.poolBalances(0)).to.equal(amount);
        });

        it("Should emit Funded event for direct transfers", async function () {
            const amount = ethers.parseEther("10");

            await expect(owner.sendTransaction({
                to: await matchingPool.getAddress(),
                value: amount
            })).to.emit(matchingPool, "Funded")
                .withArgs(0, owner.address, amount);
        });
    });

    describe("Edge Cases", function () {
        it("Should handle very small contributions", async function () {
            await matchingPool.recordContribution(1, 1, donor1.address, 1); // 1 wei
            const match = await matchingPool.calculateMatching(1, 1);
            expect(match).to.be.gte(0);
        });

        it("Should handle round ID zero", async function () {
            await matchingPool.fundPool(0, { value: ethers.parseEther("10") });
            await matchingPool.recordContribution(0, 1, donor1.address, ethers.parseEther("1"));

            const match = await matchingPool.calculateMatching(0, 1);
            expect(match).to.be.gte(0);
        });

        it("Should handle project ID zero", async function () {
            await matchingPool.recordContribution(1, 0, donor1.address, ethers.parseEther("1"));
            const match = await matchingPool.calculateMatching(1, 0);
            expect(match).to.be.gte(0);
        });
    });
});
