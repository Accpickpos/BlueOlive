'use client';

import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import debtorsApi from '@/lib/debtorsApi';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Loader, Phone, Mail, MapPin, Building2, CreditCard, Calendar } from 'lucide-react';
import type { DebtorAccount } from '@/lib/types/debtors';

interface ViewAccountPageProps {
  params: {
    id: string;
  };
}

function formatCurrency(value: number | string | null | undefined, currency = '$') {
  if (value === null || value === undefined || value === '') return `${currency}0.00`;
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return `${currency}0.00`;
  return `${currency}${num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatDateTime(dateString: string | null | undefined) {
  if (!dateString) return 'N/A';
  try {
    return new Date(dateString).toLocaleString();
  } catch {
    return 'Invalid Date';
  }
}

/**
 * Normalizes a flag value that can be either a string ('Y') or boolean
 * to a consistent boolean value
 */
function normalizeFlag(flag: string | boolean | null | undefined): boolean {
  if (flag === 'Y' || flag === true) return true;
  return false;
}

function getAccountType(acctype: string | null | undefined) {
  const types: Record<string, string> = {
    'O': 'Open Item',
    'C': 'Cash Customer',
    '': 'Balance Forward',
  };
  return types[acctype || ''] || types[''];
}

export default function ViewAccountPage({ params }: ViewAccountPageProps) {
  const router = useRouter();
  const accountId = parseInt(params.id);

  const { data: account, isLoading } = useQuery({
    queryKey: ['debtor-account', accountId],
    queryFn: () => debtorsApi.accounts.get(accountId),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!account) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button 
            variant="outline" 
            onClick={() => router.back()} 
            size="sm"
          >
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <h1 className="text-2xl font-semibold">View Account</h1>
        </div>
        <div className="text-center text-gray-600 py-8">Account not found</div>
      </div>
    );
  }

  // Normalize flags using helper function
  const isBlocked = normalizeFlag(account.blockflag);
  const isActive = normalizeFlag(account.is_active);
  const chargesInterest = normalizeFlag(account.interest_flag);
  const totalBalance = typeof account.total_balance === 'number' ? account.total_balance : 0;
  const creditLimit = typeof account.dclimit === 'number' ? account.dclimit : 0;
  const availableCredit = creditLimit - totalBalance;
  const hasOverdueBalance = account.overdue_balance && account.overdue_balance > 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button 
          variant="outline" 
          onClick={() => router.back()} 
          size="sm"
        >
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold">{account.dname}</h1>
          <p className="text-gray-600 mt-1">Account #{account.dno}</p>
        </div>
      </div>

      {/* Status Bar */}
      <div className="flex gap-3 flex-wrap">
        <Badge className={isBlocked ? 'bg-red-500' : 'bg-green-500'}>
          {isBlocked ? 'Blocked' : 'Active'}
        </Badge>
        <Badge variant="outline" className={isActive ? 'border-green-500 text-green-700' : 'border-gray-400 text-gray-600'}>
          {isActive ? 'Enabled' : 'Disabled'}
        </Badge>
        {hasOverdueBalance && (
          <Badge variant="outline" className="border-red-500 text-red-700">
            Overdue Balance
          </Badge>
        )}
      </div>

      {/* Contact Information */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Phone className="w-5 h-5" />
          Contact Information
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <p className="text-sm text-gray-600">Contact Person</p>
            <p className="font-medium">{account.dcontact || 'Not provided'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Short Name</p>
            <p className="font-medium">{account.dsname || 'Not provided'}</p>
          </div>
          <div className="flex items-center gap-3">
            <Phone className="w-4 h-4 text-gray-400" />
            <div>
              <p className="text-sm text-gray-600">Telephone</p>
              <p className="font-medium">{account.dtel || 'Not provided'}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Mail className="w-4 h-4 text-gray-400" />
            <div>
              <p className="text-sm text-gray-600">Fax</p>
              <p className="font-medium">{account.dfax || 'Not provided'}</p>
            </div>
          </div>
        </div>
      </Card>

      {/* Address Information */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <MapPin className="w-5 h-5" />
            Postal Address
          </h3>
          <address className="not-italic space-y-1 text-sm">
            {account.dadd1 || account.dadd2 || account.dadd3 || account.dpcode ? (
              <>
                {account.dadd1 && <p className="font-medium">{account.dadd1}</p>}
                {account.dadd2 && <p>{account.dadd2}</p>}
                {account.dadd3 && <p>{account.dadd3}</p>}
                {account.dpcode && <p className="font-semibold mt-2">{account.dpcode}</p>}
              </>
            ) : (
              <p className="text-gray-400 italic">No address provided</p>
            )}
          </address>
        </Card>

        <Card className="p-6">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <MapPin className="w-5 h-5" />
            Delivery Address
          </h3>
          <address className="not-italic space-y-1 text-sm">
            {account.delad1 || account.delad2 || account.delad3 || account.delad4 ? (
              <>
                {account.delad1 && <p className="font-medium">{account.delad1}</p>}
                {account.delad2 && <p>{account.delad2}</p>}
                {account.delad3 && <p>{account.delad3}</p>}
                {account.delad4 && <p>{account.delad4}</p>}
              </>
            ) : (
              <p className="text-gray-400 italic">No address provided</p>
            )}
          </address>
        </Card>
      </div>

      {/* Account Settings */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Building2 className="w-5 h-5" />
          Account Settings
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <div>
            <p className="text-sm text-gray-600">Account Type</p>
            <p className="font-medium">{getAccountType(account.acctype)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Price List</p>
            <p className="font-medium">List {account.price || 1}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Sales Area</p>
            <p className="font-medium">{account.darea_name || '-'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Trade Discount</p>
            <p className="font-medium">{account.ddiscper || 0}%</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Prompt Discount</p>
            <p className="font-medium">{account.pdisc || 0}%</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Payment Terms</p>
            <p className="font-medium">{account.terms || 30} days</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Charge Interest</p>
            <p className="font-medium">{chargesInterest ? 'Yes' : 'No'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Tax/VAT Number</p>
            <p className="font-medium">{account.dtaxno || 'Not provided'}</p>
          </div>
        </div>
      </Card>

      {/* Financial Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-6 bg-blue-50 border-blue-200">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <CreditCard className="w-5 h-5" />
            Credit Information
          </h2>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-600 mb-1">Credit Limit</p>
              <p className="text-2xl sm:text-3xl font-bold text-blue-600">
                {formatCurrency(account.dclimit)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Available Credit</p>
              <p className={`text-xl font-semibold ${availableCredit < 0 ? 'text-red-600' : 'text-blue-600'}`}>
                {formatCurrency(availableCredit)}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-6 bg-green-50 border-green-200">
          <h2 className="text-lg font-semibold mb-4">Account Balance</h2>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-600 mb-1">Current Balance</p>
              <p className="text-2xl sm:text-3xl font-bold text-green-600">
                {formatCurrency(account.total_balance)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Overdue Balance</p>
              <p className={`text-xl font-semibold ${hasOverdueBalance ? 'text-red-600' : 'text-green-600'}`}>
                {formatCurrency(account.overdue_balance)}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Audit Information */}
      <Card className="p-6 bg-gray-50">
        <h2 className="text-sm font-semibold text-gray-600 mb-3 flex items-center gap-2">
          <Calendar className="w-4 h-4" />
          System Information
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs text-gray-600">
          <div>
            <span className="font-semibold">Created: </span>
            {formatDateTime(account.created_at)}
          </div>
          <div>
            <span className="font-semibold">Last Updated: </span>
            {formatDateTime(account.updated_at)}
          </div>
        </div>
      </Card>
    </div>
  );
}
