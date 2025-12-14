"use client";

import { useState } from "react";
import Link from "next/link";
import { useWriteContract } from "wagmi";
import { GRANT_REGISTRY_ABI, GRANT_REGISTRY_ADDRESS } from "../../../lib/contracts";

export default function NewProposalPage() {
  const [step, setStep] = useState<"details" | "budget" | "review" | "success">("details");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("Environment");
  const [budget, setBudget] = useState("");
  const [timeline, setTimeline] = useState("");
  const [goals, setGoals] = useState("");
  const [errors, setErrors] = useState<string[]>([]);

  function validateStep(currentStep: string) {
    const newErrors: string[] = [];

    if (currentStep === "details") {
      if (!title.trim()) newErrors.push("Proposal title is required");
      if (!description.trim()) newErrors.push("Description is required");
      if (description.length < 50) newErrors.push("Description must be at least 50 characters");
    }

    if (currentStep === "budget") {
      if (!budget.trim()) newErrors.push("Budget is required");
      if (!timeline.trim()) newErrors.push("Timeline is required");
      if (!goals.trim()) newErrors.push("Goals are required");
    }

    setErrors(newErrors);
    return newErrors.length === 0;
  }

  function handleNextStep() {
    if (validateStep(step)) {
      if (step === "details") setStep("budget");
      else if (step === "budget") setStep("review");
    }
  }

  // Web3 Hooks
  const { writeContractAsync } = useWriteContract();

  async function handleSubmit() {
    if (validateStep("budget")) {
      try {
        // 1. Create Metadata (In a real app, upload this JSON to IPFS and get CID)
        const metadata = JSON.stringify({
          title,
          description,
          category,
          budget,
          timeline,
          goals
        });

        // 2. Call Smart Contract
        // This triggers MetaMask to ask for signature
        const txHash = await writeContractAsync({
          address: GRANT_REGISTRY_ADDRESS,
          abi: GRANT_REGISTRY_ABI,
          functionName: 'createGrant',
          args: [metadata],
        });

        console.log("Transaction Sent:", txHash);

        // 3. (Optional) You can wait for transaction confirmation here using useWaitForTransactionReceipt
        // but for now we proceed to success
        setStep("success");

      } catch (error) {
        console.error("Error creating proposal:", error);
        alert("Failed to create proposal on-chain. See console.");
      }
    }
  }

  // STEP 1: Proposal Details
  if (step === "details") {
    return (
      <main className="flex min-h-screen items-center justify-center p-12 bg-gradient-to-br from-blue-50 to-indigo-50">
        <div className="w-full max-w-2xl bg-white border rounded-lg shadow-lg p-8">
          <div className="mb-6">
            <h1 className="text-3xl font-bold">Create a Proposal</h1>
            <p className="text-gray-600 mt-2">Step 1 of 3: Proposal Details</p>
            <div className="mt-4 h-1 bg-gray-200 rounded">
              <div className="h-1 bg-blue-600 rounded w-1/3"></div>
            </div>
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleNextStep();
            }}
            className="space-y-6"
          >
            <div>
              <label className="block text-sm font-medium text-gray-700">Proposal Title *</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g., Clean Water Initiative"
                className="mt-2 w-full border px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">{title.length}/100 characters</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Category *</label>
              <select value={category} onChange={(e) => setCategory(e.target.value)} className="mt-2 w-full border px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option>Environment</option>
                <option>Education</option>
                <option>Healthcare</option>
                <option>Open Source</option>
                <option>Art & Culture</option>
                <option>Research</option>
                <option>Other</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Description *</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe your proposal, its impact, and why it matters..."
                rows={6}
                className="mt-2 w-full border px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">{description.length}/2000 characters (min. 50)</p>
            </div>

            {errors.length > 0 && (
              <div className="p-4 bg-red-50 border border-red-200 rounded">
                {errors.map((e, i) => (
                  <p key={i} className="text-sm text-red-700">
                    • {e}
                  </p>
                ))}
              </div>
            )}

            <div className="flex gap-3">
              <Link href="/proposals" className="flex-1 px-4 py-2 border rounded text-center font-semibold hover:bg-gray-50">
                Cancel
              </Link>
              <button type="submit" className="flex-1 px-4 py-2 bg-blue-600 text-white rounded font-semibold hover:bg-blue-700">
                Next: Budget →
              </button>
            </div>
          </form>
        </div>
      </main>
    );
  }

  // STEP 2: Budget & Timeline
  if (step === "budget") {
    return (
      <main className="flex min-h-screen items-center justify-center p-12 bg-gradient-to-br from-blue-50 to-indigo-50">
        <div className="w-full max-w-2xl bg-white border rounded-lg shadow-lg p-8">
          <div className="mb-6">
            <h1 className="text-3xl font-bold">Create a Proposal</h1>
            <p className="text-gray-600 mt-2">Step 2 of 3: Budget & Timeline</p>
            <div className="mt-4 h-1 bg-gray-200 rounded">
              <div className="h-1 bg-blue-600 rounded w-2/3"></div>
            </div>
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleNextStep();
            }}
            className="space-y-6"
          >
            <div>
              <label className="block text-sm font-medium text-gray-700">Budget Required (USD) *</label>
              <div className="mt-2 flex gap-2">
                <span className="flex items-center text-gray-600">$</span>
                <input type="number" min={0} value={budget} onChange={(e) => setBudget(e.target.value)} placeholder="15000" className="flex-1 border px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Timeline *</label>
              <select value={timeline} onChange={(e) => setTimeline(e.target.value)} className="mt-2 w-full border px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">Select timeline</option>
                <option>1-3 months</option>
                <option>3-6 months</option>
                <option>6-12 months</option>
                <option>12+ months</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Goals & Deliverables *</label>
              <textarea value={goals} onChange={(e) => setGoals(e.target.value)} placeholder="What are the key milestones and deliverables?" rows={4} className="mt-2 w-full border px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>

            {errors.length > 0 && (
              <div className="p-4 bg-red-50 border border-red-200 rounded">
                {errors.map((e, i) => (
                  <p key={i} className="text-sm text-red-700">
                    • {e}
                  </p>
                ))}
              </div>
            )}

            <div className="flex gap-3">
              <button onClick={() => setStep("details")} className="flex-1 px-4 py-2 border rounded text-center font-semibold hover:bg-gray-50">
                ← Back
              </button>
              <button type="submit" className="flex-1 px-4 py-2 bg-blue-600 text-white rounded font-semibold hover:bg-blue-700">
                Next: Review →
              </button>
            </div>
          </form>
        </div>
      </main>
    );
  }

  // STEP 3: Review
  if (step === "review") {
    return (
      <main className="flex min-h-screen items-center justify-center p-12 bg-gradient-to-br from-blue-50 to-indigo-50">
        <div className="w-full max-w-2xl bg-white border rounded-lg shadow-lg p-8">
          <div className="mb-6">
            <h1 className="text-3xl font-bold">Create a Proposal</h1>
            <p className="text-gray-600 mt-2">Step 3 of 3: Review & Submit</p>
            <div className="mt-4 h-1 bg-gray-200 rounded">
              <div className="h-1 bg-blue-600 rounded w-full"></div>
            </div>
          </div>

          <div className="space-y-6">
            <div>
              <h3 className="font-semibold text-gray-700">Proposal Summary</h3>
              <div className="mt-4 space-y-3 p-4 bg-gray-50 rounded border">
                <div>
                  <p className="text-xs text-gray-600">Title</p>
                  <p className="font-semibold">{title}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600">Category</p>
                  <p className="font-semibold">{category}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600">Budget</p>
                  <p className="font-semibold">${budget}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600">Timeline</p>
                  <p className="font-semibold">{timeline}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600">Description</p>
                  <p className="mt-1 text-sm">{description}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600">Goals</p>
                  <p className="mt-1 text-sm">{goals}</p>
                </div>
              </div>
            </div>

            <div className="p-4 bg-blue-50 border border-blue-100 rounded text-sm text-blue-900">
              <strong>📋 Before you submit:</strong>
              <ul className="mt-2 space-y-1 list-disc list-inside">
                <li>Make sure your proposal is clear and compelling</li>
                <li>Double-check budget and timeline</li>
                <li>You'll be able to edit after submission</li>
              </ul>
            </div>

            <div className="flex gap-3">
              <button onClick={() => setStep("budget")} className="flex-1 px-4 py-2 border rounded text-center font-semibold hover:bg-gray-50">
                ← Back
              </button>
              <button onClick={handleSubmit} className="flex-1 px-4 py-2 bg-green-600 text-white rounded font-semibold hover:bg-green-700">
                Submit Proposal 🚀
              </button>
            </div>
          </div>
        </div>
      </main>
    );
  }

  // SUCCESS
  return (
    <main className="flex min-h-screen items-center justify-center p-12 bg-gradient-to-br from-green-50 to-emerald-50">
      <div className="w-full max-w-2xl bg-white border rounded-lg shadow-lg p-8 text-center">
        <div className="text-5xl mb-4">✅</div>
        <h1 className="text-3xl font-bold">Proposal Submitted!</h1>
        <p className="text-gray-600 mt-2">Thank you for creating a proposal. The community can now discover and support your idea.</p>

        <div className="mt-6 p-4 bg-green-50 border border-green-100 rounded text-left">
          <h3 className="font-semibold text-green-900">What's next?</h3>
          <ul className="mt-3 space-y-2 text-sm text-green-800 list-disc list-inside">
            <li>Share your proposal link with the community</li>
            <li>Respond to questions and comments from donors</li>
            <li>Engage with your community to maximize donations</li>
            <li>Track your funding progress in real-time</li>
          </ul>
        </div>

        <div className="mt-6 space-y-2">
          <Link href="/proposals" className="block px-4 py-2 bg-blue-600 text-white rounded font-semibold hover:bg-blue-700">
            View All Proposals
          </Link>
          <Link href="/profile" className="block px-4 py-2 border rounded text-gray-700 font-semibold hover:bg-gray-50">
            Go to My Profile
          </Link>
        </div>
      </div>
    </main>
  );
}
