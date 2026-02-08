'use client';

import React from 'react';

interface CategoryBadgeProps {
  categoryName: string;
  categoryCode?: string;
  type?: 'INCOME' | 'EXPENSE';
  className?: string;
}

export const CategoryBadge: React.FC<CategoryBadgeProps> = ({ 
  categoryName, 
  categoryCode,
  type = 'INCOME',
  className = '' 
}) => {
  const bgColor = type === 'INCOME' 
    ? 'bg-emerald-50 border-emerald-200' 
    : 'bg-rose-50 border-rose-200';
  
  const textColor = type === 'INCOME' 
    ? 'text-emerald-700' 
    : 'text-rose-700';

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border ${bgColor} ${textColor} text-sm ${className}`}>
      {categoryCode && (
        <span className="font-mono text-xs font-semibold opacity-75">
          {categoryCode}
        </span>
      )}
      <span className="font-medium truncate">
        {categoryName}
      </span>
    </div>
  );
};

export default CategoryBadge;
