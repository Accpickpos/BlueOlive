'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Users,
  TrendingUp,
  ScrollText,
  BarChart3,
  Calendar,
  ShoppingCart,
} from 'lucide-react';
import IndividualAccountEnquiry from './components/IndividualAccountEnquiry';
import CreditorsSummaryEnquiry from './components/CreditorsSummaryEnquiry';
import TransactionScroll from './components/TransactionScroll';
import ExpenseTaxAnalysis from './components/ExpenseTaxAnalysis';
import MonthlyExpenseDetails from './components/MonthlyExpenseDetails';
import PurchaseHistory from './components/PurchaseHistory';

type EnquiryType =
  | 'menu'
  | 'individual'
  | 'summary'
  | 'transaction'
  | 'expense'
  | 'monthly'
  | 'purchase';

export default function CreditorsEnquiriesPage() {
  const [activeEnquiry, setActiveEnquiry] = useState<EnquiryType>('menu');

  const enquiryMenuItems = [
    {
      id: 'individual',
      title: 'Individual Account Enquiry',
      description: 'Search and view detailed creditor account information',
      icon: Users,
      color: 'bg-blue-50 hover:bg-blue-100',
      borderColor: 'border-blue-200',
      textColor: 'text-blue-700',
      subItems: [
        '• Current vs Archive Enquiries',
        '• Balance Brought Forward Creditors',
        '• Open Item Creditors',
        '• Outstanding Balances & Ageing',
        '• Transaction Audit Trail',
      ],
    },
    {
      id: 'summary',
      title: 'Total Creditors Summary',
      description: 'Age analysis and control enquiry for all creditors',
      icon: TrendingUp,
      color: 'bg-purple-50 hover:bg-purple-100',
      borderColor: 'border-purple-200',
      textColor: 'text-purple-700',
      subItems: [
        '• Age Analysis (by Name, Number, or Value)',
        '• Skip Zero Balances Option',
        '• Control Enquiry & Totals',
        '• Active/Inactive Status Display',
        '• Print Functionality',
      ],
    },
    {
      id: 'transaction',
      title: 'Transaction Scroll',
      description: 'Detailed transaction listing and analysis',
      icon: ScrollText,
      color: 'bg-green-50 hover:bg-green-100',
      borderColor: 'border-green-200',
      textColor: 'text-green-700',
      subItems: [
        '• Date Range Selection',
        '• Transaction Type Filtering',
        '• Scroll: Detailed Transaction List',
        '• Totals: Summary by Type',
        '• Export Capabilities',
      ],
    },
    {
      id: 'expense',
      title: 'Expense & Tax Analysis',
      description: 'Expenditure and tax analysis by category',
      icon: BarChart3,
      color: 'bg-orange-50 hover:bg-orange-100',
      borderColor: 'border-orange-200',
      textColor: 'text-orange-700',
      subItems: [
        '• Expenditure Totals',
        '• Expense Category Totals (MTD)',
        '• Expense Category Details',
        '• VAT Amount Breakdown',
        '• Monthly Comparisons',
      ],
    },
    {
      id: 'monthly',
      title: 'Monthly Expense Details',
      description: 'Monthly expense analysis by category',
      icon: Calendar,
      color: 'bg-pink-50 hover:bg-pink-100',
      borderColor: 'border-pink-200',
      textColor: 'text-pink-700',
      subItems: [
        '• Category Selection',
        '• Monthly Totals (Jan-Dec)',
        '• Percentage to Total Ratio',
        '• Graphical Representation',
        '• Year-to-Date Analysis',
      ],
    },
    {
      id: 'purchase',
      title: 'Purchase History',
      description: 'Net stock purchases analysis by supplier',
      icon: ShoppingCart,
      color: 'bg-teal-50 hover:bg-teal-100',
      borderColor: 'border-teal-200',
      textColor: 'text-teal-700',
      subItems: [
        '• Supplier Listing',
        '• Total Purchase Amounts',
        '• Monthly Purchase Amounts',
        '• Sort by Supplier or Amount',
        '• Print Report',
      ],
    },
  ];

  const handleEnquirySelect = (enquiryId: string) => {
    setActiveEnquiry(enquiryId as EnquiryType);
  };

  const handleBack = () => {
    setActiveEnquiry('menu');
  };

  // Render individual enquiry components
  if (activeEnquiry === 'individual') {
    return <IndividualAccountEnquiry onBack={handleBack} />;
  }

  if (activeEnquiry === 'summary') {
    return <CreditorsSummaryEnquiry onBack={handleBack} />;
  }

  if (activeEnquiry === 'transaction') {
    return <TransactionScroll onBack={handleBack} />;
  }

  if (activeEnquiry === 'expense') {
    return <ExpenseTaxAnalysis onBack={handleBack} />;
  }

  if (activeEnquiry === 'monthly') {
    return <MonthlyExpenseDetails onBack={handleBack} />;
  }

  if (activeEnquiry === 'purchase') {
    return <PurchaseHistory onBack={handleBack} />;
  }

  // Render menu
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Creditors - Enquiries</h1>
        <p className="text-gray-600 mt-2">
          Select an enquiry type to view and analyze creditor information
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {enquiryMenuItems.map((item) => {
          const IconComponent = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => handleEnquirySelect(item.id)}
              className={`text-left transition-all duration-200`}
            >
              <Card
                className={`h-full border-2 ${item.borderColor} ${item.color} cursor-pointer hover:shadow-lg transform hover:-translate-y-1`}
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className={`${item.textColor}`}>
                        {item.title}
                      </CardTitle>
                      <CardDescription className="mt-2">
                        {item.description}
                      </CardDescription>
                    </div>
                    <IconComponent
                      className={`w-6 h-6 ${item.textColor} ml-2 flex-shrink-0`}
                    />
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className={`space-y-1 text-sm ${item.textColor}`}>
                    {item.subItems.map((subItem, idx) => (
                      <li key={idx}>{subItem}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </button>
          );
        })}
      </div>

      {/* Quick Reference */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-blue-900">Quick Reference</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-blue-800 space-y-2">
          <p>
            <strong>Individual Account Enquiry:</strong> View specific creditor details including
            balance analysis and transaction history
          </p>
          <p>
            <strong>Total Creditors Summary:</strong> Get an overview of all creditor balances aged
            by payment period
          </p>
          <p>
            <strong>Transaction Scroll:</strong> Review all transactions within a date range,
            filtered by type
          </p>
          <p>
            <strong>Expense & Tax Analysis:</strong> Analyze expenses and tax by category and
            period
          </p>
          <p>
            <strong>Monthly Expense Details:</strong> Review monthly expense trends for specific
            categories
          </p>
          <p>
            <strong>Purchase History:</strong> View purchase activity by supplier for the year
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
