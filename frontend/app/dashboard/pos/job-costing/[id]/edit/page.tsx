'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuth } from '@/lib/useAuth';
import { jobCardsApi } from '@/lib/jobCardsApi';
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
import { DebtorPicker } from '@/components/pos';

export default function EditJobCardPage() {
  const router = useRouter();
  const params = useParams();
  const { user } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);

  const jobId = params.id as string;

  const [formData, setFormData] = useState({
    job_number: '',
    customer_name: '',
    job_description: '',
    start_date: '',
    status: 'ACTIVE',
  });

  const [lineItems, setLineItems] = useState<any[]>([]);
  const [newItem, setNewItem] = useState({
    description: '',
    quantity: '',
    unit_rate: '',
  });

  useEffect(() => {
    if (jobId) {
      fetchJobCard();
    }
  }, [jobId]);

  const fetchJobCard = async () => {
    setInitialLoading(true);
    try {
      const response = await jobCardsApi.get(jobId);
      setFormData({
        job_number: response.job_number || '',
        customer_name: response.customer_name || '',
        job_description: response.description || '',
        start_date: response.job_date || '',
        status: response.status || 'ACTIVE',
      });
      
      // Load existing line items
      if (response.lines && response.lines.length > 0) {
        setLineItems(response.lines.map((line: any, index: number) => ({
          id: line.id || Date.now() + index,
          description: line.description,
          quantity: parseFloat(line.quantity),
          unit_rate: parseFloat(line.unit_price),
          amount: parseFloat(line.line_total) || parseFloat(line.quantity) * parseFloat(line.unit_price),
        })));
      }
    } catch (err) {
      console.error('Error fetching job card:', err);
      setError('Failed to load job card');
    } finally {
      setInitialLoading(false);
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
    setNewItem({ description: '', quantity: '', unit_rate: '' });
    setError(null);
  };

  const handleRemoveLineItem = (id: number) => {
    setLineItems(lineItems.filter((item) => item.id !== id));
  };

  const totalJobCost = lineItems.reduce((sum, item) => sum + item.amount, 0);

  const mapStatusToBackend = (status: string): string => {
    switch (status) {
      case 'open': return 'ACTIVE';
      case 'in_progress': return 'ACTIVE';
      case 'completed': return 'COMPLETED';
      default: return status;
    }
  };

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

      // Update job card
      const jobCardData = {
        job_number: formData.job_number,
        job_date: formData.start_date || new Date().toISOString().split('T')[0],
        customer_name: formData.customer_name,
        description: formData.job_description,
        status: mapStatusToBackend(formData.status),
        registration_number: '',
        telephone: '',
        address: '',
      };

      await jobCardsApi.update(jobId, jobCardData as any);

      // Note: For line items, you would need to implement add/remove/update
      // For now, the basic job card update works

      setSuccess('Job card updated successfully');
      setTimeout(() => router.push(`/dashboard/pos/job-costing/${jobId}`), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update job card');
    } finally {
      setLoading(false);
    }
  };

  if (initialLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">Loading...</div>
      </div>
    );
  }

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
          <h1 className="text-2xl font-bold text-gray-900">Edit Job Card</h1>
          <p className="text-sm text-gray-500">Update job card details</p>
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
                  <DebtorPicker
                    onSelect={(debtor) =>
                      setFormData((prev) => ({ ...prev, customer_name: debtor.name }))
                    }
                    placeholder="Search customers, or edit below..."
                  />
                  <Input
                    type="text"
                    name="customer_name"
                    placeholder="Customer name"
                    value={formData.customer_name}
                    onChange={handleChange}
                    required
                    className="mt-2"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Job Description
                </label>
                <textarea
                  name="job_description"
                  placeholder="Describe the job"
                  value={formData.job_description}
                  onChange={handleChange}
                  rows={3}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Date
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
                    <option value="ACTIVE">Active</option>
                    <option value="IN_PROGRESS">In Progress</option>
                    <option value="COMPLETED">Completed</option>
                    <option value="CONVERTED_TO_INVOICE">Converted to Invoice</option>
                    <option value="CANCELLED">Cancelled</option>
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
                    Description
                  </label>
                  <Input
                    type="text"
                    placeholder="Cost description"
                    value={newItem.description}
                    onChange={(e) =>
                      setNewItem({ ...newItem, description: e.target.value })
                    }
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
              {loading ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
