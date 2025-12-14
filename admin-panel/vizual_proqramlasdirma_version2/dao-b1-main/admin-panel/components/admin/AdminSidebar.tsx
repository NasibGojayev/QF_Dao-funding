'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

interface SidebarItem {
    id: string
    label: string
    icon: string
    emoji: string
}

const SIDEBAR_ITEMS: SidebarItem[] = [
    { id: 'dashboard', label: 'Dashboard', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6', emoji: '📊' },
    { id: 'rounds', label: 'Manage Rounds', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z', emoji: '🎯' },
    { id: 'projects', label: 'Projects', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2', emoji: '📋' },
    { id: 'matching-pool', label: 'Matching Pool', icon: 'M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z', emoji: '💰' },
    { id: 'sybil', label: 'Sybil Score', icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z', emoji: '🛡️' },
    { id: 'governance', label: 'Governance', icon: 'M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3', emoji: '⚖️' },
    { id: 'logs', label: 'System Logs', icon: 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z', emoji: '📜' },
]

interface AdminSidebarProps {
    activeSection: string
    onSectionChange: (section: string) => void
    isCollapsed: boolean
    onToggleCollapse: () => void
}

export function AdminSidebar({ activeSection, onSectionChange, isCollapsed, onToggleCollapse }: AdminSidebarProps) {
    return (
        <aside
            className={`fixed left-0 top-0 h-screen z-50 transition-all duration-300 ease-in-out ${isCollapsed ? 'w-20' : 'w-64'
                }`}
            style={{
                background: 'linear-gradient(180deg, rgba(17, 24, 39, 0.98) 0%, rgba(11, 15, 23, 0.98) 100%)',
                borderRight: '1px solid rgba(255, 255, 255, 0.08)',
                backdropFilter: 'blur(20px)',
            }}
        >
            {/* Logo Section */}
            <div className="h-20 flex items-center justify-between px-4 border-b border-white/10">
                {!isCollapsed && (
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
                            style={{ background: 'linear-gradient(135deg, #A855F7, #00E5FF)' }}>
                            👑
                        </div>
                        <div>
                            <h1 className="font-bold text-white text-lg">Admin</h1>
                            <p className="text-xs text-gray-400">DAO Control Center</p>
                        </div>
                    </div>
                )}
                {isCollapsed && (
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl mx-auto"
                        style={{ background: 'linear-gradient(135deg, #A855F7, #00E5FF)' }}>
                        👑
                    </div>
                )}
                <button
                    onClick={onToggleCollapse}
                    className="p-2 rounded-lg hover:bg-white/10 transition-colors text-gray-400 hover:text-white"
                >
                    <svg className={`w-5 h-5 transition-transform ${isCollapsed ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
                    </svg>
                </button>
            </div>

            {/* Navigation */}
            <nav className="p-4 space-y-2">
                {SIDEBAR_ITEMS.map((item) => (
                    <button
                        key={item.id}
                        onClick={() => onSectionChange(item.id)}
                        className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group relative overflow-hidden ${activeSection === item.id
                                ? 'text-white'
                                : 'text-gray-400 hover:text-white hover:bg-white/5'
                            }`}
                    >
                        {/* Active indicator glow */}
                        {activeSection === item.id && (
                            <>
                                <div
                                    className="absolute inset-0 opacity-20"
                                    style={{ background: 'linear-gradient(135deg, #A855F7, #00E5FF)' }}
                                />
                                <div
                                    className="absolute left-0 top-0 bottom-0 w-1 rounded-r-full"
                                    style={{ background: 'linear-gradient(180deg, #A855F7, #00E5FF)' }}
                                />
                            </>
                        )}

                        <span className={`text-xl transition-transform group-hover:scale-110 ${activeSection === item.id ? 'animate-pulse' : ''
                            }`}>
                            {item.emoji}
                        </span>

                        {!isCollapsed && (
                            <span className="font-medium relative z-10">{item.label}</span>
                        )}

                        {/* Hover glow effect */}
                        <div className="absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity"
                            style={{ background: 'radial-gradient(circle at center, #A855F7, transparent)' }}
                        />
                    </button>
                ))}
            </nav>

            {/* Bottom Section */}
            <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-white/10">
                {!isCollapsed ? (
                    <div className="glass-panel p-4 space-y-2">
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                            <span className="text-xs text-green-400">System Online</span>
                        </div>
                        <p className="text-xs text-gray-500">v2.0.0 • Quadratic Funding</p>
                    </div>
                ) : (
                    <div className="flex justify-center">
                        <div className="w-3 h-3 rounded-full bg-green-400 animate-pulse" />
                    </div>
                )}
            </div>
        </aside>
    )
}
