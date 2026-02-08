'use client';

import React, { useState } from 'react';
import {
  RefreshCw,
  FileText,
  Download,
  Upload,
  Clock,
  AlertTriangle,
  CheckCircle,
  Trash2,
  ArrowLeft,
} from 'lucide-react';
import Link from 'next/link';

interface UtilityTask {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  action: string;
  color: 'blue' | 'yellow' | 'red' | 'green';
}

const UTILITY_TASKS: UtilityTask[] = [
  {
    id: 'recalculate-totals',
    name: 'Recalculate Order Totals',
    description: 'Recalculate VAT and totals for all orders based on current items',
    icon: <RefreshCw className="w-6 h-6" />,
    action: 'recalculate',
    color: 'blue',
  },
  {
    id: 'validate-orders',
    name: 'Validate Orders',
    description: 'Check for incomplete or invalid order data',
    icon: <CheckCircle className="w-6 h-6" />,
    action: 'validate',
    color: 'green',
  },
  {
    id: 'stuck-orders',
    name: 'Find Stuck Orders',
    description: 'Identify orders stuck in pending status for extended periods',
    icon: <Clock className="w-6 h-6" />,
    action: 'stuck-orders',
    color: 'yellow',
  },
  {
    id: 'orphan-items',
    name: 'Orphan Items Report',
    description: 'Find line items with missing or invalid supplier references',
    icon: <AlertTriangle className="w-6 h-6" />,
    action: 'orphan-items',
    color: 'red',
  },
  {
    id: 'bulk-update',
    name: 'Bulk Update Status',
    description: 'Update status for multiple orders at once',
    icon: <Upload className="w-6 h-6" />,
    action: 'bulk-update',
    color: 'blue',
  },
  {
    id: 'data-export',
    name: 'Export All Orders',
    description: 'Export complete order data for backup or analysis',
    icon: <Download className="w-6 h-6" />,
    action: 'export',
    color: 'green',
  },
];

export default function UtilitiesPage() {
  const [selectedTask, setSelectedTask] = useState<string | null>(null);
  const [executing, setExecuting] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleExecuteTask = async (taskId: string) => {
    setExecuting(true);
    // Simulated task execution - replace with actual API calls
    setTimeout(() => {
      setResult({
        taskId,
        status: 'success',
        timestamp: new Date().toISOString(),
        details: {
          'recalculate': {
            message: 'Recalculation completed',
            ordersProcessed: 24,
            timeElapsed: '2.5s',
          },
          'validate': {
            message: 'Validation completed',
            validOrders: 22,
            invalidOrders: 2,
          },
          'stuck-orders': {
            message: 'Analysis completed',
            stuckCount: 3,
            threshold: '30 days',
          },
          'orphan-items': {
            message: 'Scan completed',
            orphanCount: 0,
            damagedReferences: 0,
          },
          'bulk-update': {
            message: 'Update ready to review',
            selectedOrders: 5,
            newStatus: 'CONFIRMED',
          },
          'export': {
            message: 'Export file ready',
            fileName: 'purchase_orders_export.xlsx',
            fileSize: '2.4 MB',
          },
        }[taskId] || {},
      });
      setExecuting(false);
    }, 1500);
  };

  const getColorClasses = (color: string) => {
    const colors: Record<string, { bg: string; border: string; text: string; button: string }> = {
      blue: {
        bg: 'bg-blue-50',
        border: 'border-blue-200',
        text: 'text-blue-700',
        button: 'bg-blue-600 hover:bg-blue-700',
      },
      green: {
        bg: 'bg-green-50',
        border: 'border-green-200',
        text: 'text-green-700',
        button: 'bg-green-600 hover:bg-green-700',
      },
      yellow: {
        bg: 'bg-yellow-50',
        border: 'border-yellow-200',
        text: 'text-yellow-700',
        button: 'bg-yellow-600 hover:bg-yellow-700',
      },
      red: {
        bg: 'bg-red-50',
        border: 'border-red-200',
        text: 'text-red-700',
        button: 'bg-red-600 hover:bg-red-700',
      },
    };
    return colors[color] || colors.blue;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b px-6 py-4">
        <Link
          href="/dashboard/admin/purchase-orders"
          className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Purchase Orders
        </Link>
        <h1 className="text-xl font-bold text-gray-900">
          Purchase Orders Utilities
        </h1>
        <p className="text-sm text-gray-500">
          Administrative tools and maintenance utilities
        </p>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Task List */}
          <div className="lg:col-span-2">
            <h2 className="text-lg font-bold text-gray-900 mb-4">
              Available Utilities
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {UTILITY_TASKS.map((task) => {
                const colors = getColorClasses(task.color);
                const isSelected = selectedTask === task.id;
                return (
                  <button
                    key={task.id}
                    onClick={() => setSelectedTask(task.id)}
                    className={`p-4 rounded-lg border-2 transition text-left ${
                      isSelected
                        ? `${colors.bg} border-blue-600`
                        : `bg-white border-gray-200 hover:border-gray-300`
                    }`}
                  >
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${colors.bg} ${colors.text}`}>
                      {task.icon}
                    </div>
                    <h3 className="font-medium text-gray-900 text-sm">
                      {task.name}
                    </h3>
                    <p className="text-xs text-gray-500 mt-1">
                      {task.description}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Task Details & Execution */}
          <div className="lg:col-span-1">
            {selectedTask ? (
              <>
                {(() => {
                  const task = UTILITY_TASKS.find((t) => t.id === selectedTask);
                  if (!task) return null;
                  const colors = getColorClasses(task.color);

                  return (
                    <div className="bg-white rounded-lg border shadow-sm p-6 sticky top-6">
                      <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 ${colors.bg} ${colors.text}`}>
                        {task.icon}
                      </div>
                      <h3 className="font-bold text-gray-900 mb-2">
                        {task.name}
                      </h3>
                      <p className="text-sm text-gray-600 mb-6">
                        {task.description}
                      </p>

                      <button
                        onClick={() => handleExecuteTask(task.id)}
                        disabled={executing}
                        className={`w-full flex items-center justify-center gap-2 px-4 py-2 ${colors.button} disabled:opacity-50 text-white rounded-lg font-medium mb-4`}
                      >
                        {executing ? (
                          <>
                            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            Executing...
                          </>
                        ) : (
                          <>
                            <RefreshCw className="w-4 h-4" />
                            Execute
                          </>
                        )}
                      </button>

                      {result && result.taskId === task.id && (
                        <div className={`p-4 rounded-lg ${colors.bg} border ${colors.border}`}>
                          <div className="flex items-start gap-2 mb-3">
                            <CheckCircle className={`w-5 h-5 ${colors.text} flex-shrink-0 mt-0.5`} />
                            <div>
                              <p className="font-medium text-gray-900 text-sm">
                                {result.details.message}
                              </p>
                              <p className="text-xs text-gray-500 mt-1">
                                {new Date(result.timestamp).toLocaleTimeString(
                                  'en-ZA'
                                )}
                              </p>
                            </div>
                          </div>

                          <div className="bg-white rounded p-3 space-y-2">
                            {Object.entries(result.details).map(
                              ([key, value]) =>
                                key !== 'message' && (
                                  <div
                                    key={key}
                                    className="flex justify-between items-center text-xs"
                                  >
                                    <span className="text-gray-600 capitalize">
                                      {key.replace(/_/g, ' ')}
                                    </span>
                                    <span className="font-bold text-gray-900">
                                      {String(value)}
                                    </span>
                                  </div>
                                )
                            )}
                          </div>
                        </div>
                      )}

                      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <p className="text-xs text-blue-700">
                          <strong>Note:</strong> Some utilities may impact
                          existing data. Always review changes before confirming.
                        </p>
                      </div>
                    </div>
                  );
                })()}
              </>
            ) : (
              <div className="bg-white rounded-lg border shadow-sm p-8 text-center sticky top-6">
                <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 font-medium">
                  Select a utility to get started
                </p>
                <p className="text-sm text-gray-400 mt-1">
                  Choose a task from the list to see details and execute
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
