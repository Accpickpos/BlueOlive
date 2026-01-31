"use client";
import { Card, CardContent } from "@/components/ui/card";

export default function LaybaysPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Laybays</h1>
      <p className="text-gray-600">Track laybays and payment schedules here.</p>

      <Card>
        <CardContent>
          <p className="text-gray-500">💳 Laybays table and form placeholder.</p>
        </CardContent>
      </Card>
    </div>
  );
}