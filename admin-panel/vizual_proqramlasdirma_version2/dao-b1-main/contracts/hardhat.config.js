require("dotenv").config();
require("@nomicfoundation/hardhat-toolbox");
const { HARDHAT_NETWORK = 'localhost' } = process.env;

module.exports = {
  solidity: {
    compilers: [
      { version: "0.8.19" }
    ]
  },
  paths: {
    artifacts: './artifacts',
    sources: './contracts'
  },
  networks: {
    localhost: {
      url: 'http://127.0.0.1:8545'
    },
    dev: {
      url: process.env.RPC_URL || 'http://127.0.0.1:8545'
    }
  }
};
