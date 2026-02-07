"use client";
import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import ProtectedRoute from "@/components/ProtectedRoute";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from "recharts";
import { api } from "@/lib/api";

interface Invoice {
  id: number;
  invoice_number?: string;
  debtor_name?: string;
  total_amount?: number;
  status?: string;
  invoice_date?: string;
}

interface CashSale {
  id: number;
  sale_date?: string;
  total_amount?: number;
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

      // First, test if API is accessible with a simple endpoint
      try {
        console.log("Testing API connection with /api/shops/");
        const testResponse = await api.get("/api/shops/");
        console.log("API connection successful, test response:", testResponse.data);
      } catch (testError: any) {
        console.warn("API test endpoint failed:", testError.response?.status, testError.message);
      }

      // Try to fetch invoices - first with query to see all available
      try {
        console.log("Attempting to fetch invoices from /api/debtors/invoices/");
        const invoicesResponse = await api.get("/api/debtors/invoices/", {
          params: { limit: 100 }
        });
        console.log("Invoices response:", invoicesResponse.status, invoicesResponse.data);
        const invoicesData = invoicesResponse.data.results || invoicesResponse.data || [];
        invoices = Array.isArray(invoicesData) ? invoicesData : [];
      } catch (invoiceError: any) {
        console.warn("Failed to fetch invoices from debtors/invoices:", {
          status: invoiceError.response?.status,
          statusText: invoiceError.response?.statusText,
          data: invoiceError.response?.data,
          message: invoiceError.message
        });
        
        // Try alternative: just debtors
        try {
          console.log("Attempting fallback: /api/debtors/");
          const debtorsResponse = await api.get("/api/debtors/", {
            params: { limit: 100 }
          });
          console.log("Debtors response:", debtorsResponse.status, debtorsResponse.data);
          const debtorsData = debtorsResponse.data.results || debtorsResponse.data || [];
          invoices = Array.isArray(debtorsData) ? debtorsData : [];
        } catch (altError: any) {
          console.warn("Fallback debtors endpoint failed:", altError.response?.status);
        }
      }

      // Try to fetch cash sales
      try {
        console.log("Attempting to fetch cash sales from /api/pos/cash-sales/");
        const cashSalesResponse = await api.get("/api/pos/cash-sales/", {
          params: { limit: 100 }
        });
        console.log("Cash sales response:", cashSalesResponse.status, cashSalesResponse.data);
        const cashSalesData = cashSalesResponse.data.results || cashSalesResponse.data || [];
        cashSales = Array.isArray(cashSalesData) ? cashSalesData : [];
      } catch (cashError: any) {
        console.warn("Failed to fetch cash sales from pos/cash-sales:", {
          status: cashError.response?.status,
          statusText: cashError.response?.statusText,
          data: cashError.response?.data,
          message: cashError.message
        });
        
        // Try alternative: just pos
        try {
          console.log("Attempting fallback: /api/pos/");
          const posResponse = await api.get("/api/pos/", {
            params: { limit: 100 }
          });
          console.log("POS response:", posResponse.status, posResponse.data);
          const posData = posResponse.data.results || posResponse.data || [];
          cashSales = Array.isArray(posData) ? posData : [];
        } catch (altError: any) {
          console.warn("Fallback POS endpoint failed:", altError.response?.status);
        }
      }

      // Calculate KPIs
      const totalRevenue = cashSales.reduce((sum: number, sale: CashSale) => {
        return sum + (sale.total_amount || 0);
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
          revenueByMonth[month] = (revenueByMonth[month] || 0) + (sale.total_amount || 0);
        }
      });

      const revenueData = Object.entries(revenueByMonth)
        .map(([month, revenue]) => ({ month, revenue }))
        .slice(-6); // Last 6 months

      setData({
        invoices: invoices.slice(0, 10), // Show last 10 invoices
        cashSales,
        revenueData: revenueData.length > 0 ? revenueData : [],
        totalRevenue,
        pendingInvoices,
      });

      console.log("Dashboard data fetched successfully:", {
        invoices: invoices.length,
        cashSales: cashSales.length,
        totalRevenue
      });
    } catch (err: any) {
      console.error("Error fetching dashboard data:", err);
      setError("Failed to load dashboard data. Check browser console for API endpoint details.");
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

  return (
    <div className="grid grid-cols-3 gap-6">
      {/* KPI Cards */}
      <Card>
        <CardContent className="p-6">
          <h2 className="text-lg font-semibold">Total Revenue</h2>
          <p className="text-2xl mt-2">R{data.totalRevenue.toLocaleString("en-ZA", { maximumFractionDigits: 2 })}</p>
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
          <p className="text-2xl mt-2">R{expenseData.reduce((sum, item) => sum + item.value, 0).toLocaleString()}</p>
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
                <Tooltip />
                <Line type="monotone" dataKey="revenue" stroke="#3b82f6" strokeWidth={2} />
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
                <Tooltip />
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
                    <td className="p-3 border-b">{invoice.invoice_number || `INV-${invoice.id}`}</td>
                    <td className="p-3 border-b">{invoice.debtor_name || "N/A"}</td>
                    <td className="p-3 border-b">R{(invoice.total_amount || 0).toLocaleString("en-ZA", { maximumFractionDigits: 2 })}</td>
                    <td className="p-3 border-b">
                      {invoice.invoice_date
                        ? new Date(invoice.invoice_date).toLocaleDateString("en-ZA")
                        : "N/A"}
                    </td>
                    <td className="p-3 border-b">
                      <span
                        className={`px-2 py-1 rounded text-sm font-medium capitalize ${
                          invoice.status === "paid" || invoice.status === "Paid"
                            ? "bg-green-100 text-green-700"
                            : invoice.status === "pending" || invoice.status === "Pending"
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
            <div className="py-8 text-center text-gray-500">
              No data to display
            </div>
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
