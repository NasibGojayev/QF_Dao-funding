"use client";

import { useState, useEffect } from "react";
import { useAccount, useWriteContract, useWaitForTransactionReceipt, useReadContract, useBalance, type BaseError } from "wagmi";
import { parseEther, formatEther } from "viem";
import {
  DONATION_VAULT_ADDRESS,
  DONATION_VAULT_ABI,
  GOVERNANCE_TOKEN_ADDRESS
} from "../../lib/contracts";
import { erc20Abi } from "viem";

export default function DonationWidget({
  proposalId,
  estimatedMatch = 0,
  onChainId,
  roundId = 1,
}: {
  proposalId: string;
  estimatedMatch?: number;
  onChainId?: number;
  roundId?: number;
}) {
  const [amount, setAmount] = useState(1);
  const [description, setDescription] = useState("");
  const [message, setMessage] = useState("");

  // Transaction Hashes
  const [approveHash, setApproveHash] = useState<`0x${string}` | undefined>(undefined);
  const [donateHash, setDonateHash] = useState<`0x${string}` | undefined>(undefined);

  const { address, isConnected } = useAccount();
  const { writeContractAsync, isPending: isWritePending } = useWriteContract();

  // Watch Transactions
  const { isLoading: isApproving, isSuccess: isApproved, isError: isApproveError } = useWaitForTransactionReceipt({
    hash: approveHash,
  });
  const { isLoading: isDonating, isSuccess: isDonated, isError: isDonateError } = useWaitForTransactionReceipt({
    hash: donateHash,
  });

  // Check Allowance & Balances
  const { data: allowance, refetch: refetchAllowance } = useReadContract({
    address: GOVERNANCE_TOKEN_ADDRESS,
    abi: erc20Abi,
    functionName: "allowance",
    args: [address!, DONATION_VAULT_ADDRESS],
    query: { enabled: !!address }
  });

  const { data: govBalanceObj, refetch: refetchGovBalance } = useReadContract({
    address: GOVERNANCE_TOKEN_ADDRESS,
    abi: erc20Abi,
    functionName: "balanceOf",
    args: [address!],
    query: { enabled: !!address }
  });

  const { data: ethBalanceObj } = useBalance({
    address: address,
  });

  // Helpers
  const govBalance = govBalanceObj ? Number(formatEther(govBalanceObj)) : 0;
  const ethBalance = ethBalanceObj ? Number(ethBalanceObj.formatted) : 0;

  // Effects
  useEffect(() => {
    if (isApproved) {
      setMessage("Approval confirmed! You can now donate.");
      refetchAllowance();
    }
  }, [isApproved, refetchAllowance]);

  useEffect(() => {
    if (isDonated) {
      setMessage(`Success! Donation confirmed on-chain. Hash: ${donateHash}`);
      refetchGovBalance();
    }
  }, [isDonated, donateHash, refetchGovBalance]);

  useEffect(() => {
    if (isApproveError) setMessage("Approval transaction failed on-chain.");
    if (isDonateError) setMessage("Donation transaction failed on-chain.");
  }, [isApproveError, isDonateError]);


  const needsApproval = allowance ? Number(formatEther(allowance)) < amount : true;

  const handleApprove = async () => {
    try {
      setMessage("Please sign the approval transaction...");
      const hash = await writeContractAsync({
        address: GOVERNANCE_TOKEN_ADDRESS,
        abi: erc20Abi,
        functionName: "approve",
        args: [DONATION_VAULT_ADDRESS, parseEther(amount.toString())],
      });
      setApproveHash(hash);
      setMessage("Transaction sent! Waiting for confirmation...");
    } catch (e: any) {
      const error = e as BaseError;
      setMessage("Approval rejected: " + (error.shortMessage || error.message));
    }
  };

  const handleDonate = async () => {
    if (!onChainId) return setMessage("Error: Proposal not synced to blockchain yet.");
    if (amount <= 0) return setMessage("Amount must be greater than 0");
    if (govBalance < amount) return setMessage("Insufficient token balance");

    try {
      setMessage("Please sign the donation transaction...");
      const hash = await writeContractAsync({
        address: DONATION_VAULT_ADDRESS,
        abi: DONATION_VAULT_ABI,
        functionName: "deposit",
        args: [
          GOVERNANCE_TOKEN_ADDRESS,
          parseEther(amount.toString()),
          BigInt(roundId),
          BigInt(onChainId)
        ],
      });
      setDonateHash(hash);
      setMessage("Donation sent! Waiting for block confirmation...");

    } catch (e: any) {
      const error = e as BaseError;
      setMessage("Donation rejected: " + (error.shortMessage || error.message));
    }
  };

  const isBusy = isWritePending || isApproving || isDonating;

  return (
    <div className="w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-md p-4">
      <div className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
        Donate with Web3
      </div>
      <div className="text-sm text-gray-600 dark:text-gray-400 mb-4">
        Support this proposal on-chain using Governance Tokens.
      </div>

      {/* Wallet Overview Panel */}
      {isConnected && (
        <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 mb-4 border border-gray-100 dark:border-gray-700">
          <div className="text-xs font-bold uppercase text-gray-500 dark:text-gray-400 mb-2 tracking-wider">
            Your Wallet
          </div>

          {/* GOV Balance */}
          <div className="flex justify-between items-center mb-2">
            <div className="flex flex-col">
              <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">Governance Token (GOV)</span>
              <span className="text-xs text-gray-500">Used for donations</span>
            </div>
            <span className="font-mono font-bold text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-600 px-2 py-1 rounded shadow-sm">
              {govBalance.toFixed(2)}
            </span>
          </div>

          {/* ETH Balance */}
          <div className="flex justify-between items-center text-xs mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
            <div className="flex flex-col">
              <span className="text-gray-600 dark:text-gray-400 font-medium">Ethereum (ETH)</span>
              <span className="text-gray-400 dark:text-gray-500">Used for gas fees</span>
            </div>
            <span className="font-mono text-gray-600 dark:text-gray-400">
              {ethBalance.toFixed(4)} ETH
            </span>
          </div>
        </div>
      )}

      <div className="mt-4">
        <label className="block text-sm text-gray-700 dark:text-gray-300">
          Amount to Donate (GOV)
        </label>
        <div className="mt-2 relative">
          <input
            type="number"
            min={0}
            step="0.01"
            disabled={isBusy}
            value={amount}
            onChange={(e) => setAmount(Number(e.target.value))}
            className="w-full border border-gray-300 dark:border-gray-600 px-3 py-2 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 disabled:opacity-50 pr-12"
          />
          <span className="absolute right-3 top-2.5 text-gray-400 text-sm pointer-events-none">GOV</span>
        </div>

        <label className="block text-sm text-gray-700 dark:text-gray-300 mt-3">
          Message (Optional)
        </label>
        <div className="mt-2">
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            disabled={isBusy}
            className="w-full border border-gray-300 dark:border-gray-600 px-3 py-2 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 disabled:opacity-50"
            placeholder="Add a message..."
            rows={2}
          />
        </div>

        <div className="mt-3 text-sm text-gray-600 dark:text-gray-400">
          Estimated match:{" "}
          <strong className="text-blue-600 dark:text-blue-400">
            ${(estimatedMatch || 0).toFixed(2)}
          </strong>
        </div>

        {!isConnected ? (
          <div className="mt-4 p-3 bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-800 rounded-lg text-yellow-800 dark:text-yellow-200 text-sm">
            Please connect your wallet to donate.
          </div>
        ) : !onChainId ? (
          <div className="mt-4 p-3 bg-red-100 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg text-red-800 dark:text-red-200 text-sm">
            Proposal not found on-chain. Cannot donate.
          </div>
        ) : (
          <div className="mt-4 space-y-2">
            {needsApproval ? (
              <button
                onClick={handleApprove}
                disabled={isBusy}
                className="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition disabled:opacity-50"
              >
                {isApproving ? "Waiting for confirmation..." : isWritePending ? "Check Wallet..." : "Approve Tokens"}
              </button>
            ) : (
              <button
                onClick={handleDonate}
                disabled={isBusy}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition disabled:opacity-50"
              >
                {isDonating ? "Confirming Donation..." : isWritePending ? "Check Wallet..." : "Donate Now"}
              </button>
            )}
          </div>
        )}

        {message && (
          <div
            className={`mt-3 p-3 rounded-lg text-sm break-words ${message.includes("Error") || message.includes("failed") || message.includes("rejected")
              ? "bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200"
              : "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200"
              }`}
          >
            {message}
          </div>
        )}
      </div>
    </div>
  );
}
