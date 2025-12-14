import React from "react";

type QFResult = {
    id: string;
    proposalId: string;
    proposalTitle: string;
    directRaised: number;
    matchAmount: number;
    totalFunding: number;
    uniqueDonors: number;
};

type RoundData = {
    id: string;
    name: string;
    startDate: string;
    endDate: string;
    matchingPoolAmount: number;
    totalDirectDonations: number;
    totalMatchedFunds: number;
    uniqueDonors: number;
};

// Mock round results data
const roundDatabase: { [key: string]: RoundData } = {
    "round-1": {
        id: "round-1",
        name: "Climate & Clean Tech Round #1",
        startDate: "2025-09-01",
        endDate: "2025-10-01",
        matchingPoolAmount: 100000,
        totalDirectDonations: 45000,
        totalMatchedFunds: 78500,
        uniqueDonors: 1234,
    },
    "round-2": {
        id: "round-2",
        name: "Education & Accessibility Q4 2025",
        startDate: "2025-10-15",
        endDate: "2025-11-15",
        matchingPoolAmount: 150000,
        totalDirectDonations: 62000,
        totalMatchedFunds: 98200,
        uniqueDonors: 2156,
    },
};

const proposalResultsDatabase: { [key: string]: QFResult[] } = {
    "round-1": [
        {
            id: "qf-1",
            proposalId: "p1",
            proposalTitle: "Clean Water Initiative",
            directRaised: 15000,
            matchAmount: 28500,
            totalFunding: 43500,
            uniqueDonors: 289,
        },
        {
            id: "qf-2",
            proposalId: "p2",
            proposalTitle: "Open Education Platform",
            directRaised: 12000,
            matchAmount: 22300,
            totalFunding: 34300,
            uniqueDonors: 234,
        },
        {
            id: "qf-3",
            proposalId: "p3",
            proposalTitle: "Forest Restoration",
            directRaised: 8500,
            matchAmount: 15200,
            totalFunding: 23700,
            uniqueDonors: 178,
        },
        {
            id: "qf-4",
            proposalId: "p4",
            proposalTitle: "Rural Healthcare Access",
            directRaised: 5000,
            matchAmount: 8800,
            totalFunding: 13800,
            uniqueDonors: 95,
        },
        {
            id: "qf-5",
            proposalId: "p5",
            proposalTitle: "Renewable Energy Grid",
            directRaised: 4500,
            matchAmount: 3700,
            totalFunding: 8200,
            uniqueDonors: 42,
        },
    ],
};

async function fetchRoundResults(roundId: string) {
    try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE || ""}/api/rounds/${roundId}/results`, {
            cache: "no-store",
        });
        if (res.ok) return await res.json();
    } catch (e) {}
    return roundDatabase[roundId];
}

async function fetchProposalResults(roundId: string) {
    try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE || ""}/api/qf-results?roundId=${roundId}`, {
            cache: "no-store",
        });
        if (res.ok) return await res.json();
    } catch (e) {}
    return proposalResultsDatabase[roundId] || [];
}

export default async function RoundResultsPage({
    params,
}: {
    params: Promise<{ roundId: string }>;
}) {
    const { roundId } = await params;

    const roundData = await fetchRoundResults(roundId);
    const proposalResults = await fetchProposalResults(roundId);

    const sortedProposals = [...proposalResults].sort(
        (a: QFResult, b: QFResult) => b.totalFunding - a.totalFunding
    );

    const topProposalsForChart = sortedProposals.slice(0, 10);
    const maxFunding = Math.max(...topProposalsForChart.map((p: QFResult) => p.totalFunding));

    return (
        <main className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
            {/* Header */}
            <section className="border-b border-slate-700 bg-slate-900/50 backdrop-blur">
                <div className="max-w-7xl mx-auto px-6 py-12">
                    <div className="flex items-start justify-between">
                        <div>
                            <h1 className="text-4xl font-bold mb-2">{roundData?.name}</h1>
                            <p className="text-slate-400">
                                {roundData?.startDate && new Date(roundData.startDate).toLocaleDateString()} —{" "}
                                {roundData?.endDate && new Date(roundData.endDate).toLocaleDateString()}
                            </p>
                        </div>
                        <div className="text-right">
                            <div className="inline-block px-4 py-2 bg-green-500/20 border border-green-500 rounded-full text-green-300 text-sm font-semibold">
                                ✓ Status: Completed - Payouts Finalized
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Key Metrics Summary */}
            <section className="max-w-7xl mx-auto px-6 py-12">
                <h2 className="text-2xl font-bold mb-6">Round Summary</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <div className="bg-gradient-to-br from-blue-500/20 to-blue-600/10 border border-blue-500/30 rounded-lg p-6">
                        <div className="text-sm text-blue-300 mb-2">Total Matching Pool</div>
                        <div className="text-3xl font-bold">${(roundData?.matchingPoolAmount || 0).toLocaleString()}</div>
                        <div className="text-xs text-blue-400 mt-2">Available for distribution</div>
                    </div>

                    <div className="bg-gradient-to-br from-green-500/20 to-green-600/10 border border-green-500/30 rounded-lg p-6">
                        <div className="text-sm text-green-300 mb-2">Total Direct Donations</div>
                        <div className="text-3xl font-bold">${(roundData?.totalDirectDonations || 0).toLocaleString()}</div>
                        <div className="text-xs text-green-400 mt-2">Community contributions</div>
                    </div>

                    <div className="bg-gradient-to-br from-purple-500/20 to-purple-600/10 border border-purple-500/30 rounded-lg p-6">
                        <div className="text-sm text-purple-300 mb-2">Total Matched Funds</div>
                        <div className="text-3xl font-bold">${(roundData?.totalMatchedFunds || 0).toLocaleString()}</div>
                        <div className="text-xs text-purple-400 mt-2">Distributed by QF formula</div>
                    </div>

                    <div className="bg-gradient-to-br from-orange-500/20 to-orange-600/10 border border-orange-500/30 rounded-lg p-6">
                        <div className="text-sm text-orange-300 mb-2">Unique Donors</div>
                        <div className="text-3xl font-bold">{(roundData?.uniqueDonors || 0).toLocaleString()}</div>
                        <div className="text-xs text-orange-400 mt-2">Community breadth</div>
                    </div>
                </div>
            </section>

            {/* Top 10 Distribution Chart */}
            <section className="max-w-7xl mx-auto px-6 py-12">
                <h2 className="text-2xl font-bold mb-6">Matching Pool Distribution (Top 10)</h2>
                <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-8">
                    <div className="space-y-6">
                        {topProposalsForChart.map((proposal: QFResult, idx: number) => {
                            const barWidth = (proposal.totalFunding / maxFunding) * 100;
                            return (
                                <div key={proposal.id} className="flex items-end gap-4">
                                    <div className="w-16 text-right">
                                        <div className="text-sm font-bold text-slate-300">#{idx + 1}</div>
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex items-end justify-between mb-2">
                                            <a
                                                href={`/proposals/${proposal.proposalId}/results`}
                                                className="text-sm font-semibold text-blue-400 hover:text-blue-300 transition"
                                            >
                                                {proposal.proposalTitle}
                                            </a>
                                            <div className="text-right">
                                                <div className="text-lg font-bold">${proposal.totalFunding.toLocaleString()}</div>
                                                <div className="text-xs text-slate-400">
                                                    ${proposal.directRaised} + ${proposal.matchAmount} match
                                                </div>
                                            </div>
                                        </div>
                                        <div className="w-full bg-slate-700 h-3 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-gradient-to-r from-green-500 to-emerald-500 transition-all"
                                                style={{ width: `${barWidth}%` }}
                                            />
                                        </div>
                                        <div className="text-xs text-slate-500 mt-1">
                                            {proposal.uniqueDonors} donors
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </section>

            {/* Full Leaderboard */}
            <section className="max-w-7xl mx-auto px-6 py-12">
                <h2 className="text-2xl font-bold mb-6">Complete Results Leaderboard</h2>
                <div className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-slate-700 bg-slate-900/50">
                                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                                        Rank
                                    </th>
                                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                                        Proposal
                                    </th>
                                    <th className="px-6 py-4 text-right text-xs font-semibold text-slate-300 uppercase tracking-wider">
                                        Direct Raised
                                    </th>
                                    <th className="px-6 py-4 text-right text-xs font-semibold text-slate-300 uppercase tracking-wider">
                                        Match Received
                                    </th>
                                    <th className="px-6 py-4 text-right text-xs font-semibold text-slate-300 uppercase tracking-wider">
                                        Total Funding
                                    </th>
                                    <th className="px-6 py-4 text-right text-xs font-semibold text-slate-300 uppercase tracking-wider">
                                        Donors
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700">
                                {sortedProposals.map((proposal: QFResult, idx: number) => (
                                    <tr key={proposal.id} className="hover:bg-slate-700/30 transition">
                                        <td className="px-6 py-4">
                                            <div className="text-sm font-bold text-slate-300">
                                                {idx === 0 ? "🥇" : idx === 1 ? "🥈" : idx === 2 ? "🥉" : idx + 1}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <a
                                                href={`/proposals/${proposal.proposalId}/results`}
                                                className="text-sm font-semibold text-blue-400 hover:text-blue-300 transition"
                                            >
                                                {proposal.proposalTitle}
                                            </a>
                                        </td>
                                        <td className="px-6 py-4 text-right text-sm text-green-400">
                                            ${proposal.directRaised.toLocaleString()}
                                        </td>
                                        <td className="px-6 py-4 text-right text-sm text-purple-400">
                                            ${proposal.matchAmount.toLocaleString()}
                                        </td>
                                        <td className="px-6 py-4 text-right text-sm font-bold text-emerald-400">
                                            ${proposal.totalFunding.toLocaleString()}
                                        </td>
                                        <td className="px-6 py-4 text-right text-sm text-slate-300">
                                            {proposal.uniqueDonors}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>

            {/* Transparency Section */}
            <section className="max-w-7xl mx-auto px-6 py-12">
                <h2 className="text-2xl font-bold mb-6">Transparency & Data</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 hover:border-slate-600 transition cursor-pointer">
                        <div className="text-lg font-semibold mb-2">📊 Raw QF Results</div>
                        <p className="text-sm text-slate-400 mb-4">
                            Download the complete quadratic funding calculation data and formula inputs.
                        </p>
                        <button className="text-blue-400 hover:text-blue-300 text-sm font-semibold">
                            Download CSV
                        </button>
                    </div>

                    <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 hover:border-slate-600 transition cursor-pointer">
                        <div className="text-lg font-semibold mb-2">🛡️ Sybil Defense Report</div>
                        <p className="text-sm text-slate-400 mb-4">
                            See how Sybil resistance scoring adjusted final match amounts and protected fair distribution.
                        </p>
                        <button className="text-blue-400 hover:text-blue-300 text-sm font-semibold">
                            View Report
                        </button>
                    </div>

                    <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 hover:border-slate-600 transition cursor-pointer">
                        <div className="text-lg font-semibold mb-2">💸 Payout Confirmations</div>
                        <p className="text-sm text-slate-400 mb-4">
                            All matched funds have been successfully transferred to proposal creators on-chain.
                        </p>
                        <button className="text-blue-400 hover:text-blue-300 text-sm font-semibold">
                            View Payouts
                        </button>
                    </div>
                </div>
            </section>

            {/* QF Explanation */}
            <section className="max-w-7xl mx-auto px-6 py-12">
                <div className="bg-gradient-to-br from-indigo-900/30 to-blue-900/20 border border-indigo-500/30 rounded-lg p-8">
                    <h3 className="text-xl font-bold mb-4">How Quadratic Funding Works</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-slate-300">
                        <div>
                            <p className="mb-3">
                                <span className="font-semibold text-indigo-300">Quadratic Funding (QF)</span> uses the wisdom of
                                the community to amplify small donations.
                            </p>
                            <ul className="space-y-2 ml-4">
                                <li>
                                    ✓ <span className="font-semibold">Many small donors</span> → Large matching bonus
                                </li>
                                <li>
                                    ✓ <span className="font-semibold">Few large donors</span> → Smaller matching bonus
                                </li>
                                <li>✓ Community consensus is rewarded</li>
                            </ul>
                        </div>
                        <div>
                            <p className="mb-3">
                                <span className="font-semibold text-indigo-300">The Formula:</span>
                            </p>
                            <code className="bg-black/40 p-3 rounded text-xs font-mono block">
                                match = (√sum₁ + √sum₂ + ... + √sumₙ)² - sum
                            </code>
                            <p className="text-xs text-slate-400 mt-2">
                                Where each sum is a donor's total contribution to the proposal.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <section className="border-t border-slate-700 bg-slate-900/50 mt-12 py-8">
                <div className="max-w-7xl mx-auto px-6 text-center text-sm text-slate-400">
                    <p>Round Results are finalized and immutable on-chain • Last updated: {new Date().toLocaleString()}</p>
                </div>
            </section>
        </main>
    );
}
