<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useNotificationStore } from '@/stores/notification';
import { formatDistanceToNowStrict } from 'date-fns';

const notificationStore = useNotificationStore();
const isMarkingAllRead = ref(false);

const loadNotifications = (page: number) => {
  if (notificationStore.isLoadingList && page !== 1) return;
  if (page < 1 || (page > notificationStore.pagination.totalPages && notificationStore.pagination.totalPages > 0 && page !== 1)) return;
  notificationStore.fetchNotifications(page);
};

const markOneAsRead = async (notificationId: number) => {
  const notification = notificationStore.notifications.find(n => n.id === notificationId);
  if (notification && notification.is_read) return;
  await notificationStore.markNotificationsAsRead([notificationId]);
};

async function handleMarkAllAsRead() {
  if (isMarkingAllRead.value) return;
  isMarkingAllRead.value = true;
  await notificationStore.markAllNotificationsAsRead();
  isMarkingAllRead.value = false;
}

onMounted(() => {
  loadNotifications(1);
});
</script>

<template>
  <!-- This root div now controls its own layout -->
  <div class="container mx-auto max-w-3xl">
    <div class="bg-white rounded-lg shadow-md p-4 sm:p-6">
      <div class="flex justify-between items-center border-b border-gray-200 pb-4 mb-4">
        <h1 class="text-2xl font-bold text-gray-800">Your Notifications</h1>
        <button 
          v-if="notificationStore.unreadCount > 0"
          @click="handleMarkAllAsRead" 
          :disabled="isMarkingAllRead" 
          class="text-sm font-medium bg-gray-100 text-gray-600 hover:bg-gray-200 px-4 py-2 rounded-full transition disabled:opacity-50"
        >
          {{ isMarkingAllRead ? 'Processing...' : 'Mark all as read' }}
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="notificationStore.isLoadingList && notificationStore.notifications.length === 0" class="text-center py-10">
        <p class="text-gray-500">Loading notifications...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="notificationStore.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md text-center">
        <p>Error loading notifications: {{ notificationStore.error }}</p>
        <button @click="loadNotifications(1)" class="mt-2 bg-red-500 text-white font-bold py-1 px-3 rounded-full hover:bg-red-600">Try Again</button>
      </div>

      <!-- Empty State -->
      <div v-else-if="notificationStore.notifications.length === 0" class="text-center py-10">
        <p class="text-gray-500">You have no notifications yet.</p>
      </div>

      <!-- Notification List -->
      <ul v-else class="space-y-3">
        <li 
          v-for="notification in notificationStore.notifications" 
          :key="notification.id" 
          class="flex items-start gap-4 p-4 rounded-lg transition-colors"
          :class="notification.is_read ? 'bg-gray-50 text-gray-500' : 'bg-blue-50 hover:bg-blue-100'"
        >
          <div class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center" :class="notification.is_read ? 'bg-gray-200' : 'bg-blue-200'">
              <span v-if="notification.notification_type === 'like'">❤️</span>
              <span v-else-if="notification.notification_type === 'comment'">💬</span>
              <span v-else-if="notification.notification_type === 'reply'">↩️</span>
              <span v-else>🔔</span>
          </div>
          <div class="flex-grow">
            <p class="text-sm leading-snug">
              <strong class="font-bold" :class="notification.is_read ? 'text-gray-700' : 'text-gray-900'">{{ notification.actor.username }}</strong>
              {{ notification.verb }}
              <span v-if="notification.target" class="font-semibold" :class="notification.is_read ? 'text-gray-600' : 'text-gray-800'">
                your {{ notification.target.type }}.
              </span>
            </p>
            <p class="text-xs text-gray-500 mt-1">
              {{ formatDistanceToNowStrict(new Date(notification.timestamp), { addSuffix: true }) }}
            </p>
          </div>
          <button v-if="!notification.is_read" @click="markOneAsRead(notification.id)" class="w-3 h-3 bg-blue-500 rounded-full flex-shrink-0 mt-1" title="Mark as read"></button>
        </li>
      </ul>

      <!-- Pagination -->
      <div v-if="!notificationStore.isLoadingList && notificationStore.pagination.totalPages > 1" class="flex justify-center items-center gap-4 mt-6 pt-4 border-t border-gray-200">
        <button @click="loadNotifications(notificationStore.pagination.currentPage - 1)" :disabled="!notificationStore.pagination.previous" class="px-4 py-2 text-sm font-medium bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50">
          Previous
        </button>
        <span class="text-sm text-gray-700">Page {{ notificationStore.pagination.currentPage }} of {{ notificationStore.pagination.totalPages }}</span>
        <button @click="loadNotifications(notificationStore.pagination.currentPage + 1)" :disabled="!notificationStore.pagination.next" class="px-4 py-2 text-sm font-medium bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50">
          Next
        </button>
      </div>
    </div>
  </div>
</template>