'use client';

import React from 'react';

interface TransactionTypeBadgeProps {
  type: 'INCOME' | 'EXPENSE' | 'DEPOSIT' | 'WITHDRAWAL' | 'TRANSFER' | 'CHARGE' | 'INTEREST';
  className?: string;
}

export const TransactionTypeBadge: React.FC<TransactionTypeBadgeProps> = ({ 
  type, 
  className = '' 
}) => {
  const getStyles = () => {
    switch (type) {
      case 'INCOME':
        return 'bg-green-100 text-green-800 border border-green-300';
      case 'EXPENSE':
        return 'bg-red-100 text-red-800 border border-red-300';
      case 'DEPOSIT':
        return 'bg-blue-100 text-blue-800 border border-blue-300';
      case 'WITHDRAWAL':
        return 'bg-orange-100 text-orange-800 border border-orange-300';
      case 'TRANSFER':
        return 'bg-purple-100 text-purple-800 border border-purple-300';
      case 'CHARGE':
        return 'bg-red-100 text-red-800 border border-red-300';
      case 'INTEREST':
        return 'bg-green-100 text-green-800 border border-green-300';
      default:
        return 'bg-gray-100 text-gray-800 border border-gray-300';
    }
  };

  return (
    <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${getStyles()} ${className}`}>
      {type}
    </span>
  );
};

export default TransactionTypeBadge;
