import axios from 'axios';
import { useAuthStore } from '@/stores/auth'; // Import the Pinia store

const axiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 155000,
  headers: {
    'Accept': 'application/json',
  }
});

// --- REQUEST INTERCEPTOR (Corrected) ---
axiosInstance.interceptors.request.use(
    (config) => {
      const authStore = useAuthStore();
      // --- THE FIX ---
      // Use 'authToken' to match the property name in your auth.ts store
      const token = authStore.authToken;
  
      if (token) {
        config.headers.Authorization = `Token ${token}`;
        console.log('Interceptor: Added auth token to header');
      } else {
        delete config.headers.Authorization;
      }
      return config;
    },
    (error) => {
      console.error('Axios request interceptor error:', error);
      return Promise.reject(error);
    }
);

// --- BEST PRACTICE: Add a RESPONSE INTERCEPTOR for global 401 handling ---
axiosInstance.interceptors.response.use(
  (response) => response, // Simply return successful responses
  (error) => {
    if (error.response && error.response.status === 401) {
      const authStore = useAuthStore();
      // --- THE FIX ---
      // Also check against 'authToken' here for consistency
      if (authStore.authToken) {
        console.error("API returned 401. Token may be invalid or expired. Logging out.");
        authStore.logout();
      }
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;