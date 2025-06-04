<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useNotificationStore } from '@/stores/notification';
import { formatDistanceToNowStrict } from 'date-fns'; // For relative timestamps

const notificationStore = useNotificationStore();

const isMarkingAllRead = ref(false); // Loading state for "Mark all as read" button

const loadNotifications = (page: number) => {
  if (notificationStore.isLoadingList && page !== 1) return; // Prevent multiple calls if already loading, unless it's initial load
  
  // Basic bounds check for page number
  // Allow page 1 even if totalPages is 0 (for initial fetch)
  if (page < 1 || (page > notificationStore.pagination.totalPages && notificationStore.pagination.totalPages > 0 && page !==1 )) {
    console.warn(`NotificationsPage: Attempted to load invalid page: ${page}. Current total: ${notificationStore.pagination.totalPages}`);
    return;
  }
  notificationStore.fetchNotifications(page);
};

const markOneAsRead = async (notificationId: number) => {
  console.log(`NotificationsPage: Marking notification ID ${notificationId} as read.`);
  
  const notification = notificationStore.notifications.find(n => n.id === notificationId);
  if (notification && notification.is_read) {
    console.log(`NotificationsPage: Notification ID ${notificationId} is already marked as read.`);
    return; 
  }

  const result = await notificationStore.markNotificationsAsRead([notificationId]);

  if (result.success) {
    console.log(`NotificationsPage: Notification ID ${notificationId} successfully marked as read.`);
  } else {
    console.error(`NotificationsPage: Failed to mark notification ID ${notificationId} as read. Error:`, result.error);
    alert(result.error || "Failed to mark notification as read.");
  }
};

async function handleMarkAllAsRead() {
  if (isMarkingAllRead.value) return;

  console.log("NotificationsPage: Attempting to mark all notifications as read.");
  isMarkingAllRead.value = true;
  
  const result = await notificationStore.markAllNotificationsAsRead();

  if (result.success) {
    console.log("NotificationsPage: All notifications successfully marked as read.");
  } else {
    console.error("NotificationsPage: Failed to mark all notifications as read. Error:", result.error);
    alert(result.error || "Failed to mark all notifications as read. Please try again.");
  }
  isMarkingAllRead.value = false;
}

onMounted(() => {
  console.log("NotificationsPage.vue: Mounted. Fetching initial notifications.");
  loadNotifications(1); 
});
</script>

<template>
  <div class="notifications-page">
    <h2>Your Notifications</h2>

    <div class="notifications-actions" v-if="notificationStore.unreadCount > 0 && notificationStore.notifications.length > 0">
      <button @click="handleMarkAllAsRead" :disabled="isMarkingAllRead" class="mark-all-read-button">
        {{ isMarkingAllRead ? 'Marking all...' : 'Mark all as read' }}
      </button>
    </div>

    <div v-if="notificationStore.isLoadingList && notificationStore.notifications.length === 0" class="loading-message"> 
      Loading notifications...
    </div>

    <div v-if="notificationStore.error && !notificationStore.isLoadingList" class="error-message">
      <p>Error loading notifications: {{ notificationStore.error }}</p>
      <button @click="loadNotifications(1)">Try Again</button>
    </div>

    <div v-if="!notificationStore.isLoadingList && !notificationStore.error && notificationStore.notifications.length === 0" class="empty-message">
      You have no notifications yet.
    </div>

    <ul v-if="notificationStore.notifications.length > 0" class="notification-list">
      <li v-for="notification in notificationStore.notifications" :key="notification.id" 
          :class="['notification-item', { 'is-read': notification.is_read }]">
        <div class="notification-actor">
          <strong>{{ notification.actor.username }}</strong> {{ notification.verb }}
        </div>
        <div v-if="notification.target" class="notification-target">
          on your {{ notification.target.type }}: <em>{{ notification.target.display_text }}</em>
        </div>
        <div v-if="notification.action_object && notification.action_object.id !== notification.target?.id" class="notification-action-object">
          (Details: {{ notification.action_object.display_text }})
        </div>
        <div class="notification-timestamp">
          {{ formatDistanceToNowStrict(new Date(notification.timestamp), { addSuffix: true }) }}
        </div>
        <button v-if="!notification.is_read" @click="markOneAsRead(notification.id)" class="mark-read-button">
          Mark as Read
        </button>
      </li>
    </ul>

    <div v-if="!notificationStore.isLoadingList && notificationStore.pagination.totalPages > 1" class="pagination-controls">
      <button @click="loadNotifications(notificationStore.pagination.currentPage - 1)" :disabled="!notificationStore.pagination.previous || notificationStore.isLoadingList">
        Previous
      </button>
      <span>Page {{ notificationStore.pagination.currentPage }} of {{ notificationStore.pagination.totalPages }}</span>
      <button @click="loadNotifications(notificationStore.pagination.currentPage + 1)" :disabled="!notificationStore.pagination.next || notificationStore.isLoadingList">
        Next
      </button>
    </div>
  </div>
</template>

<style scoped>
.notifications-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 1rem;
}

.notifications-actions {
  margin-bottom: 1rem;
  text-align: right;
}

.mark-all-read-button {
  padding: 0.4rem 0.8rem;
  font-size: 0.9em;
  background-color: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.mark-all-read-button:hover {
  background-color: #5a6268;
}
.mark-all-read-button:disabled {
  background-color: #adb5bd;
  cursor: not-allowed;
}

.loading-message, 
.empty-message {
  padding: 1rem;
  text-align: center;
  color: #555;
}

.error-message {
  padding: 1rem;
  text-align: center;
  color: #dc3545;
  border: 1px solid #f5c6cb;
  background-color: #f8d7da;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.notification-list {
  list-style-type: none;
  padding: 0;
  margin: 0;
}

.notification-item {
  border: 1px solid #e0e0e0;
  padding: 0.75rem 1rem;
  margin-bottom: 0.75rem;
  border-radius: 6px;
  background-color: #ffffff;
  color: #212529;
  line-height: 1.5;
}

.notification-item.is-read {
  background-color: #f8f9fa;
  color: #6c757d;
}

.notification-actor strong {
  font-weight: bold;
  color: #0056b3;
}
.notification-item.is-read .notification-actor strong {
  color: #495057;
}

.notification-target, 
.notification-action-object {
  font-size: 0.9em;
  margin-left: 0.5em;
  color: #495057;
}
.notification-item.is-read .notification-target,
.notification-item.is-read .notification-action-object {
  color: #868e96;
}

.notification-timestamp {
  font-size: 0.8em;
  color: #6c757d;
  margin-top: 0.25rem;
  display: block;
}
.notification-item.is-read .notification-timestamp {
  color: #adb5bd;
}

.mark-read-button {
  align-self: flex-start;
  margin-top: 0.75rem;
  padding: 0.3rem 0.6rem;
  font-size: 0.85em;
  cursor: pointer;
  background-color: #e9ecef;
  border: 1px solid #ced4da;
  color: #212529;
  border-radius: 4px;
}
.mark-read-button:hover {
  background-color: #dee2e6;
}

.pagination-controls {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #eee;
  text-align: center;
}
.pagination-controls button {
  margin: 0 0.5rem;
  padding: 0.5rem 1rem;
  cursor: pointer;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
}
.pagination-controls button:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}
.pagination-controls button:not(:disabled):hover {
  background-color: #0056b3;
}
.pagination-controls span {
    margin: 0 0.5rem;
    color: #495057;
}
</style>