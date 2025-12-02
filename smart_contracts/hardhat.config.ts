// import hardhatToolboxViemPlugin from "@nomicfoundation/hardhat-toolbox-viem";
// import { configVariable, defineConfig } from "hardhat/config";

// export default defineConfig({
//   plugins: [hardhatToolboxViemPlugin],
//   solidity: {
//     profiles: {
//       default: {
//         version: "0.8.28",
//       },
//       production: {
//         version: "0.8.28",
//         settings: {
//           optimizer: {
//             enabled: true,
//             runs: 200,
//           },
//         },
//       },
//     },
//   },
//   networks: {
//     hardhatMainnet: {
//       type: "edr-simulated",
//       chainType: "l1",
//     },
//     hardhatOp: {
//       type: "edr-simulated",
//       chainType: "op",
//     },
//     baseSepolia: {
//       type:"http",
//       url: "https://base-sepolia-rpc.publicnode.com",
//       accounts: ["3c0e0ca01f5adeda20ed78af384e948764e7f186095f14b054c9b724a0c7598d"],
//     },
    
//     sepolia: {
//       type: "http",
//       chainType: "l1",
//       url: "wss://base-rpc.publicnode.com",
//       accounts: ["3c0e0ca01f5adeda20ed78af384e948764e7f186095f14b054c9b724a0c7598d"],
//     },
//   },
// });

import hardhatToolboxViemPlugin from "@nomicfoundation/hardhat-toolbox-viem";
import { defineConfig } from "hardhat/config";

export default defineConfig({
  plugins: [hardhatToolboxViemPlugin],

  solidity: {
    profiles: {
      default: {
        version: "0.8.28",
      },
      production: {
        version: "0.8.28",
        settings: {
          optimizer: {
            enabled: true,
            runs: 200,
          },
        },
      },
    },
  },

  networks: {
  localhost: {
    type: "http",
    url: "http://127.0.0.1:8545",
    accounts: [
      "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
    ]
  },
  hardhat: {
    type: "edr-simulated",
    chainType: "l1",
    chainId: 31337
  }
}
});
