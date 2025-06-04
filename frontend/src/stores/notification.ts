// frontend/src/stores/notification.ts
import { ref } from 'vue'
import { defineStore } from 'pinia'
import axiosInstance from '@/services/axiosInstance'
import type { User } from './auth' // Assuming User interface is exported from auth.ts

// Interface for the actor (user who performed the action)
// This should match your UserSerializer output
export interface NotificationActor extends User {
  // Extends User or define specific fields
  // id: number;
  // username: string;
  // profile_picture_url?: string; // If your UserSerializer includes this
}

// Interface for the Target or Action Object (from GenericRelatedObjectSerializer)
export interface NotificationRelatedObject {
  type: string // e.g., "statuspost", "comment", "like"
  id: number
  display_text: string // From obj.__str__()
  // url?: string; // Optional: If your backend serializer adds a direct link
}

// Interface for a single Notification
export interface Notification {
  id: number
  actor: NotificationActor
  verb: string // e.g., "liked", "commented on", "replied to"
  notification_type: string // e.g., "like", "comment", "reply" (from your model choices)
  target: NotificationRelatedObject | null
  action_object: NotificationRelatedObject | null
  timestamp: string // ISO date string
  is_read: boolean
}

// Interface for the paginated response when fetching notifications
export interface PaginatedNotificationResponse {
  count: number
  next: string | null
  previous: string | null
  results: Notification[]
}

// ... (interface definitions are above this) ...

export const useNotificationStore = defineStore('notification', () => {
  // --- State ---
  const notifications = ref<Notification[]>([])
  const unreadCount = ref<number>(0)

  const isLoadingList = ref<boolean>(false) // For fetching the list of notifications
  const isLoadingCount = ref<boolean>(false) // For fetching the unread count

  const error = ref<string | null>(null) // General error for any notification action

  // Pagination state for the list of notifications
  const pagination = ref({
    count: 0,
    next: null as string | null,
    previous: null as string | null,
    currentPage: 1,
    totalPages: 0, // Will calculate based on count and page size
    pageSize: 10, // If you want to store/control page size from here, otherwise API dictates
  })

  // --- Getters (Computed Properties) ---
  // Example: A simple getter for the unread count
  // const hasUnreadNotifications = computed(() => unreadCount.value > 0);

  // --- Actions (We will add these in the next steps) ---
  async function fetchUnreadCount() {
    // console.log("NotificationStore: Fetching unread count..."); // Optional: uncomment for debugging
    isLoadingCount.value = true // Set loading state for this specific action
    // error.value = null; // Optionally clear general error, or have specific error for this

    try {
      // No need to check authStore.isAuthenticated here, as API endpoint is protected.
      // If token is invalid/missing, API will return 401, and axiosInstance might handle it.
      const response = await axiosInstance.get<{ unread_count: number }>(
        '/notifications/unread-count/',
      )
      unreadCount.value = response.data.unread_count
      // console.log("NotificationStore: Unread count fetched:", unreadCount.value); // Optional
    } catch (err: any) {
      console.error('NotificationStore: Error fetching unread count:', err)
      // Don't set the main 'error.value' for this typically silent background check,
      // unless you want to display a global error if count fetching fails.
      // error.value = err.response?.data?.detail || err.message || 'Failed to fetch unread count.';
      unreadCount.value = 0 // Default to 0 on error to avoid showing stale count or NaN
    } finally {
      isLoadingCount.value = false
    }
  }

  async function fetchNotifications(page: number = 1) {
    console.log(`NotificationStore: Fetching notifications page ${page}...`)
    isLoadingList.value = true
    error.value = null // Clear previous list errors

    // If fetching the first page, clear existing notifications for a fresh list.
    // If implementing infinite scroll later, this logic would change.
    if (page === 1) {
      notifications.value = []
    }

    try {
      // API endpoint is protected, so auth is implicitly handled by axiosInstance interceptor
      const response = await axiosInstance.get<PaginatedNotificationResponse>('/notifications/', {
        params: { page: page },
      })

      const data = response.data
      console.log('NotificationStore: Notifications API response received:', data)

      if (page === 1) {
        notifications.value = data.results
      } else {
        // For simple pagination, replace. For infinite scroll, push.
        notifications.value = data.results
        // Or for infinite scroll: notifications.value.push(...data.results);
      }

      // Update pagination state
      pagination.value.count = data.count
      pagination.value.next = data.next
      pagination.value.previous = data.previous
      pagination.value.currentPage = page

      // Calculate total pages (assuming API doesn't provide it directly)
      // Use a default page_size if results are empty, otherwise derive from results length or a known page size
      const pageSize =
        data.results.length > 0 ? data.results.length : pagination.value.pageSize || 10 // Assuming default 10
      pagination.value.totalPages = Math.ceil(data.count / pageSize)
      if (pagination.value.totalPages === 0 && data.count > 0) pagination.value.totalPages = 1
    } catch (err: any) {
      console.error('NotificationStore: Error fetching notifications:', err)
      error.value = err.response?.data?.detail || err.message || 'Failed to fetch notifications.'
      // Optionally clear notifications array on error or leave stale data
      // notifications.value = [];
      // pagination.value = { count: 0, next: null, previous: null, currentPage: 1, totalPages: 0 };
    } finally {
      isLoadingList.value = false
      console.log('NotificationStore: Fetch notifications finished.')
    }
  }
  // ... (placeholders for markAsRead actions) ...

  async function markNotificationsAsRead(notificationIds: number[]) {
    if (!notificationIds || notificationIds.length === 0) {
      console.log('NotificationStore: No notification IDs provided to mark as read.')
      return { success: false, marked_count: 0 }
    }
    console.log(`NotificationStore: Attempting to mark notifications as read:`, notificationIds)
    // We don't need a specific isLoading for this, or we could add one like isLoadingMarkRead = ref(false)

    try {
      const response = await axiosInstance.post<{ detail: string }>( // Assuming backend returns { "detail": "X notification(s) marked as read."}
        '/notifications/mark-as-read/',
        { notification_ids: notificationIds }, // Send IDs in the request body
      )
      console.log('NotificationStore: Mark as read API response:', response.data.detail)

      // Update local state for the marked notifications
      let markedLocallyCount = 0
      notifications.value.forEach((notification) => {
        if (notificationIds.includes(notification.id) && !notification.is_read) {
          notification.is_read = true
          markedLocallyCount++
        }
      })

      // Re-fetch unread count to update the badge
      if (markedLocallyCount > 0) {
        await fetchUnreadCount() // Re-fetch the accurate count from backend
      }

      return { success: true, marked_count: markedLocallyCount } // Or use count from backend response if available
    } catch (err: any) {
      console.error('NotificationStore: Error marking notifications as read:', err)
      error.value =
        err.response?.data?.detail || err.message || 'Failed to mark notifications as read.'
      return { success: false, error: error.value }
    }
  }

  async function markAllNotificationsAsRead() {
  console.log("NotificationStore: Attempting to mark all notifications as read...");
  // We could set a specific loading state if this action might take time
  // or if there's specific UI feedback for it, e.g., isLoadingMarkAll = ref(false);
  // For now, we'll rely on the global isLoadingList or just proceed.

  try {
    const response = await axiosInstance.post<{ detail: string }>(
      '/notifications/mark-all-as-read/' 
      // No request body needed for this specific backend endpoint as it acts on all for the user
    ); 
    console.log("NotificationStore: Mark all as read API response:", response.data.detail);

    // If successful, update local state:
    // 1. Mark all currently loaded notifications in the 'notifications' array as read.
    notifications.value.forEach(notification => {
      if (!notification.is_read) {
        notification.is_read = true;
      }
    });
    
    // 2. Set unreadCount to 0.
    unreadCount.value = 0;
    
    // No need to re-fetch the list or unread count if we've updated locally,
    // unless the API response provides a more definitive state or new data.
    // The backend has already updated all its records.

    return { success: true, detail: response.data.detail };

  } catch (err: any) {
    console.error("NotificationStore: Error marking all notifications as read:", err);
    error.value = err.response?.data?.detail || err.message || 'Failed to mark all notifications as read.';
    return { success: false, error: error.value };
  } finally {
    // Reset any specific loading state for this action if you added one.
    // isLoadingMarkAll.value = false; 
  }
}

  // ... (placeholder for markAllNotificationsAsRead) ...

  // async function fetchNotifications(page: number = 1) { /* ... */ }
  // async function fetchUnreadCount() { /* ... */ }
  // async function markNotificationsAsRead(notificationIds: number[]) { /* ... */ }
  // async function markAllNotificationsAsRead() { /* ... */ }

  // --- Return state, getters, and actions ---
  return {
    notifications,
    unreadCount,
    isLoadingList,
    isLoadingCount,
    error,
    pagination,
    // Getters (when defined)
    // hasUnreadNotifications,
    // Actions (when defined)
    fetchNotifications,
    fetchUnreadCount,
    markNotificationsAsRead,
    markAllNotificationsAsRead
  }
})
