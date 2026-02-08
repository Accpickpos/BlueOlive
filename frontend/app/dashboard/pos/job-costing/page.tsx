"use client";
import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import Link from "next/link";

interface Job {
  id: number;
  job_number: string;
  customer: string;
  estimate: number;
  actual: number;
  status: string;
  start_date: string;
}

export default function JobCostingPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      setTimeout(() => {
        setJobs([
          { id: 1, job_number: "JOB-001", customer: "Acme Corp", estimate: 5000.00, actual: 4800.00, status: "completed", start_date: "2025-01-15" },
          { id: 2, job_number: "JOB-002", customer: "XYZ Ltd", estimate: 3500.00, actual: 3200.00, status: "invoiced", start_date: "2025-01-20" },
          { id: 3, job_number: "JOB-003", customer: "Tech Solutions", estimate: 2000.00, actual: 0, status: "open", start_date: "2025-02-01" },
        ]);
      }, 300);
    } catch (error) {
      console.error("Error fetching jobs:", error);
    } finally {
      setTimeout(() => setLoading(false), 400);
    }
  };

  const filteredJobs = jobs.filter((job) =>
    job.job_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    job.customer.toLowerCase().includes(searchTerm.toLowerCase())
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
                    <th className="text-right py-2">Estimate</th>
                    <th className="text-right py-2">Actual</th>
                    <th className="text-right py-2">Variance</th>
                    <th className="text-left py-2">Status</th>
                    <th className="text-left py-2">Start Date</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredJobs.map((job) => (
                    <tr key={job.id} className="border-b hover:bg-gray-50">
                      <td className="py-3 font-medium">{job.job_number}</td>
                      <td className="py-3">{job.customer}</td>
                      <td className="py-3 text-right">R{job.estimate.toFixed(2)}</td>
                      <td className="py-3 text-right">R{job.actual.toFixed(2)}</td>
                      <td className="py-3 text-right font-medium">
                        <span className={job.estimate - job.actual >= 0 ? "text-green-600" : "text-red-600"}>
                          R{(job.estimate - job.actual).toFixed(2)}
                        </span>
                      </td>
                      <td className="py-3">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          job.status === "completed" ? "bg-green-100 text-green-800" :
                          job.status === "invoiced" ? "bg-blue-100 text-blue-800" :
                          "bg-yellow-100 text-yellow-800"
                        }`}>
                          {job.status}
                        </span>
                      </td>
                      <td className="py-3">{job.start_date}</td>
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