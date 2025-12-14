"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import ProposalCard from "../components/ProposalCard";

type Proposal = {
    id: string;
    proposal_id?: string;
    title: string;
    description?: string;
    creator?: string;
    proposer_details?: {
        username: string;
        donor_id: string;
    };
    donations?: number;
    donation_count?: number;
    amount?: number;
    total_funding?: number;
    category?: string;
    status?: string;
    round?: string;
    round_details?: any;
};

type Round = {
    round_id: string;
    name?: string;
    status: string;
};

type Donor = {
    donor_id: string;
    username: string;
};

export default function ProposalsPage() {
    const [proposals, setProposals] = useState<Proposal[]>([]);
    const [rounds, setRounds] = useState<Round[]>([]);
    const [donors, setDonors] = useState<Donor[]>([]);
    const [showCreate, setShowCreate] = useState(false);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState("");
    const [currentUser, setCurrentUser] = useState<any>(null);

    const [formData, setFormData] = useState({
        title: "",
        description: "",
        proposer: "",
        round: "",
        funding_goal: "",
        status: "pending",
    });

    const [filters, setFilters] = useState({
        search: "",
        round: "",
        status: "",
    });

    useEffect(() => {
        // Get logged-in user from localStorage
        const storedUser = localStorage.getItem("user");
        if (storedUser) {
            const user = JSON.parse(storedUser);
            setCurrentUser(user);

            // Auto-populate proposer with user's user_id
            if (user.user_id) {
                setFormData((prev) => ({
                    ...prev,
                    proposer: user.user_id,
                }));
            }
        }

        fetchProposals();
        fetchRounds();
        fetchDonors();
    }, []);

    const fetchProposals = async () => {
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/proposals/`, {
                cache: "no-store",
            });
            if (res.ok) {
                const data = await res.json();
                const proposalsData = data.results || data;
                const mapped = proposalsData.map((p: any) => ({
                    id: p.proposal_id || p.id,
                    proposal_id: p.proposal_id,
                    title: p.title,
                    description: p.description,
                    creator: p.proposer_details?.name || "Unknown",
                    proposer_details: p.proposer_details,
                    donations: p.donation_count || 0,
                    amount: p.total_funding || p.total_donations || 0,
                    status: p.status,
                    round: p.round,
                    round_details: p.round_details,
                }));
                setProposals(mapped);
            }
        } catch (e) {
            console.error("Failed to fetch proposals:", e);
        }
    };

    const fetchRounds = async () => {
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/rounds/`);
            if (res.ok) {
                const data = await res.json();
                setRounds(data.results || data);
            }
        } catch (e) {
            console.error("Failed to fetch rounds:", e);
        }
    };

    const fetchDonors = async () => {
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/donors/`);
            if (res.ok) {
                const data = await res.json();
                setDonors(data.results || data);
            }
        } catch (e) {
            console.error("Failed to fetch donors:", e);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setMessage("");

        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/proposals/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    ...formData,
                    funding_goal: parseFloat(formData.funding_goal) || 0,
                }),
            });

            if (res.ok) {
                setMessage("Proposal created successfully!");
                setFormData({
                    title: "",
                    description: "",
                    proposer: currentUser?.user_id || "",
                    round: "",
                    funding_goal: "",
                    status: "pending",
                });
                fetchProposals();
                setTimeout(() => {
                    setShowCreate(false);
                    setMessage("");
                }, 1500);
            } else {
                const error = await res.json();
                setMessage(`Error: ${JSON.stringify(error)}`);
            }
        } catch (e) {
            setMessage(`Error: ${e}`);
        } finally {
            setLoading(false);
        }
    };

    const filteredProposals = proposals.filter((p) => {
        if (filters.search && !p.title.toLowerCase().includes(filters.search.toLowerCase())) {
            return false;
        }
        if (filters.round && p.round !== filters.round) {
            return false;
        }
        if (filters.status && p.status !== filters.status) {
            return false;
        }
        return true;
    });

    return (
        <main className="flex min-h-screen flex-col items-start justify-start p-12 space-y-6 bg-background">
            <div className="w-full max-w-6xl">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h1 className="text-3xl font-bold text-foreground">
                            Proposals
                        </h1>
                        <p className="text-sm text-muted-foreground mt-1">
                            Browse and create funding proposals for active rounds
                        </p>
                    </div>
                    <Link
                        href="/proposals/new"
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-semibold shadow-sm"
                    >
                        + Create Proposal
                    </Link>
                </div>

                {showCreate ? (
                    <div className="bg-card rounded-lg shadow-sm border border-border p-6 mb-6">
                        <h2 className="text-2xl font-semibold mb-4 text-foreground">
                            Create New Proposal
                        </h2>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-foreground mb-1">
                                    Title
                                </label>
                                <input
                                    type="text"
                                    value={formData.title}
                                    onChange={(e) =>
                                        setFormData({ ...formData, title: e.target.value })
                                    }
                                    className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground focus:ring-2 focus:ring-primary outline-none transition"
                                    placeholder="Clean Water Initiative"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-foreground mb-1">
                                    Description
                                </label>
                                <textarea
                                    value={formData.description}
                                    onChange={(e) =>
                                        setFormData({ ...formData, description: e.target.value })
                                    }
                                    className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground focus:ring-2 focus:ring-primary outline-none transition min-h-[100px]"
                                    placeholder="Describe your proposal..."
                                    required
                                />
                            </div>

                            {!currentUser ? (
                                <div className="p-3 rounded-lg bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200 border border-yellow-200 dark:border-yellow-800">
                                    Please log in to create a proposal.
                                </div>
                            ) : (
                                <div className="p-3 rounded-lg bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 border border-blue-200 dark:border-blue-800">
                                    Creating proposal as: <strong>{currentUser.name}</strong>
                                </div>
                            )}

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-foreground mb-1">
                                        Funding Goal ($)
                                    </label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        value={formData.funding_goal}
                                        onChange={(e) =>
                                            setFormData({ ...formData, funding_goal: e.target.value })
                                        }
                                        className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground focus:ring-2 focus:ring-primary outline-none transition"
                                        placeholder="10000.00"
                                        required
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-foreground mb-1">
                                        Round
                                    </label>
                                    <select
                                        value={formData.round}
                                        onChange={(e) =>
                                            setFormData({ ...formData, round: e.target.value })
                                        }
                                        className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground focus:ring-2 focus:ring-primary outline-none transition"
                                        required
                                    >
                                        <option value="">Select a round</option>
                                        {rounds.map((round) => (
                                            <option key={round.round_id} value={round.round_id}>
                                                {round.name || `Round ${round.round_id.substring(0, 8)}`} ({round.status})
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full px-6 py-3 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 transition disabled:opacity-50 shadow-sm"
                            >
                                {loading ? "Creating..." : "Create Proposal"}
                            </button>

                            {message && (
                                <div
                                    className={`p-3 rounded-lg ${message.includes("Error")
                                        ? "bg-destructive/10 text-destructive border border-destructive/20"
                                        : "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200 border border-green-200 dark:border-green-800"
                                        }`}
                                >
                                    {message}
                                </div>
                            )}
                        </form>
                    </div>
                ) : (
                    <>
                        <div className="bg-card rounded-lg shadow-sm border border-border p-4 mb-6">
                            <div className="flex gap-3 items-center flex-wrap">
                                <input
                                    value={filters.search}
                                    onChange={(e) =>
                                        setFilters({ ...filters, search: e.target.value })
                                    }
                                    placeholder="Search proposals"
                                    className="border border-input px-3 py-2 rounded-lg w-64 bg-background text-foreground focus:ring-2 focus:ring-primary outline-none transition"
                                />
                                <select
                                    value={filters.round}
                                    onChange={(e) =>
                                        setFilters({ ...filters, round: e.target.value })
                                    }
                                    className="border border-input px-3 py-2 rounded-lg bg-background text-foreground focus:ring-2 focus:ring-primary outline-none transition"
                                >
                                    <option value="">All rounds</option>
                                    {rounds.map((round) => (
                                        <option key={round.round_id} value={round.round_id}>
                                            {round.name || `Round ${round.round_id.substring(0, 8)}`}
                                        </option>
                                    ))}
                                </select>
                                <select
                                    value={filters.status}
                                    onChange={(e) =>
                                        setFilters({ ...filters, status: e.target.value })
                                    }
                                    className="border border-input px-3 py-2 rounded-lg bg-background text-foreground focus:ring-2 focus:ring-primary outline-none transition"
                                >
                                    <option value="">All statuses</option>
                                    <option value="pending">Pending</option>
                                    <option value="approved">Approved</option>
                                    <option value="rejected">Rejected</option>
                                    <option value="funded">Funded</option>
                                </select>
                                <button
                                    onClick={() =>
                                        setFilters({ search: "", round: "", status: "" })
                                    }
                                    className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition font-medium"
                                >
                                    Clear
                                </button>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {filteredProposals.length === 0 ? (
                                <div className="col-span-2 p-6 border border-dashed border-border rounded-lg bg-card/50 text-center">
                                    <p className="text-muted-foreground">
                                        No proposals found. Create one to get started!
                                    </p>
                                </div>
                            ) : (
                                filteredProposals.map((p) => (
                                    <ProposalCard key={p.id} proposal={p} />
                                ))
                            )}
                        </div>
                    </>
                )}
            </div>
        </main>
    );
}
