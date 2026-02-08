// components/DebtorForm.tsx
// Example component showing how to use settings in forms

"use client";

import { useState } from "react";
import { useSettings } from "@/lib/useSettings";
import { Card, CardContent } from "@/components/ui/card";
import { Loader } from "lucide-react";

export function DebtorForm() {
  const {
    departments,
    salesAreas,
    creditTerms,
    loading,
    error,
  } = useSettings();

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    department_id: "",
    sales_area_id: "",
    credit_terms_id: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // Submit form data to backend
    console.log("Form data:", formData);
  };

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Loader className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-500">
        <CardContent className="p-6">
          <p className="text-red-600">Error loading settings: {error}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-6">
        <h2 className="text-lg font-semibold mb-4">Create Debtor Account</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Basic Info */}
          <div className="grid grid-cols-2 gap-4">
            <input
              type="text"
              placeholder="Debtor Name"
              value={formData.name}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
              className="border p-2 rounded-lg"
              required
            />
            <input
              type="email"
              placeholder="Email"
              value={formData.email}
              onChange={(e) =>
                setFormData({ ...formData, email: e.target.value })
              }
              className="border p-2 rounded-lg"
            />
            <input
              type="tel"
              placeholder="Phone"
              value={formData.phone}
              onChange={(e) =>
                setFormData({ ...formData, phone: e.target.value })
              }
              className="border p-2 rounded-lg"
            />
          </div>

          {/* Department Selection */}
          <div>
            <label className="block text-sm font-medium mb-1">
              Department
            </label>
            <select
              value={formData.department_id}
              onChange={(e) =>
                setFormData({ ...formData, department_id: e.target.value })
              }
              className="w-full border p-2 rounded-lg"
              required
            >
              <option value="">Select Department</option>
              {departments.map((dept) => (
                <option key={dept.id} value={dept.id}>
                  {dept.number} - {dept.name}
                </option>
              ))}
            </select>
          </div>

          {/* Sales Area Selection */}
          <div>
            <label className="block text-sm font-medium mb-1">
              Sales Area
            </label>
            <select
              value={formData.sales_area_id}
              onChange={(e) =>
                setFormData({ ...formData, sales_area_id: e.target.value })
              }
              className="w-full border p-2 rounded-lg"
              required
            >
              <option value="">Select Sales Area</option>
              {salesAreas.map((area) => (
                <option key={area.id} value={area.id}>
                  {area.number} - {area.name} ({area.user_username})
                </option>
              ))}
            </select>
          </div>

          {/* Credit Terms Selection */}
          <div>
            <label className="block text-sm font-medium mb-1">
              Credit Terms
            </label>
            <select
              value={formData.credit_terms_id}
              onChange={(e) =>
                setFormData({ ...formData, credit_terms_id: e.target.value })
              }
              className="w-full border p-2 rounded-lg"
              required
            >
              <option value="">Select Credit Terms</option>
              {creditTerms.map((term) => (
                <option key={term.id} value={term.id}>
                  {term.days} days - {term.description}
                </option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Create Debtor
          </button>
        </form>
      </CardContent>
    </Card>
  );
}
