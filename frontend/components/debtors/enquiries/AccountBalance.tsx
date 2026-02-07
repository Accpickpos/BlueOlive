'use client';

interface Debtor {
  id: number;
  name: string;
  account_number: string;
  account_category: string;
  current_balance: number;
}

interface BalanceDetails {
  opening_balance: number;
  current_balance: number;
  age_current: number;
  age_30: number;
  age_60: number;
  age_90: number;
  age_120: number;
  age_150: number;
  age_180: number;
}

interface AccountBalanceProps {
  debtor: Debtor;
  balance: BalanceDetails;
}

export default function AccountBalance({ debtor, balance }: AccountBalanceProps) {
  const getAgingColor = (amount: number) => {
    if (amount > 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const balanceStatuses = [
    { label: 'Opening Balance', value: balance.opening_balance, key: 'opening' },
    { label: 'Current (0-29 days)', value: balance.age_current, key: 'current' },
    { label: '30-59 days', value: balance.age_30, key: 'age30' },
    { label: '60-89 days', value: balance.age_60, key: 'age60' },
    { label: '90-119 days', value: balance.age_90, key: 'age90' },
    { label: '120-149 days', value: balance.age_120, key: 'age120' },
    { label: '150-179 days', value: balance.age_150, key: 'age150' },
    { label: '180+ days', value: balance.age_180, key: 'age180' },
    { label: 'Closing Balance', value: balance.current_balance, key: 'closing' },
  ];

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">Account Balance & Aging Analysis</h3>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
          <p className="text-xs text-green-700 font-medium">Opening Balance</p>
          <p className="text-xl font-bold text-green-900">R{balance.opening_balance.toFixed(2)}</p>
        </div>

        <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
          <p className="text-xs text-blue-700 font-medium">Current Balance</p>
          <p className="text-xl font-bold text-blue-900">R{balance.current_balance.toFixed(2)}</p>
        </div>

        <div className={`bg-gradient-to-br ${balance.current_balance > 0 ? 'from-red-50 to-red-100' : 'from-gray-50 to-gray-100'} p-4 rounded-lg border ${balance.current_balance > 0 ? 'border-red-200' : 'border-gray-200'}`}>
          <p className={`text-xs font-medium ${balance.current_balance > 0 ? 'text-red-700' : 'text-gray-700'}`}>Total Due</p>
          <p className={`text-xl font-bold ${balance.current_balance > 0 ? 'text-red-900' : 'text-gray-900'}`}>
            R{Math.abs(balance.current_balance).toFixed(2)}
          </p>
        </div>
      </div>

      {/* Aging Analysis Table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100 border-b border-gray-200">
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Aging Period</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Amount (R)</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">%</th>
              </tr>
            </thead>
            <tbody>
              {balanceStatuses.map((status, idx) => {
                const isTotal = status.key === 'opening' || status.key === 'closing';
                const isAgingRow = !isTotal;
                const percentage = balance.current_balance !== 0 && isAgingRow 
                  ? ((status.value / balance.current_balance) * 100).toFixed(1)
                  : '0.0';

                return (
                  <tr 
                    key={status.key}
                    className={`border-b border-gray-200 ${isTotal ? 'bg-gray-50 font-semibold' : 'hover:bg-gray-50'}`}
                  >
                    <td className="px-4 py-3 text-gray-900">{status.label}</td>
                    <td className={`px-4 py-3 text-right font-medium ${getAgingColor(status.value)}`}>
                      R{status.value.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-600">
                      {isAgingRow && percentage}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Aging Bar Chart */}
      {balance.current_balance > 0 && (
        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
          <h4 className="font-semibold text-gray-900 mb-4">Balance Distribution</h4>
          <div className="space-y-2">
            {[
              { label: 'Current', value: balance.age_current, color: 'bg-green-500' },
              { label: '30 days', value: balance.age_30, color: 'bg-yellow-500' },
              { label: '60 days', value: balance.age_60, color: 'bg-orange-500' },
              { label: '90+ days', value: balance.age_90 + balance.age_120 + balance.age_150 + balance.age_180, color: 'bg-red-500' },
            ].map(item => {
              const percentage = (item.value / balance.current_balance) * 100;
              return percentage > 0 ? (
                <div key={item.label}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-700 font-medium">{item.label}</span>
                    <span className="text-gray-600">R{item.value.toFixed(2)} ({percentage.toFixed(1)}%)</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${item.color}`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              ) : null;
            })}
          </div>
        </div>
      )}
    </div>
  );
}
