'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function Header() {
    const [scrolled, setScrolled] = useState(false);
    const pathname = usePathname();

    useEffect(() => {
        const handleScroll = () => {
            if (window.scrollY > 100) {
                setScrolled(true);
            } else {
                setScrolled(false);
            }
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    return (
        <header className={`header ${scrolled ? 'scrolled' : ''}`} id="header">
            <nav className="nav container">
                <Link href="/" className="logo">
                    DonCoin
                </Link>
                <ul className="nav-links">
                    <li><Link href="/#about">About</Link></li>
                    <li><Link href="/#projects">Projects</Link></li>
                    <li><Link href="/#how-it-works">How It Works</Link></li>
                    <li><Link href="/#faq">FAQ</Link></li>
                    <li>
                        <Link
                            href="/submit"
                            className="btn"
                            style={{
                                background: 'rgba(255, 255, 255, 0.05)',
                                border: '1px solid var(--glass-border)',
                                padding: '0.5rem 1.2rem',
                                fontSize: '0.9rem',
                                borderRadius: '2rem',
                                transition: 'all 0.3s ease'
                            }}
                            onMouseEnter={(e) => {
                                e.target.style.background = 'rgba(255, 255, 255, 0.1)';
                                e.target.style.borderColor = 'var(--primary-cyan)';
                            }}
                            onMouseLeave={(e) => {
                                e.target.style.background = 'rgba(255, 255, 255, 0.05)';
                                e.target.style.borderColor = 'var(--glass-border)';
                            }}
                        >
                            Submit Project
                        </Link>
                    </li>
                    <li>
                        <Link
                            href="/account"
                            className={`btn btn-primary ${pathname === '/account' ? 'active' : ''}`}
                            style={{ padding: '0.75rem 1.5rem' }}
                        >
                            Connect Wallet
                        </Link>
                    </li>
                </ul>
            </nav>
        </header>
    );
}
