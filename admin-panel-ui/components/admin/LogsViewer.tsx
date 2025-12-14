'use client'

import React, { useState, useEffect } from 'react'

interface LogEntry {
    id: number
    timestamp: string
    level: 'info' | 'warning' | 'error' | 'debug'
    source: 'frontend' | 'backend' | 'database'
    action: string
    details: string
    duration?: string
    user?: string
}

const MOCK_LOGS: LogEntry[] = [
    {
        id: 1,
        timestamp: '2024-01-15 14:32:15.234',
        level: 'info',
        source: 'frontend',
        action: 'API_REQUEST',
        details: 'GET /api/public/projects/ - Fetching projects list',
        duration: '45ms',
        user: '0x7a2...f3b'
    },
    {
        id: 2,
        timestamp: '2024-01-15 14:32:15.279',
        level: 'info',
        source: 'backend',
        action: 'API_RESPONSE',
        details: 'GET /api/public/projects/ - 200 OK - 24 projects returned',
        duration: '38ms'
    },
    {
        id: 3,
        timestamp: '2024-01-15 14:32:15.285',
        level: 'debug',
        source: 'database',
        action: 'QUERY',
        details: 'SELECT * FROM api_project ORDER BY created_at DESC',
        duration: '12ms'
    },
    {
        id: 4,
        timestamp: '2024-01-15 14:31:42.102',
        level: 'warning',
        source: 'backend',
        action: 'RATE_LIMIT',
        details: 'Rate limit approaching for IP 192.168.1.45 (85/100 requests)',
        user: '192.168.1.45'
    },
    {
        id: 5,
        timestamp: '2024-01-15 14:30:58.891',
        level: 'info',
        source: 'frontend',
        action: 'API_REQUEST',
        details: 'POST /api/projects/ - Creating new project',
        duration: '120ms',
        user: '0x8b3...e2c'
    },
    {
        id: 6,
        timestamp: '2024-01-15 14:30:59.011',
        level: 'info',
        source: 'database',
        action: 'INSERT',
        details: 'INSERT INTO api_project (title, description, owner_id) VALUES (...)',
        duration: '25ms'
    },
    {
        id: 7,
        timestamp: '2024-01-15 14:28:33.445',
        level: 'error',
        source: 'backend',
        action: 'AUTH_FAILURE',
        details: 'Invalid token provided for protected endpoint /api/projects/',
        user: '0x9e5...b7d'
    },
    {
        id: 8,
        timestamp: '2024-01-15 14:25:12.667',
        level: 'info',
        source: 'frontend',
        action: 'PAGE_VIEW',
        details: 'Admin dashboard accessed',
        user: '0x4d1...a9f'
    },
    {
        id: 9,
        timestamp: '2024-01-15 14:22:45.123',
        level: 'info',
        source: 'backend',
        action: 'CACHE_HIT',
        details: 'Cache hit for dashboard_stats - TTL 45s remaining',
        duration: '2ms'
    },
    {
        id: 10,
        timestamp: '2024-01-15 14:20:33.789',
        level: 'warning',
        source: 'database',
        action: 'SLOW_QUERY',
        details: 'Query exceeded 100ms threshold: SELECT with JOIN on grants',
        duration: '156ms'
    }
]

export function LogsViewer() {
    const [logs, setLogs] = useState<LogEntry[]>(MOCK_LOGS)
    const [filter, setFilter] = useState<'all' | 'frontend' | 'backend' | 'database'>('all')
    const [levelFilter, setLevelFilter] = useState<'all' | 'info' | 'warning' | 'error' | 'debug'>('all')
    const [isLive, setIsLive] = useState(false)
    const [searchQuery, setSearchQuery] = useState('')

    useEffect(() => {
        if (isLive) {
            const interval = setInterval(() => {
                const newLog: LogEntry = {
                    id: Date.now(),
                    timestamp: new Date().toISOString().replace('T', ' ').slice(0, 23),
                    level: ['info', 'info', 'info', 'debug', 'warning'][Math.floor(Math.random() * 5)] as any,
                    source: ['frontend', 'backend', 'database'][Math.floor(Math.random() * 3)] as any,
                    action: ['API_REQUEST', 'QUERY', 'CACHE_HIT', 'PAGE_VIEW'][Math.floor(Math.random() * 4)],
                    details: 'Live log entry - System monitoring active',
                    duration: `${Math.floor(Math.random() * 100)}ms`
                }
                setLogs(prev => [newLog, ...prev.slice(0, 99)])
            }, 2000)
            return () => clearInterval(interval)
        }
    }, [isLive])

    const filteredLogs = logs.filter(log => {
        if (filter !== 'all' && log.source !== filter) return false
        if (levelFilter !== 'all' && log.level !== levelFilter) return false
        if (searchQuery && !log.details.toLowerCase().includes(searchQuery.toLowerCase())) return false
        return true
    })

    const levelConfig = {
        info: { bg: 'bg-blue-500/20', text: 'text-blue-400', icon: 'ℹ️' },
        warning: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', icon: '⚠️' },
        error: { bg: 'bg-red-500/20', text: 'text-red-400', icon: '❌' },
        debug: { bg: 'bg-gray-500/20', text: 'text-gray-400', icon: '🔧' }
    }

    const sourceConfig = {
        frontend: { color: '#00E5FF', label: 'Frontend' },
        backend: { color: '#A855F7', label: 'Backend' },
        database: { color: '#00FFA3', label: 'Database' }
    }

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-4xl font-bold text-white">
                        📜 <span className="text-gradient">System Logs</span>
                    </h1>
                    <p className="text-gray-400 mt-2">Front-Back and Back-Database data transfer logs</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={() => setIsLive(!isLive)}
                        className={`px-4 py-2 rounded-xl flex items-center gap-2 transition-all ${isLive
                                ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                                : 'bg-white/5 text-gray-400 border border-white/10 hover:bg-white/10'
                            }`}
                    >
                        <div className={`w-2 h-2 rounded-full ${isLive ? 'bg-green-400 animate-pulse' : 'bg-gray-500'}`} />
                        {isLive ? 'Live' : 'Paused'}
                    </button>
                    <button className="btn-premium px-6 py-2 rounded-xl flex items-center gap-2">
                        📥 Export Logs
                    </button>
                </div>
            </div>

            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {[
                    { label: 'Total Logs', value: logs.length.toLocaleString(), icon: '📊', color: '#A855F7' },
                    { label: 'Errors', value: logs.filter(l => l.level === 'error').length.toString(), icon: '❌', color: '#FF6B6B' },
                    { label: 'Warnings', value: logs.filter(l => l.level === 'warning').length.toString(), icon: '⚠️', color: '#FFB800' },
                    { label: 'Avg Response', value: '42ms', icon: '⚡', color: '#00FFA3' },
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

            {/* Filters */}
            <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1 relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">🔍</span>
                    <input
                        type="text"
                        placeholder="Search logs..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-12 pr-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-neon-purple"
                    />
                </div>
                <div className="flex gap-2">
                    <div className="flex gap-1 p-1 rounded-xl bg-white/5">
                        {['all', 'frontend', 'backend', 'database'].map((f) => (
                            <button
                                key={f}
                                onClick={() => setFilter(f as any)}
                                className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${filter === f
                                        ? 'bg-white/10 text-white'
                                        : 'text-gray-400 hover:text-white'
                                    }`}
                            >
                                {f === 'all' ? 'All Sources' : f.charAt(0).toUpperCase() + f.slice(1)}
                            </button>
                        ))}
                    </div>
                    <div className="flex gap-1 p-1 rounded-xl bg-white/5">
                        {['all', 'info', 'warning', 'error', 'debug'].map((l) => (
                            <button
                                key={l}
                                onClick={() => setLevelFilter(l as any)}
                                className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${levelFilter === l
                                        ? 'bg-white/10 text-white'
                                        : 'text-gray-400 hover:text-white'
                                    }`}
                            >
                                {l === 'all' ? 'All Levels' : l.charAt(0).toUpperCase() + l.slice(1)}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Logs Table */}
            <div className="glass-panel overflow-hidden">
                <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
                    <table className="w-full">
                        <thead className="sticky top-0 bg-dark-surface z-10">
                            <tr className="bg-white/5">
                                <th className="text-left p-4 text-gray-400 text-sm font-semibold">Timestamp</th>
                                <th className="text-left p-4 text-gray-400 text-sm font-semibold">Level</th>
                                <th className="text-left p-4 text-gray-400 text-sm font-semibold">Source</th>
                                <th className="text-left p-4 text-gray-400 text-sm font-semibold">Action</th>
                                <th className="text-left p-4 text-gray-400 text-sm font-semibold">Details</th>
                                <th className="text-left p-4 text-gray-400 text-sm font-semibold">Duration</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredLogs.map((log) => {
                                const level = levelConfig[log.level]
                                const source = sourceConfig[log.source]
                                return (
                                    <tr key={log.id} className="border-t border-white/5 hover:bg-white/5 transition-colors">
                                        <td className="p-4 text-gray-400 text-sm font-mono whitespace-nowrap">
                                            {log.timestamp}
                                        </td>
                                        <td className="p-4">
                                            <span className={`px-2 py-1 rounded-lg text-xs font-semibold ${level.bg} ${level.text} flex items-center gap-1 w-fit`}>
                                                {level.icon} {log.level.toUpperCase()}
                                            </span>
                                        </td>
                                        <td className="p-4">
                                            <span
                                                className="px-2 py-1 rounded-lg text-xs font-medium"
                                                style={{ background: `${source.color}20`, color: source.color }}
                                            >
                                                {source.label}
                                            </span>
                                        </td>
                                        <td className="p-4 text-white font-medium text-sm">
                                            {log.action}
                                        </td>
                                        <td className="p-4 text-gray-300 text-sm max-w-md truncate">
                                            {log.details}
                                            {log.user && (
                                                <span className="ml-2 text-gray-500">({log.user})</span>
                                            )}
                                        </td>
                                        <td className="p-4">
                                            {log.duration ? (
                                                <span className={`text-sm font-mono ${parseInt(log.duration) > 100 ? 'text-yellow-400' : 'text-green-400'
                                                    }`}>
                                                    {log.duration}
                                                </span>
                                            ) : (
                                                <span className="text-gray-500">-</span>
                                            )}
                                        </td>
                                    </tr>
                                )
                            })}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Log File Info */}
            <div className="glass-panel p-6">
                <h3 className="text-lg font-bold text-white mb-4">📁 Log Files</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {[
                        { name: 'frontend_requests.log', size: '2.4 MB', updated: '2 min ago', color: '#00E5FF' },
                        { name: 'backend_api.log', size: '5.1 MB', updated: '1 min ago', color: '#A855F7' },
                        { name: 'database_queries.log', size: '3.8 MB', updated: '30 sec ago', color: '#00FFA3' },
                    ].map((file) => (
                        <div key={file.name} className="p-4 rounded-xl bg-white/5 border border-white/10 hover:border-white/20 transition-colors cursor-pointer">
                            <div className="flex items-center gap-3">
                                <div
                                    className="w-10 h-10 rounded-lg flex items-center justify-center"
                                    style={{ background: `${file.color}20` }}
                                >
                                    📄
                                </div>
                                <div className="flex-1">
                                    <p className="text-white font-medium text-sm">{file.name}</p>
                                    <p className="text-gray-500 text-xs">{file.size} • Updated {file.updated}</p>
                                </div>
                                <button className="text-gray-400 hover:text-white">📥</button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}
