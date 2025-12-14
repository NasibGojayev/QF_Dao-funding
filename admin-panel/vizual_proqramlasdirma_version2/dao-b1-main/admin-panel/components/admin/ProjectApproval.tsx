'use client'

import React, { useState } from 'react'
import { useProjects } from '../../lib/hooks'

interface Project {
    id: number
    name: string
    owner: string
    category: string
    status: 'pending' | 'approved' | 'rejected'
    submittedAt: string
    fundingRequest: string
    description: string
    walletAddress: string
}

const MOCK_PROJECTS: Project[] = [
    {
        id: 1,
        name: 'DeFi Analytics Dashboard',
        owner: 'Analytics Guild',
        category: 'Tools',
        status: 'pending',
        submittedAt: '2024-01-10',
        fundingRequest: '$35,000',
        description: 'Real-time analytics and insights for decentralized autonomous organization fund management',
        walletAddress: '0x7a2...f3b'
    },
    {
        id: 2,
        name: 'Open Education Platform',
        owner: 'EduDAO',
        category: 'Education',
        status: 'pending',
        submittedAt: '2024-01-09',
        fundingRequest: '$40,000',
        description: 'Free, gamified courses teaching blockchain development to underserved communities',
        walletAddress: '0x8b3...e2c'
    },
    {
        id: 3,
        name: 'Carbon Credit Registry',
        owner: 'GreenChain',
        category: 'Climate',
        status: 'approved',
        submittedAt: '2024-01-05',
        fundingRequest: '$75,000',
        description: 'Transparent, tamper-proof carbon credit tracking on blockchain',
        walletAddress: '0x4d1...a9f'
    },
    {
        id: 4,
        name: 'Spam NFT Project',
        owner: 'Unknown',
        category: 'Marketplace',
        status: 'rejected',
        submittedAt: '2024-01-08',
        fundingRequest: '$100,000',
        description: 'Low quality submission with insufficient documentation',
        walletAddress: '0x9e5...b7d'
    },
    {
        id: 5,
        name: 'Privacy-Preserving DeFi',
        owner: 'ZK Labs',
        category: 'Infrastructure',
        status: 'pending',
        submittedAt: '2024-01-11',
        fundingRequest: '$100,000',
        description: 'Building zero-knowledge privacy solutions for DeFi',
        walletAddress: '0x2c8...d4e'
    }
]

export function ProjectApproval() {
    const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('pending')
    const [selectedProject, setSelectedProject] = useState<Project | null>(null)
    const { data: apiProjects } = useProjects()

    const filteredProjects = MOCK_PROJECTS.filter(p => filter === 'all' || p.status === filter)

    const statusConfig = {
        pending: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', icon: '⏳' },
        approved: { bg: 'bg-green-500/20', text: 'text-green-400', icon: '✅' },
        rejected: { bg: 'bg-red-500/20', text: 'text-red-400', icon: '❌' }
    }

    const categoryColors: Record<string, string> = {
        'Tools': '#FFB800',
        'Education': '#00E5FF',
        'Climate': '#00FFA3',
        'Infrastructure': '#A855F7',
        'Marketplace': '#FF6B6B'
    }

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-4xl font-bold text-white">
                        📋 <span className="text-gradient">Project Approval</span>
                    </h1>
                    <p className="text-gray-400 mt-2">Review and approve project submissions</p>
                </div>
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-yellow-500/10 border border-yellow-500/30">
                        <span className="text-yellow-400">⏳</span>
                        <span className="text-yellow-400 font-semibold">
                            {MOCK_PROJECTS.filter(p => p.status === 'pending').length} Pending Review
                        </span>
                    </div>
                </div>
            </div>

            {/* Filter Tabs */}
            <div className="flex gap-2">
                {[
                    { key: 'all', label: 'All Projects', count: MOCK_PROJECTS.length },
                    { key: 'pending', label: 'Pending', count: MOCK_PROJECTS.filter(p => p.status === 'pending').length },
                    { key: 'approved', label: 'Approved', count: MOCK_PROJECTS.filter(p => p.status === 'approved').length },
                    { key: 'rejected', label: 'Rejected', count: MOCK_PROJECTS.filter(p => p.status === 'rejected').length },
                ].map((tab) => (
                    <button
                        key={tab.key}
                        onClick={() => setFilter(tab.key as any)}
                        className={`px-4 py-2 rounded-xl text-sm font-medium transition-all flex items-center gap-2 ${filter === tab.key
                                ? 'bg-white/10 text-white border border-white/20'
                                : 'text-gray-400 hover:text-white hover:bg-white/5'
                            }`}
                    >
                        {tab.label}
                        <span className={`px-2 py-0.5 rounded-full text-xs ${filter === tab.key ? 'bg-white/20' : 'bg-white/5'
                            }`}>
                            {tab.count}
                        </span>
                    </button>
                ))}
            </div>

            {/* Projects Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {filteredProjects.map((project) => {
                    const status = statusConfig[project.status]
                    const categoryColor = categoryColors[project.category] || '#A855F7'

                    return (
                        <div
                            key={project.id}
                            className="glass-panel p-6 hover:border-white/20 transition-all cursor-pointer group"
                            onClick={() => setSelectedProject(project)}
                        >
                            {/* Header */}
                            <div className="flex items-start justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <div
                                        className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl"
                                        style={{ background: `${categoryColor}20` }}
                                    >
                                        {project.category === 'Tools' ? '🔧' :
                                            project.category === 'Education' ? '📚' :
                                                project.category === 'Climate' ? '🌱' :
                                                    project.category === 'Infrastructure' ? '🏗️' : '🛒'}
                                    </div>
                                    <div>
                                        <h3 className="text-white font-bold text-lg group-hover:text-neon-cyan transition-colors">
                                            {project.name}
                                        </h3>
                                        <p className="text-gray-500 text-sm">{project.owner}</p>
                                    </div>
                                </div>
                                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${status.bg} ${status.text} flex items-center gap-1`}>
                                    {status.icon} {project.status.charAt(0).toUpperCase() + project.status.slice(1)}
                                </span>
                            </div>

                            {/* Description */}
                            <p className="text-gray-400 text-sm mb-4 line-clamp-2">{project.description}</p>

                            {/* Meta */}
                            <div className="flex items-center justify-between text-sm border-t border-white/10 pt-4">
                                <div className="flex items-center gap-4">
                                    <span
                                        className="px-2 py-1 rounded-lg text-xs font-medium"
                                        style={{ background: `${categoryColor}20`, color: categoryColor }}
                                    >
                                        {project.category}
                                    </span>
                                    <span className="text-gray-500">
                                        📅 {project.submittedAt}
                                    </span>
                                </div>
                                <span className="text-neon-mint font-semibold">{project.fundingRequest}</span>
                            </div>

                            {/* Action Buttons for Pending */}
                            {project.status === 'pending' && (
                                <div className="flex gap-3 mt-4 pt-4 border-t border-white/10">
                                    <button
                                        onClick={(e) => { e.stopPropagation(); }}
                                        className="flex-1 px-4 py-2 rounded-xl bg-green-500/20 text-green-400 font-medium hover:bg-green-500/30 transition-colors flex items-center justify-center gap-2"
                                    >
                                        ✅ Approve
                                    </button>
                                    <button
                                        onClick={(e) => { e.stopPropagation(); }}
                                        className="flex-1 px-4 py-2 rounded-xl bg-red-500/20 text-red-400 font-medium hover:bg-red-500/30 transition-colors flex items-center justify-center gap-2"
                                    >
                                        ❌ Reject
                                    </button>
                                </div>
                            )}
                        </div>
                    )
                })}
            </div>

            {/* Detail Modal */}
            {selectedProject && (
                <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="glass-panel p-8 max-w-2xl w-full space-y-6 relative max-h-[90vh] overflow-y-auto">
                        <button
                            onClick={() => setSelectedProject(null)}
                            className="absolute top-4 right-4 text-gray-400 hover:text-white"
                        >
                            ✕
                        </button>

                        <div className="flex items-start gap-4">
                            <div
                                className="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl"
                                style={{ background: `${categoryColors[selectedProject.category]}20` }}
                            >
                                {selectedProject.category === 'Tools' ? '🔧' :
                                    selectedProject.category === 'Education' ? '📚' :
                                        selectedProject.category === 'Climate' ? '🌱' :
                                            selectedProject.category === 'Infrastructure' ? '🏗️' : '🛒'}
                            </div>
                            <div>
                                <h2 className="text-2xl font-bold text-white">{selectedProject.name}</h2>
                                <p className="text-gray-400">by {selectedProject.owner}</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-4 rounded-xl bg-white/5">
                                <p className="text-gray-400 text-sm">Funding Request</p>
                                <p className="text-xl font-bold text-neon-mint">{selectedProject.fundingRequest}</p>
                            </div>
                            <div className="p-4 rounded-xl bg-white/5">
                                <p className="text-gray-400 text-sm">Wallet Address</p>
                                <p className="text-white font-mono">{selectedProject.walletAddress}</p>
                            </div>
                        </div>

                        <div>
                            <h3 className="text-white font-semibold mb-2">Description</h3>
                            <p className="text-gray-300">{selectedProject.description}</p>
                        </div>

                        {selectedProject.status === 'pending' && (
                            <div className="flex gap-3 pt-4 border-t border-white/10">
                                <button className="flex-1 px-6 py-3 rounded-xl bg-green-500/20 text-green-400 font-semibold hover:bg-green-500/30 transition-colors">
                                    ✅ Approve Project
                                </button>
                                <button className="flex-1 px-6 py-3 rounded-xl bg-red-500/20 text-red-400 font-semibold hover:bg-red-500/30 transition-colors">
                                    ❌ Reject Project
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    )
}
