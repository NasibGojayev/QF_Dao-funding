"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import RoundCard from "../components/RoundCard";

type Round = {
    id: string;
    name?: string;
    startDate: string;
    endDate: string;
    pool?: number;
    totalDonations?: number;
    status?: string;
};

type MatchingPool = {
    pool_id: string;
    total_funds: number;
    replenished_by: string;
};

function getStatus(r: Round & { status?: string }) {
    if (r.status) {
        return r.status;
    }

    const now = Date.now();
    const s = new Date(r.startDate).getTime();
    const e = new Date(r.endDate).getTime();

    if (isNaN(s) || isNaN(e)) {
        console.error("Invalid date in round:", r);
        return "upcoming";
    }

    if (now < s) return "upcoming";
    if (now > e) return "past";
    return "active";
}

export default function RoundsPage() {
    const [tab, setTab] = useState("active");
    const [showCreate, setShowCreate] = useState(false);
    const [rounds, setRounds] = useState<Round[]>([]);
    const [matchingPools, setMatchingPools] = useState<MatchingPool[]>([]);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState("");

    const [formData, setFormData] = useState({
        start_date: "",
        end_date: "",
        matching_pool: "",
        status: "upcoming",
    });

    useEffect(() => {
        fetchRounds();
        fetchMatchingPools();
    }, []);

    const fetchRounds = async () => {
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/rounds/`, {
                cache: "no-store",
            });
            if (res.ok) {
                const data = await res.json();
                const roundsData = data.results || data;
                const mappedRounds = roundsData.map((r: any) => ({
                    id: r.id || `round-${r.round_id}`,
                    name: r.name || `Round ${r.round_id?.substring(0, 8)}`,
                    startDate: r.start_date,
                    endDate: r.end_date || r.endDate,
                    pool: r.pool || r.matching_pool_details?.total_funds,
                    totalDonations: r.total_donations || 0,
                    status: r.status,
                }));
                setRounds(mappedRounds);
            }
        } catch (e) {
            console.error("Failed to fetch rounds:", e);
            setRounds([]);
        }
    };

    const fetchMatchingPools = async () => {
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/matching-pools/`);
            if (res.ok) {
                const data = await res.json();
                setMatchingPools(data.results || data);
            }
        } catch (e) {
            console.error("Failed to fetch matching pools:", e);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setMessage("");

        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/rounds/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(formData),
            });

            if (res.ok) {
                setMessage("Round created successfully!");
                setFormData({
                    start_date: "",
                    end_date: "",
                    matching_pool: "",
                    status: "upcoming",
                });
                fetchRounds();
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

    let filtered: Round[] = [];
    if (tab === "all") {
        filtered = rounds;
    } else if (tab === "past") {
        filtered = rounds.filter((r) => {
            const status = getStatus(r);
            return status === "past" || status === "closed";
        });
    } else {
        filtered = rounds.filter((r) => getStatus(r) === tab);
    }

    return (
        <main className="flex min-h-screen flex-col items-center justify-start p-12 space-y-6 bg-background">
            <div className="w-full max-w-6xl">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h1 className="text-3xl font-bold text-foreground">
                            Rounds
                        </h1>
                        <p className="text-sm text-muted-foreground mt-1">
                            History and current funding cycles
                        </p>
                    </div>
                    <button
                        onClick={() => setShowCreate(!showCreate)}
                        className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition font-semibold shadow-sm"
                    >
                        {showCreate ? "View Rounds" : "+ Create Round"}
                    </button>
                </div>

                {showCreate ? (
                    <div className="bg-card rounded-lg shadow-sm border border-border p-6 mb-6">
                        <h2 className="text-2xl font-semibold mb-4 text-foreground">
                            Create New Round
                        </h2>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-foreground mb-1">
                                        Start Date
                                    </label>
                                    <input
                                        type="datetime-local"
                                        value={formData.start_date}
                                        onChange={(e) =>
                                            setFormData({ ...formData, start_date: e.target.value })
                                        }
                                        className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground focus:ring-2 focus:ring-primary outline-none transition"
                                        required
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-foreground mb-1">
                                        End Date
                                    </label>
                                    <input
                                        type="datetime-local"
                                        value={formData.end_date}
                                        onChange={(e) =>
                                            setFormData({ ...formData, end_date: e.target.value })
                                        }
                                        className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground focus:ring-2 focus:ring-primary outline-none transition"
                                        required
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-foreground mb-1">
                                        Matching Pool
                                    </label>
                                    <select
                                        value={formData.matching_pool}
                                        onChange={(e) =>
                                            setFormData({
                                                ...formData,
                                                matching_pool: e.target.value,
                                            })
                                        }
                                        className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground focus:ring-2 focus:ring-primary outline-none transition"
                                        required
                                    >
                                        <option value="">Select a matching pool</option>
                                        {matchingPools.map((pool) => (
                                            <option key={pool.pool_id} value={pool.pool_id}>
                                                Pool {pool.pool_id.substring(0, 8)} - $
                                                {pool.total_funds.toLocaleString()} (
                                                {pool.replenished_by})
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-foreground mb-1">
                                        Status
                                    </label>
                                    <select
                                        value={formData.status}
                                        onChange={(e) =>
                                            setFormData({ ...formData, status: e.target.value })
                                        }
                                        className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground focus:ring-2 focus:ring-primary outline-none transition"
                                    >
                                        <option value="upcoming">Upcoming</option>
                                        <option value="active">Active</option>
                                        <option value="closed">Closed</option>
                                    </select>
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full px-6 py-3 bg-primary text-primary-foreground rounded-lg font-semibold hover:bg-primary/90 transition disabled:opacity-50 shadow-sm"
                            >
                                {loading ? "Creating..." : "Create Round"}
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
                        <div className="flex items-center space-x-3 mb-6">
                            <button
                                onClick={() => setTab("active")}
                                className={`px-4 py-2 rounded-lg transition font-medium ${tab === "active"
                                    ? "bg-primary text-primary-foreground"
                                    : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
                                    }`}
                            >
                                Active
                            </button>
                            <button
                                onClick={() => setTab("upcoming")}
                                className={`px-4 py-2 rounded-lg transition font-medium ${tab === "upcoming"
                                    ? "bg-primary text-primary-foreground"
                                    : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
                                    }`}
                            >
                                Upcoming
                            </button>
                            <button
                                onClick={() => setTab("past")}
                                className={`px-4 py-2 rounded-lg transition font-medium ${tab === "past"
                                    ? "bg-primary text-primary-foreground"
                                    : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
                                    }`}
                            >
                                Past
                            </button>
                            <button
                                onClick={() => setTab("all")}
                                className={`px-4 py-2 rounded-lg transition font-medium ${tab === "all"
                                    ? "bg-primary text-primary-foreground"
                                    : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
                                    }`}
                            >
                                All
                            </button>
                        </div>

                        <div>
                            {filtered.length === 0 ? (
                                <div className="p-6 border border-dashed border-border rounded-lg bg-card/50 text-center">
                                    <div className="text-sm text-foreground">
                                        No rounds found for <strong>{tab}</strong>.
                                    </div>
                                    {tab === "upcoming" && (
                                        <div className="mt-2 text-sm text-muted-foreground">
                                            Create a new round using the button above.
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {filtered.map((r) => (
                                        <RoundCard key={r.id} round={r} status={getStatus(r)} />
                                    ))}
                                </div>
                            )}
                        </div>
                    </>
                )}
            </div>
        </main>
    );
}
