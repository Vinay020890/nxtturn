// src/services/axiosInstance.ts

import axios from 'axios';

// Base URL for your Django backend API
const API_BASE_URL = 'http://192.168.31.35:8000/api/'; // Your desktop's IP and Django port

// Create a custom Axios instance
const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 55000, // Optional: 5 second timeout
  headers: {
    // 'Content-Type': 'application/json',
    'Accept': 'application/json',
  }
});

// --- ADD REQUEST INTERCEPTOR ---
axiosInstance.interceptors.request.use(
    (config) => {
      // Get token directly from localStorage (simplest way inside interceptor)
      // The authStore keeps localStorage in sync anyway via setToken action
      const token = localStorage.getItem('authToken');
  
      if (token) {
        // If token exists, add the Authorization header to the request config
        config.headers.Authorization = `Token ${token}`;
        console.log('Interceptor: Added auth token to header'); // For debugging
      } else {
        // Optional: Delete header if no token found (might already be absent)
        delete config.headers.Authorization;
         console.log('Interceptor: No token found, Authorization header absent/removed'); // For debugging
      }
      return config; // Return the modified config for the request to proceed
    },
    (error) => {
      // Handle request errors (e.g., network issue before sending)
      console.error('Axios request interceptor error:', error);
      return Promise.reject(error); // Reject the promise to signal an error
    }
  );

// NOTE: We will add interceptors here later for handling
// auth tokens and potentially errors like 401 Unauthorized.

// Export the configured instance
export default axiosInstance;