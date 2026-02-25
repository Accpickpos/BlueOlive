'use client';

import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface GrossProfitDisplayProps {
  sellingPrice: number;
  costPrice: number;
  quantity: number;
  showPercentage?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function GrossProfitDisplay({
  sellingPrice,
  costPrice,
  quantity,
  showPercentage = true,
  size = 'md'
}: GrossProfitDisplayProps) {
  const totalSelling = sellingPrice * quantity;
  const totalCost = costPrice * quantity;
  const gp = totalSelling - totalCost;
  const gpPercent = totalSelling > 0 ? (gp / totalSelling) * 100 : 0;

  const isPositive = gp > 0;
  const isNeutral = gp === 0;

  const sizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base'
  };

  const iconSize = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5'
  };

  return (
    <div className={`flex items-center gap-1 ${sizeClasses[size]}`}>
      {isPositive && (
        <>
          <TrendingUp className={`${iconSize[size]} text-green-600`} />
          <span className="text-green-600 font-medium">
            GP: R{gp.toFixed(2)}
          </span>
        </>
      )}
      {isNeutral && (
        <>
          <Minus className={`${iconSize[size]} text-gray-400`} />
          <span className="text-gray-400">
            GP: R0.00
          </span>
        </>
      )}
      {isPositive === false && isNeutral === false && (
        <>
          <TrendingDown className={`${iconSize[size]} text-red-600`} />
          <span className="text-red-600 font-medium">
            GP: -R{Math.abs(gp).toFixed(2)}
          </span>
        </>
      )}
      
      {showPercentage && (
        <span className={`ml-1 ${isPositive ? 'text-green-500' : isNeutral ? 'text-gray-400' : 'text-red-500'}`}>
          ({gpPercent.toFixed(1)}%)
        </span>
      )}
    </div>
  );
}

// Compact version for table rows
export function GPBadge({ sellingPrice, costPrice, quantity = 1 }: { sellingPrice: number; costPrice: number; quantity?: number }) {
  const totalSelling = Number(sellingPrice) * Number(quantity);
  const totalCost = Number(costPrice) * Number(quantity);
  const gp = totalSelling - totalCost;
  const gpPercent = totalSelling > 0 ? (gp / totalSelling) * 100 : 0;

  if (gpPercent >= 20) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
        {gpPercent.toFixed(1)}%
      </span>
    );
  }
  
  if (gpPercent >= 10) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
        {gpPercent.toFixed(1)}%
      </span>
    );
  }
  
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
      {gpPercent.toFixed(1)}%
    </span>
  );
}

// Line item GP calculator
interface LineItemGPProps {
  sellingPrice: number;
  costPrice: number;
  quantity: number;
  discountPercent?: number;
}

export function LineItemGP({ sellingPrice, costPrice, quantity, discountPercent = 0 }: LineItemGPProps) {
  const lineTotal = Number(sellingPrice) * Number(quantity);
  const discount = (lineTotal * discountPercent) / 100;
  const afterDiscount = lineTotal - discount;
  const costTotal = Number(costPrice) * Number(quantity);
  const gp = afterDiscount - costTotal;
  const gpPercent = afterDiscount > 0 ? (gp / afterDiscount) * 100 : 0;

  return (
    <GrossProfitDisplay
      sellingPrice={sellingPrice - (sellingPrice * discountPercent / 100)}
      costPrice={costPrice}
      quantity={quantity}
      size="sm"
    />
  );
}

export default GrossProfitDisplay;
