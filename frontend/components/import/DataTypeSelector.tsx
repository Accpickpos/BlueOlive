'use client';

import { Users, Building, Package, Folder, ArrowRight, FileText, History, CreditCard, Receipt, RefreshCw, List, DollarSign, PieChart, Repeat } from 'lucide-react';

interface DataType {
  debtor: { label: string; icon: string; help: string; file: string; category: string };
  creditor: { label: string; icon: string; help: string; file: string; category: string };
  stock: { label: string; icon: string; help: string; file: string; category: string };
  department: { label: string; icon: string; help: string; file: string; category: string };
  [key: string]: { label: string; icon: string; help: string; file: string; category: string };
}

interface DataTypeSelectorProps {
  dataType: string;
  onDataTypeChange: (type: string) => void;
  dataTypeInfo: DataType;
}

const iconMap: Record<string, React.ComponentType<any>> = {
  Users,
  Building,
  Package,
  Folder,
  ArrowRight,
  FileText,
  History,
  CreditCard,
  Receipt,
  RefreshCw,
  List,
  DollarSign,
  PieChart,
  Repeat,
};

export function DataTypeSelector({ dataType, onDataTypeChange, dataTypeInfo }: DataTypeSelectorProps) {
  // Group by category
  const categories = ['Master Data', 'Debtor Transactions', 'Creditor Transactions', 'Stock Transactions'];
  
  const getIcon = (iconName: string) => {
    const Icon = iconMap[iconName] || FileText;
    return <Icon className="w-5 h-5" />;
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-2">Select Data Type</h2>
        <p className="text-gray-600 text-sm">Choose the type of data you want to import</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {categories.map((category) => {
          const typesInCategory = Object.entries(dataTypeInfo).filter(
            ([, value]) => value.category === category
          );
          
          return (
            <div key={category} className="space-y-2">
              <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
                {category}
              </h3>
              <div className="space-y-2">
                {typesInCategory.map(([type, info]) => (
                  <button
                    key={type}
                    onClick={() => onDataTypeChange(type)}
                    className={`w-full text-left p-3 rounded-lg border-2 transition-all ${
                      dataType === type
                        ? 'border-indigo-600 bg-indigo-50'
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <span className={dataType === type ? 'text-indigo-600' : 'text-gray-500'}>
                        {getIcon(info.icon)}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 truncate">{info.label}</p>
                        <p className="text-xs text-gray-500 truncate">{info.help}</p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>Selected:</strong> {dataTypeInfo[dataType]?.label} 
          {' '}(File: {dataTypeInfo[dataType]?.file})
        </p>
      </div>
    </div>
  );
}
