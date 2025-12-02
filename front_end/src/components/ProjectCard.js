'use client';

import { useEffect, useRef, useState } from 'react';
import DonationModal from './DonationModal';

export default function ProjectCard({ project }) {
    const cardRef = useRef(null);

    const raised = parseFloat(project.total_donations || '0');
    const progress = (raised / project.goal) * 100;
    // Simplified matching calc
    const contributors = project.contributor_count || 0;
    const matching = Math.pow(Math.sqrt(raised / contributors) * contributors, 2) * 0.3;

    const [daysLeft, setDaysLeft] = useState(0);
    const [isTrending, setIsTrending] = useState(false);

    const [isModalOpen, setIsModalOpen] = useState(false);

    useEffect(() => {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setDaysLeft(Math.floor(Math.random() * 30) + 1);
        setIsTrending(Math.random() > 0.7);
    }, []);

    const statusBadge = progress >= 100 ? '✓ Funded' : progress >= 75 ? '🔥 Hot' : daysLeft <= 7 ? '⏰ Ending Soon' : '';

    useEffect(() => {
        const card = cardRef.current;
        if (!card) return;

        const handleMouseMove = (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const centerX = rect.width / 2;
            const centerY = rect.height / 2;

            const rotateX = (y - centerY) / 20;
            const rotateY = (centerX - x) / 20;

            if (x >= 0 && x <= rect.width && y >= 0 && y <= rect.height) {
                card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-8px)`;
            } else {
                card.style.transform = '';
            }
        };

        const handleMouseLeave = () => {
            card.style.transform = '';
        };

        card.addEventListener('mousemove', handleMouseMove);
        card.addEventListener('mouseleave', handleMouseLeave);

        return () => {
            card.removeEventListener('mousemove', handleMouseMove);
            card.removeEventListener('mouseleave', handleMouseLeave);
        };
    }, []);

    return (
        <div className="project-card" ref={cardRef}>
            <div style={{ position: 'relative' }}>
                <img
                    src={`/images/${project.image}`}
                    alt={project.title}
                    className="project-image"
                    loading="lazy"
                    onError={(e) => {
                        e.target.onerror = null;
                        e.target.src = `data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22400%22 height=%22220%22%3E%3Cdefs%3E%3ClinearGradient id=%22grad%22 x1=%220%25%22 y1=%220%25%22 x2=%22100%25%22 y2=%22100%25%22%3E%3Cstop offset=%220%25%22 style=%22stop-color:%23667eea;stop-opacity:1%22 /%3E%3Cstop offset=%22100%25%22 style=%22stop-color:%23764ba2;stop-opacity:1%22 /%3E%3C/linearGradient%3E%3C/defs%3E%3Crect fill=%22url(%23grad)%22 width=%22400%22 height=%22220%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-family=%22Arial%22 font-size=%2228%22 fill=%22white%22 font-weight=%22bold%22%3E${project.category}%3C/text%3E%3C/svg%3E`;
                    }}
                />
                {isTrending && (
                    <span style={{ position: 'absolute', top: '12px', left: '12px', background: 'rgba(236, 72, 153, 0.95)', color: 'white', padding: '0.4rem 0.8rem', borderRadius: '2rem', fontSize: '0.75rem', fontWeight: 700, backdropFilter: 'blur(10px)', boxShadow: '0 4px 12px rgba(236, 72, 153, 0.4)' }}>
                        🔥 Trending
                    </span>
                )}
                {statusBadge && (
                    <span style={{ position: 'absolute', top: '12px', right: '12px', background: 'rgba(139, 92, 246, 0.95)', color: 'white', padding: '0.4rem 0.8rem', borderRadius: '2rem', fontSize: '0.75rem', fontWeight: 700, backdropFilter: 'blur(10px)', boxShadow: '0 4px 12px rgba(139, 92, 246, 0.4)' }}>
                        {statusBadge}
                    </span>
                )}
            </div>

            <div className="project-content">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.75rem' }}>
                    <h3 className="project-title">{project.title}</h3>
                </div>

                <div style={{ marginBottom: '0.75rem' }}>
                    <span style={{ display: 'inline-block', background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2))', color: 'var(--primary-purple)', padding: '0.35rem 0.85rem', borderRadius: '1.5rem', fontSize: '0.75rem', fontWeight: 600, border: '1px solid rgba(139, 92, 246, 0.3)' }}>
                        <span style={{ opacity: 0.8 }}>📁</span> {project.category}
                    </span>
                    <span style={{ display: 'inline-block', marginLeft: '0.5rem', color: 'var(--text-tertiary)', fontSize: '0.75rem' }}>
                        {daysLeft} days left
                    </span>
                </div>

                <p className="project-description">{project.description}</p>

                <div style={{ margin: '1rem 0' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.6rem', fontSize: '0.875rem' }}>
                        <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>{progress.toFixed(0)}% funded</span>
                        <span style={{ color: 'var(--primary-purple)', fontWeight: 700 }}>${(raised / 1000).toFixed(0)}K <span style={{ color: 'var(--text-tertiary)', fontWeight: 400 }}>/ ${(project.goal / 1000).toFixed(0)}K</span></span>
                    </div>
                    <div className="progress-bar">
                        <div className="progress-fill" style={{ width: `${Math.min(progress, 100)}%` }}></div>
                    </div>
                </div>

                <div className="project-meta">
                    <div className="project-funding">
                        <span className="funding-label">👥 Contributors</span>
                        <span className="funding-amount">{contributors}</span>
                    </div>
                    <div className="project-funding">
                        <span className="funding-label">💎 Matching</span>
                        <span className="funding-amount" style={{ color: 'var(--primary-cyan)' }}>${(matching / 1000).toFixed(1)}K</span>
                    </div>
                </div>

                <button
                    className="btn btn-primary"
                    style={{ width: '100%', marginTop: '1.25rem', padding: '0.85rem 1.5rem', fontWeight: 600, boxShadow: '0 4px 15px rgba(139, 92, 246, 0.3)' }}
                    onClick={() => setIsModalOpen(true)}
                >
                    💰 Contribute Now
                </button>
            </div>

            <DonationModal
                project={project}
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
            />
        </div>
    );
}
