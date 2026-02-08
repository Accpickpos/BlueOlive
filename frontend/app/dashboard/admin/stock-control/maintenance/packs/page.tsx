'use client';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

export default function PacksPage() {
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
          <h1 className="text-3xl font-bold">Packs/Bundles</h1>
          <p className="text-gray-600 mt-1">Finished goods and recipes</p>
        </div>
      </div>

      <Card className="p-12 text-center">
        <p className="text-gray-600">Packs/Bundles page coming soon...</p>
      </Card>
    </div>
  );
}
