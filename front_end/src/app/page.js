'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { getProposals } from '@/lib/api';
import ProjectCard from '@/components/ProjectCard';
import StatsCounter from '@/components/StatsCounter';
import RecentDonations from '@/components/RecentDonations';

// Dynamically import ThreeScene with no SSR to avoid window is not defined errors
const ThreeScene = dynamic(() => import('@/components/ThreeScene'), { ssr: false });

export default function Home() {
  const [visibleProjects, setVisibleProjects] = useState(6);
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    getProposals().then(setProjects);
  }, []);

  const loadMoreProjects = () => {
    setVisibleProjects(prev => prev + 6);
  };

  return (
    <main>
      {/* Hero Section with 3D Model */}
      <section className="hero">
        <div className="hero-background"></div>

        {/* 3D Canvas Container */}
        <ThreeScene />

        <div className="hero-content container">
          <h1 className="hero-title fade-in-up">
            Democratizing<br />Public Goods Funding
          </h1>
          <p className="hero-subtitle fade-in-up" style={{ animationDelay: '0.2s' }}>
            Harness the power of quadratic funding to support projects that matter.<br />
            More contributors, more matching funds.
          </p>
          <div className="hero-cta fade-in-up" style={{ animationDelay: '0.4s' }}>
            <a href="#projects" className="btn btn-primary">Explore Projects</a>
            <a href="#how-it-works" className="btn btn-secondary">Learn More</a>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="section">
        <div className="container">
          <div className="stats-grid">
            <StatsCounter target={2500000} label="Total Funded" prefix="$" />
            <StatsCounter target={487} label="Projects" />
            <StatsCounter target={12500} label="Contributors" />
            <StatsCounter target={850000} label="Matching Pool" prefix="$" />
          </div>
        </div>
      </section>

      {/* Recent Donations */}
      <RecentDonations />

      {/* About Quadratic Funding */}
      <section id="about" className="section">
        <div className="container">
          <h2 className="section-title">What is Quadratic Funding?</h2>
          <p className="section-subtitle">
            A revolutionary funding mechanism that amplifies the voice of the community while ensuring fair distribution of
            resources.
          </p>

          <div className="grid grid-3">
            <div className="card">
              <h3 style={{ fontSize: '1.5rem', marginBottom: '1rem', color: 'var(--primary-purple)' }}>
                🎯 Democratic
              </h3>
              <p style={{ color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                Number of contributors matters more than amount. Small donations are amplified through matching, giving
                everyone a voice.
              </p>
            </div>

            <div className="card">
              <h3 style={{ fontSize: '1.5rem', marginBottom: '1rem', color: 'var(--primary-blue)' }}>
                🔍 Transparent
              </h3>
              <p style={{ color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                All contributions and matching calculations are recorded on-chain, ensuring complete transparency and
                accountability.
              </p>
            </div>

            <div className="card">
              <h3 style={{ fontSize: '1.5rem', marginBottom: '1rem', color: 'var(--primary-cyan)' }}>
                ⚡ Efficient
              </h3>
              <p style={{ color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                Mathematical formula ensures optimal allocation of matching funds based on community preference and support.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Active Projects */}
      <section className="section" id="projects">
        <div className="container">
          <h2 className="section-title">Active Projects</h2>
          <p className="section-subtitle">
            Support innovative public goods projects through quadratic funding
          </p>

          <div className="grid grid-3" id="projects-grid">
            {projects.slice(0, visibleProjects).map(project => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>

          {/* View More Button */}
          {visibleProjects < projects.length && (
            <div id="view-more-container"
              style={{ display: 'flex', justifyContent: 'center', marginTop: 'var(--spacing-2xl)', animation: 'fadeInUp 0.6s ease-out' }}>
              <button onClick={loadMoreProjects} className="btn btn-secondary"
                style={{ padding: '1rem 3rem', fontSize: 'var(--font-size-lg)', fontWeight: 600, boxShadow: '0 4px 20px rgba(139, 92, 246, 0.2)' }}>
                📊 View More Projects
              </button>
            </div>
          )}
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="section">
        <div className="container">
          <h2 className="section-title">How It Works</h2>
          <p className="section-subtitle">
            Understanding the quadratic funding formula
          </p>

          <div className="glass" style={{ padding: '3rem', borderRadius: '1.5rem', maxWidth: '800px', margin: '0 auto' }}>
            <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
              <div
                style={{ fontSize: '2rem', fontFamily: "'Courier New', monospace", color: 'var(--primary-purple)', marginBottom: '1rem' }}>
                Matching = (√c₁ + √c₂ + √c₃ + ...)²
              </div>
              <p style={{ color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                Where c₁, c₂, c₃... are individual contributions to a project
              </p>
            </div>

            <div className="grid grid-2" style={{ gap: '2rem', marginTop: '2rem' }}>
              <div>
                <h4 style={{ color: 'var(--primary-purple)', marginBottom: '1rem', fontSize: '1.25rem' }}>Step 1: Contribute</h4>
                <p style={{ color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                  Choose a project and make your contribution. Every contribution counts, regardless of size.
                </p>
              </div>

              <div>
                <h4 style={{ color: 'var(--primary-blue)', marginBottom: '1rem', fontSize: '1.25rem' }}>Step 2: Calculate</h4>
                <p style={{ color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                  The quadratic formula calculates matching based on number of contributors.
                </p>
              </div>

              <div>
                <h4 style={{ color: 'var(--primary-cyan)', marginBottom: '1rem', fontSize: '1.25rem' }}>Step 3: Match</h4>
                <p style={{ color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                  Matching funds from the pool are distributed proportionally to community support.
                </p>
              </div>

              <div>
                <h4 style={{ color: 'var(--accent-pink)', marginBottom: '1rem', fontSize: '1.25rem' }}>Step 4: Impact</h4>
                <p style={{ color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                  Projects receive their total funding to create real-world impact.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="section">
        <div className="container">
          <h2 className="section-title">Frequently Asked Questions</h2>

          <div style={{ maxWidth: '800px', margin: '0 auto' }}>
            <div className="card" style={{ marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>What makes quadratic funding different?</h3>
              <p style={{ color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                Unlike traditional funding, quadratic funding prioritizes the number of supporters over the amount. This
                means a project with 100 small donations will receive more matching than one with a single large donation.
              </p>
            </div>

            <div className="card" style={{ marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>How is the matching pool distributed?</h3>
              <p style={{ color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                The matching pool is distributed using the quadratic formula, which ensures projects with broader community
                support receive proportionally more funding from the pool.
              </p>
            </div>

            <div className="card" style={{ marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>Is my contribution secure?</h3>
              <p style={{ color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                Yes! All contributions are secured through smart contracts on the blockchain, ensuring transparency and
                immutability of all transactions.
              </p>
            </div>

            <div className="card">
              <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>Can I submit my own project?</h3>
              <p style={{ color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                Absolutely! We welcome public goods projects of all kinds. Click <Link href="/submit" style={{ color: 'var(--primary-cyan)', textDecoration: 'underline' }}>&quot;Submit Project&quot;</Link> to get started with your
                application.
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
