// app/settings/page.tsx
"use client";
import { useState } from "react";
import { Settings } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    email: "admin@company.com",
    taxNumber: "TX-123456",
    dayEnd: "21:00",
    monthEnd: "Last Day",
    yearEnd: "31 December",
    autoTaxReport: true,
  });

  const handleChange = (field: string, value: string | boolean) => {
    setSettings({ ...settings, [field]: value });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Settings className="h-6 w-6" />
        <h1 className="text-2xl font-bold">Settings</h1>
      </div>

      {/* Account Settings */}
      <Card>
        <CardContent className="p-6 space-y-4">
          <h2 className="text-lg font-semibold">Account Defaults</h2>
          <div className="space-y-3">
            <div>
              <label className="block text-sm text-gray-600">Company Email</label>
              <input
                type="email"
                value={settings.email}
                onChange={(e) => handleChange("email", e.target.value)}
                className="w-full border p-2 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600">Tax Number</label>
              <input
                type="text"
                value={settings.taxNumber}
                onChange={(e) => handleChange("taxNumber", e.target.value)}
                className="w-full border p-2 rounded-lg"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Period Settings */}
      <Card>
        <CardContent className="p-6 space-y-4">
          <h2 className="text-lg font-semibold">Period Settings</h2>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm text-gray-600">Day-End Close</label>
              <input
                type="time"
                value={settings.dayEnd}
                onChange={(e) => handleChange("dayEnd", e.target.value)}
                className="w-full border p-2 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600">Month-End Close</label>
              <select
                value={settings.monthEnd}
                onChange={(e) => handleChange("monthEnd", e.target.value)}
                className="w-full border p-2 rounded-lg"
              >
                <option>Last Day</option>
                <option>25th</option>
                <option>28th</option>
                <option>30th</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-600">Year-End Close</label>
              <select
                value={settings.yearEnd}
                onChange={(e) => handleChange("yearEnd", e.target.value)}
                className="w-full border p-2 rounded-lg"
              >
                <option>31 December</option>
                <option>31 March</option>
                <option>30 June</option>
                <option>30 September</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tax Reports */}
      <Card>
        <CardContent className="p-6 space-y-4">
          <h2 className="text-lg font-semibold">Tax Reports</h2>
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={settings.autoTaxReport}
              onChange={(e) => handleChange("autoTaxReport", e.target.checked)}
              className="h-4 w-4"
            />
            <span>Automatically generate tax reports at year end</span>
          </div>
        </CardContent>
      </Card>

      {/* Live Preview */}
      <Card className="border-blue-500">
        <CardContent className="p-6 space-y-3">
          <h2 className="text-lg font-semibold text-blue-600">Preview</h2>
          <p className="text-gray-700">
            📧 <strong>Email:</strong> {settings.email}
          </p>
          <p className="text-gray-700">
            🏷 <strong>Tax Number:</strong> {settings.taxNumber}
          </p>
          <p className="text-gray-700">
            ⏰ <strong>Day-End Close:</strong> {settings.dayEnd}
          </p>
          <p className="text-gray-700">
            📆 <strong>Month-End Close:</strong> {settings.monthEnd}
          </p>
          <p className="text-gray-700">
            📅 <strong>Year-End Close:</strong> {settings.yearEnd}
          </p>
          <p className="text-gray-700">
            🧾 <strong>Tax Reports:</strong>{" "}
            {settings.autoTaxReport ? "Automatically generated" : "Manual only"}
          </p>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <button className="px-6 py-2 rounded-lg bg-blue-600 text-white shadow hover:bg-blue-700">
          Save Settings
        </button>
      </div>
    </div>
  );
}
