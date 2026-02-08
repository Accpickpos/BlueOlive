'use client';

import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface BalanceCardProps {
  title: string;
  amount: number;
  currency?: string;
  variant?: 'default' | 'income' | 'expense' | 'balance';
  trend?: number; // percentage change
  subtitle?: string;
  className?: string;
  padding?: string;
}

export const BalanceCard: React.FC<BalanceCardProps> = ({
  title,
  amount,
  currency = 'R',
  variant = 'default',
  trend,
  subtitle,
  className = '',
  padding = 'p-6',
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'income':
        return 'bg-gradient-to-br from-green-50 to-emerald-50 border-emerald-200';
      case 'expense':
        return 'bg-gradient-to-br from-red-50 to-rose-50 border-red-200';
      case 'balance':
        return 'bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-200';
      default:
        return 'bg-white border-gray-200';
    }
  };

  const getTextColor = () => {
    switch (variant) {
      case 'income':
        return 'text-emerald-900';
      case 'expense':
        return 'text-rose-900';
      case 'balance':
        return 'text-blue-900';
      default:
        return 'text-gray-900';
    }
  };

  const getTitleColor = () => {
    switch (variant) {
      case 'income':
        return 'text-emerald-700';
      case 'expense':
        return 'text-rose-700';
      case 'balance':
        return 'text-blue-700';
      default:
        return 'text-gray-600';
    }
  };

  const formatAmount = (value: number) => {
    return new Intl.NumberFormat('en-ZA', {
      style: 'currency',
      currency: 'ZAR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  return (
    <div className={`${padding} rounded-lg border ${getVariantStyles()} shadow-sm ${className}`}>
      <div className="flex items-start justify-between mb-4">
        <h3 className={`text-sm font-medium ${getTitleColor()}`}>
          {title}
        </h3>
        {trend !== undefined && (
          <div className={`flex items-center gap-1 text-sm font-semibold ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {trend >= 0 ? (
              <TrendingUp className="w-4 h-4" />
            ) : (
              <TrendingDown className="w-4 h-4" />
            )}
            {Math.abs(trend)}%
          </div>
        )}
      </div>

      <div className={`${getTextColor()} mb-2`}>
        <p className="text-3xl font-bold">
          {formatAmount(amount)}
        </p>
      </div>

      {subtitle && (
        <p className={`text-xs ${getTitleColor()} opacity-75`}>
          {subtitle}
        </p>
      )}
    </div>
  );
};

export default BalanceCard;
