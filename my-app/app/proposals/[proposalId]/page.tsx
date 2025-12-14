"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import DonationWidget from "../../components/DonationWidget";
import RecentDonors from "../../components/RecentDonors";

type Proposal = {
    id: string;
    proposal_id?: string;
    title: string;
    description?: string;
    creator?: string;
    proposer_details?: any;
    roundId?: string;
    round_details?: any;
    funding_goal?: number;
    total_donations?: number;
    status?: string;
    category?: string;
    onChainId?: number;
};

export default function ProposalDetailsPage() {
    const params = useParams();
    const proposalId = params.proposalId as string;

    const [proposal, setProposal] = useState<Proposal | null>(null);
    const [donations, setDonations] = useState<any[]>([]);
    const [qfest, setQfest] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchProposalDetails();
        fetchDonations();
        fetchQFEstimate();
    }, [proposalId]);

    const fetchProposalDetails = async () => {
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/proposals/${proposalId}/`);
            if (res.ok) {
                const data = await res.json();
                setProposal({
                    id: data.proposal_id,
                    proposal_id: data.proposal_id,
                    title: data.title,
                    description: data.description,
                    creator: data.proposer_details?.name || "Unknown",
                    proposer_details: data.proposer_details,
                    roundId: data.round,
                    round_details: data.round_details,
                    funding_goal: data.funding_goal,
                    total_donations: data.total_donations || 0,
                    status: data.status,
                    onChainId: data.on_chain_id,
                });
            }
        } catch (e) {
            console.error("Failed to fetch proposal:", e);
        } finally {
            setLoading(false);
        }
    };

    const fetchDonations = async () => {
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/donations/?proposal=${proposalId}`);
            if (res.ok) {
                const data = await res.json();
                setDonations(data.results || data || []);
            }
        } catch (e) {
            console.error("Failed to fetch donations:", e);
            setDonations([]);
        }
    };

    const fetchQFEstimate = async () => {
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/qf-results/?proposal=${proposalId}`);
            if (res.ok) {
                const data = await res.json();
                const results = data.results || data;
                if (results.length > 0) {
                    setQfest({ estimatedMatch: results[0].calculated_match || 0 });
                } else {
                    setQfest({ estimatedMatch: 0 });
                }
            }
        } catch (e) {
            console.error("Failed to fetch QF estimate:", e);
            setQfest({ estimatedMatch: 0 });
        }
    };

    if (loading) {
        return (
            <main className="flex min-h-screen items-center justify-center">
                <div className="text-lg">Loading...</div>
            </main>
        );
    }

    if (!proposal) {
        return (
            <main className="flex min-h-screen items-center justify-center">
                <div className="text-lg">Proposal not found</div>
            </main>
        );
    }

    const totalRaised = donations.reduce((sum, d) => sum + parseFloat(d.amount || 0), 0);
    const donorCount = donations.length;
    const fundingGoal = proposal.funding_goal || 0;
    const progress = fundingGoal > 0 ? (totalRaised / fundingGoal) * 100 : 0;
    const matchingPoolTotal = proposal.round_details?.matching_pool_details?.total_funds || 0;

    return (
        <main className="flex min-h-screen items-start justify-center p-12 bg-gray-50 dark:bg-gray-900">
            <div className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left column: main content */}
                <div className="lg:col-span-2">
                    <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-gray-200 dark:border-gray-700">
                        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                            {proposal.title}
                        </h1>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                            Created by <span className="font-mono">{proposal.creator}</span>
                            {proposal.round_details && (
                                <>
                                    <span className="mx-2">·</span>
                                    Round: <strong>{proposal.round_details.name || `Round ${proposal.roundId?.substring(0, 8)}`}</strong>
                                </>
                            )}
                            {proposal.status && (
                                <>
                                    <span className="mx-2">·</span>
                                    Status: <span className={`px-2 py-1 rounded text-xs ${proposal.status === 'approved' ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200' :
                                        proposal.status === 'pending' ? 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200' :
                                            proposal.status === 'funded' ? 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200' :
                                                'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
                                        }`}>{proposal.status}</span>
                                </>
                            )}
                        </div>

                        <div className="mt-6">
                            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Overview</h2>
                            <p className="mt-3 text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                                {proposal.description || "No description provided"}
                            </p>
                        </div>

                        {fundingGoal > 0 && (
                            <div className="mt-6 p-4 bg-amber-50 dark:bg-amber-900/30 border border-amber-100 dark:border-amber-800 rounded-lg">
                                <h3 className="font-semibold text-amber-900 dark:text-amber-200">Funding Goal</h3>
                                <p className="mt-2 text-lg font-bold text-amber-900 dark:text-amber-100">
                                    ${fundingGoal.toLocaleString()}
                                </p>
                            </div>
                        )}

                        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="p-4 bg-green-50 dark:bg-green-900/30 border border-green-100 dark:border-green-800 rounded-lg">
                                <div className="text-sm text-green-700 dark:text-green-300">Total Raised</div>
                                <div className="text-2xl font-bold text-green-900 dark:text-green-100">
                                    ${totalRaised.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                </div>
                                <div className="text-xs text-green-600 dark:text-green-400 mt-1">
                                    {donorCount} {donorCount === 1 ? "donor" : "donors"}
                                </div>
                            </div>
                            <div className="p-4 bg-blue-50 dark:bg-blue-900/30 border border-blue-100 dark:border-blue-800 rounded-lg">
                                <div className="text-sm text-blue-700 dark:text-blue-300">Matching Pool</div>
                                <div className="text-2xl font-bold text-blue-900 dark:text-blue-100">
                                    ${matchingPoolTotal.toLocaleString()}
                                </div>
                                <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                                    Available for this round
                                </div>
                            </div>
                        </div>

                        {/* Funding Progress */}
                        <div className="mt-6">
                            <h3 className="font-semibold mb-2 text-gray-900 dark:text-gray-100">
                                Funding Progress
                            </h3>
                            <div className="w-full bg-gray-200 dark:bg-gray-700 h-3 rounded-full overflow-hidden">
                                <div
                                    className="h-3 bg-green-500 rounded-full transition-all"
                                    style={{ width: `${Math.min(100, progress)}%` }}
                                />
                            </div>
                            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                                ${totalRaised.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} of ${fundingGoal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} goal (
                                {progress.toFixed(1)}%)
                            </p>
                        </div>
                    </div>
                </div>

                {/* Right column: action sidebar */}
                <aside className="lg:col-span-1 h-fit">
                    <DonationWidget
                        proposalId={proposalId}
                        estimatedMatch={qfest?.estimatedMatch}
                        onChainId={proposal.onChainId}
                    />

                    <div className="mt-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-md p-4">
                        <h4 className="font-semibold text-gray-900 dark:text-gray-100">Recent Donors</h4>
                        <div className="mt-3">
                            <RecentDonors donors={donations} />
                        </div>
                    </div>

                    <div className="mt-6 bg-indigo-50 dark:bg-indigo-900/30 border border-indigo-100 dark:border-indigo-800 rounded-lg p-4">
                        <h4 className="font-semibold text-indigo-900 dark:text-indigo-200">
                            About Quadratic Funding
                        </h4>
                        <p className="text-sm text-indigo-800 dark:text-indigo-300 mt-2">
                            Your donation's impact is amplified through quadratic matching. Smaller
                            donations from more donors get a larger match!
                        </p>
                    </div>
                </aside>
            </div>
        </main>
    );
}
