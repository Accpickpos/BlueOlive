"use client";
import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import ProtectedRoute from "@/components/ProtectedRoute";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from "recharts";
import { api } from "@/lib/api";

interface Invoice {
  id: number;
  invoice_number?: string;
  debtor_name?: string;
  total_amount?: number | string;
  status?: string;
  invoice_date?: string;
}

interface CashSale {
  id: number;
  sale_date?: string;
  total_amount?: number | string;
  transaction_date?: string;
}

interface DashboardData {
  invoices: Invoice[];
  cashSales: CashSale[];
  revenueData: Array<{ month: string; revenue: number }>;
  totalRevenue: number;
  pendingInvoices: number;
}

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444"];

// Helper to safely parse numeric values that may come back as strings from DRF
const toNumber = (value: number | string | undefined | null): number => {
  const parsed = Number(value);
  return isNaN(parsed) ? 0 : parsed;
};

function DashboardContent() {
  const [data, setData] = useState<DashboardData>({
    invoices: [],
    cashSales: [],
    revenueData: [],
    totalRevenue: 0,
    pendingInvoices: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      let invoices: Invoice[] = [];
      let cashSales: CashSale[] = [];

      // Test API connectivity
      try {
        await api.get("/api/shops/");
      } catch (testError: any) {
        console.warn("API test endpoint failed:", testError.response?.status, testError.message);
      }

      // Fetch invoices
      try {
        const invoicesResponse = await api.get("/api/debtors/invoices/", {
          params: { limit: 100 },
        });
        const invoicesData =
          invoicesResponse.data.results || invoicesResponse.data || [];
        invoices = Array.isArray(invoicesData) ? invoicesData : [];
      } catch (invoiceError: any) {
        console.warn("Failed to fetch invoices:", invoiceError.response?.status);
        try {
          const debtorsResponse = await api.get("/api/debtors/", {
            params: { limit: 100 },
          });
          const debtorsData =
            debtorsResponse.data.results || debtorsResponse.data || [];
          invoices = Array.isArray(debtorsData) ? debtorsData : [];
        } catch (altError: any) {
          console.warn("Fallback debtors endpoint failed:", altError.response?.status);
        }
      }

      // Fetch cash sales
      try {
        const cashSalesResponse = await api.get("/api/pos/cash-sales/", {
          params: { limit: 100 },
        });
        const cashSalesData =
          cashSalesResponse.data.results || cashSalesResponse.data || [];
        cashSales = Array.isArray(cashSalesData) ? cashSalesData : [];
      } catch (cashError: any) {
        console.warn("Failed to fetch cash sales:", cashError.response?.status);
        try {
          const posResponse = await api.get("/api/pos/", {
            params: { limit: 100 },
          });
          const posData = posResponse.data.results || posResponse.data || [];
          cashSales = Array.isArray(posData) ? posData : [];
        } catch (altError: any) {
          console.warn("Fallback POS endpoint failed:", altError.response?.status);
        }
      }

      // ✅ FIX: Use toNumber() to ensure string decimals from DRF are parsed correctly
      const totalRevenue = cashSales.reduce((sum: number, sale: CashSale) => {
        return sum + toNumber(sale.total_amount);
      }, 0);

      const pendingInvoices = invoices.filter(
        (invoice: Invoice) => invoice.status?.toLowerCase() === "pending"
      ).length;

      // Group cash sales by month for revenue trend
      const revenueByMonth: { [key: string]: number } = {};
      cashSales.forEach((sale: CashSale) => {
        const date = new Date(sale.sale_date || sale.transaction_date || "");
        if (!isNaN(date.getTime())) {
          const month = date.toLocaleDateString("en-US", { month: "short" });
          // ✅ FIX: Use toNumber() here too
          revenueByMonth[month] =
            (revenueByMonth[month] || 0) + toNumber(sale.total_amount);
        }
      });

      const revenueData = Object.entries(revenueByMonth)
        .map(([month, revenue]) => ({ month, revenue }))
        .slice(-6);

      setData({
        invoices: invoices.slice(0, 10),
        cashSales,
        revenueData: revenueData.length > 0 ? revenueData : [],
        totalRevenue,
        pendingInvoices,
      });
    } catch (err: any) {
      console.error("Error fetching dashboard data:", err);
      setError(
        "Failed to load dashboard data. Check browser console for API endpoint details."
      );
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="grid grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <div className="animate-pulse">
                <div className="h-6 bg-gray-300 rounded w-3/4 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-1/2"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-red-600">
            <p>{error}</p>
            <button
              onClick={fetchDashboardData}
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Retry
            </button>
          </div>
        </CardContent>
      </Card>
    );
  }

  const expenseData = [
    { category: "Salaries", value: 3000 },
    { category: "Rent", value: 1200 },
    { category: "Utilities", value: 800 },
    { category: "Supplies", value: 500 },
  ];

  // ✅ FIX: toNumber() on expense values too for safety
  const totalExpenses = expenseData.reduce(
    (sum, item) => sum + toNumber(item.value),
    0
  );

  return (
    <div className="grid grid-cols-3 gap-6">
      {/* KPI Cards */}
      <Card>
        <CardContent className="p-6">
          <h2 className="text-lg font-semibold">Total Revenue</h2>
          <p className="text-2xl mt-2">
            R{data.totalRevenue.toLocaleString("en-ZA", { maximumFractionDigits: 2 })}
          </p>
          <p className="text-sm text-gray-500 mt-1">{data.cashSales.length} sales</p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <h2 className="text-lg font-semibold">Outstanding Invoices</h2>
          <p className="text-2xl mt-2">{data.pendingInvoices}</p>
          <p className="text-sm text-gray-500 mt-1">of {data.invoices.length} total</p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <h2 className="text-lg font-semibold">Expenses This Month</h2>
          <p className="text-2xl mt-2">R{totalExpenses.toLocaleString("en-ZA")}</p>
          <p className="text-sm text-gray-500 mt-1">{expenseData.length} categories</p>
        </CardContent>
      </Card>

      {/* Revenue Chart */}
      <Card className="col-span-2">
        <CardContent className="p-6">
          <h2 className="text-lg font-semibold mb-4">Revenue Trend</h2>
          {data.revenueData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={data.revenueData}>
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip
                  formatter={(value: number | undefined) =>
                    value !== undefined
                      ? `R${value.toLocaleString("en-ZA", { maximumFractionDigits: 2 })}`
                      : "N/A"
                  }
                />
                <Line
                  type="monotone"
                  dataKey="revenue"
                  stroke="#3b82f6"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              No data to display
            </div>
          )}
        </CardContent>
      </Card>

      {/* Expenses Breakdown */}
      <Card>
        <CardContent className="p-6">
          <h2 className="text-lg font-semibold mb-4">Expense Breakdown</h2>
          {expenseData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={expenseData}
                  dataKey="value"
                  nameKey="category"
                  outerRadius={80}
                  label
                >
                  {expenseData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number | undefined) =>
                    value !== undefined
                      ? `R${value.toLocaleString("en-ZA")}`
                      : "N/A"
                  }
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              No data to display
            </div>
          )}
        </CardContent>
      </Card>

      {/* Invoice Table */}
      <Card className="col-span-3">
        <CardContent className="p-6">
          <h2 className="text-lg font-semibold mb-4">Recent Invoices</h2>
          {data.invoices.length > 0 ? (
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-gray-100 text-left">
                  <th className="p-3 border-b">Invoice #</th>
                  <th className="p-3 border-b">Client</th>
                  <th className="p-3 border-b">Amount</th>
                  <th className="p-3 border-b">Date</th>
                  <th className="p-3 border-b">Status</th>
                </tr>
              </thead>
              <tbody>
                {data.invoices.map((invoice) => (
                  <tr key={invoice.id} className="hover:bg-gray-50">
                    <td className="p-3 border-b">
                      {invoice.invoice_number || `INV-${invoice.id}`}
                    </td>
                    <td className="p-3 border-b">{invoice.debtor_name || "N/A"}</td>
                    <td className="p-3 border-b">
                      {/* ✅ FIX: toNumber() ensures string decimals display correctly */}
                      R{toNumber(invoice.total_amount).toLocaleString("en-ZA", {
                        maximumFractionDigits: 2,
                      })}
                    </td>
                    <td className="p-3 border-b">
                      {invoice.invoice_date
                        ? new Date(invoice.invoice_date).toLocaleDateString("en-ZA")
                        : "N/A"}
                    </td>
                    <td className="p-3 border-b">
                      <span
                        className={`px-2 py-1 rounded text-sm font-medium capitalize ${
                          invoice.status?.toLowerCase() === "paid"
                            ? "bg-green-100 text-green-700"
                            : invoice.status?.toLowerCase() === "pending"
                            ? "bg-yellow-100 text-yellow-700"
                            : "bg-red-100 text-red-700"
                        }`}
                      >
                        {invoice.status || "Unknown"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="py-8 text-center text-gray-500">No data to display</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function Page() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  );
}
