'use client'

import React, { useState } from 'react'

interface WalletScore {
    address: string
    score: number
    riskLevel: 'low' | 'medium' | 'high'
    flags: string[]
    contributions: number
    totalAmount: string
    lastActivity: string
}

const MOCK_WALLETS: WalletScore[] = [
    {
        address: '0x7a2B...f3b9',
        score: 95,
        riskLevel: 'low',
        flags: [],
        contributions: 24,
        totalAmount: '$12,500',
        lastActivity: '2 hours ago'
    },
    {
        address: '0x8b3C...e2c4',
        score: 72,
        riskLevel: 'medium',
        flags: ['Multiple small donations', 'New wallet'],
        contributions: 15,
        totalAmount: '$3,200',
        lastActivity: '1 day ago'
    },
    {
        address: '0x9e5D...b7d1',
        score: 35,
        riskLevel: 'high',
        flags: ['Suspected bot activity', 'Linked addresses', 'Unusual patterns'],
        contributions: 8,
        totalAmount: '$800',
        lastActivity: '5 hours ago'
    },
    {
        address: '0x4d1A...a9f2',
        score: 88,
        riskLevel: 'low',
        flags: [],
        contributions: 42,
        totalAmount: '$28,000',
        lastActivity: '3 hours ago'
    },
    {
        address: '0x2c8E...d4e5',
        score: 58,
        riskLevel: 'medium',
        flags: ['Funding from flagged address'],
        contributions: 6,
        totalAmount: '$1,500',
        lastActivity: '12 hours ago'
    }
]

export function SybilScorePanel() {
    const [selectedWallet, setSelectedWallet] = useState<WalletScore | null>(null)
    const [searchQuery, setSearchQuery] = useState('')
    const [filter, setFilter] = useState<'all' | 'low' | 'medium' | 'high'>('all')

    const filteredWallets = MOCK_WALLETS.filter(w => {
        if (filter !== 'all' && w.riskLevel !== filter) return false
        if (searchQuery && !w.address.toLowerCase().includes(searchQuery.toLowerCase())) return false
        return true
    })

    const riskConfig = {
        low: { bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-500/30', icon: '✅' },
        medium: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', border: 'border-yellow-500/30', icon: '⚠️' },
        high: { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/30', icon: '🚨' }
    }

    const getScoreColor = (score: number) => {
        if (score >= 80) return '#00FFA3'
        if (score >= 50) return '#FFB800'
        return '#FF6B6B'
    }

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-4xl font-bold text-white">
                        🛡️ <span className="text-gradient">Sybil Score</span>
                    </h1>
                    <p className="text-gray-400 mt-2">Monitor and adjust wallet reputation scores</p>
                </div>
                <button className="btn-premium px-6 py-3 rounded-xl flex items-center gap-2">
                    <span>🔍</span> Run Analysis
                </button>
            </div>

            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {[
                    { label: 'Total Wallets', value: '5,234', icon: '👛', color: '#A855F7' },
                    { label: 'Low Risk', value: '4,521', icon: '✅', color: '#00FFA3' },
                    { label: 'Medium Risk', value: '612', icon: '⚠️', color: '#FFB800' },
                    { label: 'High Risk', value: '101', icon: '🚨', color: '#FF6B6B' },
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

            {/* Search and Filters */}
            <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1 relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">🔍</span>
                    <input
                        type="text"
                        placeholder="Search wallet address..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-12 pr-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-neon-purple"
                    />
                </div>
                <div className="flex gap-2">
                    {['all', 'low', 'medium', 'high'].map((f) => (
                        <button
                            key={f}
                            onClick={() => setFilter(f as any)}
                            className={`px-4 py-3 rounded-xl text-sm font-medium transition-all ${filter === f
                                    ? 'bg-white/10 text-white border border-white/20'
                                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                                }`}
                        >
                            {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1) + ' Risk'}
                        </button>
                    ))}
                </div>
            </div>

            {/* Wallets Table */}
            <div className="glass-panel overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="bg-white/5">
                                <th className="text-left p-4 text-gray-400 text-sm font-semibold">Wallet Address</th>
                                <th className="text-left p-4 text-gray-400 text-sm font-semibold">Sybil Score</th>
                                <th className="text-left p-4 text-gray-400 text-sm font-semibold">Risk Level</th>
                                <th className="text-left p-4 text-gray-400 text-sm font-semibold">Flags</th>
                                <th className="text-left p-4 text-gray-400 text-sm font-semibold">Contributions</th>
                                <th className="text-left p-4 text-gray-400 text-sm font-semibold">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredWallets.map((wallet) => {
                                const config = riskConfig[wallet.riskLevel]
                                return (
                                    <tr key={wallet.address} className="border-t border-white/5 hover:bg-white/5 transition-colors">
                                        <td className="p-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-neon-purple to-neon-cyan flex items-center justify-center">
                                                    👛
                                                </div>
                                                <div>
                                                    <p className="text-white font-mono font-medium">{wallet.address}</p>
                                                    <p className="text-gray-500 text-sm">Last active: {wallet.lastActivity}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="p-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-16 h-2 rounded-full overflow-hidden bg-white/10">
                                                    <div
                                                        className="h-full rounded-full"
                                                        style={{
                                                            width: `${wallet.score}%`,
                                                            backgroundColor: getScoreColor(wallet.score)
                                                        }}
                                                    />
                                                </div>
                                                <span className="text-white font-bold" style={{ color: getScoreColor(wallet.score) }}>
                                                    {wallet.score}
                                                </span>
                                            </div>
                                        </td>
                                        <td className="p-4">
                                            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${config.bg} ${config.text} flex items-center gap-1 w-fit`}>
                                                {config.icon} {wallet.riskLevel.charAt(0).toUpperCase() + wallet.riskLevel.slice(1)}
                                            </span>
                                        </td>
                                        <td className="p-4">
                                            {wallet.flags.length > 0 ? (
                                                <div className="flex flex-wrap gap-1">
                                                    {wallet.flags.slice(0, 2).map((flag, i) => (
                                                        <span key={i} className="px-2 py-1 rounded-lg text-xs bg-red-500/10 text-red-400">
                                                            {flag}
                                                        </span>
                                                    ))}
                                                    {wallet.flags.length > 2 && (
                                                        <span className="px-2 py-1 rounded-lg text-xs bg-white/5 text-gray-400">
                                                            +{wallet.flags.length - 2}
                                                        </span>
                                                    )}
                                                </div>
                                            ) : (
                                                <span className="text-gray-500 text-sm">No flags</span>
                                            )}
                                        </td>
                                        <td className="p-4">
                                            <div>
                                                <p className="text-white font-medium">{wallet.contributions}</p>
                                                <p className="text-gray-500 text-sm">{wallet.totalAmount}</p>
                                            </div>
                                        </td>
                                        <td className="p-4">
                                            <div className="flex gap-2">
                                                <button
                                                    onClick={() => setSelectedWallet(wallet)}
                                                    className="p-2 rounded-lg hover:bg-white/10 transition-colors text-gray-400 hover:text-white"
                                                    title="Adjust Score"
                                                >
                                                    ⚙️
                                                </button>
                                                <button
                                                    className="p-2 rounded-lg hover:bg-white/10 transition-colors text-gray-400 hover:text-white"
                                                    title="View Details"
                                                >
                                                    👁️
                                                </button>
                                                {wallet.riskLevel === 'high' && (
                                                    <button
                                                        className="p-2 rounded-lg hover:bg-red-500/20 transition-colors text-gray-400 hover:text-red-400"
                                                        title="Block Wallet"
                                                    >
                                                        🚫
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

            {/* Adjust Score Modal */}
            {selectedWallet && (
                <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="glass-panel p-8 max-w-md w-full space-y-6 relative">
                        <button
                            onClick={() => setSelectedWallet(null)}
                            className="absolute top-4 right-4 text-gray-400 hover:text-white"
                        >
                            ✕
                        </button>

                        <div>
                            <h2 className="text-2xl font-bold text-white">Adjust Sybil Score</h2>
                            <p className="text-gray-400 text-sm mt-1 font-mono">{selectedWallet.address}</p>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm text-gray-400 mb-2">Current Score: {selectedWallet.score}</label>
                                <input
                                    type="range"
                                    min="0"
                                    max="100"
                                    defaultValue={selectedWallet.score}
                                    className="w-full h-2 rounded-full appearance-none cursor-pointer"
                                    style={{ background: 'linear-gradient(90deg, #FF6B6B, #FFB800, #00FFA3)' }}
                                />
                                <div className="flex justify-between text-xs text-gray-500 mt-1">
                                    <span>High Risk</span>
                                    <span>Low Risk</span>
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm text-gray-400 mb-2">Reason for Adjustment</label>
                                <textarea
                                    rows={3}
                                    placeholder="Provide justification..."
                                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-neon-purple resize-none"
                                />
                            </div>
                        </div>

                        <div className="flex gap-3">
                            <button
                                onClick={() => setSelectedWallet(null)}
                                className="flex-1 px-6 py-3 rounded-xl border border-white/10 text-gray-300 hover:bg-white/5 transition-colors"
                            >
                                Cancel
                            </button>
                            <button className="flex-1 btn-premium px-6 py-3 rounded-xl">
                                Save Changes
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
