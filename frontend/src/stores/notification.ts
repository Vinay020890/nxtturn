// C:\Users\Vinay\Project\frontend\src\stores\notification.ts
// --- FINAL CORRECTED VERSION ---

import { ref } from 'vue'
import { defineStore } from 'pinia'
import axiosInstance from '@/services/axiosInstance'
import { useToast } from 'vue-toastification'
import type { User } from './auth'

// Your interfaces remain unchanged
export interface NotificationActor extends User {}
export interface NotificationRelatedObject {
  type: string
  id: number
  display_text: string
  object_id?: number
  slug?: string;
}
export interface Notification {
  id: number
  actor: NotificationActor
  verb: string
  notification_type: string
  target: NotificationRelatedObject | null
  action_object: NotificationRelatedObject | null
  timestamp: string
  is_read: boolean
  context_snippet: string | null 
}
export interface PaginatedNotificationResponse {
  count: number
  next: string | null
  previous: string | null
  results: Notification[]
}

export const useNotificationStore = defineStore('notification', () => {
  const toast = useToast()

  const notifications = ref<Notification[]>([])
  const unreadCount = ref<number>(0)
  const isLoadingList = ref<boolean>(false)
  const isLoadingCount = ref<boolean>(false)
  const error = ref<string | null>(null)
  const pagination = ref({
    count: 0,
    next: null as string | null,
    previous: null as string | null,
    currentPage: 1,
    totalPages: 0,
    pageSize: 10,
  })
  const ITEMS_PER_PAGE_NOTIFICATIONS = 10

  // --- 1. NEW STATE PROPERTY ADDED ---
  // This flag is the key to solving the race condition.
  const hasLoadedInitialList = ref<boolean>(false)

  async function fetchUnreadCount() {
    // ... (This function is unchanged)
    isLoadingCount.value = true
    try {
      const response = await axiosInstance.get<{ unread_count: number }>(
        '/notifications/unread-count/',
      )
      unreadCount.value = response.data.unread_count
    } catch (err: any) {
      console.error('NotificationStore: Error fetching unread count:', err)
      unreadCount.value = 0
    } finally {
      isLoadingCount.value = false
    }
  }

  async function fetchNotifications(page: number = 1) {
    // ... (This function is unchanged, except for one line)
    isLoadingList.value = true
    error.value = null
    if (page === 1) {
      notifications.value = []
    }
    try {
      const response = await axiosInstance.get<PaginatedNotificationResponse>('/notifications/', {
        params: { page: page },
      })
      const data = response.data
      if (page === 1) {
        notifications.value = data.results
      } else {
        notifications.value.push(...data.results)
      }
      pagination.value.count = data.count
      pagination.value.next = data.next
      pagination.value.previous = data.previous
      pagination.value.currentPage = page
      pagination.value.totalPages =
        data.count > 0 ? Math.ceil(data.count / ITEMS_PER_PAGE_NOTIFICATIONS) : 0
        
      // --- 2. NEW LINE ADDED ON SUCCESS ---
      // If we successfully fetched any page, we mark the initial load as complete.
      hasLoadedInitialList.value = true

    } catch (err: any) {
      console.error('NotificationStore: Error fetching notifications:', err)
      error.value = err.response?.data?.detail || err.message || 'Failed to fetch notifications.'
    } finally {
      isLoadingList.value = false
    }
  }

  // ... (markNotificationsAsRead and markAllAsRead are unchanged)
  async function markNotificationsAsRead(notificationIds: number[]) {
    if (!notificationIds || notificationIds.length === 0) return { success: false }
    try {
      await axiosInstance.post('/notifications/mark-as-read/', {
        notification_ids: notificationIds,
      })
      notifications.value.forEach((n) => {
        if (notificationIds.includes(n.id) && !n.is_read) {
          n.is_read = true
        }
      })
      await fetchUnreadCount()
      return { success: true }
    } catch (err: any) {
      console.error('NotificationStore: Error marking notifications as read:', err)
      error.value = err.response?.data?.detail || 'Failed to mark notifications as read.'
      return { success: false, error: error.value }
    }
  }
  async function markAllAsRead() {
    try {
      await axiosInstance.post('/notifications/mark-all-as-read/')
      notifications.value.forEach((notification) => {
        notification.is_read = true
      })
      unreadCount.value = 0
      return { success: true }
    } catch (err: any) {
      console.error('NotificationStore: Error marking all notifications as read:', err)
      error.value = err.response?.data?.detail || 'Failed to mark all notifications as read.'
      return { success: false, error: error.value }
    }
  }

  // ... (addLiveNotification is unchanged)
  function addLiveNotification(newNotification: Notification) {
    notifications.value.unshift(newNotification)
    unreadCount.value++
    toast.info(`${newNotification.actor.username} ${newNotification.verb}`)
  }

  function resetState() {
    // ... (This function is unchanged, except for one line)
    notifications.value = []
    unreadCount.value = 0
    isLoadingList.value = false
    isLoadingCount.value = false
    error.value = null
    pagination.value = {
      count: 0,
      next: null,
      previous: null,
      currentPage: 1,
      totalPages: 0,
      pageSize: 10,
    }
    // --- 3. NEW LINE ADDED TO RESET ---
    // Ensure the flag is reset on logout.
    hasLoadedInitialList.value = false
  }

  return {
    notifications,
    unreadCount,
    isLoadingList,
    isLoadingCount,
    error,
    pagination,
    // --- 4. EXPOSE THE NEW PROPERTY ---
    hasLoadedInitialList,
    fetchNotifications,
    fetchUnreadCount,
    markNotificationsAsRead,
    markAllAsRead,
    addLiveNotification,
    resetState,
  }
})