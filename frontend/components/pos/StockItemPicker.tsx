'use client';

import { Package } from 'lucide-react';
import { stockControlApi } from '@/lib/stockControlApi';
import type { StockItem } from '@/lib/types/stockControl';
import { SearchCombobox } from '@/components/ui/search-combobox';

interface StockItemPickerProps {
  onSelect: (item: {
    stock_code: string;
    description: string;
    selling_price: number;
    cost_price: number;
    tax_code: string | number;
    tax_code_detail?: { code: string; rate?: number };
  }) => void;
  label?: string;
  placeholder?: string;
  disabled?: boolean;
}

/**
 * Thin wrapper around SearchCombobox for stock-item/line-item lookup — see
 * StockItemViewSet.lookup (backend/core/apps/stock_control/views.py) for
 * the endpoint (StockItemListSerializer response shape).
 */
export function StockItemPicker({
  onSelect,
  label = 'Stock Item',
  placeholder = 'Search stock items...',
  disabled = false,
}: StockItemPickerProps) {
  return (
    <SearchCombobox<StockItem>
      queryKeyPrefix="stock-item-lookup"
      searchFn={(query) => stockControlApi.stockItems.lookup(query)}
      getId={(item) => item.stock_code}
      getLabel={(item) => item.stock_code}
      renderOption={(item) => (
        <div className="flex items-center justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <Package className="h-4 w-4 text-gray-400 flex-shrink-0" />
              <span className="font-medium text-gray-900">{item.stock_code}</span>
              {item.barcode && <span className="text-xs text-gray-400">({item.barcode})</span>}
            </div>
            <p className="text-sm text-gray-500 truncate ml-6">{item.description}</p>
          </div>
          <div className="text-right ml-4 flex-shrink-0">
            <div className="font-medium text-green-600">R{Number(item.selling_price_1 || 0).toFixed(2)}</div>
            <div className="text-xs text-gray-400">
              Cost: R{Number(item.average_cost || item.cost_price || 0).toFixed(2)}
            </div>
          </div>
        </div>
      )}
      onSelect={(item) =>
        onSelect({
          stock_code: item.stock_code,
          description: item.description,
          selling_price: Number(item.selling_price_1 || 0),
          cost_price: Number(item.average_cost || item.cost_price || 0),
          tax_code: String(item.tax_code),
          tax_code_detail: item.tax_code_detail,
        })
      }
      label={label}
      placeholder={placeholder}
      disabled={disabled}
    />
  );
}

export default StockItemPicker;
