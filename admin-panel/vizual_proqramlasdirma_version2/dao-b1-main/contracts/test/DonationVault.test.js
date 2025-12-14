const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("DonationVault", function () {
    let donationVault;
    let owner;
    let projectOwner;
    let donor1;
    let donor2;
    let addrs;

    beforeEach(async function () {
        [owner, projectOwner, donor1, donor2, ...addrs] = await ethers.getSigners();

        const DonationVault = await ethers.getContractFactory("DonationVault");
        donationVault = await DonationVault.deploy();
        await donationVault.waitForDeployment();
    });

    describe("Project Owner Management", function () {
        it("Should set project owner", async function () {
            await donationVault.setProjectOwner(1, projectOwner.address);
            expect(await donationVault.projectOwners(1)).to.equal(projectOwner.address);
        });

        it("Should emit ProjectOwnerSet event", async function () {
            await expect(donationVault.setProjectOwner(1, projectOwner.address))
                .to.emit(donationVault, "ProjectOwnerSet")
                .withArgs(1, projectOwner.address);
        });

        it("Should fail if owner already set", async function () {
            await donationVault.setProjectOwner(1, projectOwner.address);
            await expect(
                donationVault.setProjectOwner(1, donor1.address)
            ).to.be.revertedWith("Owner already set");
        });

        it("Should fail if setting zero address as owner", async function () {
            await expect(
                donationVault.setProjectOwner(1, ethers.ZeroAddress)
            ).to.be.revertedWith("Invalid owner address");
        });

        it("Should allow setting owners for multiple projects", async function () {
            await donationVault.setProjectOwner(1, projectOwner.address);
            await donationVault.setProjectOwner(2, donor1.address);

            expect(await donationVault.projectOwners(1)).to.equal(projectOwner.address);
            expect(await donationVault.projectOwners(2)).to.equal(donor1.address);
        });
    });

    describe("Donations", function () {
        it("Should accept donations", async function () {
            const donationAmount = ethers.parseEther("1.0");
            await donationVault.connect(donor1).donate(1, { value: donationAmount });

            expect(await donationVault.projectBalances(1)).to.equal(donationAmount);
        });

        it("Should emit Donated event", async function () {
            const donationAmount = ethers.parseEther("1.0");
            await expect(donationVault.connect(donor1).donate(1, { value: donationAmount }))
                .to.emit(donationVault, "Donated")
                .withArgs(1, donor1.address, donationAmount);
        });

        it("Should fail if donation amount is zero", async function () {
            await expect(
                donationVault.connect(donor1).donate(1, { value: 0 })
            ).to.be.revertedWith("Must send ETH");
        });

        it("Should accumulate multiple donations", async function () {
            await donationVault.connect(donor1).donate(1, { value: ethers.parseEther("1.0") });
            await donationVault.connect(donor2).donate(1, { value: ethers.parseEther("2.0") });

            expect(await donationVault.projectBalances(1)).to.equal(ethers.parseEther("3.0"));
        });

        it("Should track donations for different projects separately", async function () {
            await donationVault.connect(donor1).donate(1, { value: ethers.parseEther("1.0") });
            await donationVault.connect(donor1).donate(2, { value: ethers.parseEther("2.0") });

            expect(await donationVault.projectBalances(1)).to.equal(ethers.parseEther("1.0"));
            expect(await donationVault.projectBalances(2)).to.equal(ethers.parseEther("2.0"));
        });

        it("Should accept large donations", async function () {
            const largeDonation = ethers.parseEther("1000");
            await donationVault.connect(donor1).donate(1, { value: largeDonation });
            expect(await donationVault.projectBalances(1)).to.equal(largeDonation);
        });
    });

    describe("Withdrawals", function () {
        beforeEach(async function () {
            // Set project owner and add donations
            await donationVault.setProjectOwner(1, projectOwner.address);
            await donationVault.connect(donor1).donate(1, { value: ethers.parseEther("10.0") });
        });

        it("Should allow project owner to withdraw", async function () {
            const withdrawAmount = ethers.parseEther("5.0");
            const initialBalance = await ethers.provider.getBalance(projectOwner.address);

            const tx = await donationVault.connect(projectOwner).withdraw(1, projectOwner.address, withdrawAmount);
            const receipt = await tx.wait();
            const gasUsed = receipt.gasUsed * receipt.gasPrice;

            const finalBalance = await ethers.provider.getBalance(projectOwner.address);
            expect(finalBalance).to.be.closeTo(initialBalance + withdrawAmount - gasUsed, ethers.parseEther("0.001"));
        });

        it("Should update project balance after withdrawal", async function () {
            const withdrawAmount = ethers.parseEther("5.0");
            await donationVault.connect(projectOwner).withdraw(1, projectOwner.address, withdrawAmount);

            expect(await donationVault.projectBalances(1)).to.equal(ethers.parseEther("5.0"));
        });

        it("Should emit Withdrawn event", async function () {
            const withdrawAmount = ethers.parseEther("5.0");
            await expect(donationVault.connect(projectOwner).withdraw(1, projectOwner.address, withdrawAmount))
                .to.emit(donationVault, "Withdrawn")
                .withArgs(1, projectOwner.address, withdrawAmount);
        });

        it("Should fail if non-owner tries to withdraw", async function () {
            await expect(
                donationVault.connect(donor1).withdraw(1, donor1.address, ethers.parseEther("1.0"))
            ).to.be.revertedWith("Only project owner can withdraw");
        });

        it("Should fail if withdrawal exceeds balance", async function () {
            await expect(
                donationVault.connect(projectOwner).withdraw(1, projectOwner.address, ethers.parseEther("20.0"))
            ).to.be.revertedWith("Insufficient balance");
        });

        it("Should allow withdrawing to different address", async function () {
            const withdrawAmount = ethers.parseEther("5.0");
            const initialBalance = await ethers.provider.getBalance(donor2.address);

            await donationVault.connect(projectOwner).withdraw(1, donor2.address, withdrawAmount);

            const finalBalance = await ethers.provider.getBalance(donor2.address);
            expect(finalBalance).to.equal(initialBalance + withdrawAmount);
        });

        it("Should allow multiple partial withdrawals", async function () {
            await donationVault.connect(projectOwner).withdraw(1, projectOwner.address, ethers.parseEther("3.0"));
            await donationVault.connect(projectOwner).withdraw(1, projectOwner.address, ethers.parseEther("2.0"));

            expect(await donationVault.projectBalances(1)).to.equal(ethers.parseEther("5.0"));
        });

        it("Should allow withdrawing entire balance", async function () {
            await donationVault.connect(projectOwner).withdraw(1, projectOwner.address, ethers.parseEther("10.0"));
            expect(await donationVault.projectBalances(1)).to.equal(0);
        });
    });

    describe("Security", function () {
        it("Should prevent withdrawal from unowned project", async function () {
            await donationVault.connect(donor1).donate(99, { value: ethers.parseEther("1.0") });

            await expect(
                donationVault.connect(donor1).withdraw(99, donor1.address, ethers.parseEther("1.0"))
            ).to.be.revertedWith("Only project owner can withdraw");
        });

        it("Should prevent ownership transfer attacks", async function () {
            await donationVault.setProjectOwner(1, projectOwner.address);

            // Attacker cannot change owner
            await expect(
                donationVault.connect(donor1).setProjectOwner(1, donor1.address)
            ).to.be.revertedWith("Owner already set");
        });

        it("Should handle zero balance withdrawals", async function () {
            await donationVault.setProjectOwner(2, projectOwner.address);

            await expect(
                donationVault.connect(projectOwner).withdraw(2, projectOwner.address, ethers.parseEther("1.0"))
            ).to.be.revertedWith("Insufficient balance");
        });
    });

    describe("Receive Function", function () {
        it("Should accept direct ETH transfers", async function () {
            const amount = ethers.parseEther("1.0");
            await owner.sendTransaction({
                to: await donationVault.getAddress(),
                value: amount
            });

            // Direct transfers don't go to any project
            expect(await ethers.provider.getBalance(await donationVault.getAddress())).to.equal(amount);
        });
    });

    describe("Edge Cases", function () {
        it("Should handle project ID zero", async function () {
            await donationVault.setProjectOwner(0, projectOwner.address);
            await donationVault.connect(donor1).donate(0, { value: ethers.parseEther("1.0") });
            expect(await donationVault.projectBalances(0)).to.equal(ethers.parseEther("1.0"));
        });

        it("Should handle very large project IDs", async function () {
            const largeId = 999999;
            await donationVault.setProjectOwner(largeId, projectOwner.address);
            await donationVault.connect(donor1).donate(largeId, { value: ethers.parseEther("1.0") });
            expect(await donationVault.projectBalances(largeId)).to.equal(ethers.parseEther("1.0"));
        });

        it("Should handle minimum donation amounts", async function () {
            const minAmount = 1; // 1 wei
            await donationVault.connect(donor1).donate(1, { value: minAmount });
            expect(await donationVault.projectBalances(1)).to.equal(minAmount);
        });
    });
});
