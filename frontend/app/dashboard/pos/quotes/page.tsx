"use client";
import { Card, CardContent } from "@/components/ui/card";

export default function QuotesPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Quotes</h1>
      <p className="text-gray-600">Create, view, and manage customer quotes.</p>

      <Card>
        <CardContent>
          <p className="text-gray-500">📝 Quotes table and form placeholder.</p>
        </CardContent>
      </Card>
    </div>
  );
}