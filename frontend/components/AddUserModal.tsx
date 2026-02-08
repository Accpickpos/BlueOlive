'use client';

import { useState, useEffect } from 'react';
import { createUser, getShops } from '@/lib/api';
import { extractErrorMessage } from '@/lib/utils';
import { X } from 'lucide-react';

interface AddUserModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

interface Shop {
  id: number;
  name: string;
}

export default function AddUserModal({ isOpen, onClose, onSuccess }: AddUserModalProps) {
  const [shops, setShops] = useState<Shop[]>([]);
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState('STAFF');
  const [selectedShopIds, setSelectedShopIds] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);
  const [shopsLoading, setShopsLoading] = useState(false);
  const [error, setError] = useState('');

  // Fetch shops on modal open
  useEffect(() => {
    if (isOpen) {
      fetchShops();
    }
  }, [isOpen]);

  const fetchShops = async () => {
    setShopsLoading(true);
    setError('');
    try {
      const shopsList = await getShops();
      setShops(shopsList);
      // Auto-select first shop if available
      if (shopsList.length > 0) {
        setSelectedShopIds([shopsList[0].id]);
      }
    } catch (err: any) {
      console.error('Error fetching shops:', err);
      setError(extractErrorMessage(err));
      setShops([]);
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

    // Validate passwords match
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    try {
      await createUser({
        username: username || email,
        email,
        password,
        confirm_password: confirmPassword,
        role,
        shop_ids: selectedShopIds,
      });

      // Reset form
      setEmail('');
      setUsername('');
      setPassword('');
      setConfirmPassword('');
      setRole('STAFF');
      setSelectedShopIds([]);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center p-6 border-b sticky top-0 bg-white">
          <h2 className="text-xl font-semibold text-gray-900">Add New User</h2>
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
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="user@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Username (Optional)
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Will use email if not provided"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Secure password"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Confirm Password
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Re-enter password"
            />
            {password && confirmPassword && password !== confirmPassword && (
              <p className="text-xs text-red-600 mt-1">Passwords do not match</p>
            )}
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
            {selectedShopIds.length === 0 && !shopsLoading && (
              <p className="text-xs text-amber-600 mt-1">Select at least one shop</p>
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
              disabled={loading || !email.trim() || !password.trim() || !confirmPassword.trim() || password !== confirmPassword || selectedShopIds.length === 0}
              className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating...' : 'Create User'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
