// src/stores/auth.ts

import { ref, computed } from 'vue';
import { defineStore } from 'pinia';
import axiosInstance from '@/services/axiosInstance';
import router from '@/router';

// Define the shape of the User object. This now matches what our API returns.
export interface User {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  date_joined: string;
  picture: string | null;
}

// Interface for registration data
interface RegistrationData {
  email?: string;
  username?: string;
  password1?: string;
  password2?: string;
}

// Define the store
export const useAuthStore = defineStore('auth', () => {
  // --- State ---
  const authToken = ref<string | null>(localStorage.getItem('authToken') || null);
  const currentUser = ref<User | null>(null);

  // --- Getters ---
  const isAuthenticated = computed(() => !!authToken.value);
  const userDisplay = computed(() => currentUser.value?.username || 'Guest');

  // --- Actions ---

  function setToken(token: string | null) {
    authToken.value = token;
    if (token) {
      localStorage.setItem('authToken', token);
      axiosInstance.defaults.headers.common['Authorization'] = `Token ${token}`;
    } else {
      localStorage.removeItem('authToken');
      delete axiosInstance.defaults.headers.common['Authorization'];
      // Also clear user data when logging out
      currentUser.value = null;
    }
  }

  // Simplified setUser function
  function setUser(user: User | null) {
    currentUser.value = user;
  }

  // Corrected login action
  async function login(credentials: { username: string; password: any }) {
    try {
      const response = await axiosInstance.post('/auth/login/', credentials);

      if (response.data && response.data.key) {
        // 1. Set the token from the login response
        setToken(response.data.key);

        // 2. IMMEDIATELY fetch the full user profile using the new token
        await fetchUserProfile();

        return true; // Indicate login success to the component
      } else {
        throw new Error("Login response did not contain an authentication key.");
      }
    } catch (error) {
      // Clear everything on failure
      setToken(null);
      setUser(null);
      console.error('Store login action failed:', error);
      throw error; // Re-throw for the component to handle
    }
  }

  // Logout action
  async function logout() {
    try {
      await axiosInstance.post('/auth/logout/');
    } catch (error: any) {
      console.error('Backend logout call failed (proceeding with client logout):', error);
    } finally {
      // Ensure this always runs
      setToken(null);
      router.push('/login');
    }
  }

  // Action to fetch user profile
  async function fetchUserProfile() {
    if (!authToken.value) {
      return;
    }
    try {
      const response = await axiosInstance.get<User>('/auth/user/');
      if (response.data) {
        setUser(response.data);
      } else {
        setUser(null);
      }
    } catch (error: any) {
      console.error('Failed to fetch user profile:', error);
      if (error.response && error.response.status === 401) {
        // Automatically log out if token is bad
        logout();
      } else {
        setUser(null);
      }
    }
  }

  // Registration action
  async function register(registrationData: RegistrationData) {
    try {
      await axiosInstance.post('/auth/registration/', registrationData);
    } catch (error) {
      console.error("Backend registration failed!", error);
      throw error; // Re-throw for the component to handle
    }
  }

  // Initialization action
  async function initializeAuth() {
    const tokenFromStorage = localStorage.getItem('authToken');

    if (tokenFromStorage && !authToken.value) {
      setToken(tokenFromStorage);
    }

    if (authToken.value && !currentUser.value) {
      await fetchUserProfile();
    }
  }

  // --- Return state, getters, and actions ---
  return {
    authToken,
    currentUser,
    isAuthenticated,
    userDisplay,
    setToken,
    setUser,
    login,
    logout,
    fetchUserProfile,
    register,
    initializeAuth,
  };
});