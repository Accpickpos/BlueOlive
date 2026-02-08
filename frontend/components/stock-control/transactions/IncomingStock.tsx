'use client';

import { useState, useEffect } from 'react';
import { ArrowLeft, Plus, Trash2, Save, X } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

interface StockItem {
  stock_code: string;
  description: string;
  quantity_on_hand: number;
  supplier_code?: string;
  sales_mtd_quantity?: number;
  cost_price: number;
  tax_code: number;
}

interface TransactionLine {
  stock_code: string;
  description: string;
  quantity: number;
  tax_code: number;
  unit_cost: number;
  line_total: number;
  vat_amount: number;
}

interface IncomingStockProps {
  onBack: () => void;
}

export default function IncomingStock({ onBack }: IncomingStockProps) {
  const [invoiceDate, setInvoiceDate] = useState(new Date().toISOString().split('T')[0]);
  const [vatType, setVatType] = useState<'I' | 'E'>('E');
  const [invoiceNumber, setInvoiceNumber] = useState('');
  const [supplierId, setSupplierId] = useState<number | ''>('');
  const [additionalReference, setAdditionalReference] = useState('');
  const [surcharge, setSurcharge] = useState(0);
  const [lines, setLines] = useState<TransactionLine[]>([]);
  const [showLineForm, setShowLineForm] = useState(false);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editQuantity, setEditQuantity] = useState(0);
  const [editUnitCost, setEditUnitCost] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStockCode, setSelectedStockCode] = useState('');
  const [quantity, setQuantity] = useState(0);
  const [unitCost, setUnitCost] = useState(0);
  const [selectedTaxCode, setSelectedTaxCode] = useState<number | ''>('');
  const [stockItems, setStockItems] = useState<StockItem[]>([]);
  const [filteredItems, setFilteredItems] = useState<StockItem[]>([]);
  const [showItemsList, setShowItemsList] = useState(false);
  const queryClient = useQueryClient();

  // Fetch stock items
  const { data: stockData, isLoading: stockLoading } = useQuery({
    queryKey: ['stock-items'],
    queryFn: async () => {
      const response = await api.get('/api/stock-control/stock-items/');
      return response.data.results || response.data;
    },
  });

  // Fetch suppliers
  const { data: suppliersData, isLoading: suppliersLoading, error: suppliersError } = useQuery({
    queryKey: ['suppliers'],
    queryFn: async () => {
      try {
        const response = await api.get('/api/creditors/suppliers/');
        console.log('Suppliers response:', response);
        return response.data.results || response.data;
      } catch (error) {
        console.error('Failed to fetch suppliers:', error);
        throw error;
      }
    },
  });

  // Fetch tax codes
  const { data: taxData } = useQuery({
    queryKey: ['tax-codes'],
    queryFn: async () => {
      const response = await api.get('/api/settings/tax-codes/');
      return response.data.results || response.data;
    },
  });

  // Create incoming stock transaction
  const createTransaction = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.post('/api/stock-control/transactions/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stock-transactions'] });
      // Reset form
      setInvoiceDate(new Date().toISOString().split('T')[0]);
      setInvoiceNumber('');
      setSupplierId('');
      setAdditionalReference('');
      setSurcharge(0);
      setLines([]);
      alert('Incoming stock transaction created successfully!');
      onBack();
    },
    onError: (error: any) => {
      alert(`Error: ${error.response?.data?.detail || error.message}`);
    },
  });

  useEffect(() => {
    if (stockData) {
      setStockItems(stockData);
    }
  }, [stockData]);

  useEffect(() => {
    if (searchTerm) {
      const filtered = stockItems.filter(
        (item) =>
          item.stock_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
          item.description.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredItems(filtered);
      setShowItemsList(true);
    } else {
      setFilteredItems([]);
      setShowItemsList(false);
    }
  }, [searchTerm, stockItems]);

  const handleSelectItem = (item: StockItem) => {
    setSelectedStockCode(item.stock_code);
    setSearchTerm(item.stock_code);
    setUnitCost(item.cost_price);
    setSelectedTaxCode(item.tax_code || '');
    setShowItemsList(false);
  };

  const calculateLineTotal = () => {
    const subtotal = quantity * unitCost;
    const taxRate = taxData?.find((t: any) => t.id === selectedTaxCode)?.rate || 0;
    
    if (vatType === 'E') {
      // Exclusive of VAT
      const vat = (subtotal * taxRate) / 100;
      return {
        subtotal,
        vat,
        total: subtotal + vat,
      };
    } else {
      // Inclusive of VAT
      const total = quantity * unitCost;
      const vat = (total * taxRate) / (100 + taxRate);
      return {
        subtotal: total - vat,
        vat,
        total,
      };
    }
  };

  const handleAddLine = () => {
    if (!selectedStockCode || !quantity || !unitCost) {
      alert('Please fill in all required fields');
      return;
    }

    const { subtotal, vat, total } = calculateLineTotal();
    const item = stockItems.find((s) => s.stock_code === selectedStockCode);

    const newLine: TransactionLine = {
      stock_code: selectedStockCode,
      description: item?.description || '',
      quantity,
      tax_code: selectedTaxCode as number,
      unit_cost: unitCost,
      line_total: total,
      vat_amount: vat,
    };

    setLines([...lines, newLine]);
    // Reset form
    setSelectedStockCode('');
    setSearchTerm('');
    setQuantity(0);
    setUnitCost(0);
    setSelectedTaxCode('');
  };

  const handleRemoveLine = (index: number) => {
    setLines(lines.filter((_, i) => i !== index));
  };

  const handleStartEdit = (index: number) => {
    const line = lines[index];
    setEditingIndex(index);
    setEditQuantity(line.quantity);
    setEditUnitCost(line.unit_cost);
  };

  const handleSaveEdit = (index: number) => {
    if (editQuantity <= 0 || editUnitCost <= 0) {
      alert('Quantity and Unit Cost must be greater than 0');
      return;
    }

    const updatedLines = [...lines];
    const { subtotal, vat, total } = calculateLineTotal();
    
    updatedLines[index] = {
      ...updatedLines[index],
      quantity: editQuantity,
      unit_cost: editUnitCost,
      line_total: total,
      vat_amount: vat,
    };
    
    setLines(updatedLines);
    setEditingIndex(null);
  };

  const handleCancelEdit = () => {
    setEditingIndex(null);
    setEditQuantity(0);
    setEditUnitCost(0);
  };

  const calculateTotals = () => {
    let totalQuantity = 0;
    let totalVat = 0;
    let totalAmount = 0;

    lines.forEach((line) => {
      totalQuantity += line.quantity;
      totalVat += line.vat_amount;
      totalAmount += line.line_total;
    });

    return {
      totalQuantity,
      totalVat,
      totalAmount: totalAmount + surcharge,
      surchargeAmount: surcharge,
    };
  };

  const handleSubmit = async () => {
    if (!invoiceDate || !invoiceNumber || lines.length === 0) {
      alert('Please fill in all required fields and add at least one line item');
      return;
    }

    const totals = calculateTotals();

    try {
      // Create a transaction for each line
      for (const line of lines) {
        // Find the stock item to get its ID
        const stockItemData = stockItems.find(s => s.stock_code === line.stock_code);
        
        const transactionData = {
          transaction_type: 'INCOMING',
          stock_item: stockItemData?.stock_code || line.stock_code,
          supplier: supplierId || null,
          invoice_date: invoiceDate,
          invoice_number: invoiceNumber,
          vat_type: vatType,
          additional_reference: additionalReference,
          quantity_in: line.quantity,
          unit_cost: line.unit_cost,
          unit_price: line.unit_cost,
          vat_amount: line.vat_amount,
          total_amount: line.line_total,
          surcharge: line.quantity > 0 ? (surcharge / totals.totalQuantity) * line.quantity : 0,
          surcharge_per_unit: line.quantity > 0 ? surcharge / line.quantity : 0,
          transaction_date: new Date().toISOString(),
          transaction_number: invoiceNumber,
          reference: additionalReference,
        };

        await createTransaction.mutateAsync(transactionData);
      }
    } catch (error) {
      console.error('Error creating transaction:', error);
    }
  };

  const totals = calculateTotals();

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={onBack}
          className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
        >
          <ArrowLeft size={20} />
          Back
        </button>
        <h2 className="text-2xl font-bold">Incoming Stock</h2>
      </div>

      {/* Header Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium mb-2">Invoice Date</label>
          <input
            type="date"
            value={invoiceDate}
            onChange={(e) => setInvoiceDate(e.target.value)}
            className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">VAT Option</label>
          <select
            value={vatType}
            onChange={(e) => setVatType(e.target.value as 'I' | 'E')}
            className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="E">Exclusive of VAT</option>
            <option value="I">Inclusive of VAT</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Supplier</label>
          {suppliersError && <p className="text-red-500 text-sm mb-2">Error loading suppliers</p>}
          <select
            value={String(supplierId)}
            onChange={(e) => setSupplierId(e.target.value ? parseInt(e.target.value) : '')}
            className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={suppliersLoading}
          >
            <option value="">{suppliersLoading ? 'Loading suppliers...' : '-- Select Supplier --'}</option>
            {suppliersData?.map((supplier: any, idx: number) => (
              <option key={`supplier-${supplier.id}-${idx}`} value={String(supplier.id)}>
                {supplier.supplier_number || supplier.id} - {supplier.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Invoice Number</label>
          <input
            type="text"
            value={invoiceNumber}
            onChange={(e) => setInvoiceNumber(e.target.value)}
            placeholder="Supplier's invoice number"
            className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Additional Reference</label>
          <input
            type="text"
            value={additionalReference}
            onChange={(e) => setAdditionalReference(e.target.value)}
            placeholder="Additional notes or reference"
            className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Surcharge (Exclusive of VAT)</label>
          <input
            type="number"
            value={surcharge}
            onChange={(e) => setSurcharge(parseFloat(e.target.value) || 0)}
            step="0.01"
            min="0"
            placeholder="E.g., transport charges"
            className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Add Line Item Section */}
      <div className="bg-gray-50 rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">Add Stock Item</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium mb-2">Stock Code / Description</label>
            <div className="relative">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search stock..."
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {showItemsList && (
                <div className="absolute top-full left-0 right-0 bg-white border border-t-0 rounded-b-lg shadow-lg max-h-40 overflow-y-auto z-10">
                  {filteredItems.map((item) => (
                    <div
                      key={item.stock_code}
                      onClick={() => handleSelectItem(item)}
                      className="px-4 py-2 hover:bg-gray-100 cursor-pointer"
                    >
                      <p className="font-medium">{item.stock_code}</p>
                      <p className="text-sm text-gray-600">{item.description}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Quantity</label>
            <input
              type="number"
              value={quantity || ''}
              onChange={(e) => setQuantity(e.target.value ? parseFloat(e.target.value) : 0)}
              step="0.01"
              min="0"
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Unit Cost</label>
            <input
              type="number"
              value={unitCost || ''}
              onChange={(e) => setUnitCost(e.target.value ? parseFloat(e.target.value) : 0)}
              step="0.01"
              min="0"
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Tax Code</label>
            <select
              value={selectedTaxCode}
              onChange={(e) => setSelectedTaxCode(e.target.value ? parseInt(e.target.value) : '')}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select Tax Code</option>
              {taxData?.map((tax: any, idx: number) => (
                <option key={`tax-${tax.id}-${idx}`} value={tax.id}>
                  {tax.code} ({tax.rate}%)
                </option>
              ))}
            </select>
          </div>
        </div>
        <button
          onClick={handleAddLine}
          disabled={!selectedStockCode || !quantity || !unitCost}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          <Plus size={20} />
          Add Line Item
        </button>
      </div>

      {/* Goods Received Note */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-4">Goods Received Note</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-100 border-b">
              <tr>
                <th className="text-left px-4 py-2">Stock Code</th>
                <th className="text-left px-4 py-2">Description</th>
                <th className="text-right px-4 py-2">Qty</th>
                <th className="text-right px-4 py-2">Unit Cost</th>
                <th className="text-right px-4 py-2">VAT</th>
                <th className="text-right px-4 py-2">Total</th>
                <th className="text-center px-4 py-2">Action</th>
              </tr>
            </thead>
            <tbody>
              {lines.map((line, index) => (
                <tr key={index} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-2">{line.stock_code}</td>
                  <td className="px-4 py-2">{line.description}</td>
                  <td className="text-right px-4 py-2">
                    {editingIndex === index ? (
                      <input
                        type="number"
                        value={editQuantity}
                        onChange={(e) => setEditQuantity(parseFloat(e.target.value) || 0)}
                        step="0.01"
                        min="0"
                        className="w-20 px-2 py-1 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    ) : (
                      line.quantity.toFixed(2)
                    )}
                  </td>
                  <td className="text-right px-4 py-2">
                    {editingIndex === index ? (
                      <input
                        type="number"
                        value={editUnitCost}
                        onChange={(e) => setEditUnitCost(parseFloat(e.target.value) || 0)}
                        step="0.01"
                        min="0"
                        className="w-24 px-2 py-1 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    ) : (
                      `R ${line.unit_cost.toFixed(2)}`
                    )}
                  </td>
                  <td className="text-right px-4 py-2">R {line.vat_amount.toFixed(2)}</td>
                  <td className="text-right px-4 py-2 font-semibold">R {line.line_total.toFixed(2)}</td>
                  <td className="text-center px-4 py-2 space-x-2">
                    {editingIndex === index ? (
                      <>
                        <button
                          onClick={() => handleSaveEdit(index)}
                          className="text-green-600 hover:text-green-800 font-semibold"
                        >
                          Save
                        </button>
                        <button
                          onClick={handleCancelEdit}
                          className="text-gray-600 hover:text-gray-800 ml-2"
                        >
                          Cancel
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          onClick={() => handleStartEdit(index)}
                          className="text-blue-600 hover:text-blue-800 font-semibold text-sm"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleRemoveLine(index)}
                          className="text-red-600 hover:text-red-800 ml-2"
                        >
                          <Trash2 size={18} />
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Totals */}
        <div className="mt-6 space-y-2 text-right max-w-md ml-auto">
          <div className="flex justify-between text-sm">
            <span>Total Quantity:</span>
            <span className="font-semibold">{totals.totalQuantity.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>Total VAT:</span>
            <span className="font-semibold">R {totals.totalVat.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>Surcharge:</span>
            <span className="font-semibold">R {totals.surchargeAmount.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-lg border-t pt-2">
            <span>Total Amount:</span>
            <span className="font-bold">R {totals.totalAmount.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4 justify-end">
        <button
          onClick={onBack}
          className="flex items-center gap-2 px-6 py-2 bg-gray-300 text-gray-800 rounded-lg hover:bg-gray-400 transition"
        >
          <X size={20} />
          Cancel
        </button>
        <button
          onClick={handleSubmit}
          disabled={createTransaction.isPending}
          className="flex items-center gap-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition"
        >
          <Save size={20} />
          {createTransaction.isPending ? 'Saving...' : 'Save & Update Stock'}
        </button>
      </div>
    </div>
  );
}
