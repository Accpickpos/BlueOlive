'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/useAuth';
import { jobCardsApi, JobCardLineItem } from '@/lib/jobCardsApi';
import { DebtorPicker } from '@/components/pos/DebtorPicker';
import { StockItemPicker } from '@/components/pos/StockItemPicker';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { ArrowLeft, AlertCircle, CheckCircle, Plus, Trash2 } from 'lucide-react';

interface Debtor {
  id: number;
  dno: string;
  name: string;
  telephone?: string;
}

interface StockItem {
  id: number;
  stock_code: string;
  description: string;
  selling_price: number;
}

export default function CreateJobCostingPage() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedDebtor, setSelectedDebtor] = useState<Debtor | null>(null);

  const [formData, setFormData] = useState({
    job_number: '',
    debtor_account_number: '',  // Add debtor account number
    customer_name: '',
    job_description: '',
    start_date: '',
    estimated_cost: '',
    status: 'open',
  });

  const [lineItems, setLineItems] = useState<any[]>([]);
  const [newItem, setNewItem] = useState({
    stock_item: null as StockItem | null,
    description: '',
    quantity: '',
    unit_rate: '',
  });

  // Handle debtor selection
  const handleDebtorSelect = (debtor: any) => {
    setSelectedDebtor(debtor);
    setFormData(prev => ({
      ...prev,
      debtor_account_number: debtor.account_number || debtor.dno || '',  // Use account_number from DebtorPicker, fallback to dno
      customer_name: debtor.name
    }));
  };

  // Handle manual customer name entry
  const handleCustomerNameChange = (value: string) => {
    setFormData(prev => ({
      ...prev,
      customer_name: value,
      // Clear debtor if manually typing name (user can still select debtor afterwards)
      debtor_account_number: value !== prev.customer_name ? '' : prev.debtor_account_number
    }));
  };

  // Handle stock item selection
  const handleStockSelect = (item: any) => {
    setNewItem(prev => ({
      ...prev,
      stock_item: item,
      description: item.description,
      unit_rate: item.selling_price.toString()
    }));
  };

  // Map frontend status to backend status
  const mapStatusToBackend = (status: string): string => {
    switch (status) {
      case 'open': return 'ACTIVE';
      case 'in_progress': return 'ACTIVE';
      case 'completed': return 'CONVERTED_TO_INVOICE';
      default: return 'ACTIVE';
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleAddLineItem = () => {
    if (!newItem.description.trim() || !newItem.quantity || !newItem.unit_rate) {
      setError('All line item fields are required');
      return;
    }

    const item = {
      id: Date.now(),
      description: newItem.description,
      quantity: parseFloat(newItem.quantity),
      unit_rate: parseFloat(newItem.unit_rate),
      amount: parseFloat(newItem.quantity) * parseFloat(newItem.unit_rate),
    };

    setLineItems([...lineItems, item]);
    setNewItem({ description: '', quantity: '', unit_rate: '', stock_item: null });
    setError(null);
  };

  const handleRemoveLineItem = (id: number) => {
    setLineItems(lineItems.filter((item) => item.id !== id));
  };

  const totalJobCost = lineItems.reduce((sum, item) => sum + item.amount, 0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (!formData.job_number.trim()) {
        throw new Error('Job number is required');
      }
      if (!formData.customer_name.trim()) {
        throw new Error('Customer name is required');
      }
      if (lineItems.length === 0) {
        throw new Error('At least one line item is required');
      }

      // Auto-generate job number if not provided
      const jobNumber = formData.job_number.trim() || `JB-${Date.now()}`;
      
      // First create the job card
      const jobCardData = {
        job_number: jobNumber,
        debtor_account_number: formData.debtor_account_number, // Include debtor account
        job_date: formData.start_date || new Date().toISOString().split('T')[0],
        customer_name: formData.customer_name,
        description: formData.job_description,
        status: 'ACTIVE', // Backend only accepts ACTIVE, CONVERTED_TO_INVOICE, or CANCELLED
        registration_number: '',
        telephone: '',
        address: '',
      };

      // Create the job card first
      const response = await jobCardsApi.create(jobCardData as any);
      const jobCardId = response.id;

      // Then add line items if any exist
      if (lineItems.length > 0) {
        const lineItemsData = lineItems.map((item, index) => ({
          item_code: item.stock_item?.stock_code || '',
          line_number: index + 1,
          description: item.description,
          quantity: item.quantity,
          unit_price: item.unit_rate,
          discount_percentage: 0,
          tax_code: 1, // 1 = STANDARD (14%)
          stock_code: item.stock_item?.stock_code || ''
        }));
        
        await jobCardsApi.addLineItems(jobCardId, lineItemsData as any);
      }

      setSuccess('Job card created successfully');
      setTimeout(() => router.push('/dashboard/pos/job-costing'), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create job card');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4 flex items-center gap-4">
        <button
          onClick={() => router.back()}
          className="text-blue-600 hover:text-blue-700"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Create Job Card</h1>
          <p className="text-sm text-gray-500">Record new job for costing and tracking</p>
        </div>
      </div>

      <div className="p-6">
        {error && (
          <Card className="border-red-200 bg-red-50 mb-6">
            <CardContent className="pt-6 flex gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
              <p className="text-red-800">{error}</p>
            </CardContent>
          </Card>
        )}

        {success && (
          <Card className="border-green-200 bg-green-50 mb-6">
            <CardContent className="pt-6 flex gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
              <p className="text-green-800">{success}</p>
            </CardContent>
          </Card>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Job Details */}
          <Card>
            <CardHeader>
              <CardTitle>Job Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Job Number *
                  </label>
                  <Input
                    type="text"
                    name="job_number"
                    placeholder="JOB-001"
                    value={formData.job_number}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Customer Name *
                  </label>
                  <Input
                    value={formData.customer_name}
                    onChange={(e) => handleCustomerNameChange(e.target.value)}
                    placeholder="Enter customer name manually"
                    className="mb-2"
                  />
                  <p className="text-xs text-gray-500 mb-2">
                    Or select from debtors:
                  </p>
                  <DebtorPicker
                    onSelect={handleDebtorSelect}
                    disabled={!user}
                  />
                  {selectedDebtor && (
                    <p className="mt-1 text-sm text-green-600">
                      Selected: {selectedDebtor.name} ({selectedDebtor.dno})
                    </p>
                  )}
                  {formData.customer_name && !selectedDebtor && (
                    <p className="mt-1 text-sm text-blue-600">
                      Manual entry: {formData.customer_name}
                    </p>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Job Description *
                </label>
                <textarea
                  name="job_description"
                  placeholder="Describe the job"
                  value={formData.job_description}
                  onChange={handleChange}
                  rows={3}
                  className="w-full px-3 py-2 border rounded-lg"
                  required
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Start Date
                  </label>
                  <Input
                    type="date"
                    name="start_date"
                    value={formData.start_date}
                    onChange={handleChange}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Status
                  </label>
                  <select
                    name="status"
                    value={formData.status}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border rounded-lg bg-white"
                  >
                    <option value="open">Open</option>
                    <option value="in_progress">In Progress</option>
                    <option value="completed">Completed</option>
                  </select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Line Items */}
          <Card>
            <CardHeader>
              <CardTitle>Job Costs</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Stock Item
                  </label>
                  <StockItemPicker
                    onSelect={handleStockSelect}
                    disabled={!user}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Quantity
                  </label>
                  <Input
                    type="number"
                    placeholder="0"
                    value={newItem.quantity || ''}
                    onChange={(e) =>
                      setNewItem({ ...newItem, quantity: e.target.value })
                    }
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Unit Rate
                  </label>
                  <div className="flex gap-2">
                    <Input
                      type="number"
                      placeholder="0.00"
                      step="0.01"
                      value={newItem.unit_rate}
                      onChange={(e) =>
                        setNewItem({ ...newItem, unit_rate: e.target.value })
                      }
                    />
                    <Button
                      type="button"
                      onClick={handleAddLineItem}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>

              {lineItems.length > 0 ? (
                <div className="border rounded-lg overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Description</TableHead>
                        <TableHead className="text-right">Qty</TableHead>
                        <TableHead className="text-right">Unit Rate</TableHead>
                        <TableHead className="text-right">Amount</TableHead>
                        <TableHead className="w-10"></TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {lineItems.map((item) => (
                        <TableRow key={item.id}>
                          <TableCell>{item.description}</TableCell>
                          <TableCell className="text-right">{item.quantity}</TableCell>
                          <TableCell className="text-right">
                            R{item.unit_rate.toFixed(2)}
                          </TableCell>
                          <TableCell className="text-right font-medium">
                            R{item.amount.toFixed(2)}
                          </TableCell>
                          <TableCell className="text-center">
                            <button
                              type="button"
                              onClick={() => handleRemoveLineItem(item.id)}
                              className="text-red-600 hover:text-red-700"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </TableCell>
                        </TableRow>
                      ))}
                      <TableRow className="bg-gray-50 font-bold">
                        <TableCell colSpan={3} className="text-right">
                          Total Job Cost:
                        </TableCell>
                        <TableCell className="text-right text-lg text-blue-900">
                          R{totalJobCost.toFixed(2)}
                        </TableCell>
                        <TableCell></TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <p className="text-gray-500 text-center py-4">No line items added yet</p>
              )}
            </CardContent>
          </Card>

          {/* Actions */}
          <div className="flex gap-4 justify-end">
            <Button
              type="button"
              onClick={() => router.back()}
              variant="outline"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              className="bg-blue-600 hover:bg-blue-700"
              disabled={loading}
            >
              {loading ? 'Saving...' : 'Create Job Card'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
