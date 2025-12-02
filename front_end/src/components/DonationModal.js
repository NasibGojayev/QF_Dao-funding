'use client';

import { useState } from 'react';
import { createDonation } from '@/lib/api';

export default function DonationModal({ project, isOpen, onClose }) {
    const [amount, setAmount] = useState('');
    const [isSuccess, setIsSuccess] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);

    if (!isOpen) return null;

    const handleDonate = async (e) => {
        e.preventDefault();
        setIsProcessing(true);

        // Simulate API call
        await createDonation({
            proposalId: project.proposal_id,
            amount: parseFloat(amount)
        });

        setIsProcessing(false);
        setIsSuccess(true);
    };

    const handleClose = () => {
        setIsSuccess(false);
        setAmount('');
        onClose();
    };

    return (
        <div className="modal-overlay" onClick={handleClose} style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.8)', zIndex: 2000, display: 'flex',
            alignItems: 'center', justifyContent: 'center', backdropFilter: 'blur(5px)'
        }}>
            <div className="modal-content glass" onClick={e => e.stopPropagation()} style={{
                maxWidth: '450px', width: '90%', padding: 'var(--spacing-xl)',
                borderRadius: 'var(--radius-xl)', position: 'relative',
                border: '1px solid var(--glass-border)'
            }}>
                <button
                    onClick={handleClose}
                    style={{
                        position: 'absolute', top: '1rem', right: '1rem',
                        background: 'none', border: 'none', fontSize: '1.5rem',
                        cursor: 'pointer', color: 'var(--text-secondary)'
                    }}
                >
                    ×
                </button>

                {!isSuccess ? (
                    <>
                        <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>
                            Donate to <span className="gradient-text">{project.title}</span>
                        </h2>
                        <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                            Your contribution will be matched by the quadratic funding pool.
                        </p>

                        <form onSubmit={handleDonate}>
                            <div style={{ marginBottom: '1.5rem' }}>
                                <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                                    Donation Amount (USD)
                                </label>
                                <div style={{ position: 'relative' }}>
                                    <span style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }}>$</span>
                                    <input
                                        type="number"
                                        min="1"
                                        value={amount}
                                        onChange={(e) => setAmount(e.target.value)}
                                        required
                                        style={{
                                            width: '100%', padding: '0.75rem 1rem 0.75rem 2rem',
                                            background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)',
                                            borderRadius: '0.5rem', color: 'white', fontSize: '1.125rem',
                                            outline: 'none'
                                        }}
                                        placeholder="25"
                                    />
                                </div>
                            </div>

                            <div style={{ background: 'rgba(139, 92, 246, 0.1)', padding: '1rem', borderRadius: '0.5rem', marginBottom: '1.5rem' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                                    <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Estimated Match</span>
                                    <span style={{ fontSize: '0.875rem', fontWeight: 'bold', color: 'var(--primary-cyan)' }}>
                                        +${amount ? (amount * 1.5).toFixed(2) : '0.00'}
                                    </span>
                                </div>
                                <p style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
                                    *Matching amount is an estimate based on current pool distribution.
                                </p>
                            </div>

                            <button
                                type="submit"
                                disabled={isProcessing}
                                className="btn btn-primary"
                                style={{ width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem' }}
                            >
                                {isProcessing ? 'Processing...' : 'Confirm Donation'}
                            </button>
                        </form>
                    </>
                ) : (
                    <div style={{ textAlign: 'center', padding: '1rem 0' }}>
                        <div style={{ fontSize: '4rem', marginBottom: '1rem', animation: 'pulse 1s infinite' }}>🎉</div>
                        <h2 style={{ fontSize: '1.75rem', marginBottom: '0.5rem' }}>Thank You!</h2>
                        <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                            Your donation of <strong>${amount}</strong> has been successfully processed.
                        </p>
                        <button className="btn btn-secondary" onClick={handleClose}>
                            Close
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
