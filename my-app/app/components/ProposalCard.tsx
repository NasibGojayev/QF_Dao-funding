import Link from "next/link";

export default function ProposalCard({ proposal }: { proposal: any }) {
  const progress = proposal.amount && proposal.amount > 0 ? Math.min(100, Math.round((proposal.amount / 5000) * 100)) : 0;

  return (
    <div className="border border-border rounded-lg p-5 bg-card shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <Link href={`/proposals/${proposal.id}`} className="text-lg font-semibold text-foreground hover:text-primary transition-colors line-clamp-1">{proposal.title}</Link>
          <div className="text-sm text-muted-foreground mt-1">By {proposal.creator ?? 'Unknown'}</div>

          <div className="flex items-center gap-2 mt-3 text-sm text-muted-foreground">
            <span className="font-medium text-foreground">{proposal.donations ?? 0}</span> donations
            <span>·</span>
            <span className="font-medium text-foreground">${proposal.amount?.toLocaleString() ?? 0}</span> raised
          </div>

          <div className="w-full bg-secondary h-2.5 rounded-full mt-3 overflow-hidden">
            <div className="h-full bg-green-500 rounded-full transition-all duration-500 ease-out" style={{ width: `${progress}%` }} />
          </div>
        </div>
        <div className="ml-4 pl-4 border-l border-border flex flex-col justify-center items-center h-full min-h-[80px]">
          <Link href={`/proposals/${proposal.id}`} className="px-4 py-2 border border-input rounded-md text-sm font-medium bg-background hover:bg-accent hover:text-accent-foreground transition-colors">
            View
          </Link>
        </div>
      </div>
    </div>
  );
}
