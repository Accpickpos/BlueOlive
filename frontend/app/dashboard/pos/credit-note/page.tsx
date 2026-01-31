"use client";
import { Card, CardContent } from "@/components/ui/card";

export default function CreditNotePage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Credit Notes</h1>
      <p className="text-gray-600">Create and manage credit notes here.</p>

      <Card>
        <CardContent>
          <p className="text-gray-500">📝 Credit note form and list placeholder.</p>
        </CardContent>
      </Card>
    </div>
  );
}
