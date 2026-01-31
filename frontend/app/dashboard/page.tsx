"use client";
import { Card, CardContent } from "@/components/ui/card";
import ProtectedRoute from "@/components/ProtectedRoute";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from "recharts";

const revenueData = [
  { month: "Jan", revenue: 4000 },
  { month: "Feb", revenue: 3200 },
  { month: "Mar", revenue: 4500 },
  { month: "Apr", revenue: 5000 },
  { month: "May", revenue: 6100 },
];

const expenseData = [
  { category: "Salaries", value: 3000 },
  { category: "Rent", value: 1200 },
  { category: "Utilities", value: 800 },
  { category: "Supplies", value: 500 },
];

const invoiceTable = [
  { id: "INV-001", client: "Acme Corp", amount: "R2,400", status: "Paid" },
  { id: "INV-002", client: "Globex", amount: "R1,800", status: "Pending" },
  { id: "INV-003", client: "Initech", amount: "R3,200", status: "Overdue" },
];

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444"];

function DashboardContent() {
  return (
    <div className="grid grid-cols-3 gap-6">
      {/* KPI Cards */}
      <Card>
        <CardContent className="p-6">
          <h2 className="text-lg font-semibold">Total Revenue</h2>
          <p className="text-2xl mt-2">R25,400</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-6">
          <h2 className="text-lg font-semibold">Outstanding Invoices</h2>
          <p className="text-2xl mt-2">12</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-6">
          <h2 className="text-lg font-semibold">Expenses This Month</h2>
          <p className="text-2xl mt-2">R4,820</p>
        </CardContent>
      </Card>

      {/* Revenue Chart */}
      <Card className="col-span-2">
        <CardContent className="p-6">
          <h2 className="text-lg font-semibold mb-4">Revenue Trend</h2>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={revenueData}>
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="revenue" stroke="#3b82f6" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Expenses Breakdown */}
      <Card>
        <CardContent className="p-6">
          <h2 className="text-lg font-semibold mb-4">Expense Breakdown</h2>
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
        </CardContent>
      </Card>

      {/* Invoice Table */}
      <Card className="col-span-3">
        <CardContent className="p-6">
          <h2 className="text-lg font-semibold mb-4">Recent Invoices</h2>
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gray-100 text-left">
                <th className="p-3 border-b">Invoice #</th>
                <th className="p-3 border-b">Client</th>
                <th className="p-3 border-b">Amount</th>
                <th className="p-3 border-b">Status</th>
              </tr>
            </thead>
            <tbody>
              {invoiceTable.map((invoice) => (
                <tr key={invoice.id} className="hover:bg-gray-50">
                  <td className="p-3 border-b">{invoice.id}</td>
                  <td className="p-3 border-b">{invoice.client}</td>
                  <td className="p-3 border-b">{invoice.amount}</td>
                  <td className="p-3 border-b">
                    <span
                      className={`px-2 py-1 rounded text-sm font-medium ${
                        invoice.status === "Paid"
                          ? "bg-green-100 text-green-700"
                          : invoice.status === "Pending"
                          ? "bg-yellow-100 text-yellow-700"
                          : "bg-red-100 text-red-700"
                      }`}
                    >
                      {invoice.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
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
