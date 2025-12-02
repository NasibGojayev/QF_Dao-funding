'use client';

const recentDonations = [
    { id: 1, donor: '0x71...3A4B', amount: 50, project: 'Open Source Library', time: '2 mins ago' },
    { id: 2, donor: '0x92...8C1D', amount: 120, project: 'Climate Research', time: '5 mins ago' },
    { id: 3, donor: '0x44...9E2F', amount: 25, project: 'Education Platform', time: '12 mins ago' },
    { id: 4, donor: '0x18...5B7A', amount: 500, project: 'Mental Health Toolkit', time: '25 mins ago' },
    { id: 5, donor: '0x63...2D9C', amount: 10, project: 'Community Gardens', time: '40 mins ago' },
];

export default function RecentDonations() {
    return (
        <section className="section">
            <div className="container">
                <h2 className="section-title" style={{ fontSize: 'var(--font-size-3xl)', marginBottom: 'var(--spacing-lg)' }}>
                    Recent Contributions
                </h2>

                <div className="glass" style={{
                    borderRadius: 'var(--radius-xl)',
                    padding: 'var(--spacing-lg)',
                    overflow: 'hidden'
                }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        {recentDonations.map((donation) => (
                            <div key={donation.id} style={{
                                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                padding: '1rem', borderBottom: '1px solid var(--glass-border)',
                                transition: 'background 0.2s'
                            }} className="donation-item">
                                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                    <div style={{
                                        width: '40px', height: '40px', borderRadius: '50%',
                                        background: 'var(--gradient-secondary)', display: 'flex',
                                        alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem'
                                    }}>
                                        🎁
                                    </div>
                                    <div>
                                        <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{donation.donor}</div>
                                        <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                                            donated to <span style={{ color: 'var(--primary-purple)' }}>{donation.project}</span>
                                        </div>
                                    </div>
                                </div>
                                <div style={{ textAlign: 'right' }}>
                                    <div style={{ fontWeight: '700', color: 'var(--primary-cyan)', fontSize: '1.125rem' }}>
                                        ${donation.amount}
                                    </div>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>{donation.time}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </section>
    );
}
