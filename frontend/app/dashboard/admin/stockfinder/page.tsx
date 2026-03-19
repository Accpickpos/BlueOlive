// app/dashboard/admin/stockfinder/page.tsx
"use client";
import { useState, useEffect } from "react";
import { Settings, Plus, Trash2, Edit2, Loader, Check, X, RefreshCw, Webhook } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

interface StockFinderConfig {
  id: number;
  name: string;
  base_url: string;
  fitment_center_code: string;
  auto_sync_stock: boolean;
  sync_interval_minutes: number;
  last_sync: string | null;
  is_active: boolean;
  enable_custom_pricing: boolean;
  custom_price_field_1: string;
  custom_price_field_2: string;
  custom_price_field_3: string;
  webhook_enabled: boolean;
  webhook_secret: string;
  created_at: string;
  updated_at: string;
}

export default function StockfinderSettingsPage() {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  const [configs, setConfigs] = useState<StockFinderConfig[]>([]);
  const [editingConfig, setEditingConfig] = useState<StockFinderConfig | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  
  const [formData, setFormData] = useState({
    name: '',
    base_url: '',
    api_key: '',
    api_secret: '',
    fitment_center_code: '',
    auto_sync_stock: false,
    sync_interval_minutes: 60,
    is_active: true,
    enable_custom_pricing: false,
    custom_price_field_1: '',
    custom_price_field_2: '',
    custom_price_field_3: '',
    webhook_enabled: false,
    webhook_secret: '',
  });

  useEffect(() => {
    loadConfigs();
  }, []);

  const loadConfigs = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/v1/stockfinder/configs/');
      setConfigs(response.data.results || response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load configurations');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setIsCreating(true);
    setEditingConfig(null);
    setFormData({
      name: '',
      base_url: '',
      api_key: '',
      api_secret: '',
      fitment_center_code: '',
      auto_sync_stock: false,
      sync_interval_minutes: 60,
      is_active: true,
      enable_custom_pricing: false,
      custom_price_field_1: '',
      custom_price_field_2: '',
      custom_price_field_3: '',
      webhook_enabled: false,
      webhook_secret: '',
    });
  };

  const handleEdit = (config: StockFinderConfig) => {
    setEditingConfig(config);
    setIsCreating(false);
    setFormData({
      name: config.name,
      base_url: config.base_url,
      api_key: '',
      api_secret: '',
      fitment_center_code: config.fitment_center_code,
      auto_sync_stock: config.auto_sync_stock,
      sync_interval_minutes: config.sync_interval_minutes,
      is_active: config.is_active,
      enable_custom_pricing: config.enable_custom_pricing,
      custom_price_field_1: config.custom_price_field_1 || '',
      custom_price_field_2: config.custom_price_field_2 || '',
      custom_price_field_3: config.custom_price_field_3 || '',
      webhook_enabled: config.webhook_enabled,
      webhook_secret: '', // Don't show existing secret
    });
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccessMessage(null);
    
    try {
      const payload: any = {
        name: formData.name,
        base_url: formData.base_url,
        fitment_center_code: formData.fitment_center_code,
        auto_sync_stock: formData.auto_sync_stock,
        sync_interval_minutes: formData.sync_interval_minutes,
        is_active: formData.is_active,
        enable_custom_pricing: formData.enable_custom_pricing,
        custom_price_field_1: formData.custom_price_field_1,
        custom_price_field_2: formData.custom_price_field_2,
        custom_price_field_3: formData.custom_price_field_3,
        webhook_enabled: formData.webhook_enabled,
      };
      
      // Only include API credentials if provided
      if (formData.api_key) payload['api_key'] = formData.api_key;
      if (formData.api_secret) payload['api_secret'] = formData.api_secret;
      if (formData.webhook_secret) payload['webhook_secret'] = formData.webhook_secret;

      if (editingConfig) {
        await api.patch(`/api/v1/stockfinder/configs/${editingConfig.id}/`, payload);
        setSuccessMessage('Configuration updated successfully!');
      } else {
        await api.post('/api/v1/stockfinder/configs/', payload);
        setSuccessMessage('Configuration created successfully!');
      }
      
      loadConfigs();
      setEditingConfig(null);
      setIsCreating(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || JSON.stringify(err.response?.data) || 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this configuration?')) return;
    
    try {
      await api.delete(`/api/v1/stockfinder/configs/${id}/`);
      setSuccessMessage('Configuration deleted successfully!');
      loadConfigs();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete configuration');
    }
  };

  const handleTestConnection = async (id: number) => {
    setTesting(true);
    try {
      const response = await api.post(`/api/v1/stockfinder/configs/${id}/test_connection/`);
      setSuccessMessage(response.data.message || 'Connection successful!');
    } catch (err: any) {
      setError(err.response?.data?.message || 'Connection failed');
    } finally {
      setTesting(false);
    }
  };

  const handleSyncStock = async (id: number) => {
    setTesting(true);
    try {
      const response = await api.post(`/api/v1/stockfinder/configs/${id}/sync_stock/`);
      setSuccessMessage(response.data.message || 'Stock sync initiated!');
    } catch (err: any) {
      setError(err.response?.data?.message || 'Sync failed');
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="container mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Settings className="h-8 w-8" />
            Stockfinder Integration
          </h1>
          <p className="text-gray-600 mt-1">Configure connection to Stockfinder fitment center system</p>
        </div>
        <button
          onClick={handleCreate}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" /> Add Configuration
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
          <X className="h-5 w-5 text-red-500" />
          <span className="text-red-700">{error}</span>
          <button onClick={() => setError(null)} className="ml-auto text-red-500 hover:text-red-700">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {successMessage && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2">
          <Check className="h-5 w-5 text-green-500" />
          <span className="text-green-700">{successMessage}</span>
          <button onClick={() => setSuccessMessage(null)} className="ml-auto text-green-500 hover:text-green-700">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Configuration Form */}
      {(isCreating || editingConfig) && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>{editingConfig ? 'Edit Configuration' : 'New Configuration'}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Basic Settings */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Configuration Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  placeholder="e.g., Main Stockfinder Account"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Base URL *</label>
                <input
                  type="url"
                  value={formData.base_url}
                  onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  placeholder="https://api.stockfinder.co.za"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">API Key</label>
                <input
                  type="password"
                  value={formData.api_key}
                  onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  placeholder="Enter API key (leave empty to keep existing)"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">API Secret</label>
                <input
                  type="password"
                  value={formData.api_secret}
                  onChange={(e) => setFormData({ ...formData, api_secret: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  placeholder="Enter API secret (leave empty to keep existing)"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Fitment Center Code</label>
                <input
                  type="text"
                  value={formData.fitment_center_code}
                  onChange={(e) => setFormData({ ...formData, fitment_center_code: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  placeholder="e.g., JHB001"
                />
              </div>

              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="h-4 w-4"
                  />
                  <span className="text-sm">Active</span>
                </label>

                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.auto_sync_stock}
                    onChange={(e) => setFormData({ ...formData, auto_sync_stock: e.target.checked })}
                    className="h-4 w-4"
                  />
                  <span className="text-sm">Auto-sync stock</span>
                </label>
              </div>

              {formData.auto_sync_stock && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Sync Interval (minutes)</label>
                  <input
                    type="number"
                    value={formData.sync_interval_minutes}
                    onChange={(e) => setFormData({ ...formData, sync_interval_minutes: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border rounded-lg"
                    min={5}
                  />
                </div>
              )}

              {/* Custom Pricing */}
              <div className="col-span-2 border-t pt-4 mt-2">
                <h3 className="font-medium text-gray-900 mb-3">Custom Pricing Fields</h3>
              </div>

              <label className="flex items-center gap-2 col-span-2">
                <input
                  type="checkbox"
                  checked={formData.enable_custom_pricing}
                  onChange={(e) => setFormData({ ...formData, enable_custom_pricing: e.target.checked })}
                  className="h-4 w-4"
                />
                <span className="text-sm">Enable custom pricing fields from Stockfinder</span>
              </label>

              {formData.enable_custom_pricing && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Custom Price Field 1</label>
                    <input
                      type="text"
                      value={formData.custom_price_field_1}
                      onChange={(e) => setFormData({ ...formData, custom_price_field_1: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      placeholder="e.g., wholesale_price"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Custom Price Field 2</label>
                    <input
                      type="text"
                      value={formData.custom_price_field_2}
                      onChange={(e) => setFormData({ ...formData, custom_price_field_2: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      placeholder="e.g., dealer_price"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Custom Price Field 3</label>
                    <input
                      type="text"
                      value={formData.custom_price_field_3}
                      onChange={(e) => setFormData({ ...formData, custom_price_field_3: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      placeholder="e.g., special_price"
                    />
                  </div>
                </>
              )}

              {/* Webhook Settings */}
              <div className="col-span-2 border-t pt-4 mt-2">
                <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                  <Webhook className="h-4 w-4" /> Webhook Settings
                </h3>
              </div>

              <label className="flex items-center gap-2 col-span-2">
                <input
                  type="checkbox"
                  checked={formData.webhook_enabled}
                  onChange={(e) => setFormData({ ...formData, webhook_enabled: e.target.checked })}
                  className="h-4 w-4"
                />
                <span className="text-sm">Enable webhook to receive orders from Stockfinder</span>
              </label>

              {formData.webhook_enabled && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Webhook Secret</label>
                  <input
                    type="password"
                    value={formData.webhook_secret}
                    onChange={(e) => setFormData({ ...formData, webhook_secret: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg"
                    placeholder="Enter webhook secret (leave empty to keep existing)"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Use this secret in Stockfinder webhook configuration. 
                    Webhook URL: <code className="bg-gray-100 px-1">/api/v1/stockfinder/webhook/</code>
                  </p>
                </div>
              )}
            </div>

            <div className="flex gap-2 mt-6">
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
              >
                {saving ? <Loader className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
                {saving ? 'Saving...' : 'Save Configuration'}
              </button>
              <button
                onClick={() => { setEditingConfig(null); setIsCreating(false); }}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Configurations List */}
      <div className="grid gap-4">
        {loading ? (
          <div className="flex justify-center py-8">
            <Loader className="h-8 w-8 animate-spin text-blue-600" />
          </div>
        ) : configs.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center text-gray-500">
              No Stockfinder configurations found. Click "Add Configuration" to create one.
            </CardContent>
          </Card>
        ) : (
          configs.map((config) => (
            <Card key={config.id} className={!config.is_active ? 'opacity-60' : ''}>
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-lg">{config.name}</h3>
                      {config.is_active ? (
                        <span className="px-2 py-0.5 text-xs bg-green-100 text-green-800 rounded-full">Active</span>
                      ) : (
                        <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-800 rounded-full">Inactive</span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600">{config.base_url}</p>
                    {config.fitment_center_code && (
                      <p className="text-sm text-gray-500">Fitment Center: {config.fitment_center_code}</p>
                    )}
                    {config.last_sync && (
                      <p className="text-xs text-gray-400">Last sync: {new Date(config.last_sync).toLocaleString()}</p>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleTestConnection(config.id)}
                      disabled={testing}
                      className="flex items-center gap-1 px-3 py-1.5 text-sm border rounded-lg hover:bg-gray-50"
                    >
                      <RefreshCw className={`h-3 w-3 ${testing ? 'animate-spin' : ''}`} />
                      Test
                    </button>
                    <button
                      onClick={() => handleSyncStock(config.id)}
                      disabled={testing}
                      className="flex items-center gap-1 px-3 py-1.5 text-sm border rounded-lg hover:bg-gray-50"
                    >
                      <RefreshCw className={`h-3 w-3 ${testing ? 'animate-spin' : ''}`} />
                      Sync
                    </button>
                    <button
                      onClick={() => handleEdit(config)}
                      className="flex items-center gap-1 px-3 py-1.5 text-sm border rounded-lg hover:bg-gray-50"
                    >
                      <Edit2 className="h-3 w-3" />
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(config.id)}
                      className="flex items-center gap-1 px-3 py-1.5 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
