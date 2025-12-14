"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import dynamic from "next/dynamic";

// Dynamically import ThreeBackground to avoid SSR issues with canvas
const ThreeBackground = dynamic(() => import("../components/ThreeBackground"), {
  ssr: false,
  loading: () => <div className="w-full h-[250px] md:h-[300px] flex items-center justify-center" />
});

type Round = { id: string; name: string; pool: number; endDate: string };
type Proposal = { id: string; title: string; snippet?: string };

function timeRemaining(endDate: string) {
  const diff = new Date(endDate).getTime() - Date.now();
  if (diff <= 0) return "Ended";
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hrs = Math.floor((diff / (1000 * 60 * 60)) % 24);
  return `${days}d ${hrs}h`;
}

export default function Home() {
  const [activeRound, setActiveRound] = useState<Round | null>(null);
  const [featured, setFeatured] = useState<Proposal[]>([]);

  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
    // Fetch active round
    fetchActiveRound();
    // Fetch featured proposals
    fetchFeaturedProposals();
  }, []);

  const fetchActiveRound = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/rounds/active/`);
      if (res.ok) {
        const data = await res.json();
        if (data.length > 0) {
          setActiveRound(data[0]);
        }
      }
    } catch (e) {
      console.error("Failed to fetch active round:", e);
    }
  };

  const fetchFeaturedProposals = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/proposals/`);
      if (res.ok) {
        const data = await res.json();
        const proposals = data.results || data || [];
        // Map backend data to frontend type
        const mappedProposals = proposals.slice(0, 3).map((p: any) => ({
          id: p.proposal_id,
          title: p.title,
          snippet: p.description ? (p.description.length > 100 ? p.description.substring(0, 100) + "..." : p.description) : "No description provided."
        }));
        setFeatured(mappedProposals);
      }
    } catch (e) {
      console.error("Failed to fetch proposals:", e);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-start p-12 space-y-8 relative overflow-hidden bg-background">

      <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600 mb-8 z-10 drop-shadow-sm dark:drop-shadow-[0_0_15px_rgba(59,130,246,0.5)]">
        Welcome to DonCoin
      </h1>

      {/* Hero */}
      <section className="w-full max-w-7xl z-10 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        {/* Left Column: Text & Content */}
        <div className="flex flex-col gap-6">
          <h2 className="text-3xl font-bold text-foreground">Quadratic Funding for Public Goods</h2>
          <p className="text-muted-foreground mt-2 max-w-lg">
            Support the projects you care about. Your donations are matched by a larger pool, amplifying your impact.
          </p>
          <div className="mt-6 flex items-center gap-3">
            <Link href="/rounds" className="px-6 py-3 bg-primary text-primary-foreground rounded-lg font-semibold hover:bg-primary/90 transition-colors duration-200 shadow-lg shadow-blue-500/30">
              View Active Rounds
            </Link>
            <Link href="/proposals" className="px-4 py-2 border border-border rounded-lg text-sm bg-background/50 backdrop-blur hover:bg-accent hover:text-accent-foreground transition text-foreground">
              Browse Proposals
            </Link>
          </div>

          {activeRound && (
            <div className="mt-8 text-center p-6 bg-card/50 backdrop-blur rounded-2xl shadow-sm border border-border max-w-md">
              <h3 className="text-xl font-bold text-foreground">Current Pool</h3>
              <p className="text-4xl font-extrabold text-green-600 dark:text-green-400 mt-2 text-shadow-sm">${activeRound.pool.toLocaleString()}</p>
              <p className="text-sm text-center text-muted-foreground mt-1">
                Ends in {isMounted && activeRound.endDate ? timeRemaining(activeRound.endDate) : "..."}
              </p>
            </div>
          )}
        </div>

        {/* Right Column: Interactive 3D Coin */}
        <div className="flex justify-center items-center h-full min-h-[400px]">
          <ThreeBackground key="three-bg-stable" />
        </div>
      </section>

      {/* Featured Proposals */}
      <section className="w-full max-w-6xl z-10">
        <h3 className="text-2xl font-bold mb-4 text-foreground">Featured Proposals</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {featured.map((proposal, index) => (
            <div key={`${proposal.id}-${index}`} className="p-6 border border-border rounded-xl hover:shadow-lg transition bg-card/60 backdrop-blur">
              <h4 className="font-bold text-lg text-foreground">{proposal.title}</h4>
              <p className="text-sm text-muted-foreground mt-2">{proposal.snippet}</p>
              <Link href={`/proposals/${proposal.id}`} className="text-primary text-sm font-semibold mt-4 inline-block hover:underline">
                View Project &rarr;
              </Link>
            </div>
          ))}
        </div>
      </section>
    </main >
  );
}
