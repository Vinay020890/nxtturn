// C:\Users\Vinay\Project\frontend\src\stores\auth.ts

import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import axiosInstance from '@/services/axiosInstance'
import { useFeedStore } from './feed'
import { useProfileStore } from './profile'

// Define the shape of the User object. This now matches what our API returns.
export interface User {
  id: number
  username: string
  first_name: string
  last_name: string
  date_joined: string
  picture: string | null
}

// Interface for registration data
interface RegistrationData {
  email?: string
  username?: string
  password1?: string
  password2?: string
}

// Define the store
export const useAuthStore = defineStore('auth', () => {
  // --- State ---
  const authToken = ref<string | null>(localStorage.getItem('authToken') || null)
  const currentUser = ref<User | null>(null)
  const isLoading = ref<boolean>(false)

  // --- Getters ---
  const isAuthenticated = computed(() => !!authToken.value)
  const userDisplay = computed(() => currentUser.value?.username || 'Guest')

  // --- Actions ---

  function setToken(token: string | null) {
    authToken.value = token
    if (token) {
      localStorage.setItem('authToken', token)
      axiosInstance.defaults.headers.common['Authorization'] = `Token ${token}`
    } else {
      localStorage.removeItem('authToken')
      delete axiosInstance.defaults.headers.common['Authorization']
      currentUser.value = null
    }
  }

  function setUser(user: User | null) {
    currentUser.value = user
  }

  function updateCurrentUserPicture(newPictureUrl: string) {
    if (currentUser.value) {
      currentUser.value.picture = newPictureUrl
    }
  }

  async function login(credentials: { username: string; password: any }) {
    isLoading.value = true
    try {
      const response = await axiosInstance.post('/auth/login/', credentials)
      if (response.data && response.data.key) {
        setToken(response.data.key)
        await fetchUserProfile()
        return true
      } else {
        throw new Error('Login response did not contain an authentication key.')
      }
    } catch (error) {
      setToken(null)
      setUser(null)
      console.error('Store login action failed:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  // in auth.ts
  async function logout() {
    try {
      await axiosInstance.post('/auth/logout/')
    } catch (error: any) {
      console.error('Backend logout call failed (proceeding with client logout):', error)
    } finally {
      setToken(null)

      // --- THIS IS THE FIX ---
      // We check if 'window' is defined before trying to use it.
      // In a normal browser, this is always true.
      // In the Cypress Node.js environment, this is false, and the line is safely skipped.
      if (typeof window !== 'undefined') {
        window.location.href = '/login'
      }
      // --- END OF FIX ---
    }
  }

  async function fetchUserProfile() {
    if (!authToken.value) return
    try {
      const response = await axiosInstance.get<User>('/auth/user/')
      if (response.data) setUser(response.data)
      else setUser(null)
    } catch (error: any) {
      console.error('Failed to fetch user profile:', error)
      if (error.response && error.response.status === 401) await logout()
      else setUser(null)
    }
  }

  async function register(registrationData: RegistrationData) {
    isLoading.value = true
    try {
      await axiosInstance.post('/auth/registration/', registrationData)
    } catch (error) {
      console.error('Backend registration failed!', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function initializeAuth() {
    const tokenFromStorage = localStorage.getItem('authToken')
    if (tokenFromStorage && !authToken.value) setToken(tokenFromStorage)
    if (authToken.value && !currentUser.value) await fetchUserProfile()
  }

  // --- THIS IS THE NEW FUNCTION FOR MULTI-TAB SYNC ---
  /**
   * Silently resets the client-side auth state.
   * This is called by the 'storage' event listener in App.vue when another
   * tab logs out. It does NOT make an API call.
   */
  function resetAuthState() {
    authToken.value = null
    currentUser.value = null
    console.log('Client-side auth state has been reset by multi-tab sync.')
  }
  // --- END OF NEW FUNCTION ---

  // --- Return state, getters, and actions ---
  return {
    authToken,
    currentUser,
    isAuthenticated,
    userDisplay,
    isLoading,
    setToken,
    setUser,
    login,
    logout,
    fetchUserProfile,
    register,
    initializeAuth,
    updateCurrentUserPicture,
    resetAuthState, // <-- Make sure to return the new function here!
  }
})
