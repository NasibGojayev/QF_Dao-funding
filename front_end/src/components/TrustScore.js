'use client';

import { useState, useMemo } from 'react';

export default function TrustScore({ userData }) {
    const scoreData = useMemo(() => {
        if (userData) {
            return calculateTrustScore(userData);
        }
        return null;
    }, [userData]);
    const [showBreakdown, setShowBreakdown] = useState(false);

    if (!scoreData) return null;

    const tier = getTrustTier(scoreData.totalScore);

    return (
        <div style={{ marginTop: 'var(--spacing-md)', padding: 'var(--spacing-md)', background: 'var(--glass-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--glass-border)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>Trust Score</span>
                <button
                    onClick={() => setShowBreakdown(true)}
                    style={{ background: 'none', border: 'none', color: 'var(--primary-cyan)', cursor: 'pointer', fontSize: 'var(--font-size-sm)', textDecoration: 'underline' }}
                >
                    View Breakdown
                </button>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-md)' }}>
                <span style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 800, color: tier.color }}>{scoreData.totalScore}</span>
                <span style={{ fontSize: 'var(--font-size-lg)', color: 'var(--text-secondary)' }}>/100</span>
                <span style={{ fontSize: 'var(--font-size-lg)', fontWeight: 600, marginLeft: 'auto', color: tier.color }}>
                    {tier.icon} {tier.name}
                </span>
            </div>
            <div style={{ width: '100%', height: '8px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-full)', overflow: 'hidden', marginTop: '0.5rem' }}>
                <div style={{ height: '100%', width: `${scoreData.totalScore}%`, background: `linear-gradient(90deg, ${tier.color}, ${tier.color}dd)`, transition: 'width 1s ease-out' }}></div>
            </div>

            {/* Breakdown Modal */}
            {showBreakdown && (
                <div className="score-modal" style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.8)', zIndex: 2000, display: 'flex',
                    alignItems: 'center', justifyContent: 'center'
                }} onClick={() => setShowBreakdown(false)}>
                    <div className="score-modal-content glass" style={{
                        maxWidth: '500px', width: '90%', padding: 'var(--spacing-xl)',
                        borderRadius: 'var(--radius-xl)', position: 'relative'
                    }} onClick={e => e.stopPropagation()}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-lg)' }}>
                            <h2 style={{ fontSize: 'var(--font-size-2xl)', margin: 0 }}>Trust Score Breakdown</h2>
                            <button onClick={() => setShowBreakdown(false)} style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer', color: 'var(--text-secondary)' }}>×</button>
                        </div>

                        <div style={{ marginBottom: 'var(--spacing-lg)' }}>
                            <ScoreMetric label="🕐 Account Age" value={scoreData.breakdown.accountAge} max={15} />
                            <ScoreMetric label="📊 Contribution Frequency" value={scoreData.breakdown.frequency} max={20} />
                            <ScoreMetric label="💰 Total Donated" value={scoreData.breakdown.totalDonated} max={15} />
                            <ScoreMetric label="🌈 Project Diversity" value={scoreData.breakdown.diversity} max={15} />
                            <ScoreMetric label="📈 Contribution Consistency" value={scoreData.breakdown.consistency} max={15} />
                            <ScoreMetric label="💵 Average Contribution" value={scoreData.breakdown.avgContribution} max={10} />
                            <ScoreMetric label="✅ Verification Status" value={scoreData.breakdown.verification} max={10} />
                        </div>

                        <div style={{ borderTop: '2px solid var(--glass-border)', paddingTop: 'var(--spacing-md)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontSize: 'var(--font-size-lg)', fontWeight: 700 }}>Total Score</span>
                            <span style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 800, background: 'var(--gradient-primary)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                                {scoreData.totalScore}/100
                            </span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function ScoreMetric({ label, value, max }) {
    return (
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
            <span>{label}</span>
            <span className="score-value" style={{ fontWeight: 600 }}>{value}/{max}</span>
        </div>
    );
}

// Logic helpers
function calculateTrustScore(userData) {
    // Metric 1: Account Age (15 points max)
    const accountAgeDays = userData.accountAgeDays || 0;
    const accountAgeScore = Math.min(accountAgeDays / 365, 1.0) * 15;

    // Metric 2: Contribution Frequency (20 points max)
    const totalContributions = userData.totalContributions || 0;
    const frequencyScore = Math.min(totalContributions / 50, 1.0) * 20;

    // Metric 3: Total Amount Donated (15 points max)
    const totalDonated = userData.totalDonated || 0;
    const totalDonatedScore = Math.min(totalDonated / 5000, 1.0) * 15;

    // Metric 4: Project Diversity (15 points max)
    const uniqueProjects = userData.uniqueProjects || 0;
    const diversityScore = Math.min(uniqueProjects / 20, 1.0) * 15;

    // Metric 5: Contribution Consistency (15 points max)
    const avgContribution = totalDonated / Math.max(totalContributions, 1);
    const simulatedStdDev = avgContribution * 0.3;
    const consistencyScore = (1 - Math.min(simulatedStdDev / avgContribution, 1.0)) * 15;

    // Metric 6: Average Contribution Size (10 points max)
    const avgContributionScore = Math.min(avgContribution / 100, 1.0) * 10;

    // Metric 7: Verification Status (10 points max)
    const verifiedCount = userData.verified ? 2 : 0;
    const verificationScore = Math.min(verifiedCount * 5, 10);

    const totalScore = Math.round(
        accountAgeScore + frequencyScore + totalDonatedScore +
        diversityScore + consistencyScore + avgContributionScore + verificationScore
    );

    return {
        totalScore: Math.min(totalScore, 100),
        breakdown: {
            accountAge: Math.round(accountAgeScore),
            frequency: Math.round(frequencyScore),
            totalDonated: Math.round(totalDonatedScore),
            diversity: Math.round(diversityScore),
            consistency: Math.round(consistencyScore),
            avgContribution: Math.round(avgContributionScore),
            verification: Math.round(verificationScore)
        }
    };
}

function getTrustTier(score) {
    if (score >= 81) return { name: 'Platinum', icon: '💎', color: '#00d4ff' };
    if (score >= 61) return { name: 'Gold', icon: '🥇', color: '#ffd700' };
    if (score >= 41) return { name: 'Silver', icon: '🥈', color: '#c0c0c0' };
    if (score >= 21) return { name: 'Bronze', icon: '🥉', color: '#cd7f32' };
    return { name: 'New', icon: '🌱', color: '#4ade80' };
}
