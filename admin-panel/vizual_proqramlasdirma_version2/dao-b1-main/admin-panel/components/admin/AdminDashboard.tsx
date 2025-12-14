'use client'

import React from 'react'
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
    BarChart,
    Bar,
    LineChart,
    Line,
} from 'recharts'
import { useDashboardStats, useRecentActivity, useProjects, useRounds } from '../../lib/hooks'

// Stats Card Component
function StatsCard({ icon, label, value, change, trend }: {
    icon: string
    label: string
    value: string
    change: string
    trend: 'up' | 'down' | 'neutral'
}) {
    const trendColors = {
        up: 'text-green-400',
        down: 'text-red-400',
        neutral: 'text-gray-400'
    }

    return (
        <div className="glass-panel p-6 group hover:border-white/20 transition-all duration-300 hover:shadow-[0_0_30px_rgba(168,85,247,0.15)]">
            <div className="flex items-start justify-between">
                <div className="space-y-2">
                    <p className="text-gray-400 text-sm font-medium">{label}</p>
                    <p className="text-3xl font-bold text-white">{value}</p>
                    <p className={`text-sm font-semibold ${trendColors[trend]}`}>
                        {trend === 'up' && '↑'}
                        {trend === 'down' && '↓'}
                        {change}
                    </p>
                </div>
                <div className="text-4xl opacity-80 group-hover:scale-110 transition-transform">
                    {icon}
                </div>
            </div>
            <div className="mt-4 h-1 rounded-full overflow-hidden bg-white/10">
                <div
                    className="h-full rounded-full"
                    style={{
                        width: '75%',
                        background: 'linear-gradient(90deg, #A855F7, #00E5FF)'
                    }}
                />
            </div>
        </div>
    )
}

// Activity Item Component
function ActivityItem({ type, description, time, status }: {
    type: string
    description: string
    time: string
    status?: 'success' | 'pending' | 'warning'
}) {
    const typeIcons: Record<string, string> = {
        'Project': '📝',
        'Contribution': '💳',
        'Round': '🎯',
        'Approval': '✅',
        'Vote': '🗳️',
    }

    const statusColors = {
        success: 'bg-green-500',
        pending: 'bg-yellow-500',
        warning: 'bg-red-500',
    }

    return (
        <div className="flex items-start gap-4 p-4 rounded-xl hover:bg-white/5 transition-colors group">
            <div className="text-2xl group-hover:scale-110 transition-transform">
                {typeIcons[type] || '📌'}
            </div>
            <div className="flex-1 min-w-0">
                <p className="text-white text-sm font-medium truncate">{description}</p>
                <p className="text-gray-500 text-xs mt-1">{time}</p>
            </div>
            {status && (
                <div className={`w-2 h-2 rounded-full ${statusColors[status]} mt-2`} />
            )}
        </div>
    )
}

const FUNDING_DATA = [
    { name: 'Jan', amount: 45000, projects: 12 },
    { name: 'Feb', amount: 52000, projects: 15 },
    { name: 'Mar', amount: 48000, projects: 14 },
    { name: 'Apr', amount: 61000, projects: 18 },
    { name: 'May', amount: 55000, projects: 16 },
    { name: 'Jun', amount: 67000, projects: 22 },
    { name: 'Jul', amount: 72000, projects: 25 },
]

const CATEGORY_DATA = [
    { name: 'Infrastructure', value: 35, color: '#A855F7' },
    { name: 'Climate', value: 25, color: '#00FFA3' },
    { name: 'Education', value: 20, color: '#00E5FF' },
    { name: 'Healthcare', value: 12, color: '#FFB800' },
    { name: 'Other', value: 8, color: '#FF6B6B' },
]

const RECENT_TRANSACTIONS = [
    { type: 'Contribution', description: '0x7a2...f3b contributed 2.5 ETH to Web3 Infrastructure', time: '2 min ago', status: 'success' as const },
    { type: 'Project', description: 'New project "DeFi Analytics" submitted for review', time: '15 min ago', status: 'pending' as const },
    { type: 'Vote', description: 'Governance proposal #47 passed with 78% approval', time: '1 hour ago', status: 'success' as const },
    { type: 'Round', description: 'Climate Impact Round reached $100K milestone', time: '3 hours ago', status: 'success' as const },
    { type: 'Approval', description: 'Project "Open Education" approved by committee', time: '5 hours ago', status: 'success' as const },
]

export function AdminDashboard() {
    const { data: stats } = useDashboardStats()
    const { data: activity } = useRecentActivity()

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-4xl font-bold text-white">
                        👑 <span className="text-gradient">Dashboard</span>
                    </h1>
                    <p className="text-gray-400 mt-2">Welcome back! Here's your DAO overview.</p>
                </div>
                <div className="flex gap-3">
                    <button className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-gray-300 hover:bg-white/10 transition-colors">
                        📅 This Month
                    </button>
                    <button className="btn-premium px-6 py-2 rounded-xl">
                        Export Report
                    </button>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatsCard
                    icon="💰"
                    label="Total Funding"
                    value={stats ? `$${(stats.total_funding / 1000).toFixed(1)}K` : '$2.4M'}
                    change="+12.5% from last month"
                    trend="up"
                />
                <StatsCard
                    icon="📊"
                    label="Active Projects"
                    value={stats?.total_projects?.toString() || '127'}
                    change="+8 this week"
                    trend="up"
                />
                <StatsCard
                    icon="👥"
                    label="Contributors"
                    value={stats?.contributors?.toLocaleString() || '5,234'}
                    change="+342 new"
                    trend="up"
                />
                <StatsCard
                    icon="🎯"
                    label="Active Rounds"
                    value={stats?.active_rounds?.toString() || '4'}
                    change="2 ending soon"
                    trend="neutral"
                />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Main Chart */}
                <div className="lg:col-span-2 glass-panel p-6">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-xl font-bold text-white">Funding Overview</h3>
                        <div className="flex gap-2">
                            {['7D', '1M', '3M', '1Y'].map((period) => (
                                <button
                                    key={period}
                                    className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${period === '1M'
                                            ? 'bg-white/10 text-white'
                                            : 'text-gray-400 hover:text-white'
                                        }`}
                                >
                                    {period}
                                </button>
                            ))}
                        </div>
                    </div>
                    <div className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={FUNDING_DATA}>
                                <defs>
                                    <linearGradient id="colorFunding" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#A855F7" stopOpacity={0.4} />
                                        <stop offset="95%" stopColor="#A855F7" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                                <XAxis dataKey="name" stroke="#6B7280" />
                                <YAxis stroke="#6B7280" />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: 'rgba(17, 24, 39, 0.95)',
                                        border: '1px solid rgba(255,255,255,0.1)',
                                        borderRadius: '12px',
                                    }}
                                    itemStyle={{ color: '#fff' }}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="amount"
                                    stroke="#A855F7"
                                    strokeWidth={3}
                                    fillOpacity={1}
                                    fill="url(#colorFunding)"
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Category Distribution */}
                <div className="glass-panel p-6">
                    <h3 className="text-xl font-bold text-white mb-6">Projects by Category</h3>
                    <div className="h-[200px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={CATEGORY_DATA}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={50}
                                    outerRadius={80}
                                    paddingAngle={3}
                                    dataKey="value"
                                >
                                    {CATEGORY_DATA.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: 'rgba(17, 24, 39, 0.95)',
                                        border: '1px solid rgba(255,255,255,0.1)',
                                        borderRadius: '12px',
                                    }}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="mt-4 space-y-2">
                        {CATEGORY_DATA.map((cat) => (
                            <div key={cat.name} className="flex items-center justify-between text-sm">
                                <div className="flex items-center gap-2">
                                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: cat.color }} />
                                    <span className="text-gray-300">{cat.name}</span>
                                </div>
                                <span className="text-white font-medium">{cat.value}%</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Recent Activity */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="glass-panel p-6">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-xl font-bold text-white">Recent Activity</h3>
                        <button className="text-sm text-neon-cyan hover:underline">View All</button>
                    </div>
                    <div className="space-y-1">
                        {(activity || RECENT_TRANSACTIONS).map((item, i) => (
                            <ActivityItem
                                key={i}
                                type={item.type}
                                description={item.description}
                                time={'timestamp' in item ? item.timestamp : item.time}
                                status={'status' in item ? item.status : 'success'}
                            />
                        ))}
                    </div>
                </div>

                {/* Quick Actions */}
                <div className="glass-panel p-6">
                    <h3 className="text-xl font-bold text-white mb-6">Quick Actions</h3>
                    <div className="grid grid-cols-2 gap-4">
                        {[
                            { icon: '🎯', label: 'New Round', color: '#A855F7' },
                            { icon: '📋', label: 'Review Projects', color: '#00E5FF' },
                            { icon: '💰', label: 'Add to Pool', color: '#00FFA3' },
                            { icon: '⚖️', label: 'Create Vote', color: '#FFB800' },
                            { icon: '📊', label: 'Analytics', color: '#FF6B6B' },
                            { icon: '🛡️', label: 'Security', color: '#A855F7' },
                        ].map((action) => (
                            <button
                                key={action.label}
                                className="p-4 rounded-xl border border-white/10 hover:border-white/20 transition-all hover:shadow-lg group"
                                style={{ background: `${action.color}10` }}
                            >
                                <div className="text-3xl mb-2 group-hover:scale-110 transition-transform">
                                    {action.icon}
                                </div>
                                <p className="text-white font-medium text-sm">{action.label}</p>
                            </button>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}
