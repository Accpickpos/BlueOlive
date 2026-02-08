'use client';

import React from 'react';
import { CheckCircle2, AlertCircle, Clock } from 'lucide-react';

interface ReconciliationStatusProps {
  status: 'RECONCILED' | 'PENDING' | 'VARIANCE';
  lastReconciliationDate?: string;
  varianceAmount?: number;
  className?: string;
}

export const ReconciliationStatus: React.FC<ReconciliationStatusProps> = ({
  status,
  lastReconciliationDate,
  varianceAmount,
  className = '',
}) => {
  const getStatusDisplay = () => {
    switch (status) {
      case 'RECONCILED':
        return {
          icon: CheckCircle2,
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          textColor: 'text-green-700',
          label: 'Reconciled',
          description: 'Account is balanced',
        };
      case 'PENDING':
        return {
          icon: Clock,
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
          textColor: 'text-yellow-700',
          label: 'Pending',
          description: 'Reconciliation in progress',
        };
      case 'VARIANCE':
        return {
          icon: AlertCircle,
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          textColor: 'text-red-700',
          label: 'Variance',
          description: 'Discrepancy detected',
        };
      default:
        return {
          icon: AlertCircle,
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
          textColor: 'text-gray-700',
          label: 'Unknown',
          description: 'Status unknown',
        };
    }
  };

  const display = getStatusDisplay();
  const Icon = display.icon;

  return (
    <div className={`${display.bgColor} border ${display.borderColor} rounded-lg p-4 ${className}`}>
      <div className="flex items-start gap-3">
        <Icon className={`w-5 h-5 ${display.textColor} flex-shrink-0 mt-0.5`} />
        <div className="flex-1">
          <h4 className={`font-semibold text-sm ${display.textColor}`}>
            {display.label}
          </h4>
          <p className={`text-xs ${display.textColor} opacity-75 mt-1`}>
            {display.description}
          </p>
          {lastReconciliationDate && (
            <p className={`text-xs ${display.textColor} opacity-60 mt-2`}>
              Last reconciled: {new Date(lastReconciliationDate).toLocaleDateString('en-ZA')}
            </p>
          )}
          {varianceAmount !== undefined && (
            <p className={`text-xs font-semibold ${display.textColor} mt-2`}>
              Variance: R{Math.abs(varianceAmount).toFixed(2)}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReconciliationStatus;
