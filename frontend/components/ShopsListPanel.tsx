'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { getShops, updateShop, deleteShop, api } from '@/lib/api';
import { useAuthContext } from '@/lib/AuthContext';
import { Edit2, Trash2, Plus, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import AddShopModal from './AddShopModal';
import EditShopModal from './EditShopModal';

interface Shop {
  id: number;
  name: string;
  description?: string;
  subdomain?: string;
  is_head_office?: boolean;
  setup_status?: 'pending' | 'ready' | 'failed';
  created_at?: string;
}

interface ShopsListPanelProps {
  refreshKey: number;
}

export default function ShopsListPanel({ refreshKey }: ShopsListPanelProps) {
  const { refetchShops } = useAuthContext();
  const [shops, setShops] = useState<Shop[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingShop, setEditingShop] = useState<Shop | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [error, setError] = useState('');
  const [statusMessage, setStatusMessage] = useState('');
  const [pollingShopId, setPollingShopId] = useState<number | null>(null);
  const searchParams = useSearchParams();

  // Handle query parameters from modal redirect
  useEffect(() => {
    const shopCreated = searchParams.get('shopCreated');
    const shopCreating = searchParams.get('shopCreating');
    const shopName = searchParams.get('shopName');

    if (shopCreated) {
      const decodedName = decodeURIComponent(shopName || 'your shop');
      setStatusMessage(`✅ Shop "${decodedName}" created! Setting up schema...`);
      setPollingShopId(parseInt(shopCreated));
      
      // Clear message after 5 seconds
      setTimeout(() => {
        setStatusMessage('');
      }, 5000);
    } else if (shopCreating) {
      const decodedName = decodeURIComponent(shopName || 'your shop');
      setStatusMessage(`⏳ Shop "${decodedName}" creation is in progress in the background...`);
      
      // Clear message after 8 seconds
      setTimeout(() => {
        setStatusMessage('');
      }, 8000);
    }
  }, [searchParams]);

  // Polling logic for pending shops
  useEffect(() => {
    if (pollingShopId === null) return;

    const pollShopStatus = async () => {
      try {
        const response = await api.get(`/api/v1/shops/${pollingShopId}/check_setup_status/`);
        const { setup_status, is_ready } = response.data;

        if (is_ready) {
          setStatusMessage(`✅ Shop is ready for use!`);
          setPollingShopId(null);
          
          // Refresh shops list
          setTimeout(() => {
            fetchShops();
          }, 1000);
          
          // Clear message after 5 seconds
          setTimeout(() => {
            setStatusMessage('');
          }, 5000);
        } else if (setup_status === 'failed') {
          setStatusMessage(`❌ Shop setup failed. Please contact support.`);
          setPollingShopId(null);
          
          // Refresh to show failed status
          setTimeout(() => {
            fetchShops();
          }, 1000);
        }
        // If still pending, continue polling
      } catch (err) {
        console.error('Error polling shop status:', err);
        // Continue polling even on error
      }
    };

    // Poll immediately and then every 3 seconds
    pollShopStatus();
    const interval = setInterval(pollShopStatus, 3000);

    return () => clearInterval(interval);
  }, [pollingShopId]);

  // Fetch shops
  useEffect(() => {
    fetchShops();
  }, [refreshKey]);

  const fetchShops = async () => {
    setLoading(true);
    setError('');
    try {
      const shopsList = await getShops();
      setShops(shopsList);
    } catch (err: any) {
      setError('Failed to load shops');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this shop?')) return;

    setDeleting(id);
    try {
      await deleteShop(id);
      setShops(shops.filter((s) => s.id !== id));
      // Also refresh the AuthContext accessible shops list
      refetchShops();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete shop');
    } finally {
      setDeleting(null);
    }
  };

  const handleEdit = (shop: Shop) => {
    setEditingShop(shop);
    setShowEditModal(true);
  };

  const handleEditSuccess = () => {
    fetchShops();
    // Also refresh the AuthContext accessible shops list
    refetchShops();
    setShowEditModal(false);
    setEditingShop(null);
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'ready':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-blue-600 animate-spin" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-600" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'ready':
        return <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs flex items-center gap-1"><CheckCircle className="h-3 w-3" /> Ready</span>;
      case 'pending':
        return <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs flex items-center gap-1"><Clock className="h-3 w-3 animate-spin" /> Setting up...</span>;
      case 'failed':
        return <span className="bg-red-100 text-red-800 px-2 py-1 rounded text-xs flex items-center gap-1"><AlertCircle className="h-3 w-3" /> Failed</span>;
      default:
        return <span className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-xs">Unknown</span>;
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Shops Management</h2>
        <div className="text-gray-500">Loading shops...</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-800">Shops Management</h2>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 bg-indigo-600 text-white px-3 py-2 rounded-lg hover:bg-indigo-700 text-sm"
        >
          <Plus className="h-4 w-4" />
          Add Shop
        </button>
      </div>

      {statusMessage && (
        <div className="bg-blue-50 border border-blue-200 text-blue-800 p-4 rounded-lg text-sm mb-4 flex items-center gap-2">
          <Clock className="h-4 w-4" />
          {statusMessage}
        </div>
      )}

      {error && (
        <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm mb-4">
          {error}
        </div>
      )}

      {shops.length === 0 ? (
        <div className="text-gray-500 py-8">No shops created yet. Create your first shop!</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-2 text-left font-semibold text-gray-700">Name</th>
                <th className="px-4 py-2 text-left font-semibold text-gray-700">Subdomain</th>
                <th className="px-4 py-2 text-left font-semibold text-gray-700">Type</th>
                <th className="px-4 py-2 text-left font-semibold text-gray-700">Status</th>
                <th className="px-4 py-2 text-left font-semibold text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody>
              {shops.map((shop) => (
                <tr key={shop.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-900">{shop.name}</td>
                  <td className="px-4 py-3 text-gray-600">{shop.subdomain || '-'}</td>
                  <td className="px-4 py-3">
                    {shop.is_head_office ? (
                      <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                        Head Office
                      </span>
                    ) : (
                      <span className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-xs">
                        Branch
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {getStatusBadge(shop.setup_status)}
                  </td>
                  <td className="px-4 py-3 flex gap-2">
                    <button
                      onClick={() => handleEdit(shop)}
                      disabled={shop.setup_status !== 'ready'}
                      className="text-indigo-600 hover:text-indigo-800 p-1 disabled:opacity-50 disabled:cursor-not-allowed"
                      title={shop.setup_status !== 'ready' ? 'Shop must be ready to edit' : 'Edit'}
                    >
                      <Edit2 className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(shop.id)}
                      disabled={deleting === shop.id}
                      className="text-red-600 hover:text-red-800 p-1 disabled:opacity-50"
                      title="Delete"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <AddShopModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSuccess={() => {
          setShowAddModal(false);
          fetchShops();
          // Also refresh the AuthContext accessible shops list
          refetchShops();
        }}
      />

      {editingShop && (
        <EditShopModal
          isOpen={showEditModal}
          shop={editingShop}
          onClose={() => setShowEditModal(false)}
          onSuccess={handleEditSuccess}
        />
      )}
    </div>
  );
}
