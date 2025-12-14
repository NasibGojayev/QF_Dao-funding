import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
    title: 'DAO Admin Panel',
    description: 'Admin dashboard for DAO Quadratic Funding Platform',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en">
            <body style={{ margin: 0, minHeight: '100vh' }}>{children}</body>
        </html>
    )
}
