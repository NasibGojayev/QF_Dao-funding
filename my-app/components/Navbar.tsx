"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { useTheme } from "next-themes";
import { Moon, Sun, Loader2, Coins } from "lucide-react";
import { ConnectButton } from '@rainbow-me/rainbowkit';
import { useWeb3Auth } from "../hooks/useWeb3Auth";
import { useAccount } from "wagmi";

export default function Navbar() {
    const { user, isAuthenticated, login, logout, isConnected, isLoading } = useWeb3Auth();
    const { address } = useAccount();
    const [mounted, setMounted] = useState(false);
    const { theme, setTheme } = useTheme();
    const [isClaiming, setIsClaiming] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    const handleClaimTokens = async () => {
        if (!address) return;
        setIsClaiming(true);
        try {
            // Note: Backend mounts api/urls.py at root, so it is /faucet/ not /api/faucet/
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/faucet/`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ wallet_address: address }),
            });
            const data = await response.json();
            if (response.ok) {
                alert(`Success! Sent 1000 GOV to ${address}.\nTx: ${data.tx_hash}`);
            } else {
                alert(`Error: ${data.message || data.error || "Unknown error"}`);
            }
        } catch (e) {
            alert("Failed to connect to faucet.");
            console.error(e);
        } finally {
            setIsClaiming(false);
        }
    };

    return (
        <header className="w-full border-b bg-background/80 backdrop-blur-md sticky top-0 z-50 border-border transition-colors duration-300">
            <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                <div className="flex items-center space-x-6">
                    <Link href="/" className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600 hover:opacity-80 transition-opacity">
                        DonCoin
                    </Link>
                    <nav className="hidden md:flex items-center space-x-6">
                        <Link href="/rounds" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">Rounds</Link>
                        <Link href="/proposals" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">Proposals</Link>
                        <Link href="/matching-pools" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">Matching Pool</Link>
                        {isAuthenticated && (
                            <Link href="/profile" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
                                Profile
                            </Link>
                        )}
                    </nav>
                </div>
                <div className="flex items-center space-x-4">

                    {/* Faucet Button */}
                    {isConnected && mounted && (
                        <button
                            onClick={handleClaimTokens}
                            disabled={isClaiming}
                            className="flex items-center gap-2 px-3 py-1.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-xs font-semibold rounded-full hover:bg-green-200 dark:hover:bg-green-900/50 transition border border-green-200 dark:border-green-800 disabled:opacity-50"
                            title="Get 1000 Free GOV Tokens"
                        >
                            {isClaiming ? <Loader2 size={14} className="animate-spin" /> : <Coins size={14} />}
                            {isClaiming ? "Sending..." : "Get Tokens"}
                        </button>
                    )}

                    <ConnectButton showBalance={false} chainStatus="icon" accountStatus="avatar" />

                    {/* Theme Toggle */}
                    {mounted && (
                        <button
                            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                            className="p-2 rounded-full hover:bg-accent hover:text-accent-foreground transition-colors text-muted-foreground"
                            aria-label="Toggle Theme"
                        >
                            {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
                        </button>
                    )}

                    {isAuthenticated && user ? (
                        <div className="flex items-center gap-3">
                            <Link href="/profile">
                                <div className="w-9 h-9 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-sm font-bold ring-2 ring-background shadow-sm cursor-pointer hover:ring-border transition-all" title={user.name}>
                                    {user.name ? user.name.charAt(0).toUpperCase() : 'U'}
                                </div>
                            </Link>
                            <button
                                onClick={logout}
                                className="text-sm text-destructive hover:text-destructive/80 font-medium transition-colors"
                            >
                                Logout
                            </button>
                        </div>
                    ) : (
                        isConnected && (
                            <button
                                onClick={login}
                                disabled={isLoading}
                                className="px-5 py-2 bg-primary text-primary-foreground text-sm font-semibold rounded-lg hover:bg-primary/90 transition shadow-sm disabled:opacity-50"
                            >
                                {isLoading ? "Signing..." : "Sign In with Wallet"}
                            </button>
                        )
                    )}
                </div>
            </div>
        </header>
    );
}
