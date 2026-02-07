'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowLeft, FileText, Users, Send, TrendingUp, DollarSign, Receipt } from 'lucide-react';
import AccountDetailsReport from './components/AccountDetailsReport';
import AgeAnalysisReport from './components/AgeAnalysisReport';
import RemittanceAdvices from './components/RemittanceAdvices';
import TransactionsReport from './components/TransactionsReport';
import ExpenseTaxReport from './components/ExpenseTaxReport';
import PayoutsReport from './components/PayoutsReport';

type ReportType = 'menu' | 'account_details' | 'age_analysis' | 'remittance' | 'transactions' | 'expense_tax' | 'payouts';

const REPORTS = [
  {
    id: 'account_details',
    title: 'Account Details',
    description: 'List all creditors with detailed information',
    icon: Users,
    color: 'bg-blue-50 border-blue-200',
    iconColor: 'text-blue-600',
  },
  {
    id: 'age_analysis',
    title: 'Age Analysis',
    description: 'Outstanding balances by age period',
    icon: TrendingUp,
    color: 'bg-purple-50 border-purple-200',
    iconColor: 'text-purple-600',
  },
  {
    id: 'remittance',
    title: 'Remittance Advices',
    description: 'Print remittance statements',
    icon: Send,
    color: 'bg-green-50 border-green-200',
    iconColor: 'text-green-600',
  },
  {
    id: 'transactions',
    title: 'Transactions',
    description: 'View transactions by date range',
    icon: Receipt,
    color: 'bg-orange-50 border-orange-200',
    iconColor: 'text-orange-600',
  },
  {
    id: 'expense_tax',
    title: 'Expense & Tax Reports',
    description: 'Expense analysis and tax details',
    icon: FileText,
    color: 'bg-pink-50 border-pink-200',
    iconColor: 'text-pink-600',
  },
  {
    id: 'payouts',
    title: 'Payouts',
    description: 'List payout details by date',
    icon: DollarSign,
    color: 'bg-teal-50 border-teal-200',
    iconColor: 'text-teal-600',
  },
];

export default function CreditorsReportsPage() {
  const [currentReport, setCurrentReport] = useState<ReportType>('menu');

  const handleBack = () => {
    setCurrentReport('menu');
  };

  const renderReport = () => {
    switch (currentReport) {
      case 'account_details':
        return <AccountDetailsReport onBack={handleBack} />;
      case 'age_analysis':
        return <AgeAnalysisReport onBack={handleBack} />;
      case 'remittance':
        return <RemittanceAdvices onBack={handleBack} />;
      case 'transactions':
        return <TransactionsReport onBack={handleBack} />;
      case 'expense_tax':
        return <ExpenseTaxReport onBack={handleBack} />;
      case 'payouts':
        return <PayoutsReport onBack={handleBack} />;
      default:
        return (
          <div className="p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center gap-4">
              <Button variant="outline" onClick={() => window.history.back()}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <div>
                <h1 className="text-4xl font-bold">Creditors Reports</h1>
                <p className="text-gray-600 mt-2">Generate comprehensive creditor reports</p>
              </div>
            </div>

            {/* Reports Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {REPORTS.map((report) => {
                const IconComponent = report.icon;
                return (
                  <Card
                    key={report.id}
                    className={`cursor-pointer hover:shadow-lg transition-shadow border-2 ${report.color}`}
                    onClick={() => setCurrentReport(report.id as ReportType)}
                  >
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <CardTitle className="text-lg">{report.title}</CardTitle>
                        <IconComponent className={`w-6 h-6 ${report.iconColor}`} />
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-gray-600">{report.description}</p>
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            {/* Quick Reference */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Reference</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h3 className="font-semibold text-sm mb-2">Report Types</h3>
                    <ul className="text-sm text-gray-600 space-y-1">
                      <li>✓ Account Details - Supplier information</li>
                      <li>✓ Age Analysis - Outstanding balances</li>
                      <li>✓ Remittance Advices - Payment statements</li>
                    </ul>
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm mb-2">More Reports</h3>
                    <ul className="text-sm text-gray-600 space-y-1">
                      <li>✓ Transactions - Period analysis</li>
                      <li>✓ Expense & Tax - Category breakdown</li>
                      <li>✓ Payouts - Payment details</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        );
    }
  };

  return <>{renderReport()}</>;
}

