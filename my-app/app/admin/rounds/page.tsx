"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

type MatchingPool = {
    pool_id: string;
    total_funds: number;
    allocated_funds: number;
    replenished_by: string;
};

type Round = {
    round_id: string;
    start_date: string;
    end_date: string;
    status: string;
    pool?: number;  // From RoundSerializer compatibility field
    matching_pool?: {
        pool_id: string;
        total_funds: number;
    };
};

export default function AdminRounds() {
    const [matchingPools, setMatchingPools] = useState<MatchingPool[]>([]);
    const [rounds, setRounds] = useState<Round[]>([]);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState("");

    const [formData, setFormData] = useState({
        start_date: "",
        end_date: "",
        matching_pool: "",
        status: "upcoming",
    });

    useEffect(() => {
        fetchMatchingPools();
        fetchRounds();
    }, []);

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
                fetchRounds(); // Refresh the list
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

    return (
        <main className="min-h-screen p-8 bg-gray-50 dark:bg-gray-900">
            <div className="max-w-4xl mx-auto">
                <div className="flex items-center justify-between mb-8">
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                        Admin: Manage Rounds
                    </h1>
                    <Link
                        href="/"
                        className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition"
                    >
                        ← Back to Home
                    </Link>
                </div>

                {/* Create Round Form */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-8">
                    <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-gray-100">
                        Create New Round
                    </h2>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Start Date
                            </label>
                            <input
                                type="datetime-local"
                                value={formData.start_date}
                                onChange={(e) =>
                                    setFormData({ ...formData, start_date: e.target.value })
                                }
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                End Date
                            </label>
                            <input
                                type="datetime-local"
                                value={formData.end_date}
                                onChange={(e) =>
                                    setFormData({ ...formData, end_date: e.target.value })
                                }
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Matching Pool
                            </label>
                            <select
                                value={formData.matching_pool}
                                onChange={(e) =>
                                    setFormData({ ...formData, matching_pool: e.target.value })
                                }
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                required
                            >
                                <option value="">Select a matching pool</option>
                                {matchingPools.map((pool) => (
                                    <option key={pool.pool_id} value={pool.pool_id}>
                                        Pool {pool.pool_id.substring(0, 8)} - $
                                        {pool.total_funds.toLocaleString()} ({pool.replenished_by})
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Status
                            </label>
                            <select
                                value={formData.status}
                                onChange={(e) =>
                                    setFormData({ ...formData, status: e.target.value })
                                }
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            >
                                <option value="upcoming">Upcoming</option>
                                <option value="active">Active</option>
                                <option value="closed">Closed</option>
                            </select>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? "Creating..." : "Create Round"}
                        </button>

                        {message && (
                            <div
                                className={`p-3 rounded-lg ${message.includes("Error")
                                    ? "bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200"
                                    : "bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200"
                                    }`}
                            >
                                {message}
                            </div>
                        )}
                    </form>
                </div>

                {/* Rounds List */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                    <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-gray-100">
                        Existing Rounds
                    </h2>
                    <div className="space-y-3">
                        {rounds.length === 0 ? (
                            <p className="text-gray-500 dark:text-gray-400">
                                No rounds found.
                            </p>
                        ) : (
                            rounds.map((round) => (
                                <div
                                    key={round.round_id}
                                    className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg"
                                >
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <p className="font-semibold text-gray-900 dark:text-gray-100">
                                                Round {round.round_id.substring(0, 8)}
                                            </p>
                                            <p className="text-sm text-gray-600 dark:text-gray-400">
                                                Start: {new Date(round.start_date).toLocaleString()}
                                            </p>
                                            <p className="text-sm text-gray-600 dark:text-gray-400">
                                                End: {new Date(round.end_date).toLocaleString()}
                                            </p>
                                            {round.pool != null && (
                                                <p className="text-sm text-gray-600 dark:text-gray-400">
                                                    Pool: ${round.pool.toLocaleString()}
                                                </p>
                                            )}
                                        </div>
                                        <span
                                            className={`px-3 py-1 text-xs font-semibold rounded-full ${round.status === "active"
                                                ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                                                : round.status === "upcoming"
                                                    ? "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                                                    : "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200"
                                                }`}
                                        >
                                            {round.status}
                                        </span>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </main>
    );
}
