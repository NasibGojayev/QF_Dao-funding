import Link from "next/link";

type Round = {
    id: string;
    name: string;
    description: string;
    startDate: string;
    endDate: string;
    status: "upcoming" | "active" | "completed";
    matchingPoolAmount: number;
    totalDonations: number;
    proposalCount: number;
    donorCount: number;
};

type Proposal = {
    id: string;
    title: string;
    creator: string;
    description: string;
    category: string;
    directRaised: number;
    matchAmount?: number;
    uniqueDonors: number;
};

// Mock round database
const roundDatabase: { [key: string]: Round } = {
    "round-1": {
        id: "round-1",
        name: "Climate & Clean Tech Round #1",
        description: "Supporting innovative projects tackling climate change and developing clean technologies for a sustainable future.",
        startDate: "2025-09-01",
        endDate: "2025-10-01",
        status: "completed",
        matchingPoolAmount: 100000,
        totalDonations: 45000,
        proposalCount: 5,
        donorCount: 1234,
    },
    "round-2": {
        id: "round-2",
        name: "Education & Accessibility Q4 2025",
        description: "Funding initiatives that improve educational access and make technology more accessible to underserved communities.",
        startDate: "2025-10-15",
        endDate: "2025-11-15",
        status: "active",
        matchingPoolAmount: 150000,
        totalDonations: 62000,
        proposalCount: 8,
        donorCount: 2156,
    },
    "round-3": {
        id: "round-3",
        name: "Healthcare Innovation Round #2",
        description: "Accelerating healthcare solutions including telemedicine, medical research, and public health infrastructure.",
        startDate: "2025-12-01",
        endDate: "2026-01-01",
        status: "upcoming",
        matchingPoolAmount: 200000,
        totalDonations: 0,
        proposalCount: 0,
        donorCount: 0,
    },
};

const proposalsByRound: { [key: string]: Proposal[] } = {
    "round-1": [
        {
            id: "p1",
            title: "Clean Water Initiative",
            creator: "0xabc123...def789",
            description: "Installing water filtration systems in rural areas to provide clean drinking water.",
            category: "Environment",
            directRaised: 15000,
            matchAmount: 28500,
            uniqueDonors: 289,
        },
        {
            id: "p2",
            title: "Open Education Platform",
            creator: "0xdef456...ghi012",
            description: "Building a free, decentralized learning platform with STEM courses.",
            category: "Education",
            directRaised: 12000,
            matchAmount: 22300,
            uniqueDonors: 234,
        },
        {
            id: "p3",
            title: "Forest Restoration",
            creator: "0xghi789...jkl345",
            description: "Reforestation initiative to plant 100,000 native trees.",
            category: "Environment",
            directRaised: 8500,
            matchAmount: 15200,
            uniqueDonors: 178,
        },
        {
            id: "p4",
            title: "Rural Healthcare Access",
            creator: "0xjkl012...mno678",
            description: "Establishing mobile health clinics in underserved regions.",
            category: "Healthcare",
            directRaised: 5000,
            matchAmount: 8800,
            uniqueDonors: 95,
        },
        {
            id: "p5",
            title: "Renewable Energy Grid",
            creator: "0xmno345...pqr901",
            description: "Building community-owned solar and wind energy infrastructure.",
            category: "Energy",
            directRaised: 4500,
            matchAmount: 3700,
            uniqueDonors: 42,
        },
    ],
    "round-2": [
        {
            id: "p6",
            title: "AI Literacy Program",
            creator: "0xpqr678...stu234",
            description: "Teaching AI fundamentals to underprivileged youth.",
            category: "Education",
            directRaised: 18000,
            matchAmount: 32500,
            uniqueDonors: 312,
        },
        {
            id: "p7",
            title: "Accessible Web Framework",
            creator: "0xstu901...uvw567",
            description: "Open-source framework for building accessible web applications.",
            category: "Accessibility",
            directRaised: 14000,
            matchAmount: 25600,
            uniqueDonors: 287,
        },
        {
            id: "p8",
            title: "Sign Language Video Library",
            creator: "0xuvw234...xyz890",
            description: "Building the largest free sign language video resource library.",
            category: "Accessibility",
            directRaised: 10000,
            matchAmount: 18200,
            uniqueDonors: 156,
        },
    ],
};

async function fetchRound(roundId: string) {
    try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE || ""}/api/rounds/${roundId}`, {
            cache: "no-store",
        });
        if (res.ok) return await res.json();
    } catch (e) { }
    return roundDatabase[roundId];
}

async function fetchProposals(roundId: string) {
    try {
        const res = await fetch(
            `${process.env.NEXT_PUBLIC_API_BASE || ""}/api/proposals?roundId=${roundId}`,
            { cache: "no-store" }
        );
        if (res.ok) return await res.json();
    } catch (e) { }
    return proposalsByRound[roundId] || [];
}

export default async function RoundDetailPage({
    params,
}: {
    params: Promise<{ roundId: string }>;
}) {
    const { roundId } = await params;

    const round = await fetchRound(roundId);
    const proposals = await fetchProposals(roundId);

    if (!round) {
        return (
            <main className="min-h-screen bg-background text-foreground flex items-center justify-center">
                <div className="text-center">
                    <h1 className="text-2xl font-bold mb-2">Round Not Found</h1>
                    <p className="text-muted-foreground mb-6">The round you're looking for doesn't exist.</p>
                    <Link href="/rounds" className="text-primary hover:text-primary/80">
                        ← Back to Rounds
                    </Link>
                </div>
            </main>
        );
    }

    const isActive = round.status === "active";
    const isCompleted = round.status === "completed";
    const sortedProposals = [...proposals].sort(
        (a: Proposal, b: Proposal) => (b.matchAmount || 0) - (a.matchAmount || 0)
    );

    return (
        <main className="min-h-screen bg-background text-foreground pt-20">
            {/* Header */}
            <section className="border-b border-border bg-card/50 backdrop-blur-sm">
                <div className="max-w-7xl mx-auto px-6 py-12">
                    <div className="flex items-start justify-between mb-6">
                        <div>
                            <h1 className="text-4xl font-bold mb-2 text-foreground">{round.name}</h1>
                            <p className="text-muted-foreground max-w-2xl">{round.description}</p>
                        </div>
                        <div>
                            <div className={`inline-block px-4 py-2 rounded-full text-sm font-semibold ${isActive
                                ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200 border border-green-200 dark:border-green-800"
                                : isCompleted
                                    ? "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200 border border-blue-200 dark:border-blue-800"
                                    : "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-200 border border-amber-200 dark:border-amber-800"
                                }`}>
                                {isActive ? "🔴 Active" : isCompleted ? "✓ Completed" : "📅 Upcoming"}
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <span>📅 {new Date(round.startDate).toLocaleDateString()} → {new Date(round.endDate).toLocaleDateString()}</span>
                    </div>
                </div>
            </section>

            {/* Key Metrics */}
            <section className="max-w-7xl mx-auto px-6 py-12">
                <h2 className="text-2xl font-bold mb-6 text-foreground">Round Overview</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
                        <div className="text-sm text-muted-foreground mb-2">Matching Pool</div>
                        <div className="text-3xl font-bold text-foreground">${round.matchingPoolAmount.toLocaleString()}</div>
                        <div className="text-xs text-primary mt-2">Available for QF distribution</div>
                    </div>

                    <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
                        <div className="text-sm text-muted-foreground mb-2">Community Donations</div>
                        <div className="text-3xl font-bold text-foreground">${round.totalDonations.toLocaleString()}</div>
                        <div className="text-xs text-primary mt-2">Direct contributions</div>
                    </div>

                    <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
                        <div className="text-sm text-muted-foreground mb-2">Total Proposals</div>
                        <div className="text-3xl font-bold text-foreground">{round.proposalCount}</div>
                        <div className="text-xs text-primary mt-2">Requesting funding</div>
                    </div>

                    <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
                        <div className="text-sm text-muted-foreground mb-2">Community Size</div>
                        <div className="text-3xl font-bold text-foreground">{round.donorCount.toLocaleString()}</div>
                        <div className="text-xs text-primary mt-2">Unique donors</div>
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            {isActive && (
                <section className="max-w-7xl mx-auto px-6 py-8">
                    <div className="bg-gradient-to-r from-blue-600/10 to-indigo-600/10 border border-blue-500/20 rounded-lg p-8">
                        <div className="flex items-center justify-between">
                            <div>
                                <h3 className="text-xl font-bold mb-2 text-foreground">Round is Currently Active</h3>
                                <p className="text-muted-foreground">Browse and support projects that are actively seeking funding right now.</p>
                            </div>
                            <Link href={`/proposals?roundId=${roundId}`}
                                className="px-6 py-3 bg-primary text-primary-foreground hover:bg-primary/90 rounded-lg font-semibold transition shadow-sm">
                                View Proposals
                            </Link>
                        </div>
                    </div>
                </section>
            )}

            {/* Proposals Section */}
            <section className="max-w-7xl mx-auto px-6 py-12">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-foreground">Proposals in This Round</h2>
                    {isCompleted && (
                        <Link href={`/rounds/${roundId}/results`}
                            className="text-primary hover:text-primary/80 text-sm font-semibold">
                            View Final Results →
                        </Link>
                    )}
                </div>

                {proposals && proposals.length > 0 ? (
                    <div className="grid gap-6">
                        {sortedProposals.map((proposal: Proposal, idx: number) => (
                            <div key={proposal.id} className="bg-card border border-border rounded-lg p-6 hover:shadow-md transition">
                                <div className="flex items-start justify-between mb-4">
                                    <div>
                                        <div className="flex items-center gap-2 mb-2">
                                            <span className="text-sm font-semibold text-muted-foreground">#{idx + 1}</span>
                                            <span className="bg-secondary text-secondary-foreground px-2 py-1 rounded text-xs">{proposal.category}</span>
                                        </div>
                                        <h3 className="text-xl font-bold mb-1 text-foreground">{proposal.title}</h3>
                                        <p className="text-sm text-muted-foreground">By {proposal.creator}</p>
                                    </div>
                                    <Link href={`/proposals/${proposal.id}`}
                                        className="px-4 py-2 bg-primary text-primary-foreground hover:bg-primary/90 rounded text-sm font-semibold transition">
                                        View
                                    </Link>
                                </div>

                                <p className="text-muted-foreground mb-4">{proposal.description}</p>

                                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                                    <div className="bg-secondary/20 rounded p-3 border border-border/50">
                                        <div className="text-xs text-muted-foreground mb-1">Direct Raised</div>
                                        <div className="text-lg font-bold text-green-600 dark:text-green-400">${proposal.directRaised.toLocaleString()}</div>
                                    </div>
                                    {proposal.matchAmount !== undefined && (
                                        <div className="bg-secondary/20 rounded p-3 border border-border/50">
                                            <div className="text-xs text-muted-foreground mb-1">Match Amount</div>
                                            <div className="text-lg font-bold text-purple-600 dark:text-purple-400">${proposal.matchAmount.toLocaleString()}</div>
                                        </div>
                                    )}
                                    <div className="bg-secondary/20 rounded p-3 border border-border/50">
                                        <div className="text-xs text-muted-foreground mb-1">Total Funded</div>
                                        <div className="text-lg font-bold text-emerald-600 dark:text-emerald-400">
                                            ${(proposal.directRaised + (proposal.matchAmount || 0)).toLocaleString()}
                                        </div>
                                    </div>
                                    <div className="bg-secondary/20 rounded p-3 border border-border/50">
                                        <div className="text-xs text-muted-foreground mb-1">Unique Donors</div>
                                        <div className="text-lg font-bold text-orange-600 dark:text-orange-400">{proposal.uniqueDonors}</div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="bg-card border-dashed border border-border rounded-lg p-12 text-center">
                        <p className="text-muted-foreground mb-4">No proposals yet in this round.</p>
                        {isActive && (
                            <Link href="/proposals/new" className="text-primary hover:text-primary/80 text-sm font-semibold">
                                Be the first to create a proposal →
                            </Link>
                        )}
                    </div>
                )}
            </section>

            {/* How QF Works */}
            <section className="max-w-7xl mx-auto px-6 py-12">
                <div className="bg-gradient-to-br from-indigo-50 to-blue-50 dark:from-indigo-900/20 dark:to-blue-900/10 border border-indigo-200 dark:border-indigo-800 rounded-lg p-8">
                    <h3 className="text-xl font-bold mb-6 text-foreground">How Quadratic Funding Works in This Round</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm text-foreground">
                        <div>
                            <div className="text-lg font-semibold text-indigo-600 dark:text-indigo-400 mb-2">1. Community Votes</div>
                            <p className="text-muted-foreground">Donors contribute directly to their favorite proposals. More donors = bigger match.</p>
                        </div>
                        <div>
                            <div className="text-lg font-semibold text-indigo-600 dark:text-indigo-400 mb-2">2. QF Algorithm</div>
                            <p className="text-muted-foreground">The matching pool is distributed based on the quadratic formula, amplifying community consensus.</p>
                        </div>
                        <div>
                            <div className="text-lg font-semibold text-indigo-600 dark:text-indigo-400 mb-2">3. Results Published</div>
                            <p className="text-muted-foreground">Final funding amounts are calculated and payouts are processed on-chain transparently.</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer CTA */}
            {isCompleted && (
                <section className="max-w-7xl mx-auto px-6 py-12">
                    <div className="bg-card border border-border rounded-lg p-8 text-center">
                        <h3 className="text-xl font-bold mb-4 text-foreground">Round Completed</h3>
                        <p className="text-muted-foreground mb-6">All funding has been distributed. View the complete results and on-chain records.</p>
                        <Link href={`/rounds/${roundId}/results`}
                            className="inline-block px-6 py-3 bg-primary text-primary-foreground hover:bg-primary/90 rounded-lg font-semibold transition">
                            View Final Results & Transparency Report
                        </Link>
                    </div>
                </section>
            )}
        </main>
    );
}
