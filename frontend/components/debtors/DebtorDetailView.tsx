'use client';

import React, { memo, useMemo, useCallback } from 'react';
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

const ACCOUNT_TYPES = {
  O: 'Open Item',
  C: 'Cash Customer',
  '': 'Balance Forward',
} as const;

/* ===========================
   Utility Functions
=========================== */

function formatCurrency(
  value: number | string | null | undefined,
  currency = '$',
  locale = 'en-US'
): string {
  if (value === null || value === undefined || value === '') {
    return `${currency}0.00`;
  }

  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return `${currency}0.00`;

  return `${currency}${num.toLocaleString(locale, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function normalizeFlag(flag: string | boolean | null | undefined): boolean {
  return flag === 'Y' || flag === true;
}

function formatDateTime(dateString: string | null | undefined): string {
  if (!dateString) return 'N/A';
  try {
    return new Date(dateString).toLocaleString();
  } catch {
    return 'Invalid Date';
  }
}

function getAccountType(acctype: string | null | undefined): string {
  if (!acctype) return ACCOUNT_TYPES[''];
  return ACCOUNT_TYPES[acctype as keyof typeof ACCOUNT_TYPES] ?? ACCOUNT_TYPES[''];
}

/* ===========================
   Memoized Subcomponents
=========================== */

interface DataFieldProps {
  label: string;
  value: string | number | null | undefined;
  fallback?: string;
  className?: string;
}

const DataField = memo(function DataField({
  label,
  value,
  fallback = 'Not provided',
  className = '',
}: DataFieldProps) {
  const display =
    value || value === 0 ? (
      <span>{value}</span>
    ) : (
      <span className="text-gray-400 italic">{fallback}</span>
    );

  return (
    <div className={className}>
      <dt className="text-sm text-gray-600 mb-1">{label}</dt>
      <dd className="font-medium">{display}</dd>
    </div>
  );
});

interface DataFieldWithIconProps extends DataFieldProps {
  icon: React.ReactNode;
}

const DataFieldWithIcon = memo(function DataFieldWithIcon({
  icon,
  label,
  value,
  fallback = 'Not provided',
}: DataFieldWithIconProps) {
  const display =
    value || value === 0 ? (
      <span>{value}</span>
    ) : (
      <span className="text-gray-400 italic">{fallback}</span>
    );

  return (
    <div className="flex items-center gap-3">
      <div className="text-gray-400">{icon}</div>
      <div>
        <dt className="text-sm text-gray-600">{label}</dt>
        <dd className="font-medium">{display}</dd>
      </div>
    </div>
  );
});

interface AddressCardProps {
  title: string;
  lines: (string | null | undefined)[];
  postalCode?: string | null;
}

const AddressCard = memo(function AddressCard({
  title,
  lines,
  postalCode,
}: AddressCardProps) {
  const filteredLines = useMemo(
    () => lines.filter((l) => l && l.trim()),
    [lines]
  );

  return (
    <Card className="p-6">
      <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <MapPin className="w-5 h-5" />
        {title}
      </h2>
      <address className="not-italic space-y-1 text-sm">
        {filteredLines.length ? (
          <>
            {filteredLines.map((line, index) => (
              <p key={index} className={index === 0 ? 'font-medium' : ''}>
                {line}
              </p>
            ))}
            {postalCode && <p className="font-semibold mt-2">{postalCode}</p>}
          </>
        ) : (
          <p className="text-gray-400 italic">No address provided</p>
        )}
      </address>
    </Card>
  );
});

/* ===========================
   Main Component
=========================== */

function DebtorDetailViewComponent({
  account,
  onEditClick,
}: DebtorDetailViewProps) {
  const handleEditClick = useCallback(() => {
    onEditClick?.();
  }, [onEditClick]);

  const derived = useMemo(() => {
    const isBlocked = normalizeFlag(account.blockflag);
    const isActive = normalizeFlag(account.is_active);
    const chargesInterest = normalizeFlag(account.dintflag);

    const totalBalance =
      typeof account.total_balance === 'number'
        ? account.total_balance
        : 0;

    const creditLimit =
      typeof account.dclimit === 'number'
        ? account.dclimit
        : 0;

    const availableCredit = creditLimit - totalBalance;

    const hasOverdueBalance =
      account.overdue_balance && account.overdue_balance > 0;

    return {
      isBlocked,
      isActive,
      chargesInterest,
      totalBalance,
      creditLimit,
      availableCredit,
      hasOverdueBalance,
      formattedCreditLimit: formatCurrency(account.dclimit),
      formattedAvailableCredit: formatCurrency(availableCredit),
      formattedTotalBalance: formatCurrency(account.total_balance),
      formattedOverdue: formatCurrency(account.overdue_balance),
    };
  }, [account]);

  const postalLines = useMemo(
    () => [account.dadd1, account.dadd2, account.dadd3],
    [account.dadd1, account.dadd2, account.dadd3]
  );

  const deliveryLines = useMemo(
    () => [account.delad1, account.delad2, account.delad3, account.delad4],
    [account.delad1, account.delad2, account.delad3, account.delad4]
  );

  if (!account) {
    return (
      <div className="p-8 text-center">
        <p className="text-red-600 font-semibold">
          Error: Account data is missing
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <header className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">
            {account.dname || 'Unnamed Account'}
          </h1>
          <p className="text-gray-600 mt-1">
            Account #: <span className="font-mono">{account.dno}</span>
          </p>
        </div>
        {onEditClick && (
          <Button onClick={handleEditClick}>
            Edit Account
          </Button>
        )}
      </header>

      <div className="flex gap-3 flex-wrap">
        <Badge className={derived.isBlocked ? 'bg-red-500' : 'bg-green-500'}>
          {derived.isBlocked ? 'Blocked' : 'Active'}
        </Badge>

        {derived.hasOverdueBalance && (
          <Badge variant="outline" className="border-red-500 text-red-700">
            Overdue Balance
          </Badge>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AddressCard
          title="Postal Address"
          lines={postalLines}
          postalCode={account.dpcode}
        />
        <AddressCard
          title="Delivery Address"
          lines={deliveryLines}
        />
      </div>

      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <CreditCard className="w-5 h-5" />
          Credit Information
        </h2>
        <div className="space-y-4">
          <div>
            <dt className="text-sm text-gray-600">Credit Limit</dt>
            <dd className="text-2xl font-bold">
              {derived.formattedCreditLimit}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-gray-600">Available Credit</dt>
            <dd className="text-xl font-semibold">
              {derived.formattedAvailableCredit}
            </dd>
          </div>
        </div>
      </Card>

      <Card className="p-6 bg-gray-50">
        <h2 className="text-sm font-semibold text-gray-600 mb-3 flex items-center gap-2">
          <Calendar className="w-4 h-4" />
          System Information
        </h2>
        <div className="text-xs text-gray-600 space-y-2">
          <div>
            Created: {formatDateTime(account.created_at)}
          </div>
          <div>
            Last Updated: {formatDateTime(account.updated_at)}
          </div>
        </div>
      </Card>
    </div>
  );
}

export default memo(DebtorDetailViewComponent);