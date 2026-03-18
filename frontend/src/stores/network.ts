import { defineStore } from 'pinia'
import { ref } from 'vue'
import axiosInstance from '@/services/axiosInstance'
import type { NetworkUser, DiscoveryResponse } from '@/types'

export const useNetworkStore = defineStore('network', () => {
  // --- STATE ---
  const followers = ref<NetworkUser[]>([])
  const following = ref<NetworkUser[]>([])
  const connections = ref<NetworkUser[]>([])
  const discoverResults = ref<DiscoveryResponse | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // --- ACTIONS ---

  // --- ACTIONS (Corrected Paths) ---

  async function fetchFollowers() {
    isLoading.value = true
    error.value = null
    try {
      // Corrected: Removed /api/community prefix
      const response = await axiosInstance.get('/network/followers/')
      followers.value = response.data.results
    } catch (err: any) {
      error.value = 'Failed to load followers'
      console.error(err)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchFollowing() {
    isLoading.value = true
    error.value = null
    try {
      // Corrected: Removed /api/community prefix
      const response = await axiosInstance.get('/network/following/')
      following.value = response.data.results
    } catch (err: any) {
      error.value = 'Failed to load following list'
      console.error(err)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchConnections() {
    isLoading.value = true
    error.value = null
    try {
      // Corrected: Removed /api/community prefix
      const response = await axiosInstance.get('/network/connections/')
      connections.value = response.data.results
    } catch (err: any) {
      error.value = 'Failed to load connections'
      console.error(err)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchDiscover() {
    isLoading.value = true
    error.value = null
    try {
      const response = await axiosInstance.get<DiscoveryResponse>('/network/discover/')
      discoverResults.value = response.data
    } catch (err: any) {
      error.value = 'Failed to load recommendations'
      console.error(err)
    } finally {
      isLoading.value = false
    }
  }

  /**

    Resets the store's state, called on logout.
    */
  function reset() {
    followers.value = []
    following.value = []
    connections.value = []
    discoverResults.value = null
    error.value = null
    isLoading.value = false
  }

  return {
    // State
    followers,
    following,
    connections,
    discoverResults,
    isLoading,
    error,
    // Actions
    fetchFollowers,
    fetchFollowing,
    fetchConnections,
    fetchDiscover,
    reset,
  }
})
