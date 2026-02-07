'use client';

import { useState } from 'react';
import { ChevronRight } from 'lucide-react';
import StockItemMaintenance from '@/components/stock-control/maintenance/StockItemMaintenance';
import SpecialDealMaintenance from '@/components/stock-control/maintenance/SpecialDealMaintenance';
import PriceMaintenance from '@/components/stock-control/maintenance/PriceMaintenance';
import SalesDepartmentMaintenance from '@/components/stock-control/maintenance/SalesDepartmentMaintenance';
import OneTouchLookupKeyMaintenance from '@/components/stock-control/maintenance/OneTouchLookupKeyMaintenance';
import ContractPricingMaintenance from '@/components/stock-control/maintenance/ContractPricingMaintenance';
import ShrinkWrapMaintenance from '@/components/stock-control/maintenance/ShrinkWrapMaintenance';
import PackBundleMaintenance from '@/components/stock-control/maintenance/PackBundleMaintenance';

type MaintenanceSection = 
  | 'menu' 
  | 'stock-items' 
  | 'special-deals' 
  | 'prices' 
  | 'departments' 
  | 'lookup-keys' 
  | 'contract-pricing' 
  | 'shrink-wraps' 
  | 'packs-bundles';

const maintenanceOptions = [
  {
    id: 'stock-items',
    title: 'Maintain Stock Item(s)',
    description: 'Create, update, and manage stock items with pricing and inventory levels',
    subItems: [
      'Stock Item Maintenance',
      'Preparation of Creditors Accounts (refer to Creditors)',
      'Creating Sales Departments'
    ]
  },
  {
    id: 'special-deals',
    title: 'Special Deal Maintenance',
    description: 'Set special prices for individual items or entire departments',
    subItems: [
      'Individual Stock Items',
      'Entire Departments'
    ]
  },
  {
    id: 'prices',
    title: 'Prices',
    description: 'Maintain cost prices, markup percentages, and selling prices',
    subItems: [
      'Individual Stock Items',
      'Range of Stock Items (By Department/Supplier)',
      'Future Pricing',
      'Set Maximum Discount'
    ]
  },
  {
    id: 'departments',
    title: 'Sales Departments',
    description: 'Create and modify sales departments for stock categorization',
    subItems: [
      'Create New Sales Department',
      'Modify Sales Department'
    ]
  },
  {
    id: 'lookup-keys',
    title: 'One-Touch Look-Up Keys',
    description: 'Link alphabet keys to stock codes for fast access at POS',
    subItems: [
      'Set up look-up keys',
      'View current alpha settings',
      'Clear alpha settings'
    ]
  },
  {
    id: 'contract-pricing',
    title: 'Contract Pricing',
    description: 'Link debtors to contract prices on items, departments, or suppliers',
    subItems: [
      'Fixed Pricing per Line Item',
      'Department-based Discounts/Markups',
      'Supplier-based Discounts',
      'Supplier + Department Combinations'
    ]
  },
  {
    id: 'shrink-wraps',
    title: 'Shrink Wraps',
    description: 'Define relationships between bulk and shrink-wrapped units',
    subItems: [
      'Shrink Wrap Maintenance',
      'View/Print Shrink Wrap Relationships'
    ]
  },
  {
    id: 'packs-bundles',
    title: 'Packs / Bundles',
    description: 'Create finished products from grouping multiple stock items',
    subItems: [
      'Finished Product Maintenance',
      'Ingredient Maintenance',
      'View Pack Compositions'
    ]
  }
];

export default function StockControlMaintenancePage() {
  const [activeSection, setActiveSection] = useState<MaintenanceSection>('menu');

  const handleBack = () => {
    setActiveSection('menu');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-6">
        <h1 className="text-3xl font-bold text-gray-900">Stock Control</h1>
        <p className="text-gray-600 mt-2">Maintenance & Management</p>
      </div>

      <div className="p-6">
        {/* Main Menu */}
        {activeSection === 'menu' && (
          <div className="grid gap-4">
            <div className="grid md:grid-cols-2 lg:grid-cols-2 gap-4">
              {maintenanceOptions.map((option) => (
                <button
                  key={option.id}
                  onClick={() => setActiveSection(option.id as MaintenanceSection)}
                  className="p-6 bg-white rounded-lg border border-gray-200 hover:border-blue-500 hover:shadow-lg transition-all text-left group"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                        {option.title}
                      </h3>
                      <p className="text-sm text-gray-600 mt-1">{option.description}</p>
                      <div className="mt-3 space-y-1">
                        {option.subItems.map((item, idx) => (
                          <div key={idx} className="text-xs text-gray-500">
                            • {item}
                          </div>
                        ))}
                      </div>
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-blue-600 transition-colors ml-2 flex-shrink-0 mt-1" />
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Sub-sections */}
        {activeSection === 'stock-items' && <StockItemMaintenance onBack={handleBack} />}
        {activeSection === 'special-deals' && <SpecialDealMaintenance onBack={handleBack} />}
        {activeSection === 'prices' && <PriceMaintenance onBack={handleBack} />}
        {activeSection === 'departments' && <SalesDepartmentMaintenance onBack={handleBack} />}
        {activeSection === 'lookup-keys' && <OneTouchLookupKeyMaintenance onBack={handleBack} />}
        {activeSection === 'contract-pricing' && <ContractPricingMaintenance onBack={handleBack} />}
        {activeSection === 'shrink-wraps' && <ShrinkWrapMaintenance onBack={handleBack} />}
        {activeSection === 'packs-bundles' && <PackBundleMaintenance onBack={handleBack} />}
      </div>
    </div>
  );
}
