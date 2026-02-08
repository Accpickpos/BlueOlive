'use client';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

export default function PricesPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/dashboard/admin/stock-control">
          <Button variant="outline" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold">Prices</h1>
          <p className="text-gray-600 mt-1">Cost and selling price management</p>
        </div>
      </div>

      <Card className="p-12 text-center">
        <p className="text-gray-600">Prices page coming soon...</p>
      </Card>
    </div>
  );
}
