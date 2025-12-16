import Link from "next/link";

type Round = {
    id: string;
    round_id?: string;
    name: string;
    description?: string;
    startDate?: string;
    start_date?: string;
    endDate?: string;
    end_date?: string;
    status: string;
    matching_pool_details?: {
        total_funds: number;
        allocated_funds: number;
    };
    matchingPoolAmount?: number;
    totalDonations?: number;
    total_donations?: number;
    proposalCount?: number;
    total_proposals?: number;
    donorCount?: number;
};

type Proposal = {
    proposal_id?: string;
    id?: string;
    title: string;
    proposer_details?: {
        address?: string;
        username?: string;
    };
    creator?: string;
    description: string;
    category?: string;
    directRaised?: number;
    total_donations?: number;
    matchAmount?: number;
    match_amount?: number;
    uniqueDonors?: number;
    donation_count?: number;
};

async function fetchRound(roundId: string): Promise<Round | null> {
    // Extract the UUID from "round-{uuid}" format
    const uuid = roundId.startsWith("round-") ? roundId.replace("round-", "") : roundId;

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    try {
        const res = await fetch(`${apiUrl}/rounds/${uuid}/`, {
            cache: "no-store",
        });
        if (res.ok) {
            return await res.json();
        }
    } catch (e) {
        console.error("Failed to fetch round:", e);
    }
    return null;
}

async function fetchProposals(roundId: string): Promise<Proposal[]> {
    // Extract the UUID from "round-{uuid}" format
    const uuid = roundId.startsWith("round-") ? roundId.replace("round-", "") : roundId;

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    try {
        // Use the round's proposals endpoint
        const res = await fetch(`${apiUrl}/rounds/${uuid}/proposals/`, {
            cache: "no-store",
        });
        if (res.ok) {
            return await res.json();
        }
    } catch (e) {
        console.error("Failed to fetch proposals:", e);
    }
    return [];
}

// Helper functions to normalize data from backend
function getStartDate(round: Round): string {
    return round.start_date || round.startDate || "";
}

function getEndDate(round: Round): string {
    return round.end_date || round.endDate || "";
}

function getMatchingPoolAmount(round: Round): number {
    return round.matching_pool_details?.total_funds || round.matchingPoolAmount || 0;
}

function getTotalDonations(round: Round): number {
    return round.total_donations || round.totalDonations || 0;
}

function getProposalCount(round: Round): number {
    return round.total_proposals || round.proposalCount || 0;
}

function getProposerId(proposal: Proposal): string {
    return proposal.proposal_id || proposal.id || "";
}

function getProposerDisplay(proposal: Proposal): string {
    if (proposal.proposer_details) {
        return proposal.proposer_details.username || proposal.proposer_details.address || "Unknown";
    }
    return proposal.creator || "Unknown";
}

function getDirectRaised(proposal: Proposal): number {
    return proposal.total_donations || proposal.directRaised || 0;
}

function getMatchAmount(proposal: Proposal): number {
    return proposal.match_amount || proposal.matchAmount || 0;
}

function getDonorCount(proposal: Proposal): number {
    return proposal.donation_count || proposal.uniqueDonors || 0;
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
    const isCompleted = round.status === "completed" || round.status === "closed";
    const sortedProposals = [...proposals].sort(
        (a: Proposal, b: Proposal) => getMatchAmount(b) - getMatchAmount(a)
    );

    const startDateStr = getStartDate(round);
    const endDateStr = getEndDate(round);
    const matchingPoolAmount = getMatchingPoolAmount(round);
    const totalDonations = getTotalDonations(round);
    const proposalCount = getProposalCount(round);

    return (
        <main className="min-h-screen bg-background text-foreground pt-20">
            {/* Header */}
            <section className="border-b border-border bg-card/50 backdrop-blur-sm">
                <div className="max-w-7xl mx-auto px-6 py-12">
                    <div className="flex items-start justify-between mb-6">
                        <div>
                            <h1 className="text-4xl font-bold mb-2 text-foreground">{round.name}</h1>
                            <p className="text-muted-foreground max-w-2xl">{round.description || "A funding round for community projects."}</p>
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
                        <span>📅 {startDateStr ? new Date(startDateStr).toLocaleDateString() : "TBD"} → {endDateStr ? new Date(endDateStr).toLocaleDateString() : "TBD"}</span>
                    </div>
                </div>
            </section>

            {/* Key Metrics */}
            <section className="max-w-7xl mx-auto px-6 py-12">
                <h2 className="text-2xl font-bold mb-6 text-foreground">Round Overview</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
                        <div className="text-sm text-muted-foreground mb-2">Matching Pool</div>
                        <div className="text-3xl font-bold text-foreground">${matchingPoolAmount.toLocaleString()}</div>
                        <div className="text-xs text-primary mt-2">Available for QF distribution</div>
                    </div>

                    <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
                        <div className="text-sm text-muted-foreground mb-2">Community Donations</div>
                        <div className="text-3xl font-bold text-foreground">${totalDonations.toLocaleString()}</div>
                        <div className="text-xs text-primary mt-2">Direct contributions</div>
                    </div>

                    <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
                        <div className="text-sm text-muted-foreground mb-2">Total Proposals</div>
                        <div className="text-3xl font-bold text-foreground">{proposalCount}</div>
                        <div className="text-xs text-primary mt-2">Requesting funding</div>
                    </div>

                    <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
                        <div className="text-sm text-muted-foreground mb-2">Proposals Listed</div>
                        <div className="text-3xl font-bold text-foreground">{proposals.length}</div>
                        <div className="text-xs text-primary mt-2">In this round</div>
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
                            <Link href={`/proposals`}
                                className="px-6 py-3 bg-primary text-primary-foreground hover:bg-primary/90 rounded-lg font-semibold transition shadow-sm">
                                View All Proposals
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
                        {sortedProposals.map((proposal: Proposal, idx: number) => {
                            const proposalId = getProposerId(proposal);
                            const proposerDisplay = getProposerDisplay(proposal);
                            const directRaised = getDirectRaised(proposal);
                            const matchAmount = getMatchAmount(proposal);
                            const donorCount = getDonorCount(proposal);

                            return (
                                <div key={proposalId} className="bg-card border border-border rounded-lg p-6 hover:shadow-md transition">
                                    <div className="flex items-start justify-between mb-4">
                                        <div>
                                            <div className="flex items-center gap-2 mb-2">
                                                <span className="text-sm font-semibold text-muted-foreground">#{idx + 1}</span>
                                                {proposal.category && (
                                                    <span className="bg-secondary text-secondary-foreground px-2 py-1 rounded text-xs">{proposal.category}</span>
                                                )}
                                            </div>
                                            <h3 className="text-xl font-bold mb-1 text-foreground">{proposal.title}</h3>
                                            <p className="text-sm text-muted-foreground">By {proposerDisplay}</p>
                                        </div>
                                        <Link href={`/proposals/${proposalId}`}
                                            className="px-4 py-2 bg-primary text-primary-foreground hover:bg-primary/90 rounded text-sm font-semibold transition">
                                            View
                                        </Link>
                                    </div>

                                    <p className="text-muted-foreground mb-4">{proposal.description}</p>

                                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                                        <div className="bg-secondary/20 rounded p-3 border border-border/50">
                                            <div className="text-xs text-muted-foreground mb-1">Direct Raised</div>
                                            <div className="text-lg font-bold text-green-600 dark:text-green-400">${directRaised.toLocaleString()}</div>
                                        </div>
                                        {matchAmount > 0 && (
                                            <div className="bg-secondary/20 rounded p-3 border border-border/50">
                                                <div className="text-xs text-muted-foreground mb-1">Match Amount</div>
                                                <div className="text-lg font-bold text-purple-600 dark:text-purple-400">${matchAmount.toLocaleString()}</div>
                                            </div>
                                        )}
                                        <div className="bg-secondary/20 rounded p-3 border border-border/50">
                                            <div className="text-xs text-muted-foreground mb-1">Total Funded</div>
                                            <div className="text-lg font-bold text-emerald-600 dark:text-emerald-400">
                                                ${(directRaised + matchAmount).toLocaleString()}
                                            </div>
                                        </div>
                                        <div className="bg-secondary/20 rounded p-3 border border-border/50">
                                            <div className="text-xs text-muted-foreground mb-1">Donations</div>
                                            <div className="text-lg font-bold text-orange-600 dark:text-orange-400">{donorCount}</div>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
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
