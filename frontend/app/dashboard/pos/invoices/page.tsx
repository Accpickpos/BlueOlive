"use client";
import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { Plus, FileText, Eye, ArrowLeft, TrendingUp, Clock, CheckCircle2, AlertCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/useAuth";
import { usePOSAPI } from "@/lib/posApi";

interface Invoice {
  id: string;
  invoice_number: string;
  client: string;
  debtor_name: string;
  amount: number;
  due: string;
  status: "Paid" | "Pending" | "Overdue" | "Cancelled";
  invoice_date: string;
  balance_due: number;
}

const fmt = (n: number) =>
  new Intl.NumberFormat("en-ZA", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(n);

const STATUS_META: Record<string, { label: string; icon: React.ElementType; cls: string }> = {
  Paid:      { label: "Paid",      icon: CheckCircle2, cls: "status-paid" },
  Pending:   { label: "Pending",   icon: Clock,        cls: "status-pending" },
  Overdue:   { label: "Overdue",   icon: AlertCircle,  cls: "status-overdue" },
  Cancelled: { label: "Cancelled", icon: FileText,      cls: "status-cancelled" },
};

export default function InvoicesPage() {
  const { user, isLoading: authLoading } = useAuth();

  // ── FIX 1: stabilise the API instance so it never re-triggers useEffect ──
  const posAPI = usePOSAPI(user?.tenant?.slug);
  const posAPIRef = useRef(posAPI);

  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState<string | null>(null);
  const [filter, setFilter]     = useState("All");

  useEffect(() => {
    // Don't run until auth has settled and we have a user
    if (authLoading || !user) return;

    let cancelled = false; // prevent stale setState on unmount

    const fetchInvoices = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await posAPIRef.current.listInvoices();

        if (cancelled) return;

        // ── FIX 2: handle both paginated {results:[]} and plain array responses ──
        const raw: any[] = Array.isArray(response)
          ? response
          : (response as any).results ?? [];

        setInvoices(
          raw.map((inv: any) => {
            // ── FIX 3: derive status from actual backend fields ──
            let status: Invoice["status"] = "Pending";
            if (inv.is_cancelled || inv.status === "CANCELLED") {
              status = "Cancelled";
            } else if (inv.status === "PAID") {
              status = "Paid";
            } else if (inv.is_overdue || inv.status === "OVERDUE") {
              status = "Overdue";
            }

            return {
              id:             String(inv.invoice_number || inv.id),
              invoice_number: inv.invoice_number ?? String(inv.id),
              // ── FIX 4: debtor_name comes from InvoiceListSerializer as debtor_name ──
              client:         String(inv.debtor_account_number ?? inv.debtor ?? "Unknown"),
              debtor_name:    inv.debtor_name ?? inv.debtor?.dname ?? inv.debtor?.name ?? "",
              amount:         Number(inv.total_amount ?? 0),
              due:            inv.due_date ?? inv.invoice_date ?? "—",
              status,
              invoice_date:   inv.invoice_date ?? "",
              // ── FIX 5: balance_due is a @property on Invoice model ──
              balance_due:    Number(inv.balance_due ?? inv.total_amount ?? 0),
            };
          })
        );
      } catch (err: any) {
        if (!cancelled) {
          console.error("Error fetching invoices:", err);
          setError(err?.message ?? "Failed to load invoices");
          setInvoices([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchInvoices();

    return () => { cancelled = true; };
  }, [user, authLoading]); // ── FIX 6: posAPI removed from deps — it's stable via ref ──

  const filteredInvoices =
    filter === "All" ? invoices : invoices.filter((inv) => inv.status === filter);

  const totalAmount      = invoices.reduce((s, i) => s + i.amount, 0);
  const totalOutstanding = invoices
    .filter((i) => i.status !== "Paid" && i.status !== "Cancelled")
    .reduce((s, i) => s + i.balance_due, 0);
  const overdueCount = invoices.filter((i) => i.status === "Overdue").length;
  const paidCount    = invoices.filter((i) => i.status === "Paid").length;

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');

        .inv-root {
          min-height: 100vh;
          background: #0d1117;
          color: #e6edf3;
          font-family: 'DM Sans', sans-serif;
          font-weight: 300;
          padding: 2.5rem 2rem;
        }
        .inv-wrap { max-width: 1100px; margin: 0 auto; }

        .inv-header { display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:2.5rem; gap:1rem; }
        .inv-header-left { display:flex; align-items:center; gap:1.25rem; }
        .back-btn {
          display:flex; align-items:center; justify-content:center;
          width:36px; height:36px; border-radius:8px;
          border:1px solid #30363d; background:transparent; color:#8b949e;
          cursor:pointer; transition:border-color .15s,color .15s; text-decoration:none;
        }
        .back-btn:hover { border-color:#e6edf3; color:#e6edf3; }

        .inv-title { font-family:'DM Serif Display',serif; font-size:2.25rem; font-weight:400; line-height:1; color:#e6edf3; letter-spacing:-0.02em; }
        .inv-subtitle { font-size:.8rem; color:#6e7681; margin-top:.3rem; letter-spacing:.05em; text-transform:uppercase; }

        .new-btn {
          display:flex; align-items:center; gap:.5rem;
          padding:.6rem 1.25rem; background:#e6edf3; color:#0d1117;
          border:none; border-radius:8px; font-family:'DM Sans',sans-serif;
          font-size:.85rem; font-weight:500; cursor:pointer; text-decoration:none;
          white-space:nowrap; transition:background .15s;
        }
        .new-btn:hover { background:#c9d1d9; }

        .stats-strip {
          display:grid; grid-template-columns:repeat(4,1fr);
          gap:1px; background:#21262d; border:1px solid #21262d;
          border-radius:12px; overflow:hidden; margin-bottom:2rem;
        }
        .stat-cell { background:#161b22; padding:1.25rem 1.5rem; display:flex; flex-direction:column; gap:.25rem; }
        .stat-label { font-size:.7rem; color:#6e7681; letter-spacing:.08em; text-transform:uppercase; }
        .stat-value { font-family:'DM Mono',monospace; font-size:1.5rem; font-weight:500; color:#e6edf3; line-height:1; }
        .stat-value.accent { color:#3fb950; }
        .stat-value.warn   { color:#d29922; }
        .stat-value.danger { color:#f85149; }
        .stat-sub { font-size:.75rem; color:#6e7681; margin-top:.1rem; }

        .filter-bar { display:flex; gap:.5rem; margin-bottom:1.5rem; flex-wrap:wrap; }
        .filter-pill {
          padding:.4rem 1rem; border-radius:999px; border:1px solid #30363d;
          background:transparent; color:#8b949e; font-family:'DM Sans',sans-serif;
          font-size:.8rem; cursor:pointer; transition:all .15s;
        }
        .filter-pill:hover  { border-color:#8b949e; color:#e6edf3; }
        .filter-pill.active { border-color:#e6edf3; background:#e6edf3; color:#0d1117; font-weight:500; }

        .table-card { background:#161b22; border:1px solid #21262d; border-radius:12px; overflow:hidden; }
        .table-card-header {
          padding:1.25rem 1.5rem; border-bottom:1px solid #21262d;
          display:flex; align-items:center; justify-content:space-between;
        }
        .table-card-title { font-family:'DM Serif Display',serif; font-size:1.1rem; font-weight:400; color:#e6edf3; }
        .table-count { font-family:'DM Mono',monospace; font-size:.75rem; color:#6e7681; }

        table { width:100%; border-collapse:collapse; }
        thead tr { border-bottom:1px solid #21262d; }
        th { padding:.75rem 1.25rem; font-size:.68rem; font-weight:500; color:#6e7681; letter-spacing:.1em; text-transform:uppercase; text-align:left; }
        th.right { text-align:right; }
        th.center { text-align:center; }

        tbody tr { border-bottom:1px solid #1c2128; transition:background .1s; }
        tbody tr:last-child { border-bottom:none; }
        tbody tr:hover { background:#1c2128; }

        td { padding:.9rem 1.25rem; font-size:.85rem; }
        .td-inv { font-family:'DM Mono',monospace; font-size:.8rem; font-weight:500; color:#58a6ff; }
        .td-client { color:#c9d1d9; }
        .td-client small { display:block; font-size:.72rem; color:#6e7681; margin-top:.1rem; }
        .td-amount { text-align:right; font-family:'DM Mono',monospace; font-size:.85rem; font-weight:500; color:#e6edf3; }
        .td-date { color:#8b949e; font-size:.8rem; }
        .td-actions { text-align:center; }

        .view-btn {
          display:inline-flex; align-items:center; justify-content:center;
          width:30px; height:30px; border-radius:6px; border:1px solid #30363d;
          background:transparent; color:#8b949e; cursor:pointer; text-decoration:none; transition:all .15s;
        }
        .view-btn:hover { border-color:#58a6ff; color:#58a6ff; background:rgba(88,166,255,.08); }

        .status-badge { display:inline-flex; align-items:center; gap:.35rem; padding:.25rem .65rem; border-radius:999px; font-size:.72rem; font-weight:500; letter-spacing:.02em; }
        .status-badge svg { width:11px; height:11px; }
        .status-paid      { background:rgba(63,185,80,.12);  color:#3fb950; border:1px solid rgba(63,185,80,.2); }
        .status-pending   { background:rgba(210,153,34,.12); color:#d29922; border:1px solid rgba(210,153,34,.2); }
        .status-overdue   { background:rgba(248,81,73,.12);  color:#f85149; border:1px solid rgba(248,81,73,.2); }
        .status-cancelled { background:rgba(110,118,129,.12);color:#6e7681; border:1px solid rgba(110,118,129,.2); }

        .empty-state { display:flex; flex-direction:column; align-items:center; justify-content:center; padding:5rem 2rem; gap:1rem; color:#6e7681; text-align:center; }
        .empty-icon { width:48px; height:48px; background:#21262d; border-radius:12px; display:flex; align-items:center; justify-content:center; margin-bottom:.5rem; }
        .empty-title { font-size:1rem; color:#8b949e; font-weight:500; }
        .empty-sub { font-size:.8rem; }

        .error-banner { background:rgba(248,81,73,.1); border:1px solid rgba(248,81,73,.3); border-radius:8px; padding:1rem 1.25rem; color:#f85149; font-size:.85rem; margin-bottom:1.5rem; }

        @keyframes pulse { 0%,100%{opacity:.3} 50%{opacity:.9} }
        .loading-dot { animation:pulse 1.2s ease-in-out infinite; font-size:1.5rem; }
        .loading-dot:nth-child(2) { animation-delay:.2s; }
        .loading-dot:nth-child(3) { animation-delay:.4s; }
        .loading-cell { text-align:center; padding:4rem; color:#6e7681; }

        @media (max-width:700px) {
          .stats-strip { grid-template-columns:repeat(2,1fr); }
          .inv-title { font-size:1.75rem; }
          th.hide-sm, td.hide-sm { display:none; }
        }
      `}</style>

      <div className="inv-root">
        <div className="inv-wrap">

          {/* Header */}
          <header className="inv-header">
            <div className="inv-header-left">
              <Link href="/dashboard/pos" className="back-btn" aria-label="Back">
                <ArrowLeft size={16} />
              </Link>
              <div>
                <h1 className="inv-title">Invoices</h1>
                <p className="inv-subtitle">Accounts Receivable</p>
              </div>
            </div>
            <Link href="/dashboard/pos/invoices/create" className="new-btn">
              <Plus size={15} />
              New Invoice
            </Link>
          </header>

          {/* Error banner */}
          {error && (
            <div className="error-banner">
              ⚠ {error} — check the browser console for details.
            </div>
          )}

          {/* Stats strip */}
          <div className="stats-strip">
            <div className="stat-cell">
              <span className="stat-label">Total Invoiced</span>
              <span className="stat-value">R{fmt(totalAmount)}</span>
              <span className="stat-sub">{invoices.length} invoice{invoices.length !== 1 ? "s" : ""}</span>
            </div>
            <div className="stat-cell">
              <span className="stat-label">Outstanding</span>
              <span className="stat-value warn">R{fmt(totalOutstanding)}</span>
              <span className="stat-sub">balance due</span>
            </div>
            <div className="stat-cell">
              <span className="stat-label">Overdue</span>
              <span className="stat-value danger">{overdueCount}</span>
              <span className="stat-sub">require attention</span>
            </div>
            <div className="stat-cell">
              <span className="stat-label">Paid</span>
              <span className="stat-value accent">{paidCount}</span>
              <span className="stat-sub">this period</span>
            </div>
          </div>

          {/* Filter bar */}
          <div className="filter-bar">
            {["All", "Paid", "Pending", "Overdue", "Cancelled"].map((s) => (
              <button
                key={s}
                onClick={() => setFilter(s)}
                className={`filter-pill${filter === s ? " active" : ""}`}
              >
                {s}
              </button>
            ))}
          </div>

          {/* Table */}
          <div className="table-card">
            <div className="table-card-header">
              <span className="table-card-title">
                {filter === "All" ? "All Invoices" : `${filter} Invoices`}
              </span>
              <span className="table-count">{filteredInvoices.length} records</span>
            </div>

            <div style={{ overflowX: "auto" }}>
              <table>
                <thead>
                  <tr>
                    <th>Invoice #</th>
                    <th>Client</th>
                    <th className="right">Amount</th>
                    <th className="hide-sm">Due Date</th>
                    <th>Status</th>
                    <th className="center">View</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan={6} className="loading-cell">
                        <span className="loading-dot">·</span>
                        <span className="loading-dot">·</span>
                        <span className="loading-dot">·</span>
                      </td>
                    </tr>
                  ) : filteredInvoices.length === 0 ? (
                    <tr>
                      <td colSpan={6}>
                        <div className="empty-state">
                          <div className="empty-icon">
                            <FileText size={22} color="#6e7681" />
                          </div>
                          <p className="empty-title">No invoices found</p>
                          <p className="empty-sub">
                            {filter === "All"
                              ? "Create your first invoice to get started"
                              : `No ${filter.toLowerCase()} invoices match your filter`}
                          </p>
                          {filter === "All" && (
                            <Link href="/dashboard/pos/invoices/create" className="new-btn" style={{ marginTop: ".5rem" }}>
                              <Plus size={14} /> Create Invoice
                            </Link>
                          )}
                        </div>
                      </td>
                    </tr>
                  ) : (
                    filteredInvoices.map((invoice) => {
                      const meta = STATUS_META[invoice.status] ?? STATUS_META.Pending;
                      const StatusIcon = meta.icon;
                      return (
                        <tr key={invoice.id}>
                          <td className="td-inv">{invoice.invoice_number}</td>
                          <td className="td-client">
                            {invoice.debtor_name || invoice.client}
                            {invoice.debtor_name && invoice.client && invoice.debtor_name !== invoice.client && (
                              <small>{invoice.client}</small>
                            )}
                          </td>
                          <td className="td-amount">R{fmt(invoice.amount)}</td>
                          <td className="td-date hide-sm">{invoice.due}</td>
                          <td>
                            <span className={`status-badge ${meta.cls}`}>
                              <StatusIcon />
                              {meta.label}
                            </span>
                          </td>
                          <td className="td-actions">
                            <Link
                              href={`/dashboard/pos/invoices/${invoice.id}`}
                              className="view-btn"
                              aria-label={`View invoice ${invoice.invoice_number}`}
                            >
                              <Eye size={14} />
                            </Link>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>

        </div>
      </div>
    </>
  );
}