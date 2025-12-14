const fs = require('fs');
const path = require('path');

async function main() {
    const artifactsDir = path.join(__dirname, '../artifacts/contracts');
    const outputDir = path.join(__dirname, '../../visual_programming/backend/doncoin/base/abis');

    // Create output directory if it doesn't exist
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    const contracts = [
        'GovernanceToken',
        'GrantRegistry',
        'RoundManager',
        'DonationVault',
        'MatchingPool'
    ];

    console.log('Consolidating ABIs...');

    for (const contract of contracts) {
        // Look in each contract's directory
        const contractDir = path.join(artifactsDir, `${contract}.sol`);
        const artifactPath = path.join(contractDir, `${contract}.json`);

        if (fs.existsSync(artifactPath)) {
            const artifact = JSON.parse(fs.readFileSync(artifactPath, 'utf8'));
            const abiPath = path.join(outputDir, `${contract}.json`);

            fs.writeFileSync(abiPath, JSON.stringify(artifact.abi, null, 2));
            console.log(`Copied ABI for ${contract} to ${abiPath}`);
        } else {
            console.error(`Artifact not found for ${contract} at ${artifactPath}`);
        }
    }
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
