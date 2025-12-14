'use client'

import React, { useState } from 'react'
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    BarChart,
    Bar,
} from 'recharts'

const POOL_HISTORY = [
    { date: 'Jan 1', balance: 150000, inflow: 20000, outflow: 0 },
    { date: 'Jan 5', balance: 165000, inflow: 15000, outflow: 0 },
    { date: 'Jan 10', balance: 160000, inflow: 0, outflow: 5000 },
    { date: 'Jan 15', balance: 180000, inflow: 25000, outflow: 5000 },
    { date: 'Jan 20', balance: 175000, inflow: 0, outflow: 5000 },
    { date: 'Jan 25', balance: 200000, inflow: 30000, outflow: 5000 },
    { date: 'Jan 30', balance: 220000, inflow: 25000, outflow: 5000 },
]

const ROUND_ALLOCATIONS = [
    { name: 'Web3 Infra', allocated: 100000, distributed: 75000, remaining: 25000 },
    { name: 'Climate', allocated: 75000, distributed: 45000, remaining: 30000 },
    { name: 'Education', allocated: 50000, distributed: 0, remaining: 50000 },
]

const RECENT_TRANSACTIONS = [
    { type: 'deposit', amount: '+$25,000', from: '0x7a2...f3b', timestamp: '2 hours ago' },
    { type: 'distribution', amount: '-$15,000', to: 'Web3 Infrastructure Round', timestamp: '5 hours ago' },
    { type: 'deposit', amount: '+$10,000', from: 'DAO Treasury', timestamp: '1 day ago' },
    { type: 'distribution', amount: '-$8,500', to: 'Climate Impact Round', timestamp: '2 days ago' },
]

export function MatchingPoolMonitor() {
    const [depositAmount, setDepositAmount] = useState('')

    const totalBalance = 220000
    const totalAllocated = 225000
    const availableForAllocation = totalBalance - ROUND_ALLOCATIONS.reduce((sum, r) => sum + r.remaining, 0) + 115000

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-4xl font-bold text-white">
                        💰 <span className="text-gradient">Matching Pool</span>
                    </h1>
                    <p className="text-gray-400 mt-2">Monitor and manage the quadratic matching pool</p>
                </div>
                <button className="btn-premium px-6 py-3 rounded-xl flex items-center gap-2">
                    <span>➕</span> Add Funds
                </button>
            </div>

            {/* Balance Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="glass-panel p-6 relative overflow-hidden">
                    <div className="absolute inset-0 opacity-10" style={{ background: 'linear-gradient(135deg, #00FFA3, #00E5FF)' }} />
                    <div className="relative z-10">
                        <p className="text-gray-400 text-sm mb-2">Total Pool Balance</p>
                        <p className="text-4xl font-bold text-white">${totalBalance.toLocaleString()}</p>
                        <p className="text-green-400 text-sm mt-2">↑ +15.2% this month</p>
                    </div>
                    <div className="absolute bottom-4 right-4 text-6xl opacity-20">💎</div>
                </div>

                <div className="glass-panel p-6 relative overflow-hidden">
                    <div className="absolute inset-0 opacity-10" style={{ background: 'linear-gradient(135deg, #A855F7, #00E5FF)' }} />
                    <div className="relative z-10">
                        <p className="text-gray-400 text-sm mb-2">Allocated to Rounds</p>
                        <p className="text-4xl font-bold text-white">${ROUND_ALLOCATIONS.reduce((s, r) => s + r.allocated, 0).toLocaleString()}</p>
                        <p className="text-gray-400 text-sm mt-2">Across {ROUND_ALLOCATIONS.length} active rounds</p>
                    </div>
                    <div className="absolute bottom-4 right-4 text-6xl opacity-20">🎯</div>
                </div>

                <div className="glass-panel p-6 relative overflow-hidden">
                    <div className="absolute inset-0 opacity-10" style={{ background: 'linear-gradient(135deg, #FFB800, #FF6B6B)' }} />
                    <div className="relative z-10">
                        <p className="text-gray-400 text-sm mb-2">Total Distributed</p>
                        <p className="text-4xl font-bold text-white">${ROUND_ALLOCATIONS.reduce((s, r) => s + r.distributed, 0).toLocaleString()}</p>
                        <p className="text-neon-cyan text-sm mt-2">To 45 projects</p>
                    </div>
                    <div className="absolute bottom-4 right-4 text-6xl opacity-20">📤</div>
                </div>
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Pool Balance Chart */}
                <div className="glass-panel p-6">
                    <h3 className="text-xl font-bold text-white mb-6">Pool Balance History</h3>
                    <div className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={POOL_HISTORY}>
                                <defs>
                                    <linearGradient id="colorBalance" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#00FFA3" stopOpacity={0.4} />
                                        <stop offset="95%" stopColor="#00FFA3" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                                <XAxis dataKey="date" stroke="#6B7280" />
                                <YAxis stroke="#6B7280" />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: 'rgba(17, 24, 39, 0.95)',
                                        border: '1px solid rgba(255,255,255,0.1)',
                                        borderRadius: '12px',
                                    }}
                                    formatter={(value: number) => [`$${value.toLocaleString()}`, 'Balance']}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="balance"
                                    stroke="#00FFA3"
                                    strokeWidth={3}
                                    fillOpacity={1}
                                    fill="url(#colorBalance)"
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Round Allocations */}
                <div className="glass-panel p-6">
                    <h3 className="text-xl font-bold text-white mb-6">Round Allocations</h3>
                    <div className="space-y-6">
                        {ROUND_ALLOCATIONS.map((round) => {
                            const progress = (round.distributed / round.allocated) * 100
                            return (
                                <div key={round.name} className="space-y-2">
                                    <div className="flex justify-between items-center">
                                        <span className="text-white font-medium">{round.name}</span>
                                        <span className="text-gray-400 text-sm">
                                            ${round.distributed.toLocaleString()} / ${round.allocated.toLocaleString()}
                                        </span>
                                    </div>
                                    <div className="h-3 rounded-full overflow-hidden bg-white/10">
                                        <div
                                            className="h-full rounded-full transition-all duration-500"
                                            style={{
                                                width: `${progress}%`,
                                                background: 'linear-gradient(90deg, #A855F7, #00E5FF, #00FFA3)'
                                            }}
                                        />
                                    </div>
                                    <div className="flex justify-between text-xs">
                                        <span className="text-neon-mint">{progress.toFixed(0)}% distributed</span>
                                        <span className="text-gray-500">${round.remaining.toLocaleString()} remaining</span>
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                </div>
            </div>

            {/* Recent Transactions */}
            <div className="glass-panel p-6">
                <h3 className="text-xl font-bold text-white mb-6">Recent Transactions</h3>
                <div className="space-y-4">
                    {RECENT_TRANSACTIONS.map((tx, i) => (
                        <div key={i} className="flex items-center justify-between p-4 rounded-xl hover:bg-white/5 transition-colors">
                            <div className="flex items-center gap-4">
                                <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-2xl ${tx.type === 'deposit' ? 'bg-green-500/20' : 'bg-blue-500/20'
                                    }`}>
                                    {tx.type === 'deposit' ? '📥' : '📤'}
                                </div>
                                <div>
                                    <p className="text-white font-medium">
                                        {tx.type === 'deposit' ? `Deposit from ${tx.from}` : `Distribution to ${tx.to}`}
                                    </p>
                                    <p className="text-gray-500 text-sm">{tx.timestamp}</p>
                                </div>
                            </div>
                            <span className={`text-lg font-bold ${tx.type === 'deposit' ? 'text-green-400' : 'text-blue-400'
                                }`}>
                                {tx.amount}
                            </span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}
