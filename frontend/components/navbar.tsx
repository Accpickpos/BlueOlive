"use client";
import { Bell, User, LogOut, Home, Shield } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { isAuthenticated, logout } from "@/lib/api";
import { useAuthContext } from "@/lib/AuthContext";
import ShopSelector from "@/components/ShopSelector";

export default function Navbar() {
  const router = useRouter();
  const { user, isAdmin, isLoading, refetch } = useAuthContext();
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    // Sync local state with context
    setIsLoggedIn(user !== null);
  }, [user]);

  const handleLogout = async () => {
    try {
      // First, call logout on the backend to clear cookies
      await logout();
    } catch (error) {
      console.error('Logout API call failed:', error);
      // Continue anyway - cookies might be cleared even if request fails
    }
    
    try {
      // Then refetch to update auth context (should get 401)
      await refetch();
    } catch (error) {
      console.error('Refetch failed:', error);
      // Force clear the user state
      setIsLoggedIn(false);
    }
    
    // Redirect to home page
    router.push('/');
  };

  return (
    <header className="h-16 bg-white border-b flex items-center justify-between px-6 shadow-sm">
      <div className="flex items-center gap-4">
        <Link href="/" className="flex items-center gap-2 text-indigo-600 hover:text-indigo-800">
          <Home className="h-5 w-5" />
          <span className="font-semibold">BlueOlive</span>
        </Link>
        {isLoggedIn && (
          <nav className="flex gap-4 ml-8">
            <Link href="/dashboard" className="text-gray-700 hover:text-indigo-600 text-sm">
              Dashboard
            </Link>
            {isAdmin && (
              <Link href="/dashboard/admin" className="text-indigo-600 hover:text-indigo-800 text-sm font-semibold flex items-center gap-1">
                <Shield className="h-4 w-4" />
                Admin
              </Link>
            )}
          </nav>
        )}
        {!isLoggedIn && !isLoading && (
          <nav className="flex gap-4 ml-8">
            <Link href="/auth" className="text-gray-700 hover:text-indigo-600">Login</Link>
            <Link href="/create-tenant" className="text-gray-700 hover:text-indigo-600">Create Tenant</Link>
          </nav>
        )}
      </div>
      <div className="flex items-center gap-4">
        {isLoggedIn && (
          <>
            {/* Shop Selector - only shows if user has access to multiple shops */}
            <ShopSelector />
            
            <span className="text-sm text-gray-600">{user && user.username}</span>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-3 py-1 text-sm text-gray-700 hover:text-red-600"
            >
              <LogOut className="h-4 w-4" />
              Logout
            </button>
          </>
        )}
        {!isLoggedIn && (
          <>
            <Bell className="h-5 w-5 cursor-pointer text-gray-500" />
            <User className="h-6 w-6 cursor-pointer text-gray-500" />
          </>
        )}
      </div>
    </header>
  );
}