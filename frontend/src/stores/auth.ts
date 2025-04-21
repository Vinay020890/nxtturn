// src/stores/auth.ts

import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import axiosInstance from '@/services/axiosInstance';
// Later: import router from '@/router'; // For potential redirects

// Define the shape of the User object we might store (adjust as needed)
interface User {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  // Add other relevant fields from your UserSerializer if login returns them
  // email?: string;
}

// Define the store
// 'auth' is the unique ID of this store
export const useAuthStore = defineStore('auth', () => {
  // --- State ---
  // Use refs for reactive state properties.
  // Initialize token from localStorage (if available) for persistence across refreshes.
  const authToken = ref<string | null>(localStorage.getItem('authToken') || null);
  const currentUser = ref<User | null>(null); // Initialize user as null
  // TODO: Add loading/error states if needed

  // --- Getters ---
  // Computed properties derived from state.
  const isAuthenticated = computed(() => !!authToken.value); // True if token exists
  const userDisplay = computed(() => currentUser.value?.username || 'Guest');

  // --- Actions ---
  // Functions that can modify the state. Often asynchronous for API calls.

  function setToken(token: string | null) {
    authToken.value = token;
    if (token) {
      localStorage.setItem('authToken', token);
      // TODO: Set token in axios headers for subsequent requests (via interceptor is best)
    } else {
      localStorage.removeItem('authToken');
      // TODO: Remove token from axios headers
      // Also clear user data when logging out
      currentUser.value = null;
    }
  }

  function setUser(user: User | null) {
    currentUser.value = user;
    // TODO: Potentially store user info in localStorage too, if needed,
    // but be mindful of sensitive data. Often re-fetched on refresh.
  }

  // Action to perform login API call
        // Replace the OLD login function with THIS one
        async function login(credentials: { username: string, password: any }) {
            // Clear previous user state first
            setToken(null);
            setUser(null);
            try {
              console.log('Attempting login via store action:', credentials.username);
    
              // --- REPLACE MOCK WITH REAL API CALL ---
              // Make the actual POST request to the backend login endpoint
              const response = await axiosInstance.post('/auth/login/', credentials);
              // --- END OF API CALL ---
    
              // Check if the response contains the authentication key
              if (response.data && response.data.key) {
                // If yes, store the token
                setToken(response.data.key);
                console.log('Token set from API response:', response.data.key);
    
                // NOTE: dj-rest-auth login usually doesn't return full user details.
                // We might need a separate call to get user info later.
                if (response.data.user) {
                   // If user data IS returned (less common), set it
                   setUser(response.data.user);
                   console.log('User set from login response:', response.data.user);
                } else {
                   console.log('Login successful. Token obtained. User details may need separate fetch.');
                }
                return true; // Indicate login success to the component
    
              } else {
                 // Handle unexpected response format from the API
                 console.error("Login response missing 'key':", response.data);
                 throw new Error("Login response did not contain authentication key.");
              }
    
            } catch (error) {
              // Handle errors from the Axios request (network error, 4xx/5xx status)
              console.error('Store login action failed:', error);
              setToken(null); // Ensure token/user are cleared on failure
              setUser(null);
              // Re-throw the error so the component (LoginView) can catch it
              // and display an appropriate message to the user.
              throw error;
            }
          }

  // Action to perform logout
  function logout() {
    console.log('Logging out via store action');
    setToken(null);
    // TODO: Call backend logout endpoint if necessary (e.g., /api/auth/logout/)
    // Redirect to login page (best handled in component or router guard)
    // router.push('/login');
  }

  // Action to fetch user profile (if not included in login response)
  async function fetchUserProfile() {
      if (!isAuthenticated.value) return; // Don't fetch if not logged in
      try {
          console.log('Fetching user profile...');
          // --- TODO: Call API ---
          // const response = await axiosInstance.get('/auth/user/'); // DRF default user endpoint
          // setUser(response.data);
          console.log('User profile fetched (mocked)');
      } catch (error) {
          console.error('Failed to fetch user profile:', error);
          // Handle error, maybe log out if token is invalid (401 error)
          // if (error.response && error.response.status === 401) {
          //   logout();
          // }
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
    fetchUserProfile
  }
})