/**
 * Settings API Test Helper
 * 
 * Use this in your browser console to test all settings endpoints
 * Copy and paste the functions below into your browser console while on the settings page
 * 
 * Example:
 * await testAllSettingsEndpoints()
*/

import { api } from './api';

export const settingsTestHelper = {
  /**
   * Helper function to get the first shop ID
   */
  async getShopId() {
    try {
      const shopsRes = await api.get('/api/shops/');
      const shops = shopsRes.data.results || shopsRes.data;
      if (shops && shops.length > 0) {
        console.log(`Using shop: ${shops[0].id} - ${shops[0].name}`);
        return shops[0].id;
      }
      console.error('No shops found. Please create a shop first.');
      return null;
    } catch (error: any) {
      console.error('Failed to get shops:', error.response?.data || error.message);
      return null;
    }
  },

  /**
   * Test Departments Endpoints
   */
  async testDepartments() {
    console.log('=== TESTING DEPARTMENTS ===');
    try {
      // GET all departments
      console.log('GET /api/settings/departments/');
      const getRes = await api.get('/api/settings/departments/');
      console.log('Response:', getRes.data);
      return getRes.data;
    } catch (error: any) {
      console.error('Error:', error.response?.data || error.message);
      return null;
    }
  },

  async testAddDepartment(number: number, name: string, shopId?: number) {
    console.log('=== TESTING ADD DEPARTMENT ===');
    try {
      const sid = shopId || await this.getShopId();
      if (!sid) return null;
      
      const data = { shop_id: sid, number, name, is_active: true };
      console.log(`POST /api/settings/departments/ with data: ${JSON.stringify(data)}`);
      const res = await api.post('/api/settings/departments/', data);
      console.log('Response:', res.data);
      return res.data;
    } catch (error: any) {
      console.error('Error:', error.response?.data || error.message);
      return null;
    }
  },

  /**
   * Test Income Categories Endpoints
   */
  async testIncomeCategories() {
    console.log('=== TESTING INCOME CATEGORIES ===');
    try {
      console.log('GET /api/settings/income-categories/');
      const getRes = await api.get('/api/settings/income-categories/');
      console.log('Response:', getRes.data);
      return getRes.data;
    } catch (error: any) {
      console.error('Error:', error.response?.data || error.message);
      return null;
    }
  },

  async testAddIncomeCategory(number: number, name: string, shopId?: number) {
    console.log('=== TESTING ADD INCOME CATEGORY ===');
    try {
      const sid = shopId || await this.getShopId();
      if (!sid) return null;
      
      const data = { shop_id: sid, number, name, is_active: true };
      console.log(`POST /api/settings/income-categories/ with data: ${JSON.stringify(data)}`);
      const res = await api.post('/api/settings/income-categories/', data);
      console.log('Response:', res.data);
      return res.data;
    } catch (error: any) {
      console.error('Error:', error.response?.data || error.message);
      return null;
    }
  },

  /**
   * Test Expense Categories Endpoints
   */
  async testExpenseCategories() {
    console.log('=== TESTING EXPENSE CATEGORIES ===');
    try {
      console.log('GET /api/settings/expense-categories/');
      const getRes = await api.get('/api/settings/expense-categories/');
      console.log('Response:', getRes.data);
      return getRes.data;
    } catch (error: any) {
      console.error('Error:', error.response?.data || error.message);
      return null;
    }
  },

  async testAddExpenseCategory(number: number, name: string, category_type = 'BOTH', shopId?: number) {
    console.log('=== TESTING ADD EXPENSE CATEGORY ===');
    try {
      const sid = shopId || await this.getShopId();
      if (!sid) return null;
      
      const data = { shop_id: sid, number, name, category_type, is_active: true };
      console.log(`POST /api/settings/expense-categories/ with data: ${JSON.stringify(data)}`);
      const res = await api.post('/api/settings/expense-categories/', data);
      console.log('Response:', res.data);
      return res.data;
    } catch (error: any) {
      console.error('Error:', error.response?.data || error.message);
      return null;
    }
  },

  /**
   * Test Tax Codes Endpoints
   */
  async testTaxCodes() {
    console.log('=== TESTING TAX CODES ===');
    try {
      console.log('GET /api/settings/tax-codes/');
      const getRes = await api.get('/api/settings/tax-codes/');
      console.log('Response:', getRes.data);
      return getRes.data;
    } catch (error: any) {
      console.error('Error:', error.response?.data || error.message);
      return null;
    }
  },

  async testAddTaxCode(code: number, description: string, rate: number, shopId?: number) {
    console.log('=== TESTING ADD TAX CODE ===');
    try {
      const sid = shopId || await this.getShopId();
      if (!sid) return null;
      
      const data = { shop_id: sid, code, description, rate, is_active: true };
      console.log(`POST /api/settings/tax-codes/ with data: ${JSON.stringify(data)}`);
      const res = await api.post('/api/settings/tax-codes/', data);
      console.log('Response:', res.data);
      return res.data;
    } catch (error: any) {
      console.error('Error:', error.response?.data || error.message);
      return null;
    }
  },

  /**
   * Test Payment Methods Endpoints
   */
  async testPaymentMethods() {
    console.log('=== TESTING PAYMENT METHODS ===');
    try {
      console.log('GET /api/settings/payment-methods/');
      const getRes = await api.get('/api/settings/payment-methods/');
      console.log('Response:', getRes.data);
      return getRes.data;
    } catch (error: any) {
      console.error('Error:', error.response?.data || error.message);
      return null;
    }
  },

  async testAddPaymentMethod(code: string, name: string, is_electronic = false, shopId?: number) {
    console.log('=== TESTING ADD PAYMENT METHOD ===');
    try {
      const sid = shopId || await this.getShopId();
      if (!sid) return null;
      
      const data = { shop_id: sid, code, name, is_electronic, is_active: true };
      console.log(`POST /api/settings/payment-methods/ with data: ${JSON.stringify(data)}`);
      const res = await api.post('/api/settings/payment-methods/', data);
      console.log('Response:', res.data);
      return res.data;
    } catch (error: any) {
      console.error('Error:', error.response?.data || error.message);
      return null;
    }
  },

  /**
   * Test Credit Terms Endpoints
   */
  async testCreditTerms() {
    console.log('=== TESTING CREDIT TERMS ===');
    try {
      console.log('GET /api/settings/credit-terms/');
      const getRes = await api.get('/api/settings/credit-terms/');
      console.log('Response:', getRes.data);
      return getRes.data;
    } catch (error: any) {
      console.error('Error:', error.response?.data || error.message);
      return null;
    }
  },

  async testAddCreditTerms(days: number, description: string, shopId?: number) {
    console.log('=== TESTING ADD CREDIT TERMS ===');
    try {
      const sid = shopId || await this.getShopId();
      if (!sid) return null;
      
      const data = { shop_id: sid, days, description, is_active: true };
      console.log(`POST /api/settings/credit-terms/ with data: ${JSON.stringify(data)}`);
      const res = await api.post('/api/settings/credit-terms/', data);
      console.log('Response:', res.data);
      return res.data;
    } catch (error: any) {
      console.error('Error:', error.response?.data || error.message);
      return null;
    }
  },

  /**
   * Test System Config Endpoints
   */
  async testSystemConfig() {
    console.log('=== TESTING SYSTEM CONFIG ===');
    try {
      console.log('GET /api/settings/system-config/');
      const getRes = await api.get('/api/settings/system-config/');
      console.log('Response:', getRes.data);
      return getRes.data;
    } catch (error: any) {
      console.error('Error:', error.response?.data || error.message);
      return null;
    }
  },

  /**
   * Test Update Department
   */
  async testUpdateDepartment(id: number, number: number, name: string) {
    console.log('=== TESTING UPDATE DEPARTMENT ===');
    try {
      console.log(`PUT /api/settings/departments/${id}/ with data: ${JSON.stringify({ number, name, is_active: true })}`);
      const res = await api.put(`/api/settings/departments/${id}/`, {
        number,
        name,
        is_active: true
      });
      console.log('Response:', res.data);
      return res.data;
    } catch (error: any) {
      console.error('Error:', error.response?.data || error.message);
      return null;
    }
  },

  /**
   * Test Delete Department
   */
  async testDeleteDepartment(id: number) {
    console.log('=== TESTING DELETE DEPARTMENT ===');
    try {
      console.log(`DELETE /api/settings/departments/${id}/`);
      const res = await api.delete(`/api/settings/departments/${id}/`);
      console.log('Response:', res.data);
      return res.data;
    } catch (error: any) {
      console.error('Error:', error.response?.data || error.message);
      return null;
    }
  },

  /**
   * Run all tests
   */
  async runAllTests() {
    console.log('\n\n========================================');
    console.log('RUNNING ALL SETTINGS API TESTS');
    console.log('========================================\n');

    // Get all data first
    const depts = await this.testDepartments();
    const incomes = await this.testIncomeCategories();
    const expenses = await this.testExpenseCategories();
    const taxes = await this.testTaxCodes();
    const payments = await this.testPaymentMethods();
    const credits = await this.testCreditTerms();
    const systemConfig = await this.testSystemConfig();

    console.log('\n========================================');
    console.log('TEST SUMMARY');
    console.log('========================================');
    console.log('Departments:', depts ? 'OK' : 'FAILED');
    console.log('Income Categories:', incomes ? 'OK' : 'FAILED');
    console.log('Expense Categories:', expenses ? 'OK' : 'FAILED');
    console.log('Tax Codes:', taxes ? 'OK' : 'FAILED');
    console.log('Payment Methods:', payments ? 'OK' : 'FAILED');
    console.log('Credit Terms:', credits ? 'OK' : 'FAILED');
    console.log('System Config:', systemConfig ? 'OK' : 'FAILED');
    console.log('========================================\n');
  }
};

// Type for the test helper
interface SettingsTestHelper {
  testDepartments(): Promise<any>;
  testAddDepartment(number: number, name: string): Promise<any>;
  testIncomeCategories(): Promise<any>;
  testAddIncomeCategory(number: number, name: string): Promise<any>;
  testExpenseCategories(): Promise<any>;
  testAddExpenseCategory(number: number, name: string, category_type?: string): Promise<any>;
  testTaxCodes(): Promise<any>;
  testAddTaxCode(code: number, description: string, rate: number): Promise<any>;
  testPaymentMethods(): Promise<any>;
  testAddPaymentMethod(code: string, name: string, is_electronic?: boolean): Promise<any>;
  testCreditTerms(): Promise<any>;
  testAddCreditTerms(days: number, description: string): Promise<any>;
  testSystemConfig(): Promise<any>;
  testUpdateDepartment(id: number, number: number, name: string): Promise<any>;
  testDeleteDepartment(id: number): Promise<any>;
  runAllTests(): Promise<void>;
}

// Export for global access in console
declare global {
  var settingsTestHelper: SettingsTestHelper;
}

if (typeof window !== 'undefined') {
  (window as any).settingsTestHelper = settingsTestHelper;
}
