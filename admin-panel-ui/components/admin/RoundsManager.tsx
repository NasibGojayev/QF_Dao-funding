'use client'

import React, { useState } from 'react'
import { useRounds } from '../../lib/hooks'

interface Round {
    id: number
    name: string
    status: 'active' | 'upcoming' | 'closed'
    startDate: string
    endDate: string
    matchingPool: string
    totalFunded: string
    projects: number
    participants: number
}

const MOCK_ROUNDS: Round[] = [
    {
        id: 1,
        name: 'Web3 Infrastructure Round',
        status: 'active',
        startDate: '2024-01-15',
        endDate: '2024-02-15',
        matchingPool: '$100,000',
        totalFunded: '$425,000',
        projects: 24,
        participants: 1243
    },
    {
        id: 2,
        name: 'Climate Impact Round',
        status: 'active',
        startDate: '2024-01-20',
        endDate: '2024-02-20',
        matchingPool: '$75,000',
        totalFunded: '$182,000',
        projects: 18,
        participants: 856
    },
    {
        id: 3,
        name: 'Education & Research',
        status: 'upcoming',
        startDate: '2024-03-01',
        endDate: '2024-04-01',
        matchingPool: '$50,000',
        totalFunded: '$0',
        projects: 0,
        participants: 0
    },
    {
        id: 4,
        name: 'Developer Tools Round',
        status: 'closed',
        startDate: '2023-12-01',
        endDate: '2024-01-15',
        matchingPool: '$150,000',
        totalFunded: '$398,000',
        projects: 32,
        participants: 2341
    }
]

export function RoundsManager() {
    const [showCreateModal, setShowCreateModal] = useState(false)
    const [selectedRound, setSelectedRound] = useState<Round | null>(null)
    const { data: apiRounds } = useRounds()

    const statusConfig = {
        active: { bg: 'bg-green-500/20', text: 'text-green-400', dot: 'bg-green-400' },
        upcoming: { bg: 'bg-blue-500/20', text: 'text-blue-400', dot: 'bg-blue-400' },
        closed: { bg: 'bg-gray-500/20', text: 'text-gray-400', dot: 'bg-gray-400' }
    }

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-4xl font-bold text-white">
                        🎯 <span className="text-gradient">Manage Rounds</span>
                    </h1>
                    <p className="text-gray-400 mt-2">Create, configure, and monitor funding rounds</p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="btn-premium px-6 py-3 rounded-xl flex items-center gap-2"
                >
                    <span>➕</span> Create New Round
                </button>
            </div>

            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {[
                    { label: 'Active Rounds', value: '2', icon: '🟢', color: '#00FFA3' },
                    { label: 'Upcoming', value: '1', icon: '🔵', color: '#00E5FF' },
                    { label: 'Total Distributed', value: '$1.2M', icon: '💰', color: '#A855F7' },
                    { label: 'Total Participants', value: '4.4K', icon: '👥', color: '#FFB800' },
                ].map((stat) => (
                    <div key={stat.label} className="glass-panel p-4 flex items-center gap-4">
                        <div
                            className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl"
                            style={{ background: `${stat.color}20` }}
                        >
                            {stat.icon}
                        </div>
                        <div>
                            <p className="text-gray-400 text-sm">{stat.label}</p>
                            <p className="text-2xl font-bold text-white">{stat.value}</p>
                        </div>
                    </div>
                ))}
            </div>

            {/* Rounds Table */}
            <div className="glass-panel overflow-hidden">
                <div className="p-6 border-b border-white/10">
                    <div className="flex items-center justify-between">
                        <h3 className="text-xl font-bold text-white">All Rounds</h3>
                        <div className="flex gap-2">
                            {['All', 'Active', 'Upcoming', 'Closed'].map((filter) => (
                                <button
                                    key={filter}
                                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${filter === 'All'
                                            ? 'bg-white/10 text-white'
                                            : 'text-gray-400 hover:text-white hover:bg-white/5'
                                        }`}
                                >
                                    {filter}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="bg-white/5">
                                <th className="text-left p-4 text-gray-400 text-sm font-semibold">Round Name</th>
                                <th className="text-left p-4 text-gray-400 text-sm font-semibold">Status</th>
                                <th className="text-left p-4 text-gray-400 text-sm font-semibold">Duration</th>
                                <th className="text-left p-4 text-gray-400 text-sm font-semibold">Matching Pool</th>
                                <th className="text-left p-4 text-gray-400 text-sm font-semibold">Funded</th>
                                <th className="text-left p-4 text-gray-400 text-sm font-semibold">Projects</th>
                                <th className="text-left p-4 text-gray-400 text-sm font-semibold">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {MOCK_ROUNDS.map((round) => {
                                const config = statusConfig[round.status]
                                return (
                                    <tr key={round.id} className="border-t border-white/5 hover:bg-white/5 transition-colors">
                                        <td className="p-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-neon-purple to-neon-cyan flex items-center justify-center text-lg">
                                                    🎯
                                                </div>
                                                <div>
                                                    <p className="text-white font-semibold">{round.name}</p>
                                                    <p className="text-gray-500 text-sm">{round.participants.toLocaleString()} participants</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="p-4">
                                            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${config.bg} ${config.text} flex items-center gap-2 w-fit`}>
                                                <div className={`w-2 h-2 rounded-full ${config.dot} animate-pulse`} />
                                                {round.status.charAt(0).toUpperCase() + round.status.slice(1)}
                                            </span>
                                        </td>
                                        <td className="p-4 text-gray-300 text-sm">
                                            {round.startDate} → {round.endDate}
                                        </td>
                                        <td className="p-4 text-neon-mint font-semibold">{round.matchingPool}</td>
                                        <td className="p-4 text-white font-semibold">{round.totalFunded}</td>
                                        <td className="p-4 text-white">{round.projects}</td>
                                        <td className="p-4">
                                            <div className="flex gap-2">
                                                <button
                                                    onClick={() => setSelectedRound(round)}
                                                    className="p-2 rounded-lg hover:bg-white/10 transition-colors text-gray-400 hover:text-white"
                                                    title="Edit"
                                                >
                                                    ✏️
                                                </button>
                                                <button
                                                    className="p-2 rounded-lg hover:bg-white/10 transition-colors text-gray-400 hover:text-white"
                                                    title="View Details"
                                                >
                                                    👁️
                                                </button>
                                                {round.status !== 'closed' && (
                                                    <button
                                                        className="p-2 rounded-lg hover:bg-red-500/20 transition-colors text-gray-400 hover:text-red-400"
                                                        title="Close Round"
                                                    >
                                                        ⏹️
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                )
                            })}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Create Round Modal */}
            {showCreateModal && (
                <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="glass-panel p-8 max-w-lg w-full space-y-6 relative">
                        <button
                            onClick={() => setShowCreateModal(false)}
                            className="absolute top-4 right-4 text-gray-400 hover:text-white"
                        >
                            ✕
                        </button>

                        <div>
                            <h2 className="text-2xl font-bold text-white">Create New Round</h2>
                            <p className="text-gray-400 text-sm mt-1">Configure a new funding round</p>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm text-gray-400 mb-2">Round Name</label>
                                <input
                                    type="text"
                                    placeholder="e.g., DeFi Innovation Round"
                                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-neon-purple"
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm text-gray-400 mb-2">Start Date</label>
                                    <input
                                        type="date"
                                        className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:border-neon-purple"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-2">End Date</label>
                                    <input
                                        type="date"
                                        className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:border-neon-purple"
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm text-gray-400 mb-2">Matching Pool Amount</label>
                                <input
                                    type="text"
                                    placeholder="$50,000"
                                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-neon-purple"
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-gray-400 mb-2">Description</label>
                                <textarea
                                    rows={3}
                                    placeholder="Describe the focus of this funding round..."
                                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-neon-purple resize-none"
                                />
                            </div>
                        </div>

                        <div className="flex gap-3">
                            <button
                                onClick={() => setShowCreateModal(false)}
                                className="flex-1 px-6 py-3 rounded-xl border border-white/10 text-gray-300 hover:bg-white/5 transition-colors"
                            >
                                Cancel
                            </button>
                            <button className="flex-1 btn-premium px-6 py-3 rounded-xl">
                                Create Round
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
