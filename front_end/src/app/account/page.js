'use client';

import { useState, useEffect } from 'react';
import TrustScore from '@/components/TrustScore';
import Link from 'next/link';
import { connectWallet as connectWalletApi } from '@/lib/api';

export default function AccountPage() {
    const [walletConnected, setWalletConnected] = useState(false);
    const [userAddress, setUserAddress] = useState(null);
    const [userData, setUserData] = useState(null);

    const loadUserData = () => {
        // Simulate data loading
        const totalDonated = Math.floor(Math.random() * 1000) + 100;
        const projectsSupported = Math.floor(Math.random() * 10) + 1;

        setUserData({
            totalDonated,
            projectsSupported,
            matchingEarned: Math.floor(totalDonated * 0.6),
            accountAgeDays: Math.floor(Math.random() * 500) + 30,
            totalContributions: Math.floor(Math.random() * 60) + 5,
            uniqueProjects: projectsSupported,
            verified: Math.random() > 0.5
        });
    };

    useEffect(() => {
        // Check local storage on mount
        const savedConnected = localStorage.getItem('walletConnected');
        const savedAddress = localStorage.getItem('userAddress');

        if (savedConnected === 'true' && savedAddress) {
            // eslint-disable-next-line react-hooks/set-state-in-effect
            setWalletConnected(true);
            setUserAddress(savedAddress);
            loadUserData();
        }
    }, []);

    const connectWallet = async () => {
        // Simulate connection
        const wallet = await connectWalletApi();
        const address = wallet.address;
        setWalletConnected(true);
        setUserAddress(address);
        localStorage.setItem('walletConnected', 'true');
        localStorage.setItem('userAddress', address);
        loadUserData();
    };

    const disconnectWallet = () => {
        setWalletConnected(false);
        setUserAddress(null);
        setUserData(null);
        localStorage.removeItem('walletConnected');
        localStorage.removeItem('userAddress');
    };

    return (
        <section className="section" style={{ paddingTop: '120px', minHeight: '100vh' }}>
            <div className="container">
                <h1 className="section-title">Account Management</h1>
                <p className="section-subtitle">
                    Manage your wallet, view contributions, and track your impact
                </p>

                <div className="account-container glass"
                    style={{ maxWidth: '900px', margin: '0 auto', padding: 'var(--spacing-xl)', borderRadius: 'var(--radius-xl)' }}>

                    {!walletConnected ? (
                        <div id="wallet-disconnected" className="wallet-state">
                            <div style={{ textAlign: 'center', padding: 'var(--spacing-2xl) 0' }}>
                                <div style={{ fontSize: '4rem', marginBottom: 'var(--spacing-md)' }}>🔐</div>
                                <h2 style={{ fontSize: 'var(--font-size-2xl)', marginBottom: 'var(--spacing-md)' }}>Connect Your Wallet</h2>
                                <p style={{ color: 'var(--text-secondary)', marginBottom: 'var(--spacing-xl)', maxWidth: '500px', marginLeft: 'auto', marginRight: 'auto' }}>
                                    Connect your wallet to access your account, view your contributions, and manage your profile.
                                </p>
                                <button
                                    className="btn btn-primary"
                                    onClick={connectWallet}
                                    style={{ padding: '1rem 2rem', fontSize: 'var(--font-size-lg)' }}
                                >
                                    🔗 Connect Wallet
                                </button>
                                <p style={{ marginTop: 'var(--spacing-lg)', color: 'var(--text-tertiary)', fontSize: 'var(--font-size-sm)' }}>
                                    We support MetaMask, WalletConnect, and more
                                </p>
                            </div>
                        </div>
                    ) : (
                        <div id="wallet-connected" className="wallet-state">
                            {/* User Profile Card */}
                            <div className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-lg)', flexWrap: 'wrap' }}>
                                    <div className="user-avatar"
                                        style={{ width: '80px', height: '80px', borderRadius: '50%', background: 'var(--gradient-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '2rem' }}>
                                        👤
                                    </div>
                                    <div style={{ flex: 1, minWidth: '200px' }}>
                                        <h3 style={{ fontSize: 'var(--font-size-xl)', marginBottom: '0.5rem', fontFamily: 'monospace' }}>
                                            {userAddress}
                                        </h3>
                                        <p style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                                            Member since <span id="member-since">November 2025</span>
                                        </p>
                                        <div style={{ display: 'flex', gap: 'var(--spacing-sm)', flexWrap: 'wrap' }}>
                                            <span className="badge">✓ Verified</span>
                                            <span className="badge">💎 Active Donor</span>
                                        </div>

                                        {/* Trust Score Display */}
                                        {userData && <TrustScore userData={userData} />}
                                    </div>
                                    <button
                                        className="btn btn-secondary"
                                        onClick={disconnectWallet}
                                        style={{ whiteSpace: 'nowrap' }}
                                    >
                                        Disconnect
                                    </button>
                                </div>
                            </div>

                            {/* Account Stats */}
                            {userData && (
                                <div className="grid grid-3" style={{ marginBottom: 'var(--spacing-lg)' }}>
                                    <div className="stat-card glass">
                                        <span className="stat-number" style={{ fontSize: 'var(--font-size-3xl)' }}>
                                            ${userData.totalDonated}
                                        </span>
                                        <span className="stat-label">Total Donated</span>
                                    </div>
                                    <div className="stat-card glass">
                                        <span className="stat-number" style={{ fontSize: 'var(--font-size-3xl)' }}>
                                            {userData.projectsSupported}
                                        </span>
                                        <span className="stat-label">Projects Supported</span>
                                    </div>
                                    <div className="stat-card glass">
                                        <span className="stat-number" style={{ fontSize: 'var(--font-size-3xl)' }}>
                                            ${userData.matchingEarned}
                                        </span>
                                        <span className="stat-label">Matching Earned</span>
                                    </div>
                                </div>
                            )}

                            {/* Transaction History */}
                            <div className="card">
                                <h3 style={{ fontSize: 'var(--font-size-xl)', marginBottom: 'var(--spacing-md)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    <span>📋</span> Recent Transactions
                                </h3>
                                <div id="transaction-list">
                                    <TransactionItem
                                        title="Contributed to Open Source Libraries"
                                        date="Nov 29, 2025 • 10:45 AM"
                                        amount="$50.00"
                                        matching="+$25 matching"
                                    />
                                    <TransactionItem
                                        title="Contributed to Climate Action DAO"
                                        date="Nov 28, 2025 • 3:20 PM"
                                        amount="$100.00"
                                        matching="+$80 matching"
                                    />
                                    <TransactionItem
                                        title="Contributed to Educational Content"
                                        date="Nov 27, 2025 • 9:15 AM"
                                        amount="$25.00"
                                        matching="+$15 matching"
                                    />
                                </div>

                                <div style={{ textAlign: 'center', marginTop: 'var(--spacing-lg)' }}>
                                    <Link href="/" className="btn btn-secondary">← Back to Home</Link>
                                </div>
                            </div>
                        </div>
                    )}

                </div>
            </div>
        </section>
    );
}

function TransactionItem({ title, date, amount, matching }) {
    return (
        <div className="transaction-item"
            style={{ padding: 'var(--spacing-md)', borderBottom: '1px solid var(--glass-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
                <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>{title}</p>
                <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>{date}</p>
            </div>
            <div style={{ textAlign: 'right' }}>
                <p style={{ fontWeight: 600, color: 'var(--primary-purple)' }}>{amount}</p>
                <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--primary-cyan)' }}>{matching}</p>
            </div>
        </div>
    );
}
