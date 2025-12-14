import Link from "next/link";

export default function RoundCard({ round, status }: { round: any; status: string }) {
  return (
    <div className="border border-border rounded-lg p-5 bg-card shadow-sm hover:shadow-md transition-shadow">
      <h3 className="text-xl font-bold text-foreground mb-2">{round.name}</h3>
      <div className="flex justify-between text-sm text-muted-foreground mb-3">
        <span>Start: {new Date(round.startDate).toLocaleDateString()}</span>
        <span>End: {new Date(round.endDate).toLocaleDateString()}</span>
      </div>
      <div className="text-sm text-muted-foreground mb-4">
        {round.pool ? (
          <p>
            Pool:{" "}
            <span className="font-semibold text-foreground">
              ${round.pool.toLocaleString()}
            </span>
          </p>
        ) : (
          <p>Pool: <span className="text-muted-foreground italic">TBD</span></p>
        )}
      </div>
      <div className="flex justify-between items-center mt-auto">
        <span
          className={`px-3 py-1 rounded-full text-xs font-semibold ${status === "active"
            ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200 border border-green-200 dark:border-green-800"
            : status === "past"
              ? "bg-secondary text-secondary-foreground"
              : "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200 border border-blue-200 dark:border-blue-800"
            }`}
        >
          {status.charAt(0).toUpperCase() + status.slice(1)}
        </span>
        <Link
          href={`/rounds/${round.id}`}
          className="px-4 py-2 bg-primary text-primary-foreground hover:bg-primary/90 rounded-md text-sm font-medium transition-colors"
        >
          View Round
        </Link>
      </div>
    </div>
  );
}
