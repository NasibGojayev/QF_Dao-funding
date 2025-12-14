"use client";

import { useState, useEffect } from "react";

type MatchingPool = {
    pool_id: string;
    total_funds: number;
    allocated_funds: number;
    available_funds?: number;
    replenished_by: string;
    total_rounds?: number;
};

export default function MatchingPoolsPage() {
    const [pools, setPools] = useState<MatchingPool[]>([]);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState("");
    const [showCreate, setShowCreate] = useState(false);

    const [formData, setFormData] = useState({
        total_funds: "",
        replenished_by: "",
    });

    useEffect(() => {
        fetchPools();
    }, []);

    const fetchPools = async () => {
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/matching-pools/`);
            if (res.ok) {
                const data = await res.json();
                setPools(data.results || data);
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
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/matching-pools/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    total_funds: parseFloat(formData.total_funds),
                    allocated_funds: 0,
                    replenished_by: formData.replenished_by,
                }),
            });

            if (res.ok) {
                setMessage("Matching pool created successfully!");
                setFormData({
                    total_funds: "",
                    replenished_by: "",
                });
                fetchPools();
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

    return (
        <main className="min-h-screen p-8 bg-background">
            <div className="max-w-6xl mx-auto">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-foreground">
                            Matching Pools
                        </h1>
                        <p className="text-sm text-muted-foreground mt-1">
                            Manage funding pools for quadratic funding rounds
                        </p>
                    </div>
                    <button
                        onClick={() => setShowCreate(!showCreate)}
                        className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition font-semibold shadow-sm"
                    >
                        {showCreate ? "View Pools" : "+ Add New Matching Pool"}
                    </button>
                </div>

                {showCreate ? (
                    <div className="bg-card rounded-lg shadow-sm border border-border p-6 mb-8">
                        <h2 className="text-2xl font-semibold mb-4 text-foreground">
                            Create New Matching Pool
                        </h2>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-foreground mb-1">
                                    Total Funds ($)
                                </label>
                                <input
                                    type="number"
                                    step="0.01"
                                    value={formData.total_funds}
                                    onChange={(e) =>
                                        setFormData({ ...formData, total_funds: e.target.value })
                                    }
                                    className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground focus:ring-2 focus:ring-primary outline-none transition"
                                    placeholder="50000.00"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-foreground mb-1">
                                    Replenished By
                                </label>
                                <input
                                    type="text"
                                    value={formData.replenished_by}
                                    onChange={(e) =>
                                        setFormData({ ...formData, replenished_by: e.target.value })
                                    }
                                    className="w-full px-3 py-2 border border-input rounded-lg bg-background text-foreground focus:ring-2 focus:ring-primary outline-none transition"
                                    placeholder="Community Treasury"
                                    required
                                />
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full px-6 py-3 bg-primary text-primary-foreground rounded-lg font-semibold hover:bg-primary/90 transition disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                            >
                                {loading ? "Creating..." : "Create Matching Pool"}
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
                    <div className="bg-card rounded-lg shadow-sm border border-border p-6">
                        <h2 className="text-2xl font-semibold mb-4 text-foreground">
                            Existing Pools
                        </h2>
                        <div className="space-y-3 max-h-[600px] overflow-y-auto">
                            {pools.length === 0 ? (
                                <p className="text-muted-foreground">
                                    No matching pools found.
                                </p>
                            ) : (
                                pools.map((pool) => (
                                    <div
                                        key={pool.pool_id}
                                        className="p-4 border border-border rounded-lg hover:shadow-md transition bg-card"
                                    >
                                        <div className="flex justify-between items-start mb-2">
                                            <p className="font-semibold text-foreground">
                                                Pool {pool.pool_id.substring(0, 8)}
                                            </p>
                                            <span className="px-2 py-1 text-xs bg-secondary text-secondary-foreground rounded-full">
                                                {pool.total_rounds || 0} rounds
                                            </span>
                                        </div>
                                        <div className="space-y-1 text-sm">
                                            <p className="text-muted-foreground">
                                                <span className="font-medium text-foreground">Total:</span> $
                                                {pool.total_funds.toLocaleString()}
                                            </p>
                                            <p className="text-muted-foreground">
                                                <span className="font-medium text-foreground">Allocated:</span> $
                                                {pool.allocated_funds.toLocaleString()}
                                            </p>
                                            <p className="text-green-600 dark:text-green-400">
                                                <span className="font-medium text-foreground">Available:</span> $
                                                {(pool.available_funds !== undefined
                                                    ? pool.available_funds
                                                    : pool.total_funds - pool.allocated_funds
                                                ).toLocaleString()}
                                            </p>
                                            <p className="text-muted-foreground mt-2">
                                                <span className="font-medium text-foreground">Source:</span>{" "}
                                                {pool.replenished_by}
                                            </p>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                )}
            </div>
        </main>
    );
}
