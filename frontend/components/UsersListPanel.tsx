'use client';

import { useState, useEffect } from 'react';
import { getUsers, updateUser, deleteUser } from '@/lib/api';
import { Edit2, Trash2, Plus } from 'lucide-react';
import AddUserModal from './AddUserModal';
import EditUserModal from './EditUserModal';

interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
  shop_ids?: number[];
  shops?: Array<{id: number; name: string}>;
}

interface UsersListPanelProps {
  refreshKey: number;
}

export default function UsersListPanel({ refreshKey }: UsersListPanelProps) {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [error, setError] = useState('');

  // Fetch users
  useEffect(() => {
    fetchUsers();
  }, [refreshKey]);

  const fetchUsers = async () => {
    setLoading(true);
    setError('');
    try {
      const usersList = await getUsers();
      setUsers(usersList);
    } catch (err: any) {
      setError('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this user?')) return;

    setDeleting(id);
    try {
      await deleteUser(id);
      setUsers(users.filter((u) => u.id !== id));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete user');
    } finally {
      setDeleting(null);
    }
  };

  const handleEdit = (user: User) => {
    setEditingUser(user);
    setShowEditModal(true);
  };

  const handleEditSuccess = () => {
    fetchUsers();
    setShowEditModal(false);
    setEditingUser(null);
  };

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'ADMIN':
        return 'bg-red-100 text-red-800';
      case 'MANAGER':
        return 'bg-blue-100 text-blue-800';
      case 'CASHIER':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Users Management</h2>
        <div className="text-gray-500">Loading users...</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-800">Users Management</h2>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 bg-indigo-600 text-white px-3 py-2 rounded-lg hover:bg-indigo-700 text-sm"
        >
          <Plus className="h-4 w-4" />
          Add User
        </button>
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm mb-4">
          {error}
        </div>
      )}

      {users.length === 0 ? (
        <div className="text-gray-500 py-8">No users created yet. Create your first user!</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-2 text-left font-semibold text-gray-700">Email</th>
                <th className="px-4 py-2 text-left font-semibold text-gray-700">Username</th>
                <th className="px-4 py-2 text-left font-semibold text-gray-700">Role</th>
                <th className="px-4 py-2 text-left font-semibold text-gray-700">Shops</th>
                <th className="px-4 py-2 text-left font-semibold text-gray-700">Status</th>
                <th className="px-4 py-2 text-left font-semibold text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-900">{user.email}</td>
                  <td className="px-4 py-3 text-gray-600">{user.username}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${getRoleBadgeColor(user.role)}`}>
                      {user.role}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {user.shops && user.shops.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {user.shops.map((shop) => (
                          <span key={shop.id} className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">
                            {shop.name}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-gray-400">No shops assigned</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {user.is_active ? (
                      <span className="text-green-700 text-xs font-semibold">Active</span>
                    ) : (
                      <span className="text-red-700 text-xs font-semibold">Inactive</span>
                    )}
                  </td>
                  <td className="px-4 py-3 flex gap-2">
                    <button
                      onClick={() => handleEdit(user)}
                      className="text-indigo-600 hover:text-indigo-800 p-1"
                      title="Edit"
                    >
                      <Edit2 className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(user.id)}
                      disabled={deleting === user.id}
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

      <AddUserModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSuccess={() => {
          setShowAddModal(false);
          fetchUsers();
        }}
      />

      {editingUser && (
        <EditUserModal
          isOpen={showEditModal}
          user={editingUser}
          onClose={() => setShowEditModal(false)}
          onSuccess={handleEditSuccess}
        />
      )}
    </div>
  );
}
