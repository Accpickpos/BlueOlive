'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import ReceiptForm from '@/components/debtors/forms/ReceiptForm';
import OpenItemsList from '@/components/debtors/transactions/OpenItemsList';

export default function ReceiptsPage() {
  const [debtorId, setDebtorId] = useState<number | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Receipt Posting</h1>
        <p className="text-gray-600 mt-1">Record and allocate customer payments</p>
      </div>

      <Tabs defaultValue="post" className="w-full">
        <TabsList className="grid w-full grid-cols-2 mb-6">
          <TabsTrigger value="post">Post Receipt</TabsTrigger>
          <TabsTrigger value="allocate">Allocate Payments</TabsTrigger>
        </TabsList>

        {/* Post Receipt Tab */}
        <TabsContent value="post">
          <Card className="p-6 space-y-4">
            <h2 className="text-lg font-bold">Record Customer Payment</h2>
            <ReceiptForm
              onSuccess={() => setRefreshTrigger((prev) => prev + 1)}
            />
          </Card>
        </TabsContent>

        {/* Allocate Payments Tab */}
        <TabsContent value="allocate">
          <Card className="p-6 space-y-4">
            <h2 className="text-lg font-bold">Allocate to Open Items</h2>
            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">Select Debtor</label>
              <Input
                type="number"
                placeholder="Enter debtor ID"
                onChange={(e) => setDebtorId(e.target.value ? parseInt(e.target.value) : null)}
              />
            </div>
            {debtorId && (
              <OpenItemsList
                debtorId={debtorId}
                refreshTrigger={refreshTrigger}
              />
            )}
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
