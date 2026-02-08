"use client";
import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Link from "next/link";

interface Layby {
  id: number;
  reference: string;
  customer: string;
  total: number;
  paid: number;
  outstanding: number;
  status: string;
}

export default function LaybaysPage() {
  const [laybays, setLaybays] = useState<Layby[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    fetchLaybays();
  }, []);

  const fetchLaybays = async () => {
    setLoading(true);
    try {
      setTimeout(() => {
        setLaybays([
          { id: 1, reference: "LAY-001", customer: "John Smith", total: 2500.00, paid: 1000.00, outstanding: 1500.00, status: "active" },
          { id: 2, reference: "LAY-002", customer: "ABC Corp", total: 1800.00, paid: 1800.00, outstanding: 0, status: "completed" },
          { id: 3, reference: "LAY-003", customer: "Tech Solutions", total: 5000.00, paid: 2000.00, outstanding: 3000.00, status: "active" },
        ]);
      }, 300);
    } catch (error) {
      console.error("Error fetching laybays:", error);
    } finally {
      setTimeout(() => setLoading(false), 400);
    }
  };

  const filteredLaybays = laybays.filter((layby) =>
    layby.reference.toLowerCase().includes(searchTerm.toLowerCase()) ||
    layby.customer.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Laybays</h1>
        <Link href="/dashboard/pos/laybays/create">
          <Button className="bg-blue-600 hover:bg-blue-700">New Layby</Button>
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Laybay Orders</CardTitle>
        </CardHeader>
        <CardContent>
          <Input
            type="text"
            placeholder="Search by reference or customer..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="mb-4"
          />
          {filteredLaybays.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">Reference</th>
                    <th className="text-left py-2">Customer</th>
                    <th className="text-right py-2">Total</th>
                    <th className="text-right py-2">Paid</th>
                    <th className="text-right py-2">Outstanding</th>
                    <th className="text-left py-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredLaybays.map((layby) => (
                    <tr key={layby.id} className="border-b hover:bg-gray-50">
                      <td className="py-3 font-medium">{layby.reference}</td>
                      <td className="py-3">{layby.customer}</td>
                      <td className="py-3 text-right">R{layby.total.toFixed(2)}</td>
                      <td className="py-3 text-right text-green-600">R{layby.paid.toFixed(2)}</td>
                      <td className="py-3 text-right text-red-600">R{layby.outstanding.toFixed(2)}</td>
                      <td className="py-3">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          layby.status === "completed" ? "bg-green-100 text-green-800" : "bg-blue-100 text-blue-800"
                        }`}>
                          {layby.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">No laybays found</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}