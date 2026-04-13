// app/dashboard/admin/api-keys/page.tsx
"use client";
import { useState, useEffect } from "react";
import { Key, Plus, Trash2, Copy, Check, X, Loader } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

interface APIKey {
  id: number;
  name: string;
  key: string;
  external_service: string;
  description: string;
  status: string;
  last_used: string | null;
  expires_at: string | null;
  created_at: string;
}

export default function APIKeysPage() {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newKey, setNewKey] = useState<APIKey | null>(null);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  
  const [formData, setFormData] = useState({
    name: '',
    external_service: 'Stockfinder',
    description: '',
    expires_at: '',
  });
  
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadAPIKeys();
  }, []);

  const loadAPIKeys = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/v1/api-keys/');
      setApiKeys(response.data.results || response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load API keys');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    setSaving(true);
    setError(null);
    try {
      const payload: any = {
        name: formData.name,
        external_service: formData.external_service,
        description: formData.description,
      };
      if (formData.expires_at) {
        payload.expires_at = formData.expires_at;
      }
      
      const response = await api.post('/api/v1/api-keys/', payload);
      
      // The key is only shown once on creation
      setNewKey(response.data);
      setSuccessMessage('API key created successfully!');
      setShowCreateModal(false);
      setFormData({
        name: '',
        external_service: 'Stockfinder',
        description: '',
        expires_at: '',
      });
      
      // Reload the list (without the actual key)
      loadAPIKeys();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create API key');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this API key?')) return;
    
    try {
      await api.delete(`/api/v1/api-keys/${id}/`);
      setSuccessMessage('API key deleted successfully!');
      loadAPIKeys();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete API key');
    }
  };

  const copyToClipboard = (text: string, id: number) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredKeys = apiKeys.filter(key => {
    if (filter === 'all') return true;
    if (filter === 'active') return key.status === 'ACTIVE';
    if (filter === 'inactive') return key.status === 'INACTIVE';
    if (filter === 'stockfinder') return key.external_service === 'Stockfinder';
    return true;
  });

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Key className="h-8 w-8" />
            API Keys
          </h1>
          <p className="text-gray-600 mt-1">
            Manage API keys for external integrations like Stockfinder
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          Create API Key
        </button>
      </div>

      {/* Filter */}
      <div className="mb-4 flex gap-2">
        <button
          onClick={() => setFilter('all')}
          className={`px-3 py-1 rounded ${filter === 'all' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100'}`}
        >
          All
        </button>
        <button
          onClick={() => setFilter('stockfinder')}
          className={`px-3 py-1 rounded ${filter === 'stockfinder' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100'}`}
        >
          Stockfinder
        </button>
        <button
          onClick={() => setFilter('active')}
          className={`px-3 py-1 rounded ${filter === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100'}`}
        >
          Active
        </button>
        <button
          onClick={() => setFilter('inactive')}
          className={`px-3 py-1 rounded ${filter === 'inactive' ? 'bg-red-100 text-red-800' : 'bg-gray-100'}`}
        >
          Inactive
        </button>
      </div>

      {/* Error/Success Messages */}
      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}
      {successMessage && (
        <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded">
          {successMessage}
        </div>
      )}

      {/* New Key Modal */}
      {newKey && (
        <Card className="mb-6 border-green-500">
          <CardHeader className="bg-green-50">
            <CardTitle className="text-green-800 flex items-center gap-2">
              <Check className="h-5 w-5" />
              API Key Created
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            <p className="text-sm text-gray-600 mb-2">
              Copy this key now. You won't be able to see it again!
            </p>
            <div className="flex items-center gap-2 p-3 bg-gray-100 rounded font-mono text-sm">
              <span className="flex-1 break-all">{newKey.key}</span>
              <button
                onClick={() => copyToClipboard(newKey.key, -1)}
                className="p-1 hover:bg-gray-200 rounded"
                title="Copy"
              >
                {copiedId === -1 ? <Check className="h-4 w-4 text-green-600" /> : <Copy className="h-4 w-4" />}
              </button>
            </div>
            <button
              onClick={() => setNewKey(null)}
              className="mt-3 text-sm text-gray-600 hover:text-gray-800"
            >
              I've copied the key
            </button>
          </CardContent>
        </Card>
      )}

      {/* Keys List */}
      {loading ? (
        <div className="text-center py-8">
          <Loader className="h-8 w-8 animate-spin mx-auto" />
        </div>
      ) : filteredKeys.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center text-gray-500">
            No API keys found. Click "Create API Key" to add one.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredKeys.map((key) => (
            <Card key={key.id}>
              <CardContent className="p-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold">{key.name}</h3>
                      <span className={`px-2 py-0.5 text-xs rounded ${
                        key.status === 'ACTIVE' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {key.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      {key.external_service} • {key.description || 'No description'}
                    </p>
                    <div className="text-xs text-gray-500 mt-1">
                      Last used: {key.last_used || 'Never'} • Created: {new Date(key.created_at).toLocaleDateString()}
                      {key.expires_at && ` • Expires: ${new Date(key.expires_at).toLocaleDateString()}`}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleDelete(key.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded"
                      title="Delete"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Create API Key</h2>
              <button onClick={() => setShowCreateModal(false)} className="text-gray-500">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  placeholder="e.g., Stockfinder Production"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">External Service *</label>
                <select
                  value={formData.external_service}
                  onChange={(e) => setFormData({ ...formData, external_service: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  <option value="Stockfinder">Stockfinder</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  rows={2}
                  placeholder="Optional description for this key"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Expires At</label>
                <input
                  type="datetime-local"
                  value={formData.expires_at}
                  onChange={(e) => setFormData({ ...formData, expires_at: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                />
                <p className="text-xs text-gray-500 mt-1">Leave empty for no expiration</p>
              </div>
            </div>
            
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={saving || !formData.name || !formData.external_service}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {saving ? 'Creating...' : 'Create Key'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
