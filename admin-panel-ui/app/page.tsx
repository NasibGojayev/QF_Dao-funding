'use client'

import React, { useState } from 'react'
import { AdminSidebar } from '../components/admin/AdminSidebar'
import { AdminDashboard } from '../components/admin/AdminDashboard'
import { RoundsManager } from '../components/admin/RoundsManager'
import { ProjectApproval } from '../components/admin/ProjectApproval'
import { MatchingPoolMonitor } from '../components/admin/MatchingPoolMonitor'
import { SybilScorePanel } from '../components/admin/SybilScorePanel'
import { GovernancePanel } from '../components/admin/GovernancePanel'
import { LogsViewer } from '../components/admin/LogsViewer'

export default function AdminPage() {
    const [activeSection, setActiveSection] = useState('dashboard')
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

    const renderContent = () => {
        switch (activeSection) {
            case 'dashboard':
                return <AdminDashboard />
            case 'rounds':
                return <RoundsManager />
            case 'projects':
                return <ProjectApproval />
            case 'matching-pool':
                return <MatchingPoolMonitor />
            case 'sybil':
                return <SybilScorePanel />
            case 'governance':
                return <GovernancePanel />
            case 'logs':
                return <LogsViewer />
            default:
                return <AdminDashboard />
        }
    }

    return (
        <div style={{ minHeight: '100vh', background: 'radial-gradient(circle at top center, #1a1f2e 0%, #0B0F17 100%)' }}>
            {/* Sidebar */}
            <AdminSidebar
                activeSection={activeSection}
                onSectionChange={setActiveSection}
                isCollapsed={sidebarCollapsed}
                onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
            />

            {/* Main Content */}
            <main
                style={{
                    marginLeft: sidebarCollapsed ? '80px' : '256px',
                    transition: 'margin-left 0.3s ease'
                }}
            >
                {/* Top Bar */}
                <header style={{
                    position: 'sticky',
                    top: 0,
                    zIndex: 40,
                    backdropFilter: 'blur(20px)',
                    borderBottom: '1px solid rgba(255,255,255,0.1)',
                    background: 'rgba(11, 15, 23, 0.8)'
                }}>
                    <div style={{ padding: '16px 32px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                            <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px',
                                padding: '8px 16px',
                                borderRadius: '12px',
                                background: 'rgba(0, 255, 163, 0.1)',
                                border: '1px solid rgba(0, 255, 163, 0.3)'
                            }}>
                                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#00FFA3', animation: 'pulse 2s infinite' }} />
                                <span style={{ color: '#00FFA3', fontSize: '14px', fontWeight: 500 }}>System Online</span>
                            </div>
                            <span style={{ color: '#6B7280', fontSize: '14px' }}>Port 6240</span>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                            <button style={{ padding: '8px', borderRadius: '12px', background: 'transparent', border: 'none', cursor: 'pointer', position: 'relative' }}>
                                <span style={{ fontSize: '20px' }}>🔔</span>
                                <span style={{ position: 'absolute', top: '4px', right: '4px', width: '8px', height: '8px', borderRadius: '50%', background: '#EF4444' }} />
                            </button>

                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', paddingLeft: '16px', borderLeft: '1px solid rgba(255,255,255,0.1)' }}>
                                <div style={{
                                    width: '40px',
                                    height: '40px',
                                    borderRadius: '12px',
                                    background: 'linear-gradient(135deg, #A855F7, #00E5FF)',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    fontSize: '20px'
                                }}>
                                    👑
                                </div>
                                <div>
                                    <p style={{ color: 'white', fontWeight: 500, fontSize: '14px', margin: 0 }}>Admin</p>
                                    <p style={{ color: '#6B7280', fontSize: '12px', fontFamily: 'monospace', margin: 0 }}>0x7a2...f3b</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </header>

                {/* Page Content */}
                <div style={{ padding: '32px' }}>
                    {renderContent()}
                </div>

                {/* Footer */}
                <footer style={{ borderTop: '1px solid rgba(255,255,255,0.1)', padding: '24px 32px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '14px', color: '#6B7280' }}>
                        <p style={{ margin: 0 }}>© 2024 DAO Admin Panel - Running on Port 6240</p>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                            <a href="#" style={{ color: '#6B7280', textDecoration: 'none' }}>Documentation</a>
                            <a href="#" style={{ color: '#6B7280', textDecoration: 'none' }}>API</a>
                        </div>
                    </div>
                </footer>
            </main>
        </div>
    )
}
