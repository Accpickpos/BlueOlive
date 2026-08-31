"use client";
import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Link from "next/link";
import { Eye } from "lucide-react";
import { useAuth } from "@/lib/useAuth";
import { usePOSAPI } from "@/lib/posApi";

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
  const { user, isLoading: authLoading } = useAuth();
  const posAPI = usePOSAPI(user?.tenant?.slug);
  const posAPIRef = useRef(posAPI);

  const [laybays, setLaybays] = useState<Layby[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    if (authLoading || !user) return;
    let cancelled = false;

    const fetchLaybays = async () => {
      setLoading(true);
      try {
        const response = await posAPIRef.current.listLaybyes();
        if (cancelled) return;

        const raw: any[] = Array.isArray(response) ? response : (response as any).results ?? [];
        setLaybays(
          raw.map((lb: any) => ({
            id: lb.id,
            reference: lb.laybye_number ?? String(lb.id),
            customer: lb.customer_name ?? "Unknown",
            total: Number(lb.total_amount ?? 0),
            paid: Number(lb.total_amount ?? 0) - Number(lb.balance_due ?? 0),
            outstanding: Number(lb.balance_due ?? 0),
            status: String(lb.status ?? "active").toLowerCase(),
          }))
        );
      } catch (error) {
        if (!cancelled) {
          console.error("Error fetching laybays:", error);
          setLaybays([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchLaybays();
    return () => { cancelled = true; };
  }, [user, authLoading]);

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
                    <th className="text-center py-2">View</th>
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
                      <td className="py-3 text-center">
                        <Link
                          href={`/dashboard/pos/laybays/${layby.id}`}
                          className="inline-flex items-center justify-center w-8 h-8 rounded-md border border-gray-200 text-gray-500 hover:border-blue-400 hover:text-blue-600"
                          aria-label={`View laybye ${layby.reference}`}
                        >
                          <Eye className="h-4 w-4" />
                        </Link>
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