const hre = require('hardhat');

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log('Deploying contracts with account:', deployer.address);

  const GovernanceToken = await hre.ethers.getContractFactory('GovernanceToken');
  const governance = await GovernanceToken.deploy('DAO Token', 'DAO', hre.ethers.utils.parseEther('1000000'));
  await governance.deployed();
  console.log('GovernanceToken deployed to:', governance.address);

  const GrantRegistry = await hre.ethers.getContractFactory('GrantRegistry');
  const registry = await GrantRegistry.deploy();
  await registry.deployed();
  console.log('GrantRegistry deployed to:', registry.address);

  const DonationVault = await hre.ethers.getContractFactory('DonationVault');
  const vault = await DonationVault.deploy();
  await vault.deployed();
  console.log('DonationVault deployed to:', vault.address);

  const MatchingPool = await hre.ethers.getContractFactory('MatchingPool');
  const pool = await MatchingPool.deploy();
  await pool.deployed();
  console.log('MatchingPool deployed to:', pool.address);

  // Write simple addresses file for frontend
  const fs = require('fs');
  const addresses = {
    GovernanceToken: governance.address,
    GrantRegistry: registry.address,
    DonationVault: vault.address,
    MatchingPool: pool.address
  };
  fs.writeFileSync('deployed-addresses.json', JSON.stringify(addresses, null, 2));
  console.log('Wrote deployed-addresses.json');
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
