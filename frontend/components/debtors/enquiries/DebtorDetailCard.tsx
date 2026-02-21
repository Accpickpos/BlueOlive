'use client';

import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { DebtorAccount } from '@/lib/types/debtors';

interface DebtorDetailCardProps {
  debtor: DebtorAccount;
}

export default function DebtorDetailCard({ debtor }: DebtorDetailCardProps) {
  return (
    <div className="space-y-4">
      {/* Header Card */}
      <Card className="p-6 border-l-4 border-l-blue-600">
        <div className="flex justify-between items-start mb-4">
          <div>
            <p className="text-sm text-gray-600">Account Number</p>
            <h2 className="text-2xl font-bold">{debtor.customer_number}</h2>
          </div>
          <div className="flex gap-2">
            {debtor.block_flag && <Badge className="bg-red-500">Blocked</Badge>}
            <Badge className={debtor.is_active ? 'bg-green-500' : 'bg-gray-500'}>
              {debtor.is_active ? 'Active' : 'Inactive'}
            </Badge>
          </div>
        </div>
        <h3 className="text-lg font-semibold">{debtor.name}</h3>
        {debtor.short_name && <p className="text-sm text-gray-600">({debtor.short_name})</p>}
      </Card>

      {/* Contact Information */}
      <Card className="p-4">
        <h3 className="text-sm font-bold mb-3 text-gray-700">Contact Information</h3>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-gray-600">Contact Person</p>
            <p className="font-medium">{debtor.contact_person || '-'}</p>
          </div>
          <div>
            <p className="text-gray-600">Email</p>
            <p className="font-medium">{debtor.email || '-'}</p>
          </div>
          <div>
            <p className="text-gray-600">Telephone</p>
            <p className="font-medium">{debtor.phone || '-'}</p>
          </div>
          <div>
            <p className="text-gray-600">Fax</p>
            <p className="font-medium">{debtor.fax || '-'}</p>
          </div>
        </div>
      </Card>

      {/* Address Information */}
      <Card className="p-4">
        <h3 className="text-sm font-bold mb-3 text-gray-700">Postal Address</h3>
        <div className="text-sm text-gray-600 space-y-1">
          {debtor.address_line1 && <p>{debtor.address_line1}</p>}
          {debtor.address_line2 && <p>{debtor.address_line2}</p>}
          {debtor.address_line3 && <p>{debtor.address_line3}</p>}
        </div>
      </Card>

      {/* Business Information */}
      <Card className="p-4">
        <h3 className="text-sm font-bold mb-3 text-gray-700">Business Information</h3>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-gray-600">Account Type</p>
            <p className="font-medium">
              {debtor.account_type === 'B' ? 'Balance Forward' : debtor.account_type === 'O' ? 'Open Item' : 'Cash Sale'}
            </p>
          </div>
          <div>
            <p className="text-gray-600">Sales Area</p>
            <p className="font-medium">{debtor.area_code || '-'}</p>
          </div>
          <div>
            <p className="text-gray-600">Tax/VAT Number</p>
            <p className="font-medium">{debtor.tax_number || '-'}</p>
          </div>
          <div>
            <p className="text-gray-600">Price List</p>
            <p className="font-medium">List {debtor.price_level || 1}</p>
          </div>
        </div>
      </Card>

      {/* Sales Performance */}
      <Card className="p-4">
        <h3 className="text-sm font-bold mb-3 text-gray-700">Sales Performance</h3>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-gray-600">Sales MTD</p>
            <p className="font-bold text-blue-600">${debtor.sales_month?.toLocaleString('en-US', { maximumFractionDigits: 0 })}</p>
          </div>
          <div>
            <p className="text-gray-600">Sales YTD</p>
            <p className="font-bold text-blue-600">${debtor.sales_year?.toLocaleString('en-US', { maximumFractionDigits: 0 })}</p>
          </div>
          <div>
            <p className="text-gray-600">Profit MTD</p>
            <p className="font-bold text-green-600">${debtor.profit_month?.toLocaleString('en-US', { maximumFractionDigits: 0 })}</p>
          </div>
          <div>
            <p className="text-gray-600">Profit YTD</p>
            <p className="font-bold text-green-600">${debtor.profit_year?.toLocaleString('en-US', { maximumFractionDigits: 0 })}</p>
          </div>
        </div>
      </Card>

      {/* Last Payment */}
      <Card className="p-4">
        <h3 className="text-sm font-bold mb-3 text-gray-700">Payment History</h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <p className="text-gray-600">Last Payment Amount</p>
            <p className="font-bold">${debtor.last_payment_amount?.toLocaleString('en-US', { maximumFractionDigits: 2 })}</p>
          </div>
          <div className="flex justify-between">
            <p className="text-gray-600">Last Payment Date</p>
            <p className="font-medium">
              {debtor.last_payment_date ? new Date(debtor.last_payment_date).toLocaleDateString() : '-'}
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
