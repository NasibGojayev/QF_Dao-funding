import { useState, useEffect } from 'react';
import { useAccount, useSignMessage, useDisconnect } from 'wagmi';
import { useRouter } from 'next/navigation';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function useWeb3Auth() {
    const { address, isConnected } = useAccount();
    const { signMessageAsync } = useSignMessage();
    const { disconnect } = useDisconnect();
    const [user, setUser] = useState<any | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const router = useRouter();

    // Load user from local storage on mount
    useEffect(() => {
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            setUser(JSON.parse(storedUser));
        }
    }, []);

    // Effect to handle account changes
    useEffect(() => {
        // Only run this logic if we have actually established a definitive connection state
        // If 'address' is undefined, it might be loading. 
        // We only want to auto-logout if we DEFINITELY know the wallet doesn't match the session.

        if (isConnected && user && address) {
            const sessionWallet = user.wallet?.address || user.wallet?.wallet_address || "";
            // Handle different structure naming just in case

            if (sessionWallet.toLowerCase() !== address.toLowerCase()) {
                // Wallet changed to a different address than logged in user -> Logout
                console.log("Wallet mismatch, logging out");
                logout();
            }
        }

        // Note: Removing the 'if (!isConnected && user)' check because Wagmi starts as 'disconnected' 
        // for a split second on F5 refresh, which was wiping the session.
        // We let the session persist. If the user is truly disconnected, they can click "Connect" again
        // or we can add a smarter check with 'isReconnecting'.

    }, [isConnected, address, user]); // eslint-disable-line react-hooks/exhaustive-deps


    const login = async () => {
        if (!address) return;
        setIsLoading(true);

        try {
            const message = `Login to DonCoin with address: ${address}`;
            const signature = await signMessageAsync({ message });

            const response = await fetch(`${API_BASE_URL}/auth/wallet/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    address,
                    signature,
                    message,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Login failed');
            }

            const data = await response.json();

            // Map backend response to User object structure expected by app
            // API returns 'user' (Donor data) + 'wallet_address'
            const userData = {
                ...data.user, // Donor fields (username, reputation_score, etc.)
                wallet: data.user.wallet_details, // Map nested wallet details
                name: data.user.username, // Map 'username' to 'name' for frontend compatibility
                id: data.user.donor_id // Map 'donor_id' to 'id' generic check?
            };

            localStorage.setItem('user', JSON.stringify(userData));
            setUser(userData);
            window.dispatchEvent(new Event('user-updated')); // Notify Navbar

        } catch (error) {
            console.error('Login error:', error);
            alert('Authentication failed');
            disconnect(); // Force disconnect mostly to reset state
        } finally {
            setIsLoading(false);
        }
    };

    const logout = () => {
        localStorage.removeItem('user');
        setUser(null);
        disconnect();
        window.dispatchEvent(new Event('user-updated'));
        router.push('/');
    };

    return {
        user,
        isAuthenticated: !!user,
        login,
        logout,
        isLoading,
        isConnected,
        address
    };
}
