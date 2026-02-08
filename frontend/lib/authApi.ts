/**
 * Authentication API Client
 * 
 * Handles all authentication endpoints:
 * - CSRF token management
 * - User registration and login
 * - Token refresh
 * - Logout
 * - Profile management
 * 
 * Base URL: /api/v1/users/auth/
 */

import { api } from './api';
import { ENDPOINTS } from './api-config';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface SignupData {
  email: string;
  password: string;
  password_confirm: string;
  first_name?: string;
  last_name?: string;
}

export interface UserProfile {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token?: string;
  refresh_token?: string;
  user?: UserProfile;
}

export interface TokenRefreshResponse {
  access_token: string;
}

export const authApi = {
  /**
   * Get CSRF token for form submissions
   */
  getCSRFToken: async (): Promise<{ csrfToken: string }> => {
    const response = await api.get(ENDPOINTS.AUTH.CSRF);
    return response.data;
  },

  /**
   * Register new user
   */
  signup: async (data: SignupData): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>(ENDPOINTS.AUTH.SIGNUP, data);
    return response.data;
  },

  /**
   * Login with email and password
   */
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>(ENDPOINTS.AUTH.LOGIN, credentials);
    return response.data;
  },

  /**
   * Unified login endpoint (supports multiple auth methods)
   */
  unifiedLogin: async (data: any): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>(ENDPOINTS.AUTH.UNIFIED_LOGIN, data);
    return response.data;
  },

  /**
   * Logout user
   */
  logout: async (): Promise<void> => {
    await api.post(ENDPOINTS.AUTH.LOGOUT);
  },

  /**
   * Refresh access token using refresh token
   */
  refreshToken: async (): Promise<TokenRefreshResponse> => {
    const response = await api.post<TokenRefreshResponse>(ENDPOINTS.AUTH.TOKEN_REFRESH);
    return response.data;
  },

  /**
   * Get current user profile
   */
  getProfile: async (): Promise<UserProfile> => {
    const response = await api.get<UserProfile>(ENDPOINTS.AUTH.PROFILE);
    return response.data;
  },

  /**
   * Update current user profile
   */
  updateProfile: async (data: Partial<UserProfile>): Promise<UserProfile> => {
    const response = await api.patch<UserProfile>(ENDPOINTS.AUTH.PROFILE, data);
    return response.data;
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated: async (): Promise<boolean> => {
    try {
      await authApi.getProfile();
      return true;
    } catch {
      return false;
    }
  },
};

export default authApi;
