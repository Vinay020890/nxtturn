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
  password?: string; // Corrected from password1
  password2?: string;
}

// Define the store
export const useAuthStore = defineStore('auth', () => {
  // --- State ---
  const authToken = ref<string | null>(localStorage.getItem('authToken') || null);
  const currentUser = ref<User | null>(null);
  const isLoading = ref<boolean>(false); // <-- 1. ADD isLoading STATE

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
      currentUser.value = null;
    }
  }

  function setUser(user: User | null) {
    currentUser.value = user;
  }

  // Corrected login action with loading state
  async function login(credentials: { username: string; password: any }) {
    isLoading.value = true; // <-- 2a. SET isLoading to true
    try {
      const response = await axiosInstance.post('/auth/login/', credentials);
      if (response.data && response.data.key) {
        setToken(response.data.key);
        await fetchUserProfile();
        return true;
      } else {
        throw new Error("Login response did not contain an authentication key.");
      }
    } catch (error) {
      setToken(null);
      setUser(null);
      console.error('Store login action failed:', error);
      throw error;
    } finally {
      isLoading.value = false; // <-- 2b. ALWAYS set isLoading to false
    }
  }

  async function logout() {
    try {
      await axiosInstance.post('/auth/logout/');
    } catch (error: any) {
      console.error('Backend logout call failed (proceeding with client logout):', error);
    } finally {
      setToken(null);
      router.push('/login');
    }
  }

  async function fetchUserProfile() {
    if (!authToken.value) return;
    try {
      const response = await axiosInstance.get<User>('/auth/user/');
      if (response.data) setUser(response.data);
      else setUser(null);
    } catch (error: any) {
      console.error('Failed to fetch user profile:', error);
      if (error.response && error.response.status === 401) logout();
      else setUser(null);
    }
  }

  async function register(registrationData: RegistrationData) {
      // You can add loading state here too if you want
      isLoading.value = true;
      try {
        await axiosInstance.post('/auth/registration/', registrationData);
      } catch (error) {
        console.error("Backend registration failed!", error);
        throw error;
      } finally {
      isLoading.value = false;
      }
  }

  async function initializeAuth() {
    const tokenFromStorage = localStorage.getItem('authToken');
    if (tokenFromStorage && !authToken.value) setToken(tokenFromStorage);
    if (authToken.value && !currentUser.value) await fetchUserProfile();
  }

  // --- Return state, getters, and actions ---
  return {
    authToken,
    currentUser,
    isAuthenticated,
    userDisplay,
    isLoading, // <-- 3. RETURN isLoading
    setToken,
    setUser,
    login,
    logout,
    fetchUserProfile,
    register,
    initializeAuth,
  };
});