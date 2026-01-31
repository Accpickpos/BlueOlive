"use client";
import { Card, CardContent } from "@/components/ui/card";

export default function CashSalePage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Cash Sales</h1>
      <p className="text-gray-600">Record and view all cash sales here.</p>

      <Card>
        <CardContent>
          <p className="text-gray-500">💵 Cash sales table or form will go here.</p>
        </CardContent>
      </Card>
    </div>
  );
}
