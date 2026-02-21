'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createShop } from '@/lib/api';
import { X } from 'lucide-react';

interface AddShopModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function AddShopModal({ isOpen, onClose, onSuccess }: AddShopModalProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isHeadOffice, setIsHeadOffice] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isSetupInProgress, setIsSetupInProgress] = useState(false);
  const [createdShop, setCreatedShop] = useState<any>(null);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setIsSetupInProgress(false);

    try {
      // Create the shop - this returns immediately with setup_status='pending'
      const shop = await createShop({
        name,
        description,
        is_head_office: isHeadOffice,
      });

      // Shop has been created but schema setup is still running in the background
      setCreatedShop(shop);
      setIsSetupInProgress(true);
      
      // Close the modal and redirect to admin page with status
      onClose();
      
      // Redirect to admin dashboard with shop status - migrations run in background
      setTimeout(() => {
        router.push(`/dashboard/admin?shopCreated=${shop.id}&shopName=${encodeURIComponent(shop.name)}`);
        onSuccess();
      }, 500);
      
    } catch (err: any) {
      // Only show error if it's not a timeout
      if (err.code === 'ECONNABORTED' || err.message.includes('timeout')) {
        // Timeout - shop might still be creating in the backend
        setIsSetupInProgress(true);
        setError('Shop creation is taking a bit longer. Redirecting you to the admin dashboard...');
        
        setTimeout(() => {
          onClose();
          router.push(`/dashboard/admin?shopCreating=true&shopName=${encodeURIComponent(name)}`);
          onSuccess();
        }, 2000);
      } else {
        setError(err.response?.data?.detail || err.message || 'Failed to create shop');
      }
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg max-w-md w-full mx-4">
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">Add New Shop</h2>
          <button
            onClick={onClose}
            disabled={loading}
            className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className={`p-3 rounded-lg text-sm ${
              isSetupInProgress 
                ? 'bg-blue-50 text-blue-700' 
                : 'bg-red-50 text-red-700'
            }`}>
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Shop Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              disabled={loading}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:bg-gray-100"
              placeholder="e.g., Downtown Store"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description (Optional)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              disabled={loading}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:bg-gray-100"
              placeholder="Shop description"
            />
          </div>

          <div className="flex items-center gap-3 p-3 bg-indigo-50 rounded-lg border border-indigo-200">
            <input
              type="checkbox"
              id="isHeadOffice"
              checked={isHeadOffice}
              onChange={(e) => setIsHeadOffice(e.target.checked)}
              disabled={loading}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded cursor-pointer disabled:opacity-50"
            />
            <label htmlFor="isHeadOffice" className="flex-1 cursor-pointer">
              <span className="text-sm font-medium text-gray-700">Mark as Head Office</span>
              <p className="text-xs text-gray-500 mt-0.5">The main/central location of your business</p>
            </label>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="flex-1 px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !name.trim()}
              className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading && isSetupInProgress ? (
                <>
                  <span className="inline-block h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  Setting up...
                </>
              ) : loading ? (
                'Creating...'
              ) : (
                'Create Shop'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
