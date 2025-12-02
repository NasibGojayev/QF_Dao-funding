'use client';

import { useState } from 'react';
import Link from 'next/link';
import { createProposal } from '@/lib/api';

export default function SubmitProjectPage() {
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        category: 'Public Goods',
        goal: '',
        walletAddress: '',
        email: ''
    });
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);

        // Simulate API call
        await createProposal({
            title: formData.title,
            description: formData.description,
            category: formData.category,
            goal: parseFloat(formData.goal) || 0,
            // In a real app, walletAddress and email would be handled by auth/backend
        });

        setIsSubmitting(false);
        setIsSuccess(true);
    };

    if (isSuccess) {
        return (
            <section className="section" style={{ paddingTop: '120px', minHeight: '100vh', display: 'flex', alignItems: 'center' }}>
                <div className="container" style={{ textAlign: 'center' }}>
                    <div className="glass" style={{ maxWidth: '600px', margin: '0 auto', padding: 'var(--spacing-2xl)', borderRadius: 'var(--radius-xl)' }}>
                        <div style={{ fontSize: '5rem', marginBottom: 'var(--spacing-lg)', animation: 'pulse 2s infinite' }}>🚀</div>
                        <h1 className="section-title">Project Submitted!</h1>
                        <p className="section-subtitle" style={{ marginBottom: 'var(--spacing-xl)' }}>
                            Thank you for submitting <strong>{formData.title}</strong>. Our team will review your application and get back to you at {formData.email} within 48 hours.
                        </p>
                        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
                            <Link href="/" className="btn btn-primary">Return Home</Link>
                            <button
                                onClick={() => {
                                    setIsSuccess(false);
                                    setFormData({ title: '', description: '', category: 'Public Goods', goal: '', walletAddress: '', email: '' });
                                }}
                                className="btn btn-secondary"
                            >
                                Submit Another
                            </button>
                        </div>
                    </div>
                </div>
            </section>
        );
    }

    return (
        <section className="section" style={{ paddingTop: '120px', minHeight: '100vh' }}>
            <div className="container">
                <div style={{ maxWidth: '800px', margin: '0 auto' }}>
                    <h1 className="section-title">Submit Your Project</h1>
                    <p className="section-subtitle">
                        Apply for quadratic funding and get support from the community.
                    </p>

                    <form onSubmit={handleSubmit} className="glass" style={{ padding: 'var(--spacing-xl)', borderRadius: 'var(--radius-xl)', border: '1px solid var(--glass-border)' }}>

                        <div className="grid grid-2" style={{ gap: 'var(--spacing-lg)', marginBottom: 'var(--spacing-lg)' }}>
                            <div>
                                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Project Title</label>
                                <input
                                    type="text"
                                    name="title"
                                    value={formData.title}
                                    onChange={handleChange}
                                    placeholder="e.g. Decentralized Climate Data"
                                    style={{
                                        width: '100%', padding: '0.75rem', borderRadius: '0.5rem',
                                        background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)',
                                        color: 'white', outline: 'none'
                                    }}
                                />
                            </div>

                            <div>
                                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Category</label>
                                <select
                                    name="category"
                                    value={formData.category}
                                    onChange={handleChange}
                                    style={{
                                        width: '100%', padding: '0.75rem', borderRadius: '0.5rem',
                                        background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)',
                                        color: 'white', outline: 'none'
                                    }}
                                >
                                    <option value="Public Goods" style={{ color: 'black' }}>Public Goods</option>
                                    <option value="Open Source" style={{ color: 'black' }}>Open Source</option>
                                    <option value="Education" style={{ color: 'black' }}>Education</option>
                                    <option value="Environment" style={{ color: 'black' }}>Environment</option>
                                    <option value="Community" style={{ color: 'black' }}>Community</option>
                                </select>
                            </div>
                        </div>

                        <div style={{ marginBottom: 'var(--spacing-lg)' }}>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Description</label>
                            <textarea
                                name="description"
                                value={formData.description}
                                onChange={handleChange}
                                rows="5"
                                placeholder="Describe your project, its goals, and how it benefits the public..."
                                style={{
                                    width: '100%', padding: '0.75rem', borderRadius: '0.5rem',
                                    background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)',
                                    color: 'white', outline: 'none', resize: 'vertical'
                                }}
                            ></textarea>
                        </div>

                        <div className="grid grid-2" style={{ gap: 'var(--spacing-lg)', marginBottom: 'var(--spacing-lg)' }}>
                            <div>
                                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Funding Goal (USD)</label>
                                <div style={{ position: 'relative' }}>
                                    <span style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }}>$</span>
                                    <input
                                        type="text"
                                        name="goal"
                                        value={formData.goal}
                                        onChange={handleChange}
                                        placeholder="10000"
                                        style={{
                                            width: '100%', padding: '0.75rem 0.75rem 0.75rem 2rem', borderRadius: '0.5rem',
                                            background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)',
                                            color: 'white', outline: 'none'
                                        }}
                                    />
                                </div>
                            </div>

                            <div>
                                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Contact Email</label>
                                <input
                                    type="text"
                                    name="email"
                                    value={formData.email}
                                    onChange={handleChange}
                                    placeholder="you@example.com"
                                    style={{
                                        width: '100%', padding: '0.75rem', borderRadius: '0.5rem',
                                        background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)',
                                        color: 'white', outline: 'none'
                                    }}
                                />
                            </div>
                        </div>

                        <div style={{ marginBottom: 'var(--spacing-xl)' }}>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Wallet Address (ETH)</label>
                            <input
                                type="text"
                                name="walletAddress"
                                value={formData.walletAddress}
                                onChange={handleChange}
                                placeholder="0x..."
                                style={{
                                    width: '100%', padding: '0.75rem', borderRadius: '0.5rem',
                                    background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)',
                                    color: 'white', outline: 'none', fontFamily: 'monospace'
                                }}
                            />
                            <p style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginTop: '0.25rem' }}>
                                This address will receive the funds. Ensure it supports ETH/ERC-20 tokens.
                            </p>
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
                            <Link href="/" className="btn btn-secondary">Cancel</Link>
                            <button
                                type="submit"
                                disabled={isSubmitting}
                                className="btn btn-primary"
                                style={{ minWidth: '150px' }}
                            >
                                {isSubmitting ? 'Submitting...' : 'Submit Project'}
                            </button>
                        </div>

                    </form>
                </div>
            </div>
        </section>
    );
}
