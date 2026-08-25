'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/useAuth';
import { usePOSAPI, LineItem, TenderData, CashSaleCreateData } from '@/lib/posApi';
import { useRouter } from 'next/navigation';
import { StockItemPicker, GrossProfitDisplay, GPBadge } from '@/components/pos';
import { Card, CardContent } from '@/components/ui/card';

export default function CreateCashSale() {
  const { user } = useAuth();
  const router = useRouter();
  const posAPI = usePOSAPI(user?.tenant?.slug);

  const [formData, setFormData] = useState({
    sale_date: new Date().toISOString().split('T')[0],
    notes: '',
  });

  const [lineItems, setLineItems] = useState<LineItem[]>([
    {
      stock_code: '',  // Use 'stock_code' to match backend
      description: '',
      quantity: 1,
      unit_price: 0,
      discount_percentage: 0,
      tax_code: 1, // STANDARD - 14% VAT
    },
  ]);

  // Track cost prices for GP calculation (not sent to backend)
  const [costPrices, setCostPrices] = useState<{ [key: number]: number }>({});

  const [tenders, setTenders] = useState<TenderData[]>([
    {
      tender_type: 'CASH',
      amount: 0,
    },
  ]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totals, setTotals] = useState({
    subtotal: 0,
    tax: 0,
    total: 0,
  });
  const [change, setChange] = useState(0);

  // Calculate totals
  useEffect(() => {
    const newTotals = lineItems.reduce(
      (acc, item) => {
        const lineAmount = item.quantity * item.unit_price;
        const discount = (lineAmount * (item.discount_percentage || 0)) / 100;
        const taxableAmount = lineAmount - discount;
        const taxRate = item.tax_code === 0 ? 0 : item.tax_code === 1 ? 0.14 : 0;
        const tax = taxableAmount * taxRate;

        return {
          subtotal: acc.subtotal + taxableAmount,
          tax: acc.tax + tax,
          total: acc.total + taxableAmount + tax,
        };
      },
      { subtotal: 0, tax: 0, total: 0 }
    );

    setTotals(newTotals);

    // Calculate change
    const tenderTotal = tenders.reduce((sum, t) => sum + (t.amount || 0), 0);
    setChange(tenderTotal - newTotals.total);
  }, [lineItems, tenders]);

  const addLineItem = () => {
    setLineItems([
      ...lineItems,
      {
        stock_code: '',  // Use 'stock_code' to match backend
        description: '',
        quantity: 1,
        unit_price: 0,
        discount_percentage: 0,
        tax_code: 1, // STANDARD - 14% VAT
      },
    ]);
  };

  const removeLineItem = (index: number) => {
    setLineItems(lineItems.filter((_, i) => i !== index));
  };

  const updateLineItem = (index: number, field: string, value: any) => {
    const updated = [...lineItems];
    updated[index] = { ...updated[index], [field]: value };
    setLineItems(updated);
  };

  const addTender = () => {
    setTenders([
      ...tenders,
      {
        tender_type: 'CASH',
        amount: 0,
      },
    ]);
  };

  const removeTender = (index: number) => {
    setTenders(tenders.filter((_, i) => i !== index));
  };

  const updateTender = (index: number, field: string, value: any) => {
    const updated = [...tenders];
    updated[index] = { ...updated[index], [field]: value };
    setTenders(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (lineItems.some((item) => !item.stock_code || !item.quantity || !item.unit_price)) {
      setError('All line items must have item code, quantity, and selling price');
      return;
    }

    if (tenders.some((t) => !t.tender_type || !t.amount)) {
      setError('All tenders must have type and amount');
      return;
    }

    const tenderTotal = tenders.reduce((sum, t) => sum + (t.amount || 0), 0);
    if (tenderTotal < totals.total) {
      setError('Tender amount must be at least equal to the total');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const saleData: CashSaleCreateData = {
        sale_date: formData.sale_date,
        lines: lineItems,
        tenders: tenders,
        notes: formData.notes,
      };

      console.log('Submitting Cash Sale data:', JSON.stringify(saleData, null, 2));
      
      const result = await posAPI.createCashSale(saleData);
      console.log('Cash Sale created, result:', result);
      
      // Get the sale ID - could be 'id' or 'pk' or the sale_number
      const saleId = result.id || result.pk || result.sale_number;
      console.log('Sale ID:', saleId);
      
      if (saleId) {
        router.push(`/dashboard/pos/cash-sales/${saleId}`);
      } else {
        // Go back to the list if no ID available
        router.push('/dashboard/pos/cash-sales');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create cash sale');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Cash Sale</h1>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Header Information */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Sale Details</h2>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sale Date *
              </label>
              <input
                type="date"
                value={formData.sale_date}
                onChange={(e) =>
                  setFormData({ ...formData, sale_date: e.target.value })
                }
                className="w-full md:w-1/3 px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
          </div>

          {/* Line Items */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Items</h2>
              <button
                type="button"
                onClick={addLineItem}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm"
              >
                + Add Item
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-2 py-2 text-left w-48">Item</th>
                    <th className="px-2 py-2 text-left">Description</th>
                    <th className="px-2 py-2 text-right w-20">Qty</th>
                    <th className="px-2 py-2 text-right w-24">Price</th>
                    <th className="px-2 py-2 text-right w-20">Disc %</th>
                    <th className="px-2 py-2 text-left w-24">Tax</th>
                    <th className="px-2 py-2 text-right w-24">Total</th>
                    <th className="px-2 py-2 text-center w-20">GP</th>
                    <th className="px-2 py-2 text-center w-16">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {lineItems.map((item, index) => {
                    const lineAmount = item.quantity * item.unit_price;
                    const discount = (lineAmount * (item.discount_percentage || 0)) / 100;
                    const taxableAmount = lineAmount - discount;
                    const taxRate = item.tax_code === 0 ? 0 : item.tax_code === 1 ? 0.14 : 0;
                    const tax = taxableAmount * taxRate;
                    const lineTotal = taxableAmount + tax;
                    const costPrice = Number(costPrices[index]) || 0;

                    return (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="px-2 py-2">
                          <StockItemPicker
                            onSelect={(stockItem) => {
                              console.log('CashSale: Received stockItem:', stockItem);
                              console.log('CashSale: Updating line item at index:', index);
                              
                              // Batch all updates into one state change
                              const updatedItems = [...lineItems];
                              updatedItems[index] = {
                                ...updatedItems[index],
                                stock_code: stockItem.stock_code,  // Use 'stock_code' for backend
                                description: stockItem.description,
                                unit_price: stockItem.selling_price,
                                tax_code: stockItem.tax_code === 'ZERO' ? 0 : stockItem.tax_code === 'REDUCED' ? 2 : 1,
                              };
                              setLineItems(updatedItems);
                              
                              // Update cost prices
                              setCostPrices(prev => ({ ...prev, [index]: stockItem.cost_price }));
                              
                              console.log('CashSale: Line items after update:', updatedItems);
                            }}
                            placeholder="Search item..."
                          />
                        </td>
                        <td className="px-2 py-2">
                          <input
                            type="text"
                            value={item.description}
                            onChange={(e) =>
                              updateLineItem(index, 'description', e.target.value)
                            }
                            className="w-full px-2 py-1 border rounded text-sm"
                            placeholder="Description"
                          />
                        </td>
                        <td className="px-2 py-2">
                          <input
                            type="number"
                            value={item.quantity}
                            onChange={(e) =>
                              updateLineItem(index, 'quantity', Number(e.target.value))
                            }
                            className="w-full px-2 py-1 border rounded text-sm text-right"
                            min="0"
                          />
                        </td>
                        <td className="px-2 py-2">
                          <input
                            type="number"
                            value={item.unit_price}
                            onChange={(e) =>
                              updateLineItem(index, 'unit_price', Number(e.target.value))
                            }
                            className="w-full px-2 py-1 border rounded text-sm text-right"
                            min="0"
                            step="0.01"
                          />
                        </td>
                        <td className="px-2 py-2">
                          <input
                            type="number"
                            value={item.discount_percentage || 0}
                            onChange={(e) =>
                              updateLineItem(index, 'discount_percentage', Number(e.target.value))
                            }
                            className="w-full px-2 py-1 border rounded text-sm text-right"
                            min="0"
                            max="100"
                            step="0.01"
                          />
                        </td>
                        <td className="px-2 py-2">
                          <select
                            value={item.tax_code}
                            onChange={(e) =>
                              updateLineItem(index, 'tax_code', Number(e.target.value))
                            }
                            className="w-full px-2 py-1 border rounded text-sm"
                          >
                            <option value={0}>Zero-rated (0%)</option>
                            <option value={1}>Standard (14%)</option>
                          </select>
                        </td>
                        <td className="px-2 py-2 text-right">
                          {lineTotal.toFixed(2)}
                        </td>
                        <td className="px-4 py-2 text-center">
                          {item.quantity > 0 && item.unit_price > 0 ? (
                            <GPBadge 
                              sellingPrice={Number(item.unit_price)} 
                              costPrice={Number(costPrice)} 
                              quantity={Number(item.quantity)} 
                            />
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="px-2 py-2 text-center">
                          <button
                            type="button"
                            onClick={() => removeLineItem(index)}
                            className="text-red-600 hover:text-red-800 text-sm disabled:opacity-50"
                            disabled={lineItems.length === 1}
                          >
                            ✕
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* GP Summary */}
            {lineItems.some(item => item.quantity > 0 && item.unit_price > 0) && (
              <div className="mt-4 p-4 bg-green-50 rounded-lg">
                <div className="flex justify-between items-center">
                  <span className="font-medium text-gray-700">Total Gross Profit:</span>
                  <div className="text-right">
                    {(() => {
                      const totalGP = lineItems.reduce((sum, item, idx) => {
                        const cost = Number(costPrices[idx]) || 0;
                        return sum + ((Number(item.unit_price) - cost) * Number(item.quantity));
                      }, 0);
                      const totalSales = lineItems.reduce((sum, item) => sum + (Number(item.unit_price) * Number(item.quantity)), 0);
                      const gpPercent = totalSales > 0 ? (totalGP / totalSales) * 100 : 0;
                      return (
                        <>
                          <span className="text-xl font-bold text-green-700">R{totalGP.toFixed(2)}</span>
                          <span className="text-sm text-green-600 ml-2">({gpPercent.toFixed(1)}%)</span>
                        </>
                      );
                    })()}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Tenders */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Payment Methods</h2>
              <button
                type="button"
                onClick={addTender}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm"
              >
                + Add Payment
              </button>
            </div>

            <div className="space-y-4">
              {tenders.map((tender, index) => (
                <div key={index} className="flex gap-4 items-end pb-4 border-b">
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Payment Type
                    </label>
                    <select
                      value={tender.tender_type}
                      onChange={(e) =>
                        updateTender(index, 'tender_type', e.target.value)
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    >
                      <option value="CASH">Cash</option>
                      <option value="CHEQUE">Cheque</option>
                      <option value="CREDIT_CARD">Credit Card</option>
                      <option value="EFT">EFT</option>
                    </select>
                  </div>

                  <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Amount
                    </label>
                    <input
                      type="number"
                      value={tender.amount}
                      onChange={(e) =>
                        updateTender(index, 'amount', Number(e.target.value))
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-right"
                      min="0"
                      step="0.01"
                    />
                  </div>

                  {tender.tender_type === 'CHEQUE' && (
                    <div className="flex-1">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Cheque No
                      </label>
                      <input
                        type="text"
                        value={tender.drawer_name || ''}  // Use 'drawer_name' for backend
                        onChange={(e) =>
                          updateTender(index, 'drawer_name', e.target.value)  // Use 'drawer_name'
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>
                  )}

                  <button
                    type="button"
                    onClick={() => removeTender(index)}
                    className="text-red-600 hover:text-red-800 px-4 py-2"
                  >
                    Delete
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Totals and Change */}
          <div className="bg-white rounded-lg shadow p-6 flex justify-end">
            <div className="w-64 space-y-3">
              <div className="flex justify-between pb-2 border-b">
                <span>Subtotal:</span>
                <span>{totals.subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between pb-2 border-b">
                <span>Tax:</span>
                <span>{totals.tax.toFixed(2)}</span>
              </div>
              <div className="flex justify-between font-bold text-lg pb-2 border-b">
                <span>Total:</span>
                <span>{totals.total.toFixed(2)}</span>
              </div>
              <div className="flex justify-between font-semibold text-green-600">
                <span>Change:</span>
                <span>{change >= 0 ? change.toFixed(2) : '(' + Math.abs(change).toFixed(2) + ')'}</span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-4">
            <button
              type="submit"
              disabled={loading || change < 0}
              className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white px-6 py-2 rounded-lg font-medium"
            >
              {loading ? 'Processing...' : 'Complete Sale'}
            </button>
            <button
              type="button"
              onClick={() => router.back()}
              className="bg-gray-300 hover:bg-gray-400 text-gray-800 px-6 py-2 rounded-lg font-medium"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
