const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
    const [deployer] = await hre.ethers.getSigners();
    console.log("Deploying contracts with the account:", deployer.address);

    const timestamp = new Date().toISOString();
    const logEntries = [];
    const deployments = {};

    async function deploy(name, args = []) {
        const Factory = await hre.ethers.getContractFactory(name);
        const contract = await Factory.deploy(...args);
        await contract.waitForDeployment();
        const address = await contract.getAddress();

        console.log(`${name} deployed to: ${address}`);

        deployments[name] = address;
        logEntries.push({
            event: "ContractDeployed",
            contract: name,
            address: address,
            deployer: deployer.address,
            timestamp: timestamp,
            network: hre.network.name
        });

        return contract;
    }

    // Deploy contracts
    const govToken = await deploy("GovernanceToken", [deployer.address]);
    const grantRegistry = await deploy("GrantRegistry", [deployer.address]);
    const roundManager = await deploy("RoundManager", [deployer.address]);
    const donationVault = await deploy("DonationVault", [deployer.address]);
    const matchingPool = await deploy("MatchingPool", [deployer.address]);

    // Write outputs
    const artifactsDir = path.join(__dirname, "../artifacts-store"); // Custom dir for user artifacts
    if (!fs.existsSync(artifactsDir)) {
        fs.mkdirSync(artifactsDir);
    }

    fs.writeFileSync(
        path.join(artifactsDir, "local-deployments.json"),
        JSON.stringify(deployments, null, 2)
    );

    const logsPath = path.join(artifactsDir, "deployment-logs.json");
    let existingLogs = [];
    if (fs.existsSync(logsPath)) {
        try {
            existingLogs = JSON.parse(fs.readFileSync(logsPath));
        } catch (e) { }
    }

    fs.writeFileSync(
        logsPath,
        JSON.stringify([...existingLogs, ...logEntries], null, 2)
    );

    console.log("Deployment logs written to artifacts-store/");

    // ---------------------------------------------------------
    // AUTO-UPDATE FRONTEND CONFIG
    // ---------------------------------------------------------
    const frontendConfigPath = path.join(__dirname, "../../my-app/lib/contracts.ts");

    if (fs.existsSync(frontendConfigPath)) {
        console.log("Updating frontend config at:", frontendConfigPath);
        let content = fs.readFileSync(frontendConfigPath, "utf8");

        // Helper to replace address
        const replaceAddress = (key, newAddress) => {
            const regex = new RegExp(`export const ${key} = "0x[a-fA-F0-9]{40}";`);
            if (regex.test(content)) {
                content = content.replace(regex, `export const ${key} = "${newAddress}";`);
                console.log(`  Updated ${key}`);
            } else {
                console.warn(`  Could not find ${key} in contracts.ts to update.`);
            }
        };

        replaceAddress("GRANT_REGISTRY_ADDRESS", deployments["GrantRegistry"]);
        replaceAddress("DONATION_VAULT_ADDRESS", deployments["DonationVault"]);
        replaceAddress("GOVERNANCE_TOKEN_ADDRESS", deployments["GovernanceToken"]);

        fs.writeFileSync(frontendConfigPath, content);
        console.log("Frontend config updated successfully!");
    } else {
        console.warn("Could not find frontend config at:", frontendConfigPath);
    }
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
