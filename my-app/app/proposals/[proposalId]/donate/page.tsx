"use client";

import { useState, use } from "react";
import Link from "next/link";

type Stage = "review" | "confirm" | "pending" | "success" | "error";

export default function DonatePage({ params }: { params: Promise<{ proposalId: string }> }) {
  const { proposalId } = use(params);
  const [stage, setStage] = useState<Stage>("review");
  const [amount, setAmount] = useState(1);
  const [token, setToken] = useState("DAI");
  const [txHash, setTxHash] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  const gasEstimate = 0.005;
  const total = amount + gasEstimate;
  const sybilScore = 0.95;
  const proposalTitle = "Clean Water Initiative";
  const creatorAddr = "0xabc123";

  function handleReviewSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (amount <= 0) {
      setErrorMsg("Please enter a valid amount");
      return;
    }
    setStage("confirm");
  }

  function handleConfirmDonation() {
    setStage("pending");
    // Simulate transaction submission
    setTimeout(() => {
      const success = Math.random() > 0.1;
      if (success) {
        setTxHash("0x" + Math.random().toString(16).slice(2, 66));
        setTimeout(() => setStage("success"), 2000);
      } else {
        setErrorMsg("Transaction failed: Insufficient gas or network error");
        setStage("error");
      }
    }, 1500);
  }

  // STAGE 1: Review & Finalize Amount
  if (stage === "review") {
    return (
      <main className="flex min-h-screen items-center justify-center p-12 bg-gradient-to-br from-blue-50 to-indigo-50">
        <div className="w-full max-w-lg bg-white border rounded-lg shadow-lg p-8">
          {/* Wizard Header */}
          <div className="mb-6">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <span className="bg-blue-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">1</span>
              <span>Review</span>
              <span className="text-gray-300">→</span>
              <span className="bg-gray-300 text-gray-600 rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">2</span>
              <span className="text-gray-400">Confirm</span>
              <span className="text-gray-300">→</span>
              <span className="bg-gray-300 text-gray-600 rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">3</span>
              <span className="text-gray-400">Complete</span>
            </div>
          </div>

          <h1 className="text-2xl font-bold">Review Your Donation</h1>
          <p className="text-gray-600 mt-1">Step 1 of 3</p>

          {/* Proposal Summary */}
          <div className="mt-6 p-4 bg-indigo-50 border border-indigo-100 rounded">
            <h3 className="font-semibold text-indigo-900">You're funding:</h3>
            <p className="text-indigo-800 font-bold mt-1">{proposalTitle}</p>
            <p className="text-sm text-indigo-700 mt-1">By {creatorAddr}</p>
          </div>

          {/* Sybil Status */}
          <div className="mt-4 p-3 bg-green-50 border border-green-100 rounded text-sm text-green-700">
            ✓ Your wallet is Sybil-verified (Score: {sybilScore})
          </div>

          {/* Amount Input */}
          <form onSubmit={handleReviewSubmit} className="mt-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Donation Amount</label>
              <div className="mt-2 flex gap-2">
                <input
                  type="number"
                  min={0}
                  step={0.01}
                  value={amount}
                  onChange={(e) => {
                    setAmount(Number(e.target.value));
                    setErrorMsg("");
                  }}
                  className="border px-3 py-2 rounded flex-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="0.00"
                />
                <select value={token} onChange={(e) => setToken(e.target.value)} className="border px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <option>ETH</option>
                  <option>DAI</option>
                  <option>USDC</option>
                </select>
              </div>
            </div>

            {errorMsg && <div className="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">{errorMsg}</div>}

            <div className="p-4 bg-blue-50 rounded text-sm text-blue-900">
              <strong>💡 How quadratic funding works:</strong> Your donation amount is squared along with others', then matched by the matching pool. Smaller donations get amplified impact!
            </div>

            <button type="submit" className="w-full px-4 py-2 bg-blue-600 text-white rounded font-semibold hover:bg-blue-700 transition">
              Proceed to Confirmation →
            </button>
            <Link href={`/proposals/${proposalId}`} className="block text-center px-4 py-2 border rounded text-gray-700 hover:bg-gray-50 transition">
              Cancel
            </Link>
          </form>
        </div>
      </main>
    );
  }

  // STAGE 2: Transaction Confirmation & Wallet Interaction
  if (stage === "confirm") {
    return (
      <main className="flex min-h-screen items-center justify-center p-12 bg-gradient-to-br from-blue-50 to-indigo-50">
        <div className="w-full max-w-lg bg-white border rounded-lg shadow-lg p-8">
          <div className="mb-6 text-sm text-gray-600">
            <span className="text-gray-400">Step 1</span> → <span className="text-blue-600 font-semibold">Step 2 of 3: Confirm</span>
          </div>

          <h1 className="text-2xl font-bold">Confirm Transaction</h1>
          <p className="text-gray-600 mt-1">Review details and confirm in your wallet</p>

          {/* Transaction Details */}
          <div className="mt-6 space-y-3 p-4 bg-gray-50 rounded border">
            <div className="flex items-center justify-between">
              <span className="text-gray-700">Proposal:</span>
              <span className="font-mono text-sm">{proposalId}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-700">Amount:</span>
              <span className="font-semibold">{amount} {token}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-700">Gas Estimate:</span>
              <span className="font-semibold">0.005 ETH</span>
            </div>
            <div className="border-t pt-3 flex items-center justify-between">
              <span className="font-bold text-gray-800">Total Cost:</span>
              <span className="font-bold text-lg text-blue-600">{total} {token === "ETH" ? "ETH" : token}</span>
            </div>
          </div>

          {/* Smart Contract Info */}
          <div className="mt-4 p-4 bg-yellow-50 border border-yellow-100 rounded text-sm text-yellow-800">
            <strong>⚠️ Smart Contract Call:</strong>
            <div className="font-mono text-xs mt-2 break-all">
              DonationVault.donate(proposalId: {proposalId}, amount: {amount} {token})
            </div>
          </div>

          {/* Funds Check */}
          <div className="mt-4 p-3 bg-green-50 border border-green-100 rounded text-sm text-green-700">
            ✓ Your wallet has sufficient {token} to complete this transaction.
          </div>

          <div className="mt-6 space-y-2">
            <button onClick={handleConfirmDonation} className="w-full px-4 py-2 bg-green-600 text-white rounded font-semibold hover:bg-green-700 transition">
              Confirm Donation in Wallet →
            </button>
            <button onClick={() => setStage("review")} className="w-full px-4 py-2 border rounded text-gray-700 hover:bg-gray-50 transition">
              ← Back
            </button>
          </div>

          <p className="text-xs text-gray-500 mt-4 text-center">A wallet popup will appear. Please approve the transaction in your wallet.</p>
        </div>
      </main>
    );
  }

  // STAGE 3: Pending & Database Logging
  if (stage === "pending") {
    return (
      <main className="flex min-h-screen items-center justify-center p-12 bg-gradient-to-br from-blue-50 to-indigo-50">
        <div className="w-full max-w-lg bg-white border rounded-lg shadow-lg p-8 text-center">
          <div className="mb-6 text-sm text-gray-600">
            <span className="text-gray-400">Steps 1-2</span> → <span className="text-blue-600 font-semibold">Step 3 of 3: Processing</span>
          </div>

          {/* Spinner */}
          <div className="flex justify-center mb-6">
            <div className="relative w-12 h-12">
              <div className="absolute inset-0 rounded-full border-4 border-gray-200"></div>
              <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-blue-600 animate-spin"></div>
            </div>
          </div>

          <h1 className="text-2xl font-bold">Processing Your Donation</h1>
          <p className="text-gray-600 mt-2">Please wait while we confirm your transaction...</p>

          {txHash && (
            <div className="mt-6 p-4 bg-blue-50 border border-blue-100 rounded">
              <p className="text-sm text-gray-600">Transaction Hash:</p>
              <p className="font-mono text-sm mt-1 break-all text-blue-600">{txHash}</p>
            </div>
          )}

          <div className="mt-6 space-y-2 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <span>⏳</span>
              <span>Waiting for blockchain confirmation...</span>
            </div>
            <div className="flex items-center gap-2">
              <span>📝</span>
              <span>Syncing with backend...</span>
            </div>
          </div>
        </div>
      </main>
    );
  }

  // STAGE 4a: Success
  if (stage === "success") {
    return (
      <main className="flex min-h-screen items-center justify-center p-12 bg-gradient-to-br from-green-50 to-emerald-50">
        <div className="w-full max-w-lg bg-white border rounded-lg shadow-lg p-8 text-center">
          <div className="text-5xl mb-4">🚀</div>

          <h1 className="text-2xl font-bold">Donation Complete!</h1>
          <p className="text-gray-600 mt-2">Thank you for supporting public goods with quadratic funding.</p>

          {/* Success Details */}
          <div className="mt-6 space-y-3 p-4 bg-green-50 border border-green-100 rounded">
            <div className="text-sm">
              <span className="text-gray-700">Amount Donated:</span>
              <div className="font-bold text-lg">{amount} {token}</div>
            </div>
            <div className="text-sm">
              <span className="text-gray-700">Proposal:</span>
              <div className="font-mono text-sm">{proposalId}</div>
            </div>
            <div className="text-sm">
              <span className="text-gray-700">Transaction Hash:</span>
              <div className="font-mono text-xs break-all text-gray-600">{txHash}</div>
            </div>
            <div className="text-sm pt-3 border-t">
              <span className="text-gray-700">Estimated New Match:</span>
              <div className="font-bold text-green-600">+$250</div>
            </div>
          </div>

          <div className="mt-6 space-y-2">
            <Link href={`/proposals/${proposalId}`} className="block px-4 py-2 bg-blue-600 text-white rounded font-semibold hover:bg-blue-700 transition">
              View Proposal Updates
            </Link>
            <Link href="/proposals" className="block px-4 py-2 border rounded text-gray-700 hover:bg-gray-50 transition">
              Browse More Proposals
            </Link>
            <a href="https://twitter.com/intent/tweet?text=I%20just%20donated%20to%20public%20goods%20via%20quadratic%20funding!" target="_blank" className="block px-4 py-2 border rounded text-gray-700 hover:bg-gray-50 transition">
              📢 Share Your Contribution
            </a>
          </div>
        </div>
      </main>
    );
  }

  // STAGE 4b: Error
  if (stage === "error") {
    return (
      <main className="flex min-h-screen items-center justify-center p-12 bg-gradient-to-br from-red-50 to-rose-50">
        <div className="w-full max-w-lg bg-white border rounded-lg shadow-lg p-8 text-center">
          <div className="text-5xl mb-4">❌</div>

          <h1 className="text-2xl font-bold">Transaction Failed</h1>
          <p className="text-gray-600 mt-2">Your donation could not be processed.</p>

          <div className="mt-6 p-4 bg-red-50 border border-red-100 rounded text-sm text-red-700">
            <strong>Error:</strong>
            <p className="mt-2">{errorMsg}</p>
          </div>

          <div className="mt-6 space-y-2">
            <button
              onClick={() => {
                setStage("review");
                setErrorMsg("");
              }}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded font-semibold hover:bg-blue-700 transition"
            >
              Try Again
            </button>
            <Link href={`/proposals/${proposalId}`} className="block px-4 py-2 border rounded text-gray-700 hover:bg-gray-50 transition">
              Back to Proposal
            </Link>
            <a href="mailto:support@dao.org" className="block px-4 py-2 border rounded text-gray-700 hover:bg-gray-50 transition">
              📧 Contact Support
            </a>
          </div>
        </div>
      </main>
    );
  }
}
