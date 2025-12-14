"use client";

import { useState } from "react";

export default function WalletButton() {
  const [addr, setAddr] = useState<string | null>(null);

  function connect() {
    // Mock connect — replace this with real web3 connect logic
    const fake = `0x${Math.random().toString(16).slice(2, 10)}${Math.random().toString(16).slice(2, 6)}`;
    setAddr(fake);
  }

  return (
    <div>
      {addr ? (
        <div className="flex items-center space-x-3">
          <span className="font-mono text-sm">{addr.slice(0, 6)}...{addr.slice(-4)}</span>
          <button
            onClick={() => setAddr(null)}
            className="text-sm text-gray-600 hover:underline"
          >
            Disconnect
          </button>
        </div>
      ) : (
        <button
          onClick={connect}
          className="px-3 py-1 bg-blue-600 text-white rounded text-sm"
        >
          Connect Wallet
        </button>
      )}
    </div>
  );
}
