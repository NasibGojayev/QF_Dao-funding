const { expect } = require('chai');
const { ethers } = require('hardhat');

describe('MilestoneFunding (local)', function () {
  let mf, owner, addr1, addr2;

  beforeEach(async function () {
    [owner, addr1, addr2] = await ethers.getSigners();
    const Milestone = await ethers.getContractFactory('MilestoneFunding');
    mf = await Milestone.deploy();
    await mf.deployed();
  });

  it('sets owner', async function () {
    expect(await mf.owner()).to.equal((await ethers.getSigners())[0].address);
  });

  it('creates project and emits', async function () {
    await expect(mf.connect(addr1).createProject('Test'))
      .to.emit(mf, 'ProjectCreated');
  });

  it('contribute and balance update', async function () {
    await mf.connect(addr1).createProject('P');
    await expect(mf.connect(addr2).contribute(1, 'donation', { value: ethers.utils.parseEther('0.1') }))
      .to.emit(mf, 'TransactionCreated');
  });

});
