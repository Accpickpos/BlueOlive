'use client';

import { useState, useEffect } from 'react';
import { updateUser, getShops } from '@/lib/api';
import { X } from 'lucide-react';

interface EditUserModalProps {
  isOpen: boolean;
  user: {
    id: number;
    username: string;
    email: string;
    role: string;
    is_active: boolean;
    shop_ids?: number[];
    shops?: Array<{id: number; name: string}>;
  };
  onClose: () => void;
  onSuccess: () => void;
}

interface Shop {
  id: number;
  name: string;
}

export default function EditUserModal({
  isOpen,
  user,
  onClose,
  onSuccess,
}: EditUserModalProps) {
  const [role, setRole] = useState(user.role);
  const [isActive, setIsActive] = useState(user.is_active);
  const [password, setPassword] = useState('');
  const [shops, setShops] = useState<Shop[]>([]);
  const [selectedShopIds, setSelectedShopIds] = useState<number[]>(user.shop_ids || []);
  const [loading, setLoading] = useState(false);
  const [shopsLoading, setShopsLoading] = useState(false);
  const [error, setError] = useState('');

  // Fetch shops when modal opens
  useEffect(() => {
    if (isOpen) {
      fetchShops();
      setSelectedShopIds(user.shop_ids || []);
    }
  }, [isOpen, user.shop_ids]);

  const fetchShops = async () => {
    setShopsLoading(true);
    try {
      const shopsList = await getShops();
      setShops(shopsList);
    } catch (err) {
      setError('Failed to load shops');
    } finally {
      setShopsLoading(false);
    }
  };

  const toggleShop = (shopId: number) => {
    setSelectedShopIds((prev) =>
      prev.includes(shopId)
        ? prev.filter((id) => id !== shopId)
        : [...prev, shopId]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const updateData: any = {
        role,
        is_active: isActive,
        shop_ids: selectedShopIds,
      };
      
      // Only include password if it was entered
      if (password.trim()) {
        updateData.password = password;
      }
      
      await updateUser(user.id, updateData);
      onSuccess();
    } catch (err: any) {
      console.error('Update error:', err);
      const errorMsg = err.response?.data?.detail || 
                      err.response?.data?.[0] ||
                      JSON.stringify(err.response?.data) ||
                      err.message || 
                      'Failed to update user';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg max-w-md w-full mx-4">
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">Edit User</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              type="email"
              value={user.email}
              disabled
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-600"
            />
            <p className="text-xs text-gray-500 mt-1">Email cannot be changed</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Role
            </label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="STAFF">Staff</option>
              <option value="CASHIER">Cashier</option>
              <option value="MANAGER">Manager</option>
              <option value="ADMIN">Admin</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              New Password (Leave blank to keep current)
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter new password"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <p className="text-xs text-gray-500 mt-1">Password should be at least 8 characters</p>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="isActive"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            />
            <label htmlFor="isActive" className="ml-2 text-sm text-gray-700">
              User is active
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Assign to Shops
            </label>
            {shopsLoading ? (
              <div className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-500">
                Loading shops...
              </div>
            ) : shops.length === 0 ? (
              <div className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-500">
                No shops available
              </div>
            ) : (
              <div className="space-y-2 border border-gray-300 rounded-lg p-3 bg-gray-50">
                {shops.map((shop) => (
                  <label key={shop.id} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedShopIds.includes(shop.id)}
                      onChange={() => toggleShop(shop.id)}
                      className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                    />
                    <span className="text-sm text-gray-700">{shop.name}</span>
                  </label>
                ))}
              </div>
            )}
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Updating...' : 'Update User'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
