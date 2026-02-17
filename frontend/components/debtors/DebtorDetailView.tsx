'use client';

import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Phone,
  Mail,
  MapPin,
  CreditCard,
  User,
  Building2,
  Calendar,
} from 'lucide-react';
import type { DebtorAccount } from '@/lib/types/debtors';

interface DebtorDetailViewProps {
  account: DebtorAccount;
  onEditClick?: () => void;
}

// Constants
const ACCOUNT_TYPES = {
  O: 'Open Item',
  C: 'Cash Customer',
  '': 'Balance Forward',
} as const;

// Utility Functions

/**
 * Formats a number as currency
 * @param value - The numeric value to format
 * @param currency - Currency symbol (default: '$')
 * @param locale - Locale for formatting (default: 'en-US')
 */
function formatCurrency(
  value: number | string | null | undefined,
  currency: string = '$',
  locale: string = 'en-US'
): string {
  if (value === null || value === undefined || value === '') {
    return `${currency}0.00`;
  }
  
  const num = typeof value === 'string' ? parseFloat(value) : value;
  
  if (isNaN(num)) {
    return `${currency}0.00`;
  }
  
  return `${currency}${num.toLocaleString(locale, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

/**
 * Normalizes boolean flags from API (handles 'Y'/'N' or true/false)
 */
function normalizeFlag(flag: string | boolean | null | undefined): boolean {
  if (flag === 'Y' || flag === true) return true;
  return false;
}

/**
 * Formats a date string to localized date/time
 */
function formatDateTime(dateString: string | null | undefined): string {
  if (!dateString) return 'N/A';
  
  try {
    return new Date(dateString).toLocaleString();
  } catch {
    return 'Invalid Date';
  }
}

/**
 * Gets account type display name
 */
function getAccountType(acctype: string | null | undefined): string {
  if (!acctype) return ACCOUNT_TYPES[''];
  return ACCOUNT_TYPES[acctype as keyof typeof ACCOUNT_TYPES] || ACCOUNT_TYPES[''];
}

// Reusable Components

interface DataFieldProps {
  label: string;
  value: string | number | null | undefined;
  fallback?: string;
  className?: string;
}

function DataField({ label, value, fallback = 'Not provided', className = '' }: DataFieldProps) {
  return (
    <div className={className}>
      <dt className="text-sm text-gray-600 mb-1">{label}</dt>
      <dd className="font-medium">
        {value || value === 0 ? (
          <span>{value}</span>
        ) : (
          <span className="text-gray-400 italic">{fallback}</span>
        )}
      </dd>
    </div>
  );
}

interface DataFieldWithIconProps extends DataFieldProps {
  icon: React.ReactNode;
}

function DataFieldWithIcon({ icon, label, value, fallback = 'Not provided' }: DataFieldWithIconProps) {
  return (
    <div className="flex items-center gap-3">
      <div className="text-gray-400" aria-hidden="true">
        {icon}
      </div>
      <div>
        <dt className="text-sm text-gray-600">{label}</dt>
        <dd className="font-medium">
          {value || value === 0 ? (
            <span>{value}</span>
          ) : (
            <span className="text-gray-400 italic">{fallback}</span>
          )}
        </dd>
      </div>
    </div>
  );
}

interface AddressCardProps {
  title: string;
  lines: (string | null | undefined)[];
  postalCode?: string | null;
}

function AddressCard({ title, lines, postalCode }: AddressCardProps) {
  const hasAddress = lines.some(line => line && line.trim());
  
  return (
    <Card className="p-6">
      <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <MapPin className="w-5 h-5" aria-hidden="true" />
        {title}
      </h2>
      <address className="not-italic space-y-1 text-sm">
        {hasAddress ? (
          <>
            {lines.map((line, index) => 
              line && line.trim() ? (
                <p key={index} className={index === 0 ? 'font-medium' : ''}>
                  {line}
                </p>
              ) : null
            )}
            {postalCode && (
              <p className="font-semibold mt-2">{postalCode}</p>
            )}
          </>
        ) : (
          <p className="text-gray-400 italic">No address provided</p>
        )}
      </address>
    </Card>
  );
}

// Main Component

export default function DebtorDetailView({
  account,
  onEditClick,
}: DebtorDetailViewProps) {
  // Validate required data
  if (!account) {
    return (
      <div className="p-8 text-center">
        <p className="text-red-600 font-semibold">Error: Account data is missing</p>
      </div>
    );
  }

  // Normalize flags
  const isBlocked = normalizeFlag(account.blockflag);
  const isActive = normalizeFlag(account.is_active);
  const chargesInterest = normalizeFlag(account.dintflag);
  
  // Calculate available credit
  const totalBalance = typeof account.total_balance === 'number' 
    ? account.total_balance 
    : 0;
  const creditLimit = typeof account.dclimit === 'number' 
    ? account.dclimit 
    : 0;
  const availableCredit = creditLimit - totalBalance;
  
  const hasOverdueBalance = account.overdue_balance && account.overdue_balance > 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <header className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4">
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl sm:text-3xl font-bold truncate">
            {account.dname || 'Unnamed Account'}
          </h1>
          <p className="text-gray-600 mt-1">
            Account #: <span className="font-mono">{account.dno || 'N/A'}</span>
          </p>
        </div>
        {onEditClick && (
          <Button
            onClick={onEditClick}
            className="bg-blue-600 hover:bg-blue-700 shrink-0"
          >
            Edit Account
          </Button>
        )}
      </header>

      {/* Status Bar */}
      <div className="flex gap-3 flex-wrap" role="status" aria-label="Account status">
        <Badge 
          className={isBlocked ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'}
          aria-label={isBlocked ? 'Account is blocked' : 'Account is active'}
        >
          {isBlocked ? 'Blocked' : 'Active'}
        </Badge>
        <Badge
          variant="outline"
          className={isActive ? 'border-green-500 text-green-700' : 'border-gray-400 text-gray-600'}
          aria-label={isActive ? 'Account is enabled' : 'Account is disabled'}
        >
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
          <User className="w-5 h-5" aria-hidden="true" />
          Contact Information
        </h2>
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <DataField label="Contact Person" value={account.dcontact} />
          <DataField label="Short Name" value={account.dsname} />
          <DataFieldWithIcon
            icon={<Phone className="w-5 h-5" />}
            label="Telephone"
            value={account.dtel}
          />
          <DataFieldWithIcon
            icon={<Mail className="w-5 h-5" />}
            label="Fax"
            value={account.dfax}
          />
        </dl>
      </Card>

      {/* Address Information */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AddressCard
          title="Postal Address"
          lines={[account.dadd1, account.dadd2, account.dadd3]}
          postalCode={account.dpcode}
        />
        <AddressCard
          title="Delivery Address"
          lines={[account.delad1, account.delad2, account.delad3, account.delad4]}
        />
      </div>

      {/* Account Settings */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Building2 className="w-5 h-5" aria-hidden="true" />
          Account Settings
        </h2>
        <dl className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <DataField 
            label="Account Type" 
            value={getAccountType(account.acctype)} 
          />
          <DataField 
            label="Price List" 
            value={`List ${account.price || 1}`} 
          />
          <DataField 
            label="Sales Area" 
            value={account.darea_name || account.darea?.toString() || '-'} 
          />
          <DataField 
            label="Trade Discount" 
            value={`${account.ddiscper || 0}%`} 
          />
          <DataField 
            label="Prompt Discount" 
            value={`${account.pdisc || 0}%`} 
          />
          <DataField 
            label="Payment Terms" 
            value={`${account.terms || 30} days`} 
          />
          <DataField 
            label="Charge Interest" 
            value={chargesInterest ? 'Yes' : 'No'} 
          />
          <DataField 
            label="Tax/VAT Number" 
            value={account.dtaxno} 
          />
        </dl>
      </Card>

      {/* Financial Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Credit Limit Card */}
        <Card className="p-6 bg-blue-50 border-blue-200">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <CreditCard className="w-5 h-5" aria-hidden="true" />
            Credit Information
          </h2>
          <dl className="space-y-4">
            <div>
              <dt className="text-sm text-gray-600 mb-1">Credit Limit</dt>
              <dd className="text-2xl sm:text-3xl font-bold text-blue-600">
                {formatCurrency(account.dclimit)}
              </dd>
            </div>
            <div>
              <dt className="text-sm text-gray-600 mb-1">Available Credit</dt>
              <dd className={`text-xl font-semibold ${
                availableCredit < 0 ? 'text-red-600' : 'text-blue-600'
              }`}>
                {formatCurrency(availableCredit)}
              </dd>
            </div>
          </dl>
        </Card>

        {/* Account Balance Card */}
        <Card className="p-6 bg-green-50 border-green-200">
          <h2 className="text-lg font-semibold mb-4">Account Balance</h2>
          <dl className="space-y-4">
            <div>
              <dt className="text-sm text-gray-600 mb-1">Current Balance</dt>
              <dd className="text-2xl sm:text-3xl font-bold text-green-600">
                {formatCurrency(account.total_balance)}
              </dd>
            </div>
            <div>
              <dt className="text-sm text-gray-600 mb-1">Overdue Balance</dt>
              <dd className={`text-xl font-semibold ${
                hasOverdueBalance ? 'text-red-600' : 'text-green-600'
              }`}>
                {formatCurrency(account.overdue_balance)}
              </dd>
            </div>
          </dl>
        </Card>
      </div>

      {/* Audit Information */}
      <Card className="p-6 bg-gray-50">
        <h2 className="text-sm font-semibold text-gray-600 mb-3 flex items-center gap-2">
          <Calendar className="w-4 h-4" aria-hidden="true" />
          System Information
        </h2>
        <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs text-gray-600">
          <div>
            <dt className="font-semibold inline">Created: </dt>
            <dd className="inline">{formatDateTime(account.created_at)}</dd>
          </div>
          <div>
            <dt className="font-semibold inline">Last Updated: </dt>
            <dd className="inline">{formatDateTime(account.updated_at)}</dd>
          </div>
        </dl>
      </Card>
    </div>
  );
}