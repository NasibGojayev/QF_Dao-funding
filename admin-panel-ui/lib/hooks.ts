'use client'

import { useState, useEffect, useCallback } from 'react'

// API Base URL - defaults to localhost:8000 (Django backend)
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Generic fetch hook
function useFetch<T>(endpoint: string, refreshInterval?: number) {
    const [data, setData] = useState<T | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<Error | null>(null)

    const fetchData = useCallback(async () => {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`)
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`)
            }
            const json = await response.json()
            // Handle paginated responses
            setData(json.results || json)
            setError(null)
        } catch (e) {
            console.error(`Error fetching ${endpoint}:`, e)
            setError(e as Error)
        } finally {
            setLoading(false)
        }
    }, [endpoint])

    useEffect(() => {
        fetchData()

        if (refreshInterval) {
            const interval = setInterval(fetchData, refreshInterval)
            return () => clearInterval(interval)
        }
    }, [fetchData, refreshInterval])

    return { data, loading, error, refetch: fetchData }
}

// Dashboard Stats Hook
export interface DashboardStats {
    total_funding: number
    total_projects: number
    contributors: number
    active_rounds: number
}

export function useDashboardStats() {
    const [stats, setStats] = useState<DashboardStats | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<Error | null>(null)

    useEffect(() => {
        async function fetchStats() {
            try {
                // Fetch from multiple endpoints and aggregate
                const [proposalsRes, roundsRes, donationsRes] = await Promise.all([
                    fetch(`${API_BASE_URL}/api/proposals/`).catch(() => null),
                    fetch(`${API_BASE_URL}/api/rounds/`).catch(() => null),
                    fetch(`${API_BASE_URL}/api/donations/`).catch(() => null),
                ])

                const proposals = proposalsRes?.ok ? await proposalsRes.json() : { results: [] }
                const rounds = roundsRes?.ok ? await roundsRes.json() : { results: [] }
                const donations = donationsRes?.ok ? await donationsRes.json() : { results: [] }

                const proposalList = proposals.results || proposals || []
                const roundList = rounds.results || rounds || []
                const donationList = donations.results || donations || []

                // Calculate stats
                const totalFunding = donationList.reduce((sum: number, d: { amount?: number }) =>
                    sum + (parseFloat(String(d.amount)) || 0), 0)

                const activeRounds = roundList.filter((r: { status?: string }) =>
                    r.status === 'active').length

                // Get unique donors
                const uniqueDonors = new Set(donationList.map((d: { donor?: number }) => d.donor))

                setStats({
                    total_funding: totalFunding,
                    total_projects: proposalList.length,
                    contributors: uniqueDonors.size,
                    active_rounds: activeRounds,
                })
                setError(null)
            } catch (e) {
                console.error('Error fetching dashboard stats:', e)
                setError(e as Error)
            } finally {
                setLoading(false)
            }
        }

        fetchStats()
        const interval = setInterval(fetchStats, 30000) // Refresh every 30 seconds
        return () => clearInterval(interval)
    }, [])

    return { data: stats, loading, error }
}

// Recent Activity Hook
export interface Activity {
    type: string
    description: string
    timestamp: string
    status: 'success' | 'pending' | 'warning'
}

export function useRecentActivity() {
    const { data: events, loading, error } = useFetch<any[]>('/api/contract-events/', 15000)

    const activities: Activity[] = events?.slice(0, 10).map((event: any) => ({
        type: event.event_type || 'Event',
        description: `${event.event_type}: ${event.tx_hash?.slice(0, 10)}...`,
        timestamp: new Date(event.timestamp).toLocaleString(),
        status: 'success' as const,
    })) || []

    return { data: activities, loading, error }
}

// Projects Hook
export interface Project {
    proposal_id: number
    title: string
    description: string
    status: string
    total_donations: number
    created_at: string
    proposer: number
}

export function useProjects() {
    return useFetch<Project[]>('/api/proposals/', 30000)
}

// Rounds Hook
export interface Round {
    round_id: number
    name: string
    description: string
    start_date: string
    end_date: string
    status: string
    matching_pool: number | null
}

export function useRounds() {
    return useFetch<Round[]>('/api/rounds/', 30000)
}

// Donations Hook
export interface Donation {
    donation_id: number
    amount: string
    donor: number
    proposal: number
    created_at: string
    tx_hash: string
}

export function useDonations() {
    return useFetch<Donation[]>('/api/donations/', 30000)
}

// Matching Pool Hook
export interface MatchingPool {
    pool_id: number
    name: string
    total_funds: string
    allocated_funds: string
}

export function useMatchingPools() {
    return useFetch<MatchingPool[]>('/api/matching-pools/', 60000)
}

// Governance Tokens Hook
export interface GovernanceToken {
    token_id: number
    wallet: number
    role: string
    voting_power: string
}

export function useGovernanceTokens() {
    return useFetch<GovernanceToken[]>('/api/governance-tokens/', 60000)
}

// Contract Events Hook
export interface ContractEvent {
    event_id: number
    event_type: string
    tx_hash: string
    block_number: number
    timestamp: string
    raw_data: object
}

export function useContractEvents() {
    return useFetch<ContractEvent[]>('/api/contract-events/', 15000)
}

// Sybil Scores Hook
export interface SybilScore {
    score_id: number
    wallet: number
    score: string
    last_updated: string
    factors: object
}

export function useSybilScores() {
    return useFetch<SybilScore[]>('/api/sybil-scores/', 60000)
}

// API Actions (mutations)
export async function updateProjectStatus(projectId: number, status: string) {
    const response = await fetch(`${API_BASE_URL}/api/proposals/${projectId}/update_status/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
    })
    if (!response.ok) throw new Error('Failed to update project status')
    return response.json()
}

export async function createRound(roundData: Partial<Round>) {
    const response = await fetch(`${API_BASE_URL}/api/rounds/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(roundData),
    })
    if (!response.ok) throw new Error('Failed to create round')
    return response.json()
}

export async function addToMatchingPool(poolId: number, amount: number) {
    const response = await fetch(`${API_BASE_URL}/api/matching-pools/${poolId}/add_funds/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount }),
    })
    if (!response.ok) throw new Error('Failed to add funds to pool')
    return response.json()
}

export async function calculateQF(roundId: number) {
    const response = await fetch(`${API_BASE_URL}/api/rounds/${roundId}/calculate_qf/`, {
        method: 'POST',
    })
    if (!response.ok) throw new Error('Failed to calculate QF')
    return response.json()
}
