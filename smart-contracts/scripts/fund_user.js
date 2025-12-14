const hre = require("hardhat");

async function main() {
    const [deployer] = await hre.ethers.getSigners();

    // Load deployment address dynamically
    const fs = require("fs");
    const path = require("path");
    const deploymentsPath = path.join(__dirname, "../artifacts-store/local-deployments.json");

    if (!fs.existsSync(deploymentsPath)) {
        throw new Error("Deployments file not found. Run 'npx hardhat run scripts/deploy.js' first.");
    }

    const deployments = JSON.parse(fs.readFileSync(deploymentsPath, "utf8"));
    const tokenAddress = deployments["GovernanceToken"];

    if (!tokenAddress) throw new Error("GovernanceToken address not found in deployments.");

    const userAddress = "0x9b7ddb0790dc95c2487fb0be4442afc67a49a532"; // The address from your logs
    const amount = hre.ethers.parseEther("1000"); // 1000 Tokens

    const Token = await hre.ethers.getContractAt("GovernanceToken", tokenAddress);

    console.log(`Funding user ${userAddress} with 1000 GOV tokens...`);
    console.log(`Token Contract: ${tokenAddress}`);
    console.log(`Sender: ${deployer.address} (Balance: ${(await Token.balanceOf(deployer.address)).toString()})`);

    const tx = await Token.transfer(userAddress, amount);
    await tx.wait();

    console.log(`Transfer successful! Hash: ${tx.hash}`);
    console.log(`New Balance: ${(await Token.balanceOf(userAddress)).toString()}`);
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
