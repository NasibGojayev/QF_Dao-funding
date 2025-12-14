const path = require('path');
require("@nomicfoundation/hardhat-toolbox");
// Go up two levels to find the root .env (from smart-contracts folder)
// Actually the centralized .env is in ../../visual_programming/backend/.env 
// But we want to support the user moving it. 
// Let's assume user might copy it to root of next_js_project or we point to the master one.
// Let's try to load from the known master location for now, but also check local.
// Load from root .env (two levels up)
require("dotenv").config({ path: path.resolve(__dirname, "../.env") });
// Also load local .env if exists (overrides)
require("dotenv").config();


/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
    solidity: "0.8.20",
    networks: {
        localhost: {
            // Use HOST_IP if set, otherwise default to 127.0.0.1
            url: `http://${process.env.HOST_IP || "127.0.0.1"}:8545`,
            hostname: "0.0.0.0"  // Bind to all interfaces
        },
        lan: {
            url: "http://192.168.1.67:8545",
            chainId: 31337 // Default Hardhat chain ID
        },
        docker: {
            url: process.env.HARDHAT_NETWORK_URL || "http://hardhat:8545",
            chainId: 31337
        },
        hardhat: {
            // Enable verbose logging for all transactions
            loggingEnabled: true,
        }
    },
};
