'use client';

import React, { useState } from 'react';
import {
  ChevronRight,
  ChevronLeft,
  Check,
  Package,
  FileText,
  Building2,
  AlertTriangle,
} from 'lucide-react';
import { PurchaseOrder, PurchaseOrderLineItem, PurchaseOrderStatus, OrderLayoutOption } from '@/lib/types/purchaseOrders';
import { purchaseOrdersApi } from '@/lib/purchaseOrdersApi';
import { getApiErrorMessage } from '@/lib/api';
import { CreditorPicker } from '@/components/creditors';
import { StockItemPicker } from '@/components/pos';

interface PurchaseOrderWizardProps {
  onComplete: () => void;
  onCancel: () => void;
}

type WizardStep = 'supplier' | 'parameters' | 'line-items' | 'review';

interface FormData extends Partial<Omit<PurchaseOrder, 'status' | 'layout_option'>> {
  order_type: 'COST' | 'RETAIL';
  extract_stock_items: boolean;
  layout_option: OrderLayoutOption;
  status: PurchaseOrderStatus;
}

export function PurchaseOrderWizard({ onComplete, onCancel }: PurchaseOrderWizardProps) {
  const [currentStep, setCurrentStep] = useState<WizardStep>('supplier');
  const [formData, setFormData] = useState<FormData>({
    order_type: 'COST',
    extract_stock_items: false,
    layout_option: 'MONTH_TO_DATE_SALES' as OrderLayoutOption,
    status: 'DRAFT' as PurchaseOrderStatus,
    order_date: new Date().toISOString().split('T')[0],
    delivery_date: '',
    supplier_id: 0,
    total_amount: 0,
    total_vat: 0,
    total_landed_cost: 0,
  });
  const [lineItems, setLineItems] = useState<PurchaseOrderLineItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const steps: { key: WizardStep; label: string; icon: React.ReactNode }[] = [
    { key: 'supplier', label: 'Supplier', icon: <Building2 className="w-5 h-5" /> },
    { key: 'parameters', label: 'Parameters', icon: <FileText className="w-5 h-5" /> },
    { key: 'line-items', label: 'Line Items', icon: <Package className="w-5 h-5" /> },
    { key: 'review', label: 'Review', icon: <Check className="w-5 h-5" /> },
  ];

  const currentStepIndex = steps.findIndex((s) => s.key === currentStep);

  const handleNext = () => {
    if (!validateStep()) return;
    const nextIndex = currentStepIndex + 1;
    if (nextIndex < steps.length) {
      setCurrentStep(steps[nextIndex].key);
    }
  };

  const handleBack = () => {
    const prevIndex = currentStepIndex - 1;
    if (prevIndex >= 0) {
      setCurrentStep(steps[prevIndex].key);
    }
  };

  const validateStep = (): boolean => {
    if (currentStep === 'supplier') {
      if (!formData.supplier_id || !formData.delivery_date) {
        setError('Please fill in all required fields');
        return false;
      }
    }
    setError('');
    return true;
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    try {
      const extractStockItems = formData.extract_stock_items || false;

      const payload = {
        supplier: formData.supplier_id,
        order_date: formData.order_date,
        delivery_date: formData.delivery_date,
        pricing_method: formData.order_type,
        notes: formData.reference || '',
        // Backend only supports two extraction modes; REORDER_QUANTITY maps to
        // "items below reorder level", anything else extracts all supplier items.
        extract_all_items: extractStockItems && formData.layout_option !== 'REORDER_QUANTITY',
        extract_below_reorder: extractStockItems && formData.layout_option === 'REORDER_QUANTITY',
        line_items: extractStockItems
          ? undefined
          : lineItems.map((item) => ({
              stock_item: item.stock_code,
              quantity_ordered: item.quantity,
              unit_cost: item.current_cost,
              tax_code: item.tax_code === 'Z' ? 2 : 1,
            })),
      };

      await purchaseOrdersApi.orders.create(payload as any);
      onComplete();
    } catch (err: any) {
      setError(getApiErrorMessage(err, 'Failed to create order'));
    } finally {
      setLoading(false);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 'supplier':
        return <SupplierStep formData={formData} setFormData={setFormData} />;
      case 'parameters':
        return <ParametersStep formData={formData} setFormData={setFormData} />;
      case 'line-items':
        return (
          <LineItemsStep
            lineItems={lineItems}
            setLineItems={setLineItems}
            extractStockItems={formData.extract_stock_items || false}
          />
        );
      case 'review':
        return <ReviewStep formData={formData} lineItems={lineItems} />;
      default:
        return null;
    }
  };

  const lineItemsTotal = lineItems.reduce((sum, item) => sum + item.total_cost, 0);
  const vat = lineItemsTotal * 0.15;

  return (
    <div className="bg-white rounded-lg shadow-lg">
      {/* Progress Steps */}
      <div className="border-b px-6 py-4">
        <div className="flex items-center justify-between gap-2">
          {steps.map((step, index) => (
            <React.Fragment key={step.key}>
              <div className="flex items-center gap-2 flex-1">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                    index <= currentStepIndex
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-400'
                  }`}
                >
                  {step.icon}
                </div>
                <span
                  className={`text-sm font-medium hidden md:inline ${
                    index <= currentStepIndex ? 'text-gray-900' : 'text-gray-400'
                  }`}
                >
                  {step.label}
                </span>
              </div>
              {index < steps.length - 1 && (
                <div
                  className={`flex-shrink-0 h-1 w-8 ${
                    index < currentStepIndex ? 'bg-blue-600' : 'bg-gray-200'
                  }`}
                />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className="p-6 min-h-96">
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <span className="text-red-600 text-sm">{error}</span>
          </div>
        )}
        {renderStepContent()}
      </div>

      {/* Summary for line items */}
      {currentStep !== 'review' && lineItems.length > 0 && (
        <div className="border-t px-6 py-4 bg-gray-50">
          <div className="flex justify-end">
            <div className="w-64 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Subtotal:</span>
                <span className="font-medium">R {lineItemsTotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">VAT (15%):</span>
                <span className="font-medium">R {vat.toFixed(2)}</span>
              </div>
              <div className="flex justify-between border-t pt-2 text-base">
                <span className="font-semibold">Total:</span>
                <span className="font-bold">R {(lineItemsTotal + vat).toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Navigation Buttons */}
      <div className="border-t px-6 py-4 flex items-center justify-between bg-white">
        <button
          onClick={onCancel}
          className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium"
        >
          Cancel
        </button>
        <div className="flex gap-3">
          <button
            onClick={handleBack}
            disabled={currentStepIndex === 0}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            <ChevronLeft className="w-4 h-4" />
            Back
          </button>
          {currentStepIndex === steps.length - 1 ? (
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating...' : 'Create Order'}
              <Check className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={handleNext}
              className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium"
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ============ STEP COMPONENTS ============

function SupplierStep({
  formData,
  setFormData,
}: {
  formData: FormData;
  setFormData: (data: FormData) => void;
}) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">Select Supplier</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Order Date *</label>
          <input
            type="date"
            value={formData.order_date || ''}
            onChange={(e) => setFormData({ ...formData, order_date: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Delivery Date *</label>
          <input
            type="date"
            value={formData.delivery_date || ''}
            onChange={(e) => setFormData({ ...formData, delivery_date: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Supplier *</label>
        <CreditorPicker
          onSelect={(creditor) =>
            setFormData({
              ...formData,
              supplier_id: Number(creditor.id),
              supplier_name: creditor.name,
              supplier_code: creditor.account_number,
            })
          }
          placeholder="Search suppliers..."
        />
        {formData.supplier_id ? (
          <p className="text-sm text-gray-600 mt-1">
            Selected: {formData.supplier_code} - {formData.supplier_name}
          </p>
        ) : null}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Reference</label>
        <input
          type="text"
          value={formData.reference || ''}
          onChange={(e) => setFormData({ ...formData, reference: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Supplier reference or PO number"
        />
      </div>
    </div>
  );
}

function ParametersStep({
  formData,
  setFormData,
}: {
  formData: FormData;
  setFormData: (data: FormData) => void;
}) {
  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-900">Order Parameters</h3>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">Order Type *</label>
        <div className="grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={() => setFormData({ ...formData, order_type: 'COST' })}
            className={`p-4 border-2 rounded-lg text-center transition-colors ${
              formData.order_type === 'COST'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <span className="font-medium text-gray-900">At Cost</span>
            <p className="text-xs mt-1 text-gray-500">Create order at cost price</p>
          </button>
          <button
            type="button"
            onClick={() => setFormData({ ...formData, order_type: 'RETAIL' })}
            className={`p-4 border-2 rounded-lg text-center transition-colors ${
              formData.order_type === 'RETAIL'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <span className="font-medium text-gray-900">At Retail</span>
            <p className="text-xs mt-1 text-gray-500">Create order at retail price</p>
          </button>
        </div>
      </div>

      <div>
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={formData.extract_stock_items || false}
            onChange={(e) => setFormData({ ...formData, extract_stock_items: e.target.checked })}
            className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm font-medium text-gray-700">Extract Stock Items</span>
        </label>
        <p className="ml-7 text-xs text-gray-500 mt-1">
          Automatically populate line items based on supplier stock items
        </p>
      </div>

      {formData.extract_stock_items && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Order Layout *</label>
          <select
            value={formData.layout_option || 'MONTH_TO_DATE_SALES'}
            onChange={(e) => setFormData({ ...formData, layout_option: e.target.value as OrderLayoutOption })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="MONTH_TO_DATE_SALES">Month to Date Sales and Quantity on Hand</option>
            <option value="REORDER_QUANTITY">Re-Order Quantity and Quantity to Order</option>
            <option value="QUANTITY_TO_ORDER">Quantity to Order</option>
          </select>
        </div>
      )}
    </div>
  );
}

function LineItemsStep({
  lineItems,
  setLineItems,
  extractStockItems,
}: {
  lineItems: PurchaseOrderLineItem[];
  setLineItems: (items: PurchaseOrderLineItem[]) => void;
  extractStockItems: boolean;
}) {
  const [newItem, setNewItem] = useState({
    stock_code: '',
    stock_description: '',
    quantity: 1,
    current_cost: 0,
    tax_code: 'T',
    tax_rate: 15,
    last_cost: 0,
    landed_cost: 0,
    total_cost: 0,
    total_vat: 0,
    is_ordered: false,
    comments: '',
  });

  const handleAddItem = () => {
    if (!newItem.stock_code) return;
    const total = newItem.quantity * newItem.current_cost;
    const vat = total * 0.15;
    setLineItems([
      ...lineItems,
      {
        ...newItem,
        line_number: lineItems.length + 1,
        total_cost: total,
        total_vat: vat,
      } as any,
    ]);
    setNewItem({
      stock_code: '',
      stock_description: '',
      quantity: 1,
      current_cost: 0,
      tax_code: 'T',
      tax_rate: 15,
      last_cost: 0,
      landed_cost: 0,
      total_cost: 0,
      total_vat: 0,
      is_ordered: false,
      comments: '',
    });
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">Line Items</h3>

      {!extractStockItems && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 p-4 bg-gray-50 rounded-lg">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Stock Code *</label>
            <StockItemPicker
              onSelect={(item) =>
                setNewItem((prev) => ({
                  ...prev,
                  stock_code: item.stock_code,
                  stock_description: item.description,
                  current_cost: item.cost_price,
                }))
              }
              placeholder={newItem.stock_code || 'Search stock...'}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Quantity</label>
            <input
              type="number"
              value={newItem.quantity}
              onChange={(e) => setNewItem({ ...newItem, quantity: parseInt(e.target.value) || 1 })}
              className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
              min="1"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Cost</label>
            <input
              type="number"
              value={newItem.current_cost}
              onChange={(e) => setNewItem({ ...newItem, current_cost: parseFloat(e.target.value) || 0 })}
              className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
              step="0.01"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Tax</label>
            <select
              value={newItem.tax_code}
              onChange={(e) => setNewItem({ ...newItem, tax_code: e.target.value })}
              className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
            >
              <option value="T">Standard (15%)</option>
              <option value="Z">Zero (0%)</option>
              <option value="E">Exempt</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              type="button"
              onClick={handleAddItem}
              className="w-full px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-medium"
            >
              Add Item
            </button>
          </div>
        </div>
      )}

      {lineItems.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="bg-gray-100">
                <th className="text-left px-3 py-2 text-xs font-medium text-gray-600">#</th>
                <th className="text-left px-3 py-2 text-xs font-medium text-gray-600">Code</th>
                <th className="text-right px-3 py-2 text-xs font-medium text-gray-600">Qty</th>
                <th className="text-right px-3 py-2 text-xs font-medium text-gray-600">Cost</th>
                <th className="text-right px-3 py-2 text-xs font-medium text-gray-600">Total</th>
                <th className="text-center px-3 py-2 text-xs font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody>
              {lineItems.map((item, index) => (
                <tr key={index} className="border-b">
                  <td className="px-3 py-2">{item.line_number}</td>
                  <td className="px-3 py-2 font-medium">{item.stock_code}</td>
                  <td className="px-3 py-2 text-right">{item.quantity}</td>
                  <td className="px-3 py-2 text-right">R {item.current_cost.toFixed(2)}</td>
                  <td className="px-3 py-2 text-right font-medium">R {item.total_cost.toFixed(2)}</td>
                  <td className="px-3 py-2 text-center">
                    <button
                      type="button"
                      onClick={() => setLineItems(lineItems.filter((_, i) => i !== index))}
                      className="text-red-500 hover:text-red-700 text-xs font-medium"
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {lineItems.length === 0 && !extractStockItems && (
        <div className="p-8 text-center text-gray-500 border-2 border-dashed rounded-lg">
          <Package className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p className="font-medium">No line items added yet</p>
          <p className="text-sm">Enter stock code and quantity above to add items</p>
        </div>
      )}
    </div>
  );
}

function ReviewStep({
  formData,
  lineItems,
}: {
  formData: FormData;
  lineItems: PurchaseOrderLineItem[];
}) {
  const subtotal = lineItems.reduce((sum, item) => sum + item.total_cost, 0);
  const vat = subtotal * 0.15;

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-900">Review & Submit</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gray-50 p-4 rounded-lg">
          <h4 className="font-semibold text-gray-900 mb-4">Order Details</h4>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between">
              <dt className="text-gray-600">Order Type:</dt>
              <dd className="font-medium">
                {formData.order_type === 'COST' ? 'At Cost' : 'At Retail'}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">Order Date:</dt>
              <dd className="font-medium">
                {new Date(formData.order_date!).toLocaleDateString('en-ZA')}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">Delivery Date:</dt>
              <dd className="font-medium">
                {new Date(formData.delivery_date!).toLocaleDateString('en-ZA')}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">Line Items:</dt>
              <dd className="font-medium">{lineItems.length}</dd>
            </div>
          </dl>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg">
          <h4 className="font-semibold text-gray-900 mb-4">Order Total</h4>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between">
              <dt className="text-gray-600">Subtotal:</dt>
              <dd className="font-medium">R {subtotal.toFixed(2)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">VAT (15%):</dt>
              <dd className="font-medium">R {vat.toFixed(2)}</dd>
            </div>
            <div className="flex justify-between border-t pt-3 text-base">
              <dt className="font-semibold">Total:</dt>
              <dd className="font-bold">R {(subtotal + vat).toFixed(2)}</dd>
            </div>
          </dl>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>Note:</strong> This order will be created as <strong>Outstanding</strong> and is
          immediately live — stock will show as on order for the supplier.
        </p>
      </div>
    </div>
  );
}
