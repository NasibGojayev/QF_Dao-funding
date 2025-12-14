export default function RecentDonors({ donors }: { donors: any[] }) {
  if (!donors || donors.length === 0) {
    return <div className="text-sm text-gray-500 dark:text-gray-400">No donations yet</div>;
  }

  return (
    <div className="space-y-2">
      {donors.slice(0, 5).map((d, i) => (
        <div key={i} className="flex items-center justify-between text-sm">
          <div className="text-gray-700 dark:text-gray-300">
            {d.donor_details?.name || "Anonymous"}
          </div>
          <div className="font-semibold text-gray-900 dark:text-gray-100">
            ${parseFloat(d.amount).toLocaleString()}
          </div>
        </div>
      ))}
    </div>
  );
}
