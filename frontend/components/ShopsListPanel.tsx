'use client';

import { useState, useEffect } from 'react';
import { getShops, updateShop, deleteShop } from '@/lib/api';
import { Edit2, Trash2, Plus } from 'lucide-react';
import AddShopModal from './AddShopModal';
import EditShopModal from './EditShopModal';

interface Shop {
  id: number;
  name: string;
  description?: string;
  subdomain?: string;
  is_head_office?: boolean;
}

interface ShopsListPanelProps {
  refreshKey: number;
}

export default function ShopsListPanel({ refreshKey }: ShopsListPanelProps) {
  const [shops, setShops] = useState<Shop[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingShop, setEditingShop] = useState<Shop | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [error, setError] = useState('');

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
    setShowEditModal(false);
    setEditingShop(null);
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
                  <td className="px-4 py-3 flex gap-2">
                    <button
                      onClick={() => handleEdit(shop)}
                      className="text-indigo-600 hover:text-indigo-800 p-1"
                      title="Edit"
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
