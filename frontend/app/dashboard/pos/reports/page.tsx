import Link from 'next/link';

export default function ReportsPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Reports</h1>
      <Link
        href="/dashboard/pos/reports/card-reconciliation"
        className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium"
      >
        Card Tender Reconciliation →
      </Link>
    </div>
  );
}