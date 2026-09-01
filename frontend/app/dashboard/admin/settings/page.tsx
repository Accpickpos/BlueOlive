// app/dashboard/admin/settings/page.tsx
"use client";
import { useState, useEffect } from "react";
import { Settings, Plus, Trash2, Edit2, Loader, Zap, Upload, Download, Check, X, Clock, FileBarChart, ShieldCheck, Receipt, ArrowRight } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { api, getApiErrorMessage } from "@/lib/api";
import UsersListPanel from "@/components/UsersListPanel";
import Link from "next/link";

// Available fields for import mapping by model type
const IMPORT_FIELD_MAPPINGS = {
  debtor: [
    'account_number','name','search_name','contact_person','telephone1','telephone2','fax',
    'postal_address_line1','postal_address_line2','postal_address_line3','postal_code',
    'delivery_address_line1','delivery_address_line2','delivery_address_line3','delivery_code',
    'vat_number','credit_limit','trade_discount','price_level','terms','prompt_discount_percentage',
    'account_category','current_balance','balance_30_days','balance_60_days','balance_90_days','is_blocked',
  ],
  creditor: [
    'supplier_code','supplier_name','contact_person','telephone','fax','email',
    'postal_address_line1','postal_address_line2','postal_address_line3','postal_code',
    'vat_number','payment_terms','discount_percentage','settlement_discount','current_balance',
  ],
  stock: [
    'item_code','item_name','description','quantity_on_hand','quantity_on_order','reorder_level',
    'unit_price','cost_price','category','unit_of_measure',
  ],
};

interface SalesDepartment { id: number; number: number; name: string; is_active: boolean; }
interface User { id: number; number: number; name: string; user_username?: string; commission_rate: number; is_active: boolean; }
interface IncomeCategory { id: number; number: number; name: string; is_active: boolean; }
interface ExpenseCategory { id: number; number: number; name: string; category_type: string; is_active: boolean; }
interface TaxCode { id: number; code: number; description: string; rate: number; is_default: boolean; is_active: boolean; }
interface CostingCategory { id: number; name: string; costing_method: 'A' | 'L'; pricing_method: 'I' | 'E'; description?: string; is_default: boolean; is_active: boolean; }
interface PaymentMethod { id: number; code: string; name: string; requires_reference: boolean; is_electronic: boolean; is_active: boolean; }
interface CreditTerms { id: number; days: number; description: string; is_active: boolean; }
interface SystemConfig {
  id: number; company_name: string; company_address: string; company_phone: string; company_email: string;
  company_vat_number: string; company_registration_number: string; current_financial_year: number;
  current_period: number; default_interest_rate: number; charge_interest_on_overdue: boolean;
  currency_symbol: string; decimal_places: number;
}

type TabType = 'departments' | 'users' | 'income' | 'expense' | 'tax' | 'costing' | 'payment' | 'credit' | 'system' | 'seeding';

interface Shop { id: number; name: string; }
interface FileAnalysis { import_id: string; file_type: string; headers: string[]; total_rows: number; sample_data: any[]; suggested_mappings: { [key: string]: string }; }
interface ImportMapping { [key: string]: string; }


export default function AdminSettingsPage() {
  const [activeTab, setActiveTab] = useState<TabType>('departments');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [refreshUsersKey, setRefreshUsersKey] = useState(0);
  const [shops, setShops] = useState<Shop[]>([]);
  const [shopId, setShopId] = useState<number | null>(null);

  const [departments, setDepartments] = useState<SalesDepartment[]>([]);
  const [newDept, setNewDept] = useState({ number: '', name: '' });
  const [editingDeptId, setEditingDeptId] = useState<number | null>(null);

  const [incomeCategories, setIncomeCategories] = useState<IncomeCategory[]>([]);
  const [newIncome, setNewIncome] = useState({ number: '', name: '' });
  const [editingIncomeId, setEditingIncomeId] = useState<number | null>(null);
  const [editingIncome, setEditingIncome] = useState<IncomeCategory | null>(null);

  const [expenseCategories, setExpenseCategories] = useState<ExpenseCategory[]>([]);
  const [newExpense, setNewExpense] = useState({ number: '', name: '', category_type: 'BOTH' });
  const [editingExpenseId, setEditingExpenseId] = useState<number | null>(null);
  const [editingExpense, setEditingExpense] = useState<ExpenseCategory | null>(null);

  const [taxCodes, setTaxCodes] = useState<TaxCode[]>([]);
  const [newTax, setNewTax] = useState({ code: '', description: '', rate: '' });
  const [editingTaxId, setEditingTaxId] = useState<number | null>(null);
  const [editingTax, setEditingTax] = useState<TaxCode | null>(null);

  const [costingCategories, setCostingCategories] = useState<CostingCategory[]>([]);
  const [newCosting, setNewCosting] = useState({ name: '', costing_method: 'A', pricing_method: 'E', description: '' });
  const [editingCostingId, setEditingCostingId] = useState<number | null>(null);
  const [editingCosting, setEditingCosting] = useState<CostingCategory | null>(null);

  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [newPayment, setNewPayment] = useState({ code: '', name: '', is_electronic: false });
  const [editingPaymentId, setEditingPaymentId] = useState<number | null>(null);
  const [editingPayment, setEditingPayment] = useState<PaymentMethod | null>(null);

  const [creditTerms, setCreditTerms] = useState<CreditTerms[]>([]);
  const [newCredit, setNewCredit] = useState({ days: '', description: '' });
  const [editingCreditId, setEditingCreditId] = useState<number | null>(null);
  const [editingCredit, setEditingCredit] = useState<CreditTerms | null>(null);

  const [importFile, setImportFile] = useState<File | null>(null);
  const [fileAnalysis, setFileAnalysis] = useState<FileAnalysis | null>(null);
  const [importMappings, setImportMappings] = useState<ImportMapping>({});
  const [selectedModelType, setSelectedModelType] = useState<'debtor' | 'creditor' | 'stock'>('debtor');
  const [importLoading, setImportLoading] = useState(false);
  const [importProgress, setImportProgress] = useState<number>(0);
  const [showPreview, setShowPreview] = useState(false);
  const [importResult, setImportResult] = useState<any>(null);
  const [importStep, setImportStep] = useState<'upload' | 'map' | 'preview' | 'import' | 'complete'>('upload');
  const [systemConfig, setSystemConfig] = useState<SystemConfig | null>(null);
  const [editingConfig, setEditingConfig] = useState(false);

  const [seedingStatus, setSeedingStatus] = useState<{ [key: string]: boolean }>({ settings: false, debtors: false, creditors: false, stock: false, all: false });
  const [seedingOutput, setSeedingOutput] = useState<{ [key: string]: string }>({});
  const [seedingError, setSeedingError] = useState<string | null>(null);

  useEffect(() => {
    loadShops();
    loadData();
  }, [activeTab]);

  const loadShops = async () => {
    try {
      const shopsRes = await api.get('/api/shops/');
      const shopsList = shopsRes.data.results || shopsRes.data;
      setShops(shopsList);
      if (shopsList.length > 0 && !shopId) setShopId(shopsList[0].id);
    } catch (error) { console.error('Failed to load shops:', error); }
  };

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      switch (activeTab) {
        case 'departments':
          try {
            const deptRes = await api.get('/api/settings/departments/');
            setDepartments(deptRes.data.results || deptRes.data);
          } catch (error: any) {
            if (error.response?.status === 500) { setError('Settings database not initialized. Please create a shop first.'); setDepartments([]); }
            else throw error;
          }
          break;
        case 'users': break;
        case 'income':
          try {
            const incomeRes = await api.get('/api/settings/income-categories/');
            setIncomeCategories(incomeRes.data.results || incomeRes.data);
          } catch (error: any) {
            if (error.response?.status === 500) { setError('Settings database not initialized. Please create a shop first.'); setIncomeCategories([]); }
            else throw error;
          }
          break;
        case 'expense':
          try {
            const expenseRes = await api.get('/api/settings/expense-categories/');
            setExpenseCategories(expenseRes.data.results || expenseRes.data);
          } catch (error: any) {
            if (error.response?.status === 500) { setError('Settings database not initialized. Please create a shop first.'); setExpenseCategories([]); }
            else throw error;
          }
          break;
        case 'tax':
          try {
            const taxRes = await api.get('/api/settings/tax-codes/');
            setTaxCodes(taxRes.data.results || taxRes.data);
          } catch (error: any) {
            if (error.response?.status === 500) { setError('Settings database not initialized. Please create a shop first.'); setTaxCodes([]); }
            else throw error;
          }
          break;
        case 'costing':
          try {
            const costingRes = await api.get('/api/settings/costing-categories/');
            setCostingCategories(costingRes.data.results || costingRes.data);
          } catch (error: any) {
            if (error.response?.status === 500) { setError('Settings database not initialized. Please create a shop first.'); setCostingCategories([]); }
            else throw error;
          }
          break;
        case 'payment':
          try {
            const paymentRes = await api.get('/api/settings/payment-methods/');
            setPaymentMethods(paymentRes.data.results || paymentRes.data);
          } catch (error: any) {
            if (error.response?.status === 500) { setError('Settings database not initialized. Please create a shop first.'); setPaymentMethods([]); }
            else throw error;
          }
          break;
        case 'credit':
          try {
            const creditRes = await api.get('/api/settings/credit-terms/');
            setCreditTerms(creditRes.data.results || creditRes.data);
          } catch (error: any) {
            if (error.response?.status === 500) { setError('Settings database not initialized. Please create a shop first.'); setCreditTerms([]); }
            else throw error;
          }
          break;
        case 'system':
          try {
            const systemRes = await api.get('/api/settings/system-config/');
            setSystemConfig(systemRes.data.results?.[0] || systemRes.data);
          } catch (error: any) {
            if (error.response?.status === 500) { setError('Settings database not initialized. Please create a shop first.'); setSystemConfig(null); }
            else throw error;
          }
          break;
        case 'seeding': break;
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const addDepartment = async () => {
    if (!newDept.number || !newDept.name) { setError('Please fill in all fields'); return; }
    if (!shopId) { setError('No shop selected. Please ensure a shop has been created.'); return; }
    try {
      setLoading(true);
      await api.post('/api/settings/departments/', { shop_id: shopId, number: parseInt(newDept.number), name: newDept.name, is_active: true });
      setSuccessMessage('Department added successfully!');
      setNewDept({ number: '', name: '' });
      setError(null);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadData();
    } catch (error: any) { setError(error.response?.data?.detail || 'Failed to add department'); }
    finally { setLoading(false); }
  };

  const deleteDepartment = async (id: number) => {
    if (!confirm('Are you sure you want to delete this department?')) return;
    try {
      setLoading(true);
      await api.delete(`/api/settings/departments/${id}/`);
      setSuccessMessage('Department deleted successfully!');
      setError(null);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadData();
    } catch (error: any) { setError(error.response?.data?.detail || 'Failed to delete department'); }
    finally { setLoading(false); }
  };

  const updateDepartment = async (id: number, data: any) => {
    try {
      setLoading(true);
      await api.put(`/api/settings/departments/${id}/`, data);
      setSuccessMessage('Department updated successfully!');
      setEditingDeptId(null);
      setError(null);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadData();
    } catch (error: any) { setError(error.response?.data?.detail || 'Failed to update department'); }
    finally { setLoading(false); }
  };

  const addIncomeCategory = async () => {
    if (!newIncome.number || !newIncome.name) { setError('Please fill in all fields'); return; }
    if (!shopId) { setError('No shop selected. Please ensure a shop has been created.'); return; }
    try {
      setLoading(true);
      await api.post('/api/settings/income-categories/', { number: parseInt(newIncome.number), name: newIncome.name, is_active: true });
      setSuccessMessage('Income category added successfully!');
      setNewIncome({ number: '', name: '' });
      setError(null);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadData();
    } catch (error: any) { setError(error.response?.data?.detail || 'Failed to add income category'); }
    finally { setLoading(false); }
  };

  const deleteIncomeCategory = async (id: number) => {
    if (!confirm('Are you sure you want to delete this income category?')) return;
    try {
      setLoading(true);
      await api.delete(`/api/settings/income-categories/${id}/`);
      setSuccessMessage('Income category deleted successfully!');
      setError(null);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadData();
    } catch (error: any) { setError(error.response?.data?.detail || 'Failed to delete income category'); }
    finally { setLoading(false); }
  };

  const updateIncomeCategory = async (id: number, data: any) => {
    try {
      setLoading(true);
      await api.put(`/api/settings/income-categories/${id}/`, data);
      setSuccessMessage('Income category updated successfully!');
      setEditingIncomeId(null);
      setEditingIncome(null);
      setError(null);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadData();
    } catch (error: any) { setError(error.response?.data?.detail || 'Failed to update income category'); }
    finally { setLoading(false); }
  };

  const addExpenseCategory = async () => {
    if (!newExpense.number || !newExpense.name) { setError('Please fill in all fields'); return; }
    if (!shopId) { setError('No shop selected. Please ensure a shop has been created.'); return; }
    try {
      setLoading(true);
      await api.post('/api/settings/expense-categories/', { number: parseInt(newExpense.number), name: newExpense.name, category_type: newExpense.category_type || 'BOTH', is_active: true });
      setSuccessMessage('Expense category added successfully!');
      setNewExpense({ number: '', name: '', category_type: '' });
      setError(null);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadData();
    } catch (error: any) { setError(error.response?.data?.detail || 'Failed to add expense category'); }
    finally { setLoading(false); }
  };

  const deleteExpenseCategory = async (id: number) => {
    if (!confirm('Are you sure you want to delete this expense category?')) return;
    try {
      setLoading(true);
      await api.delete(`/api/settings/expense-categories/${id}/`);
      setSuccessMessage('Expense category deleted successfully!');
      setError(null);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadData();
    } catch (error: any) { setError(error.response?.data?.detail || 'Failed to delete expense category'); }
    finally { setLoading(false); }
  };

  const updateExpenseCategory = async (id: number, data: any) => {
    try {
      setLoading(true);
      await api.put(`/api/settings/expense-categories/${id}/`, data);
      setSuccessMessage('Expense category updated successfully!');
      setEditingExpenseId(null);
      setEditingExpense(null);
      setError(null);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadData();
    } catch (error: any) { setError(error.response?.data?.detail || 'Failed to update expense category'); }
    finally { setLoading(false); }
  };

  const addTaxCode = async () => {
    if (!newTax.code || !newTax.description || !newTax.rate) { setError('Please fill in all fields'); return; }
    if (!shopId) { setError('No shop selected. Please ensure a shop has been created.'); return; }
    try {
      setLoading(true);
      await api.post('/api/settings/tax-codes/', { shop_id: shopId, code: parseInt(newTax.code), description: newTax.description, rate: parseFloat(newTax.rate), is_active: true });
      setSuccessMessage('Tax code added successfully!');
      setNewTax({ code: '', description: '', rate: '' });
      setError(null);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadData();
    } catch (error: any) { setError(error.response?.data?.detail || 'Failed to add tax code'); }
    finally { setLoading(false); }
  };

  const deleteTaxCode = async (id: number) => {
    if (!confirm('Are you sure you want to delete this tax code?')) return;
    try {
      setLoading(true);
      await api.delete(`/api/settings/tax-codes/${id}/`);
      setSuccessMessage('Tax code deleted successfully!');
      setError(null);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadData();
    } catch (error: any) { setError(error.response?.data?.detail || 'Failed to delete tax code'); }
    finally { setLoading(false); }
  };

  const updateTaxCode = async (id: number, data: any) => {
    try {
      setLoading(true);
      await api.put(`/api/settings/tax-codes/${id}/`, data);
      setSuccessMessage('Tax code updated successfully!');
      setEditingTaxId(null);
      setEditingTax(null);
      setError(null);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadData();
    } catch (error: any) { setError(error.response?.data?.detail || 'Failed to update tax code'); }
    finally { setLoading(false); }
  };

  const addCostingCategory = async () => {
    if (!newCosting.name) { setError('Please fill in the name'); return; }
    try {
      setLoading(true);
      await api.post('/api/settings/costing-categories/', { name: newCosting.name, costing_method: newCosting.costing_method, pricing_method: newCosting.pricing_method, description: newCosting.description, is_active: true });
      setSuccessMessage('Costing category added successfully!');
      setNewCosting({ name: '', costing_method: 'A', pricing_method: 'E', description: '' });
      setError(null);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadData();
    } catch (error: any) { setError(error.response?.data?.detail || 'Failed to add costing category'); }
    finally { setLoading(false); }
  };

  const deleteCostingCategory = async (id: number) => {
    if (!confirm('Are you sure you want to delete this costing category?')) return;
    try {
      setLoading(true);
      await api.delete(`/api/settings/costing-categories/${id}/`);
      setSuccessMessage('Costing category deleted successfully!');
      setError(null);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadData();
    } catch (error: any) { setError(error.response?.data?.detail || 'Failed to delete costing category'); }
    finally { setLoading(false); }
  };

  const updateCostingCategory = async (id: number, data: any) => {
    try {
      setLoading(true);
      await api.put(`/api/settings/costing-categories/${id}/`, data);
      setSuccessMessage('Costing category updated successfully!');
      setEditingCostingId(null);
      setEditingCosting(null);
      setError(null);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadData();
    } catch (error: any) { setError(error.response?.data?.detail || 'Failed to update costing category'); }
    finally { setLoading(false); }
  };

  const setDefaultCostingCategory = async (id: number) => {
    try {
      setLoading(true);
      await api.post(`/api/settings/costing-categories/${id}/set_default/`);
      setSuccessMessage('Default costing method updated!');
      setError(null);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadData();
    } catch (error: any) { setError(error.response?.data?.detail || 'Failed to set default costing category'); }
    finally { setLoading(false); }
  };

  const addPaymentMethod = async () => {
    if (!newPayment.code || !newPayment.name) { setError('Please fill in all fields'); return; }
    if (!shopId) { setError('No shop selected. Please ensure a shop has been created.'); return; }
    try {
      setLoading(true);
      await api.post('/api/settings/payment-methods/', { shop_id: shopId, code: newPayment.code, name: newPayment.name, is_electronic: newPayment.is_electronic, is_active: true });
      setSuccessMessage('Payment method added successfully!');
      setNewPayment({ code: '', name: '', is_electronic: false });
      setError(null);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadData();
    } catch (error: any) { setError(error.response?.data?.detail || 'Failed to add payment method'); }
    finally { setLoading(false); }
  };

  const deletePaymentMethod = async (id: number) => {
    if (!confirm('Are you sure you want to delete this payment method?')) return;
    try {
      setLoading(true);
      await api.delete(`/api/settings/payment-methods/${id}/`);
      setSuccessMessage('Payment method deleted successfully!');
      setError(null);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadData();
    } catch (error: any) { setError(error.response?.data?.detail || 'Failed to delete payment method'); }
    finally { setLoading(false); }
  };

  const updatePaymentMethod = async (id: number, data: any) => {
    try {
      setLoading(true);
      await api.put(`/api/settings/payment-methods/${id}/`, data);
      setSuccessMessage('Payment method updated successfully!');
      setEditingPaymentId(null);
      setEditingPayment(null);
      setError(null);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadData();
    } catch (error: any) { setError(error.response?.data?.detail || 'Failed to update payment method'); }
    finally { setLoading(false); }
  };

  const addCreditTerms = async () => {
    if (!newCredit.days || !newCredit.description) { setError('Please fill in all fields'); return; }
    if (!shopId) { setError('No shop selected. Please ensure a shop has been created.'); return; }
    try {
      setLoading(true);
      await api.post('/api/settings/credit-terms/', { shop_id: shopId, days: parseInt(newCredit.days), description: newCredit.description, is_active: true });
      setSuccessMessage('Credit term added successfully!');
      setNewCredit({ days: '', description: '' });
      setError(null);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadData();
    } catch (error: any) { setError(error.response?.data?.detail || 'Failed to add credit terms'); }
    finally { setLoading(false); }
  };

  const deleteCreditTerms = async (id: number) => {
    if (!confirm('Are you sure you want to delete these credit terms?')) return;
    try {
      setLoading(true);
      await api.delete(`/api/settings/credit-terms/${id}/`);
      setSuccessMessage('Credit term deleted successfully!');
      setError(null);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadData();
    } catch (error: any) { setError(error.response?.data?.detail || 'Failed to delete credit terms'); }
    finally { setLoading(false); }
  };

  const updateCreditTerms = async (id: number, data: any) => {
    try {
      setLoading(true);
      await api.put(`/api/settings/credit-terms/${id}/`, data);
      setSuccessMessage('Credit term updated successfully!');
      setEditingCreditId(null);
      setEditingCredit(null);
      setError(null);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadData();
    } catch (error: any) { setError(error.response?.data?.detail || 'Failed to update credit terms'); }
    finally { setLoading(false); }
  };

  // System Config Functions
  const saveSystemConfig = async () => {
    if (!systemConfig) return;
    try {
      setLoading(true);
      await api.put(`/api/settings/system-config/${systemConfig.id}/`, systemConfig);
      setSuccessMessage('System configuration saved successfully!');
      setEditingConfig(false);
      setError(null);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (error: any) {
      console.error('Failed to save system config:', error);
      setError(error.response?.data?.detail || 'Failed to save system configuration');
    } finally {
      setLoading(false);
    }
  };

  // Seeding Functions
  const seedData = async (seedType: 'settings' | 'debtors' | 'creditors' | 'stock' | 'all') => {
    try {
      setSeedingStatus((prev) => ({ ...prev, [seedType]: true }));
      setSeedingError(null);
      const endpoints = {
        settings: '/api/settings/system-config/seed_settings/',
        debtors: '/api/settings/system-config/seed_debtors/',
        creditors: '/api/settings/system-config/seed_creditors/',
        stock: '/api/settings/system-config/seed_stock_items/',
        all: '/api/settings/system-config/seed_all_data/',
      };
      const response = await api.post(endpoints[seedType]);
      setSeedingOutput((prev) => ({ ...prev, [seedType]: response.data.output || response.data.message || 'Seeding completed successfully!' }));
      setSuccessMessage(`${seedType.charAt(0).toUpperCase() + seedType.slice(1)} data seeded successfully!`);
      setTimeout(() => setSuccessMessage(null), 3000);
      setTimeout(() => loadData(), 1000);
    } catch (error: any) {
      setSeedingError(getApiErrorMessage(error, `Failed to seed ${seedType} data`));
    } finally {
      setSeedingStatus((prev) => ({ ...prev, [seedType]: false }));
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.name.endsWith('.csv') && !file.name.endsWith('.dbf')) { setError('Please select a CSV or DBF file'); return; }
      setImportFile(file);
      setFileAnalysis(null);
      setError(null);
    }
  };

  const handleFileUpload = async () => {
    if (!importFile) { setError('Please select a file first'); return; }
    try {
      setImportLoading(true);
      setError(null);
      const formData = new FormData();
      formData.append('file', importFile);
      const response = await api.post('/api/settings/import/upload_and_analyze/', formData);
      setFileAnalysis(response.data);
      const allFields = IMPORT_FIELD_MAPPINGS[selectedModelType] || [];
      const suggestedMappings = response.data.suggested_mappings || {};
      const fullMappings: ImportMapping = {};
      allFields.forEach(field => { fullMappings[field] = suggestedMappings[field] || ''; });
      setImportMappings(fullMappings);
      setImportStep('map');
      setSuccessMessage(`File analyzed: ${response.data.total_rows} rows found`);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (error: any) { setError(getApiErrorMessage(error, 'Failed to analyze file')); }
    finally { setImportLoading(false); }
  };

  const handleColumnMapping = (djangoField: string, sourceColumn: string) => {
    setImportMappings((prev) => ({ ...prev, [djangoField]: sourceColumn }));
  };

  const handlePreview = async () => {
    if (!fileAnalysis) { setError('No file analyzed'); return; }
    try {
      setImportLoading(true);
      setError(null);
      const response = await api.post('/api/settings/import/preview/', { import_id: fileAnalysis.import_id, mappings: importMappings, model_type: selectedModelType });
      setImportResult(response.data);
      setShowPreview(true);
      setImportStep('preview');
    } catch (error: any) { setError(getApiErrorMessage(error, 'Failed to generate preview')); }
    finally { setImportLoading(false); }
  };

  const handleImport = async () => {
    if (!fileAnalysis) { setError('No file analyzed'); return; }
    try {
      setImportLoading(true);
      setImportStep('import');
      setError(null);
      setImportProgress(0);
      const response = await api.post('/api/settings/import/import_data/', { import_id: fileAnalysis.import_id, mappings: importMappings, model_type: selectedModelType });
      setImportResult(response.data);
      setImportProgress(100);
      setImportStep('complete');
      setSuccessMessage(`Import complete! ${response.data.created || 0} records created, ${response.data.updated || 0} updated`);
      setTimeout(() => { setImportFile(null); setFileAnalysis(null); setImportMappings({}); setShowPreview(false); setImportStep('upload'); setImportResult(null); }, 3000);
    } catch (error: any) { setError(getApiErrorMessage(error, 'Failed to import data')); setImportStep('preview'); }
    finally { setImportLoading(false); }
  };

  const resetImport = () => {
    setImportFile(null); setFileAnalysis(null); setImportMappings({}); setShowPreview(false); setImportStep('upload'); setImportResult(null); setError(null);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Settings className="h-6 w-6" />
        <h1 className="text-2xl font-bold">Admin Settings</h1>
      </div>

      <div className="flex gap-2 border-b overflow-x-auto">
        {(['departments', 'users', 'income', 'expense', 'tax', 'costing', 'payment', 'credit', 'system', 'seeding'] as TabType[]).map((tab) => (
          <button key={tab} onClick={() => setActiveTab(tab)} className={`px-4 py-2 font-medium whitespace-nowrap ${activeTab === tab ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600 hover:text-gray-900'}`}>
            {tab.replace('-', ' ').toUpperCase()}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-8"><Loader className="h-6 w-6 animate-spin" /></div>
      ) : (
        <>
          {activeTab === 'departments' && (
            <div className="space-y-4">
              {error && <Card className="border-red-200 bg-red-50"><CardContent className="p-6"><p className="text-red-800">{error}</p></CardContent></Card>}
              {successMessage && <Card className="border-green-200 bg-green-50"><CardContent className="p-6"><p className="text-green-800">{successMessage}</p></CardContent></Card>}
              <Card>
                <CardContent className="p-6 space-y-4">
                  <h2 className="text-lg font-semibold">Add Department</h2>
                  <div className="grid grid-cols-2 gap-4">
                    <input type="number" placeholder="Number (1-999)" value={newDept.number} onChange={(e) => setNewDept({ ...newDept, number: e.target.value })} className="border p-2 rounded-lg" />
                    <input type="text" placeholder="Department Name" value={newDept.name} onChange={(e) => setNewDept({ ...newDept, name: e.target.value })} className="border p-2 rounded-lg" />
                  </div>
                  <button onClick={addDepartment} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"><Plus className="h-4 w-4" /> Add Department</button>
                </CardContent>
              </Card>
              {departments.length === 0 ? (
                <Card><CardContent className="p-6"><p className="text-gray-600">No departments created yet.</p></CardContent></Card>
              ) : (
                <div className="space-y-2">
                  {departments.map((dept) => (
                    <Card key={dept.id}>
                      <CardContent className="p-4 flex justify-between items-center">
                        <div>
                          <p className="font-semibold">{dept.number} - {dept.name}</p>
                          <p className="text-sm text-gray-600">{dept.is_active ? 'Active' : 'Inactive'}</p>
                        </div>
                        <div className="flex gap-2">
                          <button onClick={() => deleteDepartment(dept.id)} className="p-2 text-red-600 hover:bg-red-50 rounded"><Trash2 className="h-4 w-4" /></button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'users' && <UsersListPanel refreshKey={refreshUsersKey} />}

          {activeTab === 'income' && (
            <div className="space-y-4">
              {error && <Card className="border-red-200 bg-red-50"><CardContent className="p-6"><p className="text-red-800">{error}</p></CardContent></Card>}
              {successMessage && <Card className="border-green-200 bg-green-50"><CardContent className="p-6"><p className="text-green-800">{successMessage}</p></CardContent></Card>}
              <Card>
                <CardContent className="p-6 space-y-4">
                  <h2 className="text-lg font-semibold">Add Income Category</h2>
                  <div className="grid grid-cols-2 gap-4">
                    <input type="number" placeholder="Number" value={newIncome.number} onChange={(e) => setNewIncome({ ...newIncome, number: e.target.value })} className="border p-2 rounded-lg" />
                    <input type="text" placeholder="Category Name" value={newIncome.name} onChange={(e) => setNewIncome({ ...newIncome, name: e.target.value })} className="border p-2 rounded-lg" />
                  </div>
                  <button onClick={addIncomeCategory} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"><Plus className="h-4 w-4" /> Add Income Category</button>
                </CardContent>
              </Card>
              <div className="space-y-2">
                {incomeCategories.map((income) => (
                  <Card key={income.id}>
                    <CardContent className="p-4">
                      {editingIncomeId === income.id && editingIncome ? (
                        <div className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                            <input type="number" value={editingIncome.number} onChange={(e) => setEditingIncome({ ...editingIncome, number: parseInt(e.target.value) })} className="border p-2 rounded-lg" />
                            <input type="text" value={editingIncome.name} onChange={(e) => setEditingIncome({ ...editingIncome, name: e.target.value })} className="border p-2 rounded-lg" />
                          </div>
                          <div className="flex gap-2">
                            <button onClick={() => updateIncomeCategory(income.id, editingIncome)} className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm">Save</button>
                            <button onClick={() => { setEditingIncomeId(null); setEditingIncome(null); }} className="px-3 py-1 bg-gray-400 text-white rounded hover:bg-gray-500 text-sm">Cancel</button>
                          </div>
                        </div>
                      ) : (
                        <div className="flex justify-between items-center">
                          <div>
                            <p className="font-semibold">{income.number} - {income.name}</p>
                            <p className="text-sm text-gray-600">{income.is_active ? 'Active' : 'Inactive'}</p>
                          </div>
                          <div className="flex gap-2">
                            <button onClick={() => { setEditingIncomeId(income.id); setEditingIncome(income); }} className="p-2 text-blue-600 hover:bg-blue-50 rounded"><Edit2 className="h-4 w-4" /></button>
                            <button onClick={() => deleteIncomeCategory(income.id)} className="p-2 text-red-600 hover:bg-red-50 rounded"><Trash2 className="h-4 w-4" /></button>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'expense' && (
            <div className="space-y-4">
              {error && <Card className="border-red-200 bg-red-50"><CardContent className="p-6"><p className="text-red-800">{error}</p></CardContent></Card>}
              {successMessage && <Card className="border-green-200 bg-green-50"><CardContent className="p-6"><p className="text-green-800">{successMessage}</p></CardContent></Card>}
              <Card>
                <CardContent className="p-6 space-y-4">
                  <h2 className="text-lg font-semibold">Add Expense Category</h2>
                  <div className="grid grid-cols-3 gap-4">
                    <input type="number" placeholder="Number" value={newExpense.number} onChange={(e) => setNewExpense({ ...newExpense, number: e.target.value })} className="border p-2 rounded-lg" />
                    <input type="text" placeholder="Category Name" value={newExpense.name} onChange={(e) => setNewExpense({ ...newExpense, name: e.target.value })} className="border p-2 rounded-lg" />
                    <select value={newExpense.category_type} onChange={(e) => setNewExpense({ ...newExpense, category_type: e.target.value })} className="border p-2 rounded-lg">
                      <option value="BOTH">Both</option>
                      <option value="CASHBOOK">Cash Book Only</option>
                      <option value="CREDITORS">Creditors Only</option>
                    </select>
                  </div>
                  <button onClick={addExpenseCategory} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"><Plus className="h-4 w-4" /> Add Expense Category</button>
                </CardContent>
              </Card>
              <div className="space-y-2">
                {expenseCategories.map((expense) => (
                  <Card key={expense.id}>
                    <CardContent className="p-4">
                      {editingExpenseId === expense.id && editingExpense ? (
                        <div className="space-y-4">
                          <div className="grid grid-cols-3 gap-4">
                            <input type="number" value={editingExpense.number} onChange={(e) => setEditingExpense({ ...editingExpense, number: parseInt(e.target.value) })} className="border p-2 rounded-lg" />
                            <input type="text" value={editingExpense.name} onChange={(e) => setEditingExpense({ ...editingExpense, name: e.target.value })} className="border p-2 rounded-lg" />
                            <select value={editingExpense.category_type} onChange={(e) => setEditingExpense({ ...editingExpense, category_type: e.target.value })} className="border p-2 rounded-lg">
                              <option value="BOTH">Both</option>
                              <option value="CASHBOOK">Cash Book Only</option>
                              <option value="CREDITORS">Creditors Only</option>
                            </select>
                          </div>
                          <div className="flex gap-2">
                            <button onClick={() => updateExpenseCategory(expense.id, editingExpense)} className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm">Save</button>
                            <button onClick={() => { setEditingExpenseId(null); setEditingExpense(null); }} className="px-3 py-1 bg-gray-400 text-white rounded hover:bg-gray-500 text-sm">Cancel</button>
                          </div>
                        </div>
                      ) : (
                        <div className="flex justify-between items-center">
                          <div>
                            <p className="font-semibold">{expense.number} - {expense.name}</p>
                            <p className="text-sm text-gray-600">Type: {expense.category_type}</p>
                          </div>
                          <div className="flex gap-2">
                            <button onClick={() => { setEditingExpenseId(expense.id); setEditingExpense(expense); }} className="p-2 text-blue-600 hover:bg-blue-50 rounded"><Edit2 className="h-4 w-4" /></button>
                            <button onClick={() => deleteExpenseCategory(expense.id)} className="p-2 text-red-600 hover:bg-red-50 rounded"><Trash2 className="h-4 w-4" /></button>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'tax' && (
            <div className="space-y-4">
              {error && <Card className="border-red-200 bg-red-50"><CardContent className="p-6"><p className="text-red-800">{error}</p></CardContent></Card>}
              {successMessage && <Card className="border-green-200 bg-green-50"><CardContent className="p-6"><p className="text-green-800">{successMessage}</p></CardContent></Card>}
              <Card>
                <CardContent className="p-6 space-y-4">
                  <h2 className="text-lg font-semibold">Add Tax Code</h2>
                  <div className="grid grid-cols-3 gap-4">
                    <input type="number" placeholder="Code" value={newTax.code} onChange={(e) => setNewTax({ ...newTax, code: e.target.value })} className="border p-2 rounded-lg" />
                    <input type="text" placeholder="Description" value={newTax.description} onChange={(e) => setNewTax({ ...newTax, description: e.target.value })} className="border p-2 rounded-lg" />
                    <input type="number" placeholder="Rate (%)" step="0.01" value={newTax.rate} onChange={(e) => setNewTax({ ...newTax, rate: e.target.value })} className="border p-2 rounded-lg" />
                  </div>
                  <button onClick={addTaxCode} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"><Plus className="h-4 w-4" /> Add Tax Code</button>
                </CardContent>
              </Card>
              <div className="space-y-2">
                {taxCodes.map((tax) => (
                  <Card key={tax.id}>
                    <CardContent className="p-4">
                      {editingTaxId === tax.id && editingTax ? (
                        <div className="space-y-4">
                          <div className="grid grid-cols-3 gap-4">
                            <input type="number" value={editingTax.code} onChange={(e) => setEditingTax({ ...editingTax, code: parseInt(e.target.value) })} className="border p-2 rounded-lg" />
                            <input type="text" value={editingTax.description} onChange={(e) => setEditingTax({ ...editingTax, description: e.target.value })} className="border p-2 rounded-lg" />
                            <input type="number" step="0.01" value={editingTax.rate} onChange={(e) => setEditingTax({ ...editingTax, rate: parseFloat(e.target.value) })} className="border p-2 rounded-lg" />
                          </div>
                          <div className="flex gap-2">
                            <button onClick={() => updateTaxCode(tax.id, editingTax)} className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm">Save</button>
                            <button onClick={() => { setEditingTaxId(null); setEditingTax(null); }} className="px-3 py-1 bg-gray-400 text-white rounded hover:bg-gray-500 text-sm">Cancel</button>
                          </div>
                        </div>
                      ) : (
                        <div className="flex justify-between items-center">
                          <div>
                            <p className="font-semibold">{tax.code} - {tax.description}</p>
                            <p className="text-sm text-gray-600">Rate: {tax.rate}% {tax.is_default && '(Default)'}</p>
                          </div>
                          <div className="flex gap-2">
                            <button onClick={() => { setEditingTaxId(tax.id); setEditingTax(tax); }} className="p-2 text-blue-600 hover:bg-blue-50 rounded"><Edit2 className="h-4 w-4" /></button>
                            <button onClick={() => deleteTaxCode(tax.id)} className="p-2 text-red-600 hover:bg-red-50 rounded"><Trash2 className="h-4 w-4" /></button>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'costing' && (
            <div className="space-y-4">
              {error && <Card className="border-red-200 bg-red-50"><CardContent className="p-6"><p className="text-red-800">{error}</p></CardContent></Card>}
              {successMessage && <Card className="border-green-200 bg-green-50"><CardContent className="p-6"><p className="text-green-800">{successMessage}</p></CardContent></Card>}
              <Card className="border-blue-200 bg-blue-50">
                <CardContent className="p-4">
                  <p className="text-sm text-blue-800">
                    Only one costing category can be the active system-wide method at a time (manual §8.1). Mark one as
                    Default below — that category&apos;s Costing Method (Average/Last Cost) drives Gross Profit calculations
                    across POS and Stock Control.
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-6 space-y-4">
                  <h2 className="text-lg font-semibold">Add Costing Category</h2>
                  <div className="grid grid-cols-2 gap-4">
                    <input type="text" placeholder="Name" value={newCosting.name} onChange={(e) => setNewCosting({ ...newCosting, name: e.target.value })} className="border p-2 rounded-lg" />
                    <input type="text" placeholder="Description (optional)" value={newCosting.description} onChange={(e) => setNewCosting({ ...newCosting, description: e.target.value })} className="border p-2 rounded-lg" />
                    <select value={newCosting.costing_method} onChange={(e) => setNewCosting({ ...newCosting, costing_method: e.target.value })} className="border p-2 rounded-lg">
                      <option value="A">Average Cost</option>
                      <option value="L">Last Cost</option>
                    </select>
                    <select value={newCosting.pricing_method} onChange={(e) => setNewCosting({ ...newCosting, pricing_method: e.target.value })} className="border p-2 rounded-lg">
                      <option value="I">Inclusive of VAT</option>
                      <option value="E">Exclusive of VAT</option>
                    </select>
                  </div>
                  <button onClick={addCostingCategory} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"><Plus className="h-4 w-4" /> Add Costing Category</button>
                </CardContent>
              </Card>
              <div className="space-y-2">
                {costingCategories.map((cat) => (
                  <Card key={cat.id}>
                    <CardContent className="p-4">
                      {editingCostingId === cat.id && editingCosting ? (
                        <div className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                            <input type="text" value={editingCosting.name} onChange={(e) => setEditingCosting({ ...editingCosting, name: e.target.value })} className="border p-2 rounded-lg" />
                            <input type="text" value={editingCosting.description || ''} onChange={(e) => setEditingCosting({ ...editingCosting, description: e.target.value })} className="border p-2 rounded-lg" />
                            <select value={editingCosting.costing_method} onChange={(e) => setEditingCosting({ ...editingCosting, costing_method: e.target.value as 'A' | 'L' })} className="border p-2 rounded-lg">
                              <option value="A">Average Cost</option>
                              <option value="L">Last Cost</option>
                            </select>
                            <select value={editingCosting.pricing_method} onChange={(e) => setEditingCosting({ ...editingCosting, pricing_method: e.target.value as 'I' | 'E' })} className="border p-2 rounded-lg">
                              <option value="I">Inclusive of VAT</option>
                              <option value="E">Exclusive of VAT</option>
                            </select>
                          </div>
                          <div className="flex gap-2">
                            <button onClick={() => updateCostingCategory(cat.id, editingCosting)} className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm">Save</button>
                            <button onClick={() => { setEditingCostingId(null); setEditingCosting(null); }} className="px-3 py-1 bg-gray-400 text-white rounded hover:bg-gray-500 text-sm">Cancel</button>
                          </div>
                        </div>
                      ) : (
                        <div className="flex justify-between items-center">
                          <div>
                            <p className="font-semibold">{cat.name} {cat.is_default && <span className="text-xs font-normal text-blue-700">(Default)</span>}</p>
                            <p className="text-sm text-gray-600">
                              {cat.costing_method === 'A' ? 'Average Cost' : 'Last Cost'} · {cat.pricing_method === 'I' ? 'Inclusive of VAT' : 'Exclusive of VAT'}
                            </p>
                          </div>
                          <div className="flex gap-2">
                            {!cat.is_default && (
                              <button onClick={() => setDefaultCostingCategory(cat.id)} className="px-3 py-1 text-sm text-blue-700 border border-blue-300 rounded hover:bg-blue-50">Set as Default</button>
                            )}
                            <button onClick={() => { setEditingCostingId(cat.id); setEditingCosting(cat); }} className="p-2 text-blue-600 hover:bg-blue-50 rounded"><Edit2 className="h-4 w-4" /></button>
                            <button onClick={() => deleteCostingCategory(cat.id)} className="p-2 text-red-600 hover:bg-red-50 rounded"><Trash2 className="h-4 w-4" /></button>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'payment' && (
            <div className="space-y-4">
              {error && <Card className="border-red-200 bg-red-50"><CardContent className="p-6"><p className="text-red-800">{error}</p></CardContent></Card>}
              {successMessage && <Card className="border-green-200 bg-green-50"><CardContent className="p-6"><p className="text-green-800">{successMessage}</p></CardContent></Card>}
              <Card>
                <CardContent className="p-6 space-y-4">
                  <h2 className="text-lg font-semibold">Add Payment Method</h2>
                  <div className="grid grid-cols-2 gap-4">
                    <input type="text" placeholder="Code (e.g., CASH)" value={newPayment.code} onChange={(e) => setNewPayment({ ...newPayment, code: e.target.value })} className="border p-2 rounded-lg" />
                    <input type="text" placeholder="Name" value={newPayment.name} onChange={(e) => setNewPayment({ ...newPayment, name: e.target.value })} className="border p-2 rounded-lg" />
                  </div>
                  <label className="flex items-center gap-2">
                    <input type="checkbox" checked={newPayment.is_electronic} onChange={(e) => setNewPayment({ ...newPayment, is_electronic: e.target.checked })} className="h-4 w-4" />
                    <span>Electronic Payment</span>
                  </label>
                  <button onClick={addPaymentMethod} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"><Plus className="h-4 w-4" /> Add Payment Method</button>
                </CardContent>
              </Card>
              <div className="space-y-2">
                {paymentMethods.map((method) => (
                  <Card key={method.id}>
                    <CardContent className="p-4">
                      {editingPaymentId === method.id && editingPayment ? (
                        <div className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                            <input type="text" value={editingPayment.code} onChange={(e) => setEditingPayment({ ...editingPayment, code: e.target.value })} className="border p-2 rounded-lg" />
                            <input type="text" value={editingPayment.name} onChange={(e) => setEditingPayment({ ...editingPayment, name: e.target.value })} className="border p-2 rounded-lg" />
                          </div>
                          <label className="flex items-center gap-2">
                            <input type="checkbox" checked={editingPayment.is_electronic} onChange={(e) => setEditingPayment({ ...editingPayment, is_electronic: e.target.checked })} className="h-4 w-4" />
                            <span>Electronic Payment</span>
                          </label>
                          <div className="flex gap-2">
                            <button onClick={() => updatePaymentMethod(method.id, editingPayment)} className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm">Save</button>
                            <button onClick={() => { setEditingPaymentId(null); setEditingPayment(null); }} className="px-3 py-1 bg-gray-400 text-white rounded hover:bg-gray-500 text-sm">Cancel</button>
                          </div>
                        </div>
                      ) : (
                        <div className="flex justify-between items-center">
                          <div>
                            <p className="font-semibold">{method.code} - {method.name}</p>
                            <p className="text-sm text-gray-600">{method.is_electronic ? 'Electronic' : 'Manual'}</p>
                          </div>
                          <div className="flex gap-2">
                            <button onClick={() => { setEditingPaymentId(method.id); setEditingPayment(method); }} className="p-2 text-blue-600 hover:bg-blue-50 rounded"><Edit2 className="h-4 w-4" /></button>
                            <button onClick={() => deletePaymentMethod(method.id)} className="p-2 text-red-600 hover:bg-red-50 rounded"><Trash2 className="h-4 w-4" /></button>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'credit' && (
            <div className="space-y-4">
              {error && <Card className="border-red-200 bg-red-50"><CardContent className="p-6"><p className="text-red-800">{error}</p></CardContent></Card>}
              {successMessage && <Card className="border-green-200 bg-green-50"><CardContent className="p-6"><p className="text-green-800">{successMessage}</p></CardContent></Card>}
              <Card>
                <CardContent className="p-6 space-y-4">
                  <h2 className="text-lg font-semibold">Add Credit Terms</h2>
                  <div className="grid grid-cols-2 gap-4">
                    <input type="number" placeholder="Days (0 = COD)" value={newCredit.days} onChange={(e) => setNewCredit({ ...newCredit, days: e.target.value })} className="border p-2 rounded-lg" />
                    <input type="text" placeholder="Description" value={newCredit.description} onChange={(e) => setNewCredit({ ...newCredit, description: e.target.value })} className="border p-2 rounded-lg" />
                  </div>
                  <button onClick={addCreditTerms} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"><Plus className="h-4 w-4" /> Add Credit Terms</button>
                </CardContent>
              </Card>
              <div className="space-y-2">
                {creditTerms.map((term) => (
                  <Card key={term.id}>
                    <CardContent className="p-4">
                      {editingCreditId === term.id && editingCredit ? (
                        <div className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                            <input type="number" value={editingCredit.days} onChange={(e) => setEditingCredit({ ...editingCredit, days: parseInt(e.target.value) })} className="border p-2 rounded-lg" />
                            <input type="text" value={editingCredit.description} onChange={(e) => setEditingCredit({ ...editingCredit, description: e.target.value })} className="border p-2 rounded-lg" />
                          </div>
                          <div className="flex gap-2">
                            <button onClick={() => updateCreditTerms(term.id, editingCredit)} className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm">Save</button>
                            <button onClick={() => { setEditingCreditId(null); setEditingCredit(null); }} className="px-3 py-1 bg-gray-400 text-white rounded hover:bg-gray-500 text-sm">Cancel</button>
                          </div>
                        </div>
                      ) : (
                        <div className="flex justify-between items-center">
                          <p className="font-semibold">{term.days} days - {term.description}</p>
                          <div className="flex gap-2">
                            <button onClick={() => { setEditingCreditId(term.id); setEditingCredit(term); }} className="p-2 text-blue-600 hover:bg-blue-50 rounded"><Edit2 className="h-4 w-4" /></button>
                            <button onClick={() => deleteCreditTerms(term.id)} className="p-2 text-red-600 hover:bg-red-50 rounded"><Trash2 className="h-4 w-4" /></button>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'system' && (
            <>
              {error && <Card className="border-red-200 bg-red-50"><CardContent className="p-6"><p className="text-red-800">{error}</p></CardContent></Card>}
              {successMessage && <Card className="border-green-200 bg-green-50"><CardContent className="p-6"><p className="text-green-800">{successMessage}</p></CardContent></Card>}
              {seedingError && <Card className="border-red-200 bg-red-50"><CardContent className="p-6"><p className="text-red-800">{seedingError}</p></CardContent></Card>}
              {!error && systemConfig && (
                <div className="space-y-4">
                  <Card>
                    <CardContent className="p-6 space-y-4">
                      <div className="flex justify-between items-center mb-4">
                        <h2 className="text-lg font-semibold">System Configuration</h2>
                        <button onClick={() => setEditingConfig(!editingConfig)} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                          <Edit2 className="h-4 w-4" /> {editingConfig ? 'Cancel' : 'Edit'}
                        </button>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        {editingConfig ? (
                          <>
                            <input type="text" placeholder="Company Name" value={systemConfig.company_name} onChange={(e) => setSystemConfig({ ...systemConfig, company_name: e.target.value })} className="border p-2 rounded-lg col-span-2" />
                            <input type="email" placeholder="Company Email" value={systemConfig.company_email} onChange={(e) => setSystemConfig({ ...systemConfig, company_email: e.target.value })} className="border p-2 rounded-lg" />
                            <input type="text" placeholder="Company Phone" value={systemConfig.company_phone} onChange={(e) => setSystemConfig({ ...systemConfig, company_phone: e.target.value })} className="border p-2 rounded-lg" />
                            <input type="text" placeholder="VAT Number" value={systemConfig.company_vat_number} onChange={(e) => setSystemConfig({ ...systemConfig, company_vat_number: e.target.value })} className="border p-2 rounded-lg" />
                            <input type="number" placeholder="Current Financial Year" value={systemConfig.current_financial_year} onChange={(e) => setSystemConfig({ ...systemConfig, current_financial_year: parseInt(e.target.value) })} className="border p-2 rounded-lg" />
                            <input type="number" placeholder="Current Period" min="1" max="12" value={systemConfig.current_period} onChange={(e) => setSystemConfig({ ...systemConfig, current_period: parseInt(e.target.value) })} className="border p-2 rounded-lg" />
                            <input type="number" placeholder="Default Interest Rate" step="0.01" value={systemConfig.default_interest_rate} onChange={(e) => setSystemConfig({ ...systemConfig, default_interest_rate: parseFloat(e.target.value) })} className="border p-2 rounded-lg" />
                            <input type="text" placeholder="Currency Symbol" value={systemConfig.currency_symbol} onChange={(e) => setSystemConfig({ ...systemConfig, currency_symbol: e.target.value })} className="border p-2 rounded-lg" />
                          </>
                        ) : (
                          <>
                            <div><p className="text-sm text-gray-600">Company</p><p className="font-semibold">{systemConfig.company_name}</p></div>
                            <div><p className="text-sm text-gray-600">Email</p><p className="font-semibold">{systemConfig.company_email}</p></div>
                            <div><p className="text-sm text-gray-600">Phone</p><p className="font-semibold">{systemConfig.company_phone}</p></div>
                            <div><p className="text-sm text-gray-600">VAT Number</p><p className="font-semibold">{systemConfig.company_vat_number}</p></div>
                            <div><p className="text-sm text-gray-600">Financial Year</p><p className="font-semibold">{systemConfig.current_financial_year}</p></div>
                            <div><p className="text-sm text-gray-600">Current Period</p><p className="font-semibold">{systemConfig.current_period}</p></div>
                            <div><p className="text-sm text-gray-600">Interest Rate</p><p className="font-semibold">{systemConfig.default_interest_rate}%</p></div>
                            <div><p className="text-sm text-gray-600">Currency</p><p className="font-semibold">{systemConfig.currency_symbol}</p></div>
                          </>
                        )}
                      </div>
                      {editingConfig && (
                        <button onClick={saveSystemConfig} className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">Save Configuration</button>
                      )}
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="p-6 space-y-3">
                      <h2 className="text-lg font-semibold mb-2">Period End &amp; Reports</h2>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <Link href="/dashboard/admin/settings/period-end" className="flex items-center justify-between gap-2 px-4 py-3 border rounded-lg hover:bg-gray-50 transition">
                          <span className="flex items-center gap-2"><Clock className="h-4 w-4 text-blue-600" />Day End / Month End / Year End</span>
                          <ArrowRight className="h-4 w-4 text-gray-400" />
                        </Link>
                        <Link href="/dashboard/admin/settings/reports/consolidated-expenditure" className="flex items-center justify-between gap-2 px-4 py-3 border rounded-lg hover:bg-gray-50 transition">
                          <span className="flex items-center gap-2"><Receipt className="h-4 w-4 text-emerald-600" />Consolidated Expenditure</span>
                          <ArrowRight className="h-4 w-4 text-gray-400" />
                        </Link>
                        <Link href="/dashboard/admin/settings/reports/data-integrity" className="flex items-center justify-between gap-2 px-4 py-3 border rounded-lg hover:bg-gray-50 transition">
                          <span className="flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-amber-600" />Data Integrity Report</span>
                          <ArrowRight className="h-4 w-4 text-gray-400" />
                        </Link>
                        <Link href="/dashboard/admin/settings/reports/tax-control" className="flex items-center justify-between gap-2 px-4 py-3 border rounded-lg hover:bg-gray-50 transition">
                          <span className="flex items-center gap-2"><FileBarChart className="h-4 w-4 text-purple-600" />Tax Control / VAT-201</span>
                          <ArrowRight className="h-4 w-4 text-gray-400" />
                        </Link>
                        <Link href="/dashboard/admin/settings/permissions" className="flex items-center justify-between gap-2 px-4 py-3 border rounded-lg hover:bg-gray-50 transition">
                          <span className="flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-indigo-600" />Access Grants (Permissions)</span>
                          <ArrowRight className="h-4 w-4 text-gray-400" />
                        </Link>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="border-purple-200 bg-purple-50">
                    <CardContent className="p-6 space-y-4">
                      <div className="flex items-center gap-2 mb-4">
                        <Zap className="h-5 w-5 text-purple-600" />
                        <h2 className="text-lg font-semibold text-purple-900">Sample Data Seeding</h2>
                      </div>
                      <p className="text-sm text-purple-800">Populate the system with sample data for testing and development.</p>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {(['settings', 'debtors', 'creditors', 'stock'] as const).map((type) => {
                          const colors: Record<string, string> = { settings: 'indigo', debtors: 'blue', creditors: 'emerald', stock: 'amber' };
                          const c = colors[type];
                          return (
                            <button key={type} onClick={() => seedData(type)} disabled={seedingStatus[type] || seedingStatus.all}
                              className={`flex items-center justify-center gap-2 px-4 py-3 bg-${c}-600 text-white rounded-lg hover:bg-${c}-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition`}>
                              {seedingStatus[type] ? <><Loader className="h-4 w-4 animate-spin" />Seeding...</> : <><Zap className="h-4 w-4" />Seed {type.charAt(0).toUpperCase() + type.slice(1)}</>}
                            </button>
                          );
                        })}
                      </div>
                      <div className="pt-2 border-t border-purple-200">
                        <button onClick={() => seedData('all')} disabled={seedingStatus.all || Object.values(seedingStatus).some(v => v)}
                          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-purple-700 text-white rounded-lg hover:bg-purple-800 disabled:bg-gray-400 disabled:cursor-not-allowed transition font-semibold">
                          {seedingStatus.all ? <><Loader className="h-4 w-4 animate-spin" />Seeding All Data...</> : <><Zap className="h-4 w-4" />Seed All Data (Complete Setup)</>}
                        </button>
                      </div>
                      {Object.values(seedingOutput).length > 0 && (
                        <div className="mt-4 space-y-2">
                          {Object.entries(seedingOutput).map(([key, output]) => output && (
                            <div key={key} className="bg-white p-3 rounded-lg border border-purple-200">
                              <p className="text-xs font-semibold text-purple-900 mb-2 capitalize">{key} Output:</p>
                              <pre className="text-xs text-purple-700 overflow-auto max-h-40 whitespace-pre-wrap break-words">{output}</pre>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>
              )}
            </>
          )}

          {activeTab === 'seeding' && (
            <div className="space-y-4">
              {error && <Card className="border-red-200 bg-red-50"><CardContent className="p-6"><p className="text-red-800">{error}</p></CardContent></Card>}
              {successMessage && <Card className="border-green-200 bg-green-50"><CardContent className="p-6"><p className="text-green-800">{successMessage}</p></CardContent></Card>}
              {seedingError && <Card className="border-red-200 bg-red-50"><CardContent className="p-6"><p className="text-red-800">{seedingError}</p></CardContent></Card>}

              <Card className="border-blue-200 bg-blue-50">
                <CardContent className="p-6 space-y-4">
                  <div className="flex items-center gap-2 mb-4">
                    <Upload className="h-5 w-5 text-blue-600" />
                    <h2 className="text-lg font-semibold text-blue-900">Import Data from File</h2>
                  </div>
                  <p className="text-sm text-blue-800">Import real data from CSV or DBF files. Select a file, map columns, preview data, and import.</p>

                  <div className="flex gap-2 items-center text-xs font-semibold">
                    {(['upload', 'map', 'preview', 'import'] as const).map((step, i) => {
                      const steps = ['upload', 'map', 'preview', 'import', 'complete'];
                      const active = steps.indexOf(importStep) >= i;
                      return (
                        <>
                          <span key={step} className={`px-3 py-1 rounded-full ${active ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'}`}>{i + 1}. {step.charAt(0).toUpperCase() + step.slice(1)}</span>
                          {i < 3 && <span key={`arrow-${i}`} className="text-gray-400">→</span>}
                        </>
                      );
                    })}
                  </div>

                  {importStep === 'upload' && (
                    <div className="space-y-4 border-t border-blue-200 pt-4">
                      <div className="space-y-2">
                        <label className="block text-sm font-semibold text-blue-900">Select File (CSV or DBF)</label>
                        <div className="flex gap-2">
                          <input type="file" accept=".csv,.dbf" onChange={handleFileSelect} disabled={importLoading} className="flex-1 px-4 py-2 border border-blue-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100" />
                          <button onClick={handleFileUpload} disabled={!importFile || importLoading} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition flex items-center gap-2">
                            {importLoading ? <><Loader className="h-4 w-4 animate-spin" />Analyzing...</> : <><Upload className="h-4 w-4" />Analyze File</>}
                          </button>
                        </div>
                        {importFile && <p className="text-xs text-blue-700">Selected: <span className="font-semibold">{importFile.name}</span></p>}
                      </div>
                    </div>
                  )}

                  {importStep === 'map' && fileAnalysis && (
                    <div className="space-y-4 border-t border-blue-200 pt-4">
                      <div className="space-y-2">
                        <label className="block text-sm font-semibold text-blue-900">Select Data Type to Import</label>
                        <select value={selectedModelType} onChange={(e) => {
                          const newType = e.target.value as 'debtor' | 'creditor' | 'stock';
                          setSelectedModelType(newType);
                          const allFields = IMPORT_FIELD_MAPPINGS[newType] || [];
                          const suggestedMappings = fileAnalysis?.suggested_mappings || {};
                          const fullMappings: ImportMapping = {};
                          allFields.forEach(field => { fullMappings[field] = suggestedMappings[field] || ''; });
                          setImportMappings(fullMappings);
                        }} className="w-full px-4 py-2 border border-blue-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                          <option value="debtor">Debtors (Customers)</option>
                          <option value="creditor">Creditors (Suppliers)</option>
                          <option value="stock">Stock Items</option>
                        </select>
                      </div>
                      <div className="space-y-2">
                        <label className="block text-sm font-semibold text-blue-900">Map Columns</label>
                        <p className="text-xs text-blue-700">Select which columns in your file correspond to each field.</p>
                        <div className="bg-white border border-blue-200 rounded-lg p-3 space-y-2 max-h-64 overflow-y-auto">
                          {Object.entries(importMappings).map(([djangoField, sourceColumn]) => (
                            <div key={djangoField} className="flex gap-2 items-center text-sm">
                              <span className="font-semibold text-blue-900 w-40 flex-shrink-0">{djangoField}:</span>
                              <select value={sourceColumn || ''} onChange={(e) => handleColumnMapping(djangoField, e.target.value)} className="flex-1 px-3 py-1 border border-blue-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500">
                                <option value="">-- Not mapped --</option>
                                {fileAnalysis.headers.map((header) => (<option key={header} value={header}>{header}</option>))}
                              </select>
                            </div>
                          ))}
                        </div>
                      </div>
                      <div className="flex gap-2 pt-2 border-t border-blue-200">
                        <button onClick={() => setImportStep('upload')} className="flex-1 px-4 py-2 border border-blue-300 text-blue-600 rounded-lg hover:bg-blue-50 transition">Back</button>
                        <button onClick={handlePreview} disabled={importLoading || !Object.values(importMappings).some(v => v)} className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition flex items-center justify-center gap-2">
                          {importLoading ? <><Loader className="h-4 w-4 animate-spin" />Loading...</> : <><Download className="h-4 w-4" />Preview Data</>}
                        </button>
                      </div>
                    </div>
                  )}

                  {importStep === 'preview' && importResult && (
                    <div className="space-y-4 border-t border-blue-200 pt-4">
                      <div className="space-y-2">
                        <label className="block text-sm font-semibold text-blue-900">Preview Sample Data</label>
                        <div className="bg-white border border-blue-200 rounded-lg p-3 overflow-x-auto">
                          <table className="w-full text-xs">
                            <thead>
                              <tr className="border-b border-blue-200">
                                {fileAnalysis && fileAnalysis.headers.map((header) => (<th key={header} className="px-2 py-1 text-left text-blue-900 font-semibold">{header}</th>))}
                              </tr>
                            </thead>
                            <tbody>
                              {importResult.rows && importResult.rows.slice(0, 5).map((row: any, idx: number) => (
                                <tr key={idx} className="border-b border-blue-100 hover:bg-blue-50">
                                  {fileAnalysis && fileAnalysis.headers.map((header) => (
                                    <td key={header} className="px-2 py-1 text-blue-700">
                                      {row[importMappings[Object.keys(importMappings).find((k) => importMappings[k] === header) || ''] || header] || '-'}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                        {fileAnalysis && <p className="text-xs text-blue-700">Showing first 5 of {fileAnalysis.total_rows} rows</p>}
                      </div>
                      {importResult.warnings && importResult.warnings.length > 0 && (
                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                          <p className="text-xs font-semibold text-yellow-900 mb-2">Warnings:</p>
                          <ul className="text-xs text-yellow-700 space-y-1">{importResult.warnings.map((warning: string, idx: number) => (<li key={idx}>• {warning}</li>))}</ul>
                        </div>
                      )}
                      <div className="flex gap-2 pt-2 border-t border-blue-200">
                        <button onClick={() => setImportStep('map')} className="flex-1 px-4 py-2 border border-blue-300 text-blue-600 rounded-lg hover:bg-blue-50 transition">Back</button>
                        <button onClick={handleImport} disabled={importLoading} className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition flex items-center justify-center gap-2">
                          {importLoading ? <><Loader className="h-4 w-4 animate-spin" />Importing...</> : <><Check className="h-4 w-4" />Execute Import</>}
                        </button>
                      </div>
                    </div>
                  )}

                  {importStep === 'complete' && importResult && (
                    <div className="space-y-4 border-t border-blue-200 pt-4">
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <div className="flex items-start gap-3">
                          <Check className="h-6 w-6 text-green-600 flex-shrink-0 mt-0.5" />
                          <div>
                            <h3 className="font-semibold text-green-900">Import Completed Successfully!</h3>
                            <div className="mt-2 space-y-1 text-sm text-green-800">
                              <p>✓ Created: <span className="font-semibold">{importResult.created || 0} records</span></p>
                              <p>✓ Updated: <span className="font-semibold">{importResult.updated || 0} records</span></p>
                              {importResult.errors && importResult.errors.length > 0 && <p className="text-orange-600">⚠ Errors: <span className="font-semibold">{importResult.errors.length} rows</span></p>}
                            </div>
                          </div>
                        </div>
                      </div>
                      {importResult.errors && importResult.errors.length > 0 && (
                        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                          <p className="text-xs font-semibold text-red-900 mb-2">Import Errors:</p>
                          <div className="space-y-1 max-h-40 overflow-y-auto">{importResult.errors.map((error: string, idx: number) => (<p key={idx} className="text-xs text-red-700">• {error}</p>))}</div>
                        </div>
                      )}
                      <button onClick={resetImport} className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">Import Another File</button>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card className="border-purple-200 bg-purple-50">
                <CardContent className="p-6 space-y-4">
                  <div className="flex items-center gap-2 mb-4">
                    <Zap className="h-5 w-5 text-purple-600" />
                    <h2 className="text-lg font-semibold text-purple-900">Sample Data Seeding</h2>
                  </div>
                  <p className="text-sm text-purple-800">Populate the system with sample data for testing and development.</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <button onClick={() => seedData('settings')} disabled={seedingStatus.settings || seedingStatus.all} className="flex items-center justify-center gap-2 px-4 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition">
                      {seedingStatus.settings ? <><Loader className="h-4 w-4 animate-spin" />Seeding...</> : <><Zap className="h-4 w-4" />Seed Settings</>}
                    </button>
                    <button onClick={() => seedData('debtors')} disabled={seedingStatus.debtors || seedingStatus.all} className="flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition">
                      {seedingStatus.debtors ? <><Loader className="h-4 w-4 animate-spin" />Seeding...</> : <><Zap className="h-4 w-4" />Seed Debtors</>}
                    </button>
                    <button onClick={() => seedData('creditors')} disabled={seedingStatus.creditors || seedingStatus.all} className="flex items-center justify-center gap-2 px-4 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition">
                      {seedingStatus.creditors ? <><Loader className="h-4 w-4 animate-spin" />Seeding...</> : <><Zap className="h-4 w-4" />Seed Creditors</>}
                    </button>
                    <button onClick={() => seedData('stock')} disabled={seedingStatus.stock || seedingStatus.all} className="flex items-center justify-center gap-2 px-4 py-3 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition">
                      {seedingStatus.stock ? <><Loader className="h-4 w-4 animate-spin" />Seeding...</> : <><Zap className="h-4 w-4" />Seed Stock Items</>}
                    </button>
                  </div>
                  <div className="pt-2 border-t border-purple-200">
                    <button onClick={() => seedData('all')} disabled={seedingStatus.all || Object.values(seedingStatus).some(v => v)} className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-purple-700 text-white rounded-lg hover:bg-purple-800 disabled:bg-gray-400 disabled:cursor-not-allowed transition font-semibold">
                      {seedingStatus.all ? <><Loader className="h-4 w-4 animate-spin" />Seeding All Data...</> : <><Zap className="h-4 w-4" />Seed All Data (Complete Setup)</>}
                    </button>
                  </div>
                  {Object.values(seedingOutput).length > 0 && (
                    <div className="mt-4 space-y-2">
                      {Object.entries(seedingOutput).map(([key, output]) => output && (
                        <div key={key} className="bg-white p-3 rounded-lg border border-purple-200">
                          <p className="text-xs font-semibold text-purple-900 mb-2 capitalize">{key} Output:</p>
                          <pre className="text-xs text-purple-700 overflow-auto max-h-40 whitespace-pre-wrap break-words">{output}</pre>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </>
      )}
    </div>
  );
}