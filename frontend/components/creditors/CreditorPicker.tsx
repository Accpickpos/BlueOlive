'use client';

import { CreditCard } from 'lucide-react';
import { creditorsApi } from '@/lib/creditorsApi';
import type { CreditorAccount } from '@/lib/types/creditors';
import { SearchCombobox } from '@/components/ui/search-combobox';

interface CreditorPickerProps {
  onSelect: (creditor: {
    id: number;
    account_number: string;
    name: string;
    balance: number;
  }) => void;
  label?: string;
  placeholder?: string;
  disabled?: boolean;
}

/**
 * Thin wrapper around SearchCombobox for creditor/supplier lookup — see
 * CreditorViewSet.lookup (backend/core/apps/creditors/views.py) for the
 * endpoint (CreditorListSerializer response shape). Same pattern as
 * DebtorPicker/StockItemPicker so supplier search behaves identically to
 * customer/stock search everywhere it's used (Creditors module, Purchase
 * Orders supplier selection, etc).
 */
export function CreditorPicker({
  onSelect,
  label = 'Supplier',
  placeholder = 'Search suppliers...',
  disabled = false,
}: CreditorPickerProps) {
  return (
    <SearchCombobox<CreditorAccount>
      queryKeyPrefix="creditor-lookup"
      searchFn={(query, offset) => creditorsApi.accounts.lookup(query, 20, offset)}
      getId={(creditor) => creditor.id}
      getLabel={(creditor) => creditor.name}
      renderOption={(creditor) => (
        <div className="flex items-center justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <CreditCard className="h-4 w-4 text-gray-400 flex-shrink-0" />
              <span className="font-medium text-gray-900">{creditor.supplier_number}</span>
              <span className="text-gray-500 truncate">{creditor.name}</span>
            </div>
          </div>
          <div className="text-right ml-4 flex-shrink-0">
            <div
              className={`font-medium ${
                (creditor.total_outstanding_balance || 0) > 0 ? 'text-red-600' : 'text-green-600'
              }`}
            >
              R{Number(creditor.total_outstanding_balance || 0).toFixed(2)}
            </div>
          </div>
        </div>
      )}
      onSelect={(creditor) =>
        onSelect({
          id: creditor.id,
          account_number: creditor.supplier_number,
          name: creditor.name,
          balance: Number(creditor.total_outstanding_balance || 0),
        })
      }
      label={label}
      placeholder={placeholder}
      disabled={disabled}
    />
  );
}

export default CreditorPicker;
