"use client";
import { Card, CardContent } from "@/components/ui/card";

export default function JobCostingPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Job Costing</h1>
      <p className="text-gray-600">Manage job costing for services and projects.</p>

      <Card>
        <CardContent>
          <p className="text-gray-500">📊 Job costing table and calculation placeholder.</p>
        </CardContent>
      </Card>
    </div>
  );
}