"use client";
import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAuth } from "@/lib/useAuth";
import { jobCardsApi } from "@/lib/jobCardsApi";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Edit, Eye } from "lucide-react";

interface Job {
  id: number;
  job_number: string;
  customer_name: string;
  subtotal: number;
  total_amount: number;
  status: string;
  job_date: string;
}

interface Job {
  id: number;
  job_number: string;
  customer_name: string;
  total_amount: number;
  status: string;
  job_date: string;
}

export default function JobCostingPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const response = await jobCardsApi.list({ limit: 100 });
      // Map backend data to frontend interface
      const mappedJobs = response.results.map((job: any) => ({
        id: job.id,
        job_number: job.job_number,
        customer_name: job.customer_name,
        subtotal: parseFloat(job.subtotal) || 0,
        total_amount: parseFloat(job.total_amount) || 0,
        status: job.status,
        job_date: job.job_date
      }));
      setJobs(mappedJobs);
    } catch (error) {
      console.error("Error fetching jobs:", error);
      setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (jobId: number, newStatus: string) => {
    try {
      await jobCardsApi.updateStatus(jobId, newStatus);
      // Refresh the list
      fetchJobs();
    } catch (error) {
      console.error("Error updating status:", error);
    }
  };

  const filteredJobs = jobs.filter((job) =>
    job.job_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    job.customer_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Job Costing</h1>
        <Link href="/dashboard/pos/job-costing/create">
          <Button className="bg-blue-600 hover:bg-blue-700">New Job</Button>
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Active Jobs</CardTitle>
        </CardHeader>
        <CardContent>
          <Input
            type="text"
            placeholder="Search by job number or customer..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="mb-4"
          />
          {filteredJobs.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">Job #</th>
                    <th className="text-left py-2">Customer</th>
                    <th className="text-right py-2">Subtotal</th>
                    <th className="text-right py-2">Total</th>
                    <th className="text-left py-2">Status</th>
                    <th className="text-left py-2">Date</th>
                    <th className="text-left py-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredJobs.map((job) => (
                    <tr key={job.id} className="border-b hover:bg-gray-50">
                      <td className="py-3 font-medium">{job.job_number}</td>
                      <td className="py-3">{job.customer_name}</td>
                      <td className="py-3 text-right">R{job.subtotal.toFixed(2)}</td>
                      <td className="py-3 text-right font-medium">R{job.total_amount.toFixed(2)}</td>
                      <td className="py-3">
                        <select
                          value={job.status}
                          onChange={(e) => handleStatusChange(job.id, e.target.value)}
                          className={`px-2 py-1 rounded-full text-xs font-medium border-0 cursor-pointer ${
                            job.status === "COMPLETED" || job.status === "CONVERTED_TO_INVOICE" ? "bg-green-100 text-green-800" :
                            job.status === "IN_PROGRESS" ? "bg-blue-100 text-blue-800" :
                            "bg-yellow-100 text-yellow-800"
                          }`}
                        >
                          <option value="ACTIVE">Active</option>
                          <option value="IN_PROGRESS">In Progress</option>
                          <option value="COMPLETED">Completed</option>
                          <option value="CONVERTED_TO_INVOICE">Converted to Invoice</option>
                          <option value="CANCELLED">Cancelled</option>
                        </select>
                      </td>
                      <td className="py-3">{job.job_date}</td>
                      <td className="py-3">
                        <div className="flex gap-2">
                          <Link href={`/dashboard/pos/job-costing/${job.id}`}>
                            <Button variant="ghost" size="sm">
                              <Eye className="w-4 h-4" />
                            </Button>
                          </Link>
                          <Link href={`/dashboard/pos/job-costing/${job.id}/edit`}>
                            <Button variant="ghost" size="sm">
                              <Edit className="w-4 h-4" />
                            </Button>
                          </Link>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">No jobs found</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}