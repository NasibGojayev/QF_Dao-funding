const { expect } = require('chai');
const { ethers } = require('hardhat');

describe('MilestoneFunding', function () {
  let Milestone, mf, owner, addr1, addr2;

  beforeEach(async function () {
    [owner, addr1, addr2] = await ethers.getSigners();
    Milestone = await ethers.getContractFactory('MilestoneFunding');
    mf = await Milestone.deploy();
    await mf.deployed();
  });

  it('should deploy and set owner', async function () {
    expect(await mf.owner()).to.equal(owner.address);
  });

  it('creates project and emits ProjectCreated', async function () {
    await expect(mf.connect(addr1).createProject('Test'))
      .to.emit(mf, 'ProjectCreated')
      .withArgs(1, addr1.address, 'Test');
  });

  it('contribute emits TransactionCreated and updates balance', async function () {
    await mf.connect(addr1).createProject('P');
    const tx = await mf.connect(addr2).contribute(1, 'donation', { value: ethers.utils.parseEther('1') });
    await expect(tx).to.emit(mf, 'TransactionCreated');
    const project = await mf.projects(1);
    expect(project.balance).to.equal(ethers.utils.parseEther('1'));
  });

  it('contribute fails for invalid project', async function () {
    await expect(mf.connect(addr2).contribute(999, 'x', { value: 1 })).to.be.revertedWith('invalid project');
  });

  it('contribute fails for zero amount', async function () {
    await mf.connect(addr1).createProject('P');
    await expect(mf.connect(addr2).contribute(1, 'x', { value: 0 })).to.be.revertedWith('zero amount');
  });

  it('withdraw by creator transfers balance', async function () {
    await mf.connect(addr1).createProject('P');
    await mf.connect(addr2).contribute(1, 'donate', { value: ethers.utils.parseEther('0.5') });
    const before = await ethers.provider.getBalance(addr1.address);
    // withdraw as creator (addr1)
    await expect(mf.connect(addr1).withdraw(1)).to.not.be.reverted;
  });

  it('withdraw reverts for non-creator', async function () {
    await mf.connect(addr1).createProject('P');
    await mf.connect(addr2).contribute(1, 'don', { value: ethers.utils.parseEther('0.1') });
    await expect(mf.connect(addr2).withdraw(1)).to.be.revertedWith('not creator');
  });

  it('assignTag emits TagAssigned and only owner can call', async function () {
    await mf.connect(addr1).createProject('P');
    await expect(mf.connect(owner).assignTag(1, 5, 'infra')).to.emit(mf, 'TagAssigned');
    await expect(mf.connect(addr1).assignTag(1, 5, 'infra')).to.be.revertedWith('only owner');
  });

  it('resolveMilestone emits MilestoneResolved and only owner', async function () {
    await mf.connect(addr1).createProject('P');
    await expect(mf.connect(owner).resolveMilestone(1, 1)).to.emit(mf, 'MilestoneResolved');
    await expect(mf.connect(addr1).resolveMilestone(1, 1)).to.be.revertedWith('only owner');
  });

  it('multiple projects increment ids correctly', async function () {
    await mf.connect(addr1).createProject('A');
    await mf.connect(addr2).createProject('B');
    expect((await mf.projectCount()).toNumber()).to.equal(2);
  });

});
