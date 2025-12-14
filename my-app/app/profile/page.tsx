"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAccount, useBalance } from "wagmi";
import { useWeb3Auth } from "@/hooks/useWeb3Auth";
import { GOVERNANCE_TOKEN_ADDRESS } from "@/lib/contracts";
import { formatEther } from "viem";

// Types
type Donation = {
    donation_id: string;
    proposal: string;
    proposal_title?: string;
    proposal_details?: {
        title: string;
    };
    amount: number;
    created_at: string;
};

type Proposal = {
    proposal_id: string;
    title: string;
    description: string;
    status: string;
    total_donations: number;
    created_at: string;
};

type TabType = "contributions" | "proposals" | "settings";

export default function ProfilePage() {
    const { user, isAuthenticated, isLoading: authLoading } = useWeb3Auth();
    const { address, isConnected } = useAccount();
    const router = useRouter();

    const [activeTab, setActiveTab] = useState<TabType>("contributions");
    const [contributions, setContributions] = useState<Donation[]>([]);
    const [proposals, setProposals] = useState<Proposal[]>([]);
    const [loadingData, setLoadingData] = useState(false);

    // ETH Balance
    const { data: ethBalance } = useBalance({
        address: address,
    });

    // GOV Token Balance
    const { data: govBalance } = useBalance({
        address: address,
        token: GOVERNANCE_TOKEN_ADDRESS as `0x${string}`,
    });

    // Redirect if not connected
    useEffect(() => {
        if (!authLoading && !isConnected) {
            router.push("/");
        }
    }, [authLoading, isConnected, router]);

    // Fetch data when user is available
    useEffect(() => {
        if (user?.donor_id) {
            fetchUserData(user.donor_id);
        }
    }, [user]);

    const fetchUserData = async (donorId: string) => {
        setLoadingData(true);
        try {
            // Fetch donations (contributions) by donor ID
            const donationsRes = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/donations/?donor=${donorId}`
            );
            if (donationsRes.ok) {
                const data = await donationsRes.json();
                setContributions(data.results || data || []);
            }

            // Fetch proposals by proposer (donor) ID
            const proposalsRes = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/proposals/?proposer=${donorId}`
            );
            if (proposalsRes.ok) {
                const data = await proposalsRes.json();
                setProposals(data.results || data || []);
            }
        } catch (e) {
            console.error("Failed to fetch user data:", e);
        } finally {
            setLoadingData(false);
        }
    };

    // Loading state
    if (authLoading || !isConnected) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background text-foreground">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
                    <p className="text-muted-foreground">Connecting wallet...</p>
                </div>
            </div>
        );
    }

    const displayName = user?.name || address?.slice(0, 8) + "..." + address?.slice(-6) || "Unknown";
    const shortAddress = address ? `${address.slice(0, 6)}...${address.slice(-4)}` : "";

    return (
        <main className="min-h-screen bg-background text-foreground pt-24 pb-12">
            {/* Identity Header */}
            <section className="bg-card border-b border-border shadow-sm mb-8">
                <div className="max-w-7xl mx-auto px-6 py-8">
                    <div className="flex flex-col md:flex-row items-center justify-between gap-8">
                        <div className="flex items-center gap-6">
                            <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-4xl font-bold text-white shadow-lg ring-4 ring-background">
                                {displayName.charAt(0).toUpperCase()}
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold mb-1 text-foreground">{displayName}</h1>
                                {address && (
                                    <p className="text-muted-foreground text-xs mt-2 bg-secondary px-3 py-1 rounded inline-block font-mono">
                                        {shortAddress}
                                    </p>
                                )}
                                {isConnected && (
                                    <span className="ml-2 inline-flex items-center px-2 py-1 rounded text-xs bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200">
                                        <span className="w-2 h-2 bg-green-500 rounded-full mr-1.5 animate-pulse"></span>
                                        Connected
                                    </span>
                                )}
                            </div>
                        </div>

                        {/* Wallet Balances Card */}
                        <div className="bg-card border border-border rounded-xl p-6 min-w-[320px] shadow-sm">
                            <p className="text-muted-foreground text-sm mb-3 font-semibold">Wallet Balances</p>

                            {/* ETH Balance */}
                            <div className="flex justify-between items-center mb-3 pb-3 border-b border-border">
                                <div className="flex items-center gap-2">
                                    <div className="w-8 h-8 bg-blue-500/10 rounded-full flex items-center justify-center">
                                        <span className="text-blue-500 text-sm font-bold">Ξ</span>
                                    </div>
                                    <span className="text-sm text-muted-foreground">Ethereum</span>
                                </div>
                                <span className="text-lg font-bold text-foreground">
                                    {ethBalance ? parseFloat(formatEther(ethBalance.value)).toFixed(4) : "0.0000"} ETH
                                </span>
                            </div>

                            {/* GOV Token Balance */}
                            <div className="flex justify-between items-center">
                                <div className="flex items-center gap-2">
                                    <div className="w-8 h-8 bg-purple-500/10 rounded-full flex items-center justify-center">
                                        <span className="text-purple-500 text-sm font-bold">G</span>
                                    </div>
                                    <span className="text-sm text-muted-foreground">Governance Token</span>
                                </div>
                                <span className="text-lg font-bold text-foreground">
                                    {govBalance ? parseFloat(formatEther(govBalance.value)).toFixed(2) : "0.00"} GOV
                                </span>
                            </div>

                            <p className="text-xs text-muted-foreground mt-4 text-center">
                                Use the Faucet in the navbar to get test GOV tokens
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Content Area */}
            <section className="max-w-7xl mx-auto px-6">
                {/* Tabs */}
                <div className="flex gap-2 mb-8 border-b border-border overflow-x-auto">
                    {(["contributions", "proposals", "settings"] as TabType[]).map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`px-6 py-3 font-semibold transition border-b-2 capitalize whitespace-nowrap ${activeTab === tab
                                    ? "border-primary text-primary"
                                    : "border-transparent text-muted-foreground hover:text-foreground"
                                }`}
                        >
                            {tab === "contributions" ? "My Donations" : tab === "proposals" ? "My Proposals" : tab}
                        </button>
                    ))}
                </div>

                {/* Tab Content */}
                {activeTab === "contributions" && (
                    <div className="space-y-4">
                        <h2 className="text-xl font-bold text-foreground mb-4">Your Donations</h2>
                        {loadingData ? (
                            <div className="flex items-center gap-2 text-muted-foreground">
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                                Loading contributions...
                            </div>
                        ) : contributions.length > 0 ? (
                            <div className="grid gap-4">
                                {contributions.map((donation) => (
                                    <div
                                        key={donation.donation_id}
                                        className="bg-card p-4 rounded-lg shadow-sm border border-border flex justify-between items-center transition hover:shadow-md hover:border-border/80"
                                    >
                                        <div>
                                            <Link
                                                href={`/proposals/${donation.proposal}`}
                                                className="font-semibold text-primary hover:underline"
                                            >
                                                {donation.proposal_details?.title || donation.proposal_title || "Unknown Proposal"}
                                            </Link>
                                            <p className="text-xs text-muted-foreground mt-1">
                                                {new Date(donation.created_at).toLocaleDateString()} at{" "}
                                                {new Date(donation.created_at).toLocaleTimeString()}
                                            </p>
                                        </div>
                                        <div className="text-right">
                                            <p className="text-lg font-bold text-foreground">
                                                {parseFloat(donation.amount.toString()).toFixed(2)} GOV
                                            </p>
                                            <p className="text-xs text-muted-foreground">
                                                ID: {donation.donation_id.slice(0, 8)}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-12 bg-card rounded-lg border border-dashed border-border">
                                <p className="text-muted-foreground mb-4">You haven't made any donations yet.</p>
                                <Link href="/proposals" className="text-primary hover:underline font-semibold">
                                    Browse Proposals to Donate →
                                </Link>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === "proposals" && (
                    <div className="space-y-4">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-bold text-foreground">Your Proposals</h2>
                            <Link
                                href="/proposals"
                                className="bg-primary text-primary-foreground px-4 py-2 rounded-lg text-sm font-semibold hover:bg-primary/90 transition shadow-sm"
                            >
                                Create New Proposal
                            </Link>
                        </div>

                        {loadingData ? (
                            <div className="flex items-center gap-2 text-muted-foreground">
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                                Loading proposals...
                            </div>
                        ) : proposals.length > 0 ? (
                            <div className="grid gap-4">
                                {proposals.map((proposal) => (
                                    <div
                                        key={proposal.proposal_id}
                                        className="bg-card p-6 rounded-lg shadow-sm border border-border transition hover:shadow-md"
                                    >
                                        <div className="flex justify-between items-start mb-2">
                                            <Link
                                                href={`/proposals/${proposal.proposal_id}`}
                                                className="text-lg font-bold text-foreground hover:text-primary transition-colors"
                                            >
                                                {proposal.title}
                                            </Link>
                                            <span
                                                className={`px-2 py-1 rounded text-xs uppercase font-bold ${proposal.status === "approved"
                                                        ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200"
                                                        : proposal.status === "pending"
                                                            ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200"
                                                            : "bg-secondary text-secondary-foreground"
                                                    }`}
                                            >
                                                {proposal.status}
                                            </span>
                                        </div>
                                        <p className="text-muted-foreground text-sm mb-4 line-clamp-2">
                                            {proposal.description || "No description provided."}
                                        </p>
                                        <div className="flex gap-4 text-sm text-muted-foreground">
                                            <div>
                                                <span className="font-semibold text-foreground">
                                                    {parseFloat(proposal.total_donations.toString()).toFixed(2)} GOV
                                                </span>{" "}
                                                raised
                                            </div>
                                            <div>Created {new Date(proposal.created_at).toLocaleDateString()}</div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-12 bg-card rounded-lg border border-dashed border-border">
                                <p className="text-muted-foreground mb-4">You haven't created any proposals yet.</p>
                                <Link href="/proposals" className="text-primary hover:underline font-semibold">
                                    Create a Proposal →
                                </Link>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === "settings" && (
                    <div className="max-w-2xl mx-auto bg-card border border-border rounded-lg p-8 shadow-sm">
                        <h3 className="text-lg font-bold mb-6 text-foreground">Account Settings</h3>
                        <div className="space-y-6">
                            <div>
                                <label className="block text-sm font-semibold text-foreground mb-2">Display Name</label>
                                <div className="p-3 bg-secondary/50 rounded border border-border text-foreground">
                                    {displayName}
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-semibold text-foreground mb-2">Wallet Address</label>
                                <div className="p-3 bg-secondary/50 rounded border border-border font-mono text-sm text-muted-foreground break-all">
                                    {address || "Not connected"}
                                </div>
                            </div>
                            {user?.donor_id && (
                                <div>
                                    <label className="block text-sm font-semibold text-foreground mb-2">Donor ID</label>
                                    <div className="p-3 bg-secondary/50 rounded border border-border font-mono text-sm text-muted-foreground">
                                        {user.donor_id}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </section>
        </main>
    );
}
