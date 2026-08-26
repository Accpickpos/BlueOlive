'use client';

import { User } from 'lucide-react';
import { useAuth } from '@/lib/useAuth';
import { usePOSAPI } from '@/lib/posApi';
import { SearchCombobox } from '@/components/ui/search-combobox';

interface DebtorLookupResult {
  account_number: number | string;
  name: string;
  balance: number;
  credit_limit: number;
}

interface DebtorPickerProps {
  onSelect: (debtor: {
    account_number: string;
    name: string;
    balance: number;
    credit_limit: number;
  }) => void;
  label?: string;
  placeholder?: string;
  disabled?: boolean;
}

/**
 * Thin wrapper around SearchCombobox for debtor/customer lookup — see
 * DebtorViewSet.lookup (backend/core/apps/debtors/views.py) for the
 * endpoint and DebtorLookupSerializer for the response shape.
 */
export function DebtorPicker({
  onSelect,
  label = 'Customer',
  placeholder = 'Search customers...',
  disabled = false,
}: DebtorPickerProps) {
  const { user } = useAuth();
  const posAPI = usePOSAPI(user?.tenant?.slug);

  return (
    <SearchCombobox<DebtorLookupResult>
      queryKeyPrefix="debtor-lookup"
      searchFn={(query) => posAPI.lookupDebtors(query)}
      getId={(debtor) => debtor.account_number}
      getLabel={(debtor) => debtor.name}
      renderOption={(debtor) => (
        <div className="flex items-center justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-gray-400 flex-shrink-0" />
              <span className="font-medium text-gray-900">{debtor.account_number}</span>
            </div>
            <p className="text-sm text-gray-500 truncate ml-6">{debtor.name}</p>
          </div>
          <div className="text-right ml-4 flex-shrink-0">
            <div className="font-medium text-red-600">R{Number(debtor.balance || 0).toFixed(2)}</div>
            <div className="text-xs text-gray-400">Balance</div>
          </div>
        </div>
      )}
      onSelect={(debtor) =>
        onSelect({
          account_number: String(debtor.account_number),
          name: debtor.name,
          balance: Number(debtor.balance || 0),
          credit_limit: Number(debtor.credit_limit || 0),
        })
      }
      label={label}
      placeholder={placeholder}
      disabled={disabled}
    />
  );
}

export default DebtorPicker;
