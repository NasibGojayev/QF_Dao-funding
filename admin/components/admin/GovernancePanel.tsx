'use client'

import React, { useState } from 'react'

interface Proposal {
    id: number
    title: string
    description: string
    proposer: string
    status: 'active' | 'passed' | 'rejected' | 'pending'
    votesFor: number
    votesAgainst: number
    quorum: number
    endDate: string
    category: string
}

const MOCK_PROPOSALS: Proposal[] = [
    {
        id: 1,
        title: 'Increase Matching Pool Allocation',
        description: 'Proposal to increase the quarterly matching pool allocation from $100K to $150K to support more projects',
        proposer: '0x7a2...f3b',
        status: 'active',
        votesFor: 1250,
        votesAgainst: 320,
        quorum: 2000,
        endDate: '2024-01-20',
        category: 'Treasury'
    },
    {
        id: 2,
        title: 'Add Climate Category',
        description: 'Create a dedicated Climate Impact category for environmental projects with specialized matching criteria',
        proposer: '0x8b3...e2c',
        status: 'active',
        votesFor: 890,
        votesAgainst: 150,
        quorum: 1500,
        endDate: '2024-01-22',
        category: 'Governance'
    },
    {
        id: 3,
        title: 'Reduce Sybil Threshold',
        description: 'Lower the sybil detection threshold from 50 to 40 for stricter security measures',
        proposer: '0x4d1...a9f',
        status: 'passed',
        votesFor: 2100,
        votesAgainst: 400,
        quorum: 2000,
        endDate: '2024-01-10',
        category: 'Security'
    },
    {
        id: 4,
        title: 'New Partnership Agreement',
        description: 'Approve partnership with XYZ Protocol for cross-chain funding capabilities',
        proposer: '0x2c8...d4e',
        status: 'rejected',
        votesFor: 500,
        votesAgainst: 1800,
        quorum: 2000,
        endDate: '2024-01-08',
        category: 'Partnership'
    }
]

export function GovernancePanel() {
    const [filter, setFilter] = useState<'all' | 'active' | 'passed' | 'rejected'>('all')
    const [showCreateModal, setShowCreateModal] = useState(false)

    const filteredProposals = MOCK_PROPOSALS.filter(p => filter === 'all' || p.status === filter)

    const statusConfig = {
        active: { bg: 'bg-blue-500/20', text: 'text-blue-400', icon: '🗳️' },
        passed: { bg: 'bg-green-500/20', text: 'text-green-400', icon: '✅' },
        rejected: { bg: 'bg-red-500/20', text: 'text-red-400', icon: '❌' },
        pending: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', icon: '⏳' }
    }

    const categoryColors: Record<string, string> = {
        'Treasury': '#00FFA3',
        'Governance': '#A855F7',
        'Security': '#FF6B6B',
        'Partnership': '#00E5FF'
    }

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-4xl font-bold text-white">
                        ⚖️ <span className="text-gradient">Governance</span>
                    </h1>
                    <p className="text-gray-400 mt-2">Manage proposals, voting, and DAO decisions</p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="btn-premium px-6 py-3 rounded-xl flex items-center gap-2"
                >
                    <span>📝</span> Create Proposal
                </button>
            </div>

            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {[
                    { label: 'Active Proposals', value: '2', icon: '🗳️', color: '#00E5FF' },
                    { label: 'Total Proposals', value: '47', icon: '📋', color: '#A855F7' },
                    { label: 'Participation Rate', value: '68%', icon: '👥', color: '#00FFA3' },
                    { label: 'Passed This Month', value: '5', icon: '✅', color: '#FFB800' },
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

            {/* Filter Tabs */}
            <div className="flex gap-2">
                {['all', 'active', 'passed', 'rejected'].map((f) => (
                    <button
                        key={f}
                        onClick={() => setFilter(f as any)}
                        className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${filter === f
                                ? 'bg-white/10 text-white border border-white/20'
                                : 'text-gray-400 hover:text-white hover:bg-white/5'
                            }`}
                    >
                        {f === 'all' ? 'All Proposals' : f.charAt(0).toUpperCase() + f.slice(1)}
                    </button>
                ))}
            </div>

            {/* Proposals List */}
            <div className="space-y-4">
                {filteredProposals.map((proposal) => {
                    const config = statusConfig[proposal.status]
                    const totalVotes = proposal.votesFor + proposal.votesAgainst
                    const forPercentage = totalVotes > 0 ? (proposal.votesFor / totalVotes) * 100 : 0
                    const quorumProgress = (totalVotes / proposal.quorum) * 100
                    const categoryColor = categoryColors[proposal.category] || '#A855F7'

                    return (
                        <div key={proposal.id} className="glass-panel p-6 hover:border-white/20 transition-all">
                            <div className="flex items-start justify-between mb-4">
                                <div className="flex-1">
                                    <div className="flex items-center gap-3 mb-2">
                                        <span
                                            className="px-3 py-1 rounded-lg text-xs font-medium"
                                            style={{ background: `${categoryColor}20`, color: categoryColor }}
                                        >
                                            {proposal.category}
                                        </span>
                                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${config.bg} ${config.text} flex items-center gap-1`}>
                                            {config.icon} {proposal.status.charAt(0).toUpperCase() + proposal.status.slice(1)}
                                        </span>
                                    </div>
                                    <h3 className="text-xl font-bold text-white">{proposal.title}</h3>
                                    <p className="text-gray-400 text-sm mt-2">{proposal.description}</p>
                                </div>
                            </div>

                            {/* Voting Progress */}
                            <div className="space-y-4 mt-6">
                                <div className="flex justify-between text-sm">
                                    <span className="text-green-400">For: {proposal.votesFor.toLocaleString()}</span>
                                    <span className="text-red-400">Against: {proposal.votesAgainst.toLocaleString()}</span>
                                </div>
                                <div className="h-3 rounded-full overflow-hidden bg-white/10 flex">
                                    <div
                                        className="h-full bg-green-500 transition-all"
                                        style={{ width: `${forPercentage}%` }}
                                    />
                                    <div
                                        className="h-full bg-red-500 transition-all"
                                        style={{ width: `${100 - forPercentage}%` }}
                                    />
                                </div>

                                <div className="flex items-center justify-between text-sm">
                                    <div className="flex items-center gap-2">
                                        <span className="text-gray-400">Quorum:</span>
                                        <div className="w-20 h-2 rounded-full overflow-hidden bg-white/10">
                                            <div
                                                className="h-full rounded-full"
                                                style={{
                                                    width: `${Math.min(quorumProgress, 100)}%`,
                                                    background: quorumProgress >= 100 ? '#00FFA3' : '#FFB800'
                                                }}
                                            />
                                        </div>
                                        <span className={quorumProgress >= 100 ? 'text-green-400' : 'text-yellow-400'}>
                                            {totalVotes.toLocaleString()}/{proposal.quorum.toLocaleString()}
                                        </span>
                                    </div>
                                    <span className="text-gray-500">
                                        {proposal.status === 'active' ? `Ends: ${proposal.endDate}` : `Ended: ${proposal.endDate}`}
                                    </span>
                                </div>
                            </div>

                            {/* Action Buttons */}
                            {proposal.status === 'active' && (
                                <div className="flex gap-3 mt-6 pt-4 border-t border-white/10">
                                    <button className="flex-1 px-6 py-3 rounded-xl bg-green-500/20 text-green-400 font-semibold hover:bg-green-500/30 transition-colors flex items-center justify-center gap-2">
                                        👍 Vote For
                                    </button>
                                    <button className="flex-1 px-6 py-3 rounded-xl bg-red-500/20 text-red-400 font-semibold hover:bg-red-500/30 transition-colors flex items-center justify-center gap-2">
                                        👎 Vote Against
                                    </button>
                                </div>
                            )}
                        </div>
                    )
                })}
            </div>

            {/* Create Proposal Modal */}
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
                            <h2 className="text-2xl font-bold text-white">Create Proposal</h2>
                            <p className="text-gray-400 text-sm mt-1">Submit a new governance proposal</p>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm text-gray-400 mb-2">Title</label>
                                <input
                                    type="text"
                                    placeholder="Proposal title..."
                                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-neon-purple"
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-gray-400 mb-2">Category</label>
                                <select className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:border-neon-purple cursor-pointer">
                                    <option value="Treasury" className="bg-dark-bg">Treasury</option>
                                    <option value="Governance" className="bg-dark-bg">Governance</option>
                                    <option value="Security" className="bg-dark-bg">Security</option>
                                    <option value="Partnership" className="bg-dark-bg">Partnership</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm text-gray-400 mb-2">Description</label>
                                <textarea
                                    rows={4}
                                    placeholder="Describe your proposal..."
                                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-neon-purple resize-none"
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-gray-400 mb-2">Voting Period (days)</label>
                                <input
                                    type="number"
                                    defaultValue={7}
                                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:border-neon-purple"
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
                                Submit Proposal
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
