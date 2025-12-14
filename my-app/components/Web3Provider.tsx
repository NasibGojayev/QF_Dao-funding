"use client";

import '@rainbow-me/rainbowkit/styles.css';
import {
    getDefaultConfig,
    RainbowKitProvider,
} from '@rainbow-me/rainbowkit';
import { WagmiProvider } from 'wagmi';
import {
    mainnet,
    polygon,
    optimism,
    arbitrum,
    base,
} from 'wagmi/chains';
import { defineChain } from 'viem';
import {
    QueryClientProvider,
    QueryClient,
} from "@tanstack/react-query";
import { useEffect, useState } from 'react';

// Custom Hardhat chain that works on LAN
// Set NEXT_PUBLIC_HARDHAT_RPC in .env.local to your Mac's IP
// Example: NEXT_PUBLIC_HARDHAT_RPC=http://192.168.1.100:8545
const hardhatLocal = defineChain({
    id: 31337,
    name: 'Hardhat Local',
    nativeCurrency: {
        decimals: 18,
        name: 'Ether',
        symbol: 'ETH',
    },
    rpcUrls: {
        default: {
            http: [process.env.NEXT_PUBLIC_HARDHAT_RPC || 'http://127.0.0.1:8545'],
        },
    },
    testnet: true,
});

const config = getDefaultConfig({
    appName: 'DonCoin App',
    projectId: process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID || 'YOUR_PROJECT_ID', // You can get one at https://cloud.walletconnect.com
    chains: [hardhatLocal, mainnet, polygon, optimism, arbitrum, base],
    ssr: true,
});

const queryClient = new QueryClient();

export function Web3Provider({ children }: { children: React.ReactNode }) {
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    return (
        <WagmiProvider config={config}>
            <QueryClientProvider client={queryClient}>
                <RainbowKitProvider>
                    {children}
                </RainbowKitProvider>
            </QueryClientProvider>
        </WagmiProvider>
    );
}
