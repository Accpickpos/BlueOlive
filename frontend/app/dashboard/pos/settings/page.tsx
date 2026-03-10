// app/dashboard/pos/settings/page.tsx
"use client";

import { useState, useEffect, useRef } from "react";
import { Settings, Upload, Image as ImageIcon, Loader2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";
import { getCurrentShopId, getCurrentShop, setCurrentShop, Shop } from "@/lib/shopContext";

interface ShopSettings {
  id: number;
  name: string;
  address: string;
  phone: string;
  logo: string | null;
}

export default function POSSettingsPage() {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  const [shopSettings, setShopSettings] = useState<ShopSettings>({
    id: 0,
    name: "",
    address: "",
    phone: "",
    logo: null,
  });
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadShopSettings();
  }, []);

  const loadShopSettings = async () => {
    const shopId = getCurrentShopId();
    if (!shopId) {
      setMessage({ type: 'error', text: 'No shop selected' });
      return;
    }

    setLoading(true);
    try {
      const response = await api.get(`/api/shops/${shopId}/`);
      const shop: ShopSettings = response.data;
      setShopSettings(shop);
      if (shop.logo) {
        setLogoPreview(shop.logo);
      }
    } catch (error) {
      console.error('Failed to load shop settings:', error);
      setMessage({ type: 'error', text: 'Failed to load shop settings' });
    } finally {
      setLoading(false);
    }
  };

  const handleLogoSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      setMessage({ type: 'error', text: 'Please select an image file' });
      return;
    }

    // Validate file size (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      setMessage({ type: 'error', text: 'File size must be less than 2MB' });
      return;
    }

    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setLogoPreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);

    // Save the file
    uploadLogo(file);
  };

  const uploadLogo = async (file: File) => {
    const shopId = getCurrentShopId();
    if (!shopId) return;

    setSaving(true);
    setMessage(null);

    const formData = new FormData();
    formData.append('logo', file);

    try {
      const response = await api.patch(`/api/shops/${shopId}/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setShopSettings(prev => ({ ...prev, logo: response.data.logo }));
      
      // Update localStorage with new shop data
      const currentShop = getCurrentShop();
      if (currentShop) {
        setCurrentShop({ ...currentShop, logo: response.data.logo });
      }

      setMessage({ type: 'success', text: 'Logo uploaded successfully!' });
    } catch (error: any) {
      console.error('Failed to upload logo:', error);
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to upload logo' });
      // Revert preview on error
      setLogoPreview(shopSettings.logo);
    } finally {
      setSaving(false);
    }
  };

  const handleRemoveLogo = async () => {
    const shopId = getCurrentShopId();
    if (!shopId) return;

    setSaving(true);
    setMessage(null);

    try {
      // Create an empty FormData to clear the logo
      const formData = new FormData();
      // Send empty string to clear the logo
      await api.patch(`/api/shops/${shopId}/`, { logo: '' });

      setShopSettings(prev => ({ ...prev, logo: null }));
      setLogoPreview(null);

      // Update localStorage
      const currentShop = getCurrentShop();
      if (currentShop) {
        setCurrentShop({ ...currentShop, logo: null });
      }

      setMessage({ type: 'success', text: 'Logo removed successfully!' });
    } catch (error: any) {
      console.error('Failed to remove logo:', error);
      setMessage({ type: 'error', text: 'Failed to remove logo' });
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (field: keyof ShopSettings, value: string) => {
    setShopSettings(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    const shopId = getCurrentShopId();
    if (!shopId) return;

    setSaving(true);
    setMessage(null);

    try {
      const response = await api.patch(`/api/shops/${shopId}/`, {
        name: shopSettings.name,
        address: shopSettings.address,
        phone: shopSettings.phone,
      });

      setShopSettings(prev => ({ 
        ...prev, 
        name: response.data.name,
        address: response.data.address,
        phone: response.data.phone,
      }));

      // Update localStorage
      const currentShop = getCurrentShop();
      if (currentShop) {
        setCurrentShop({ 
          ...currentShop, 
          name: response.data.name,
          address: response.data.address,
          phone: response.data.phone,
        });
      }

      setMessage({ type: 'success', text: 'Settings saved successfully!' });
    } catch (error: any) {
      console.error('Failed to save settings:', error);
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to save settings' });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Settings className="h-6 w-6" />
        <h1 className="text-2xl font-bold">Shop Settings</h1>
      </div>

      {/* Message */}
      {message && (
        <div className={`p-4 rounded-lg ${message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
          {message.text}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center p-8">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        </div>
      ) : (
        <>
          {/* Logo Upload */}
          <Card>
            <CardContent className="p-6 space-y-4">
              <h2 className="text-lg font-semibold">Shop Logo</h2>
              <p className="text-sm text-gray-500">
                Upload a logo to display on invoices and PDFs. Recommended size: 200x200px.
              </p>
              
              <div className="flex items-center gap-6">
                {/* Logo Preview */}
                <div className="w-32 h-32 border-2 border-dashed border-gray-200 rounded-lg flex items-center justify-center bg-gray-50 overflow-hidden">
                  {logoPreview ? (
                    <img 
                      src={logoPreview} 
                      alt="Shop logo preview" 
                      className="w-full h-full object-contain"
                    />
                  ) : (
                    <div className="text-gray-400 text-center">
                      <ImageIcon className="h-8 w-8 mx-auto mb-1" />
                      <span className="text-xs">No logo</span>
                    </div>
                  )}
                </div>

                {/* Upload Buttons */}
                <div className="flex flex-col gap-2">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleLogoSelect}
                    className="hidden"
                  />
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={saving}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                    {shopSettings.logo ? 'Change Logo' : 'Upload Logo'}
                  </button>
                  
                  {shopSettings.logo && (
                    <button
                      onClick={handleRemoveLogo}
                      disabled={saving}
                      className="flex items-center gap-2 px-4 py-2 text-red-600 border border-red-200 rounded-lg hover:bg-red-50 disabled:opacity-50"
                    >
                      Remove Logo
                    </button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Shop Details */}
          <Card>
            <CardContent className="p-6 space-y-4">
              <h2 className="text-lg font-semibold">Shop Details</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Shop Name
                  </label>
                  <input
                    type="text"
                    value={shopSettings.name}
                    onChange={(e) => handleChange('name', e.target.value)}
                    className="w-full border border-gray-300 p-2 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Address
                  </label>
                  <textarea
                    value={shopSettings.address}
                    onChange={(e) => handleChange('address', e.target.value)}
                    rows={3}
                    className="w-full border border-gray-300 p-2 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter shop address"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Phone Number
                  </label>
                  <input
                    type="text"
                    value={shopSettings.phone}
                    onChange={(e) => handleChange('phone', e.target.value)}
                    className="w-full border border-gray-300 p-2 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter phone number"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Save Button */}
          <div className="flex justify-end">
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 disabled:opacity-50"
            >
              {saving && <Loader2 className="h-4 w-4 animate-spin" />}
              Save Settings
            </button>
          </div>
        </>
      )}
    </div>
  );
}
