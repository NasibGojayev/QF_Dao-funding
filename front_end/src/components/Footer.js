import Link from 'next/link';

export default function Footer() {
    return (
        <footer className="footer">
            <div className="container">
                <div className="footer-content">
                    <div className="footer-section">
                        <h3>DonCoin</h3>
                        <p style={{ color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                            Democratizing funding for public goods through quadratic funding mechanisms.
                        </p>
                    </div>

                    <div className="footer-section">
                        <h3>Resources</h3>
                        <ul>
                            <li><Link href="#">Documentation</Link></li>
                            <li><Link href="#">Whitepaper</Link></li>
                            <li><Link href="#">Research</Link></li>
                            <li><Link href="#">Blog</Link></li>
                        </ul>
                    </div>

                    <div className="footer-section">
                        <h3>Community</h3>
                        <ul>
                            <li><Link href="#">Discord</Link></li>
                            <li><Link href="#">Twitter</Link></li>
                            <li><Link href="#">GitHub</Link></li>
                            <li><Link href="#">Forum</Link></li>
                        </ul>
                    </div>

                    <div className="footer-section">
                        <h3>Legal</h3>
                        <ul>
                            <li><Link href="#">Terms of Service</Link></li>
                            <li><Link href="#">Privacy Policy</Link></li>
                            <li><Link href="#">Cookie Policy</Link></li>
                        </ul>
                    </div>
                </div>

                <div className="footer-bottom">
                    <p>&copy; 2025 DonCoin. All rights reserved.</p>
                </div>
            </div>
        </footer>
    );
}
