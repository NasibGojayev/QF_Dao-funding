async function main() {
  const [deployer] = await ethers.getSigners();
  console.log('Deploying contracts with account:', deployer.address);

  const MilestoneFunding = await ethers.getContractFactory('MilestoneFunding');
  const contract = await MilestoneFunding.deploy();
  await contract.deployed();
  console.log('MilestoneFunding deployed to:', contract.address);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
