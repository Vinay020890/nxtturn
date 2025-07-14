// C:\Users\Vinay\Project\frontend\src/views/NotificationsPage.vue

<script setup lang="ts">
import { onMounted, ref } from 'vue'; // <-- Removed unused 'computed' import
import { useNotificationStore } from '@/stores/notification';
import { formatDistanceToNowStrict } from 'date-fns';
import { getAvatarUrl } from '@/utils/avatars';
import type { Notification } from '@/stores/notification'; // Import the type for better safety

const notificationStore = useNotificationStore();
const isMarkingAllRead = ref(false);

// --- THIS IS THE FIX ---
// The helper function is now smarter and uses the correct route names.
const getNotificationLink = (notification: Notification) => {
  // 1. Handle Like, Comment, Reply - these should link to the post
  if (['like', 'comment', 'reply'].includes(notification.notification_type)) {
    if (notification.target && notification.target.type.toLowerCase() === 'statuspost') {
      return { name: 'single-post', params: { postId: notification.target.object_id } };
    }
  }

  // 2. Handle Mentions - these should also link to the post where the mention occurred
  if (notification.notification_type === 'mention') {
    if (notification.target && notification.target.type.toLowerCase() === 'statuspost') {
      return { name: 'single-post', params: { postId: notification.target.object_id } };
    }
    if (notification.target && notification.target.type.toLowerCase() === 'comment') {
      // If the comment's parent is a post, we can link there.
      // This requires the parent post ID to be part of the notification payload,
      // which is a future backend improvement. For now, we link to the user.
      return { name: 'profile', params: { username: notification.actor.username } };
    }
  }

  // 3. Fallback for other types (like new follower) or if target is missing
  return { name: 'feed' }; // <-- Use 'feed' instead of 'home'
};
// --- END OF FIX ---


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

      <!-- Loading, Error, Empty states (unchanged) -->
      <div v-if="notificationStore.isLoadingList && notificationStore.notifications.length === 0" class="text-center py-10">
        <p class="text-gray-500">Loading notifications...</p>
      </div>
      <div v-else-if="notificationStore.error" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4">
        <p>{{ notificationStore.error }}</p>
      </div>
      <div v-else-if="notificationStore.notifications.length === 0" class="text-center py-10 text-gray-500">
        <p>You have no notifications yet.</p>
      </div>

      <!-- Notification List -->
      <ul v-else class="space-y-1">
        <li 
          v-for="notification in notificationStore.notifications" 
          :key="notification.id" 
          class="block"
        >
          <router-link
            :to="getNotificationLink(notification)"
            @click="markOneAsRead(notification.id)"
            class="flex items-start gap-4 p-4 rounded-lg transition-colors w-full text-left"
            :class="notification.is_read ? 'bg-white hover:bg-gray-100' : 'bg-gray-50 hover:bg-gray-100'"
          >
            <div class="flex-shrink-0">
              <img 
                v-if="notification.actor"
                :src="getAvatarUrl(notification.actor.picture, notification.actor.first_name, notification.actor.last_name)"
                class="w-10 h-10 rounded-full object-cover"
                alt=""
              >
            </div>
            
            <div class="flex-grow">
              <p class="text-sm leading-snug">
                <strong class="font-bold" :class="notification.is_read ? 'text-gray-700' : 'text-gray-900'">{{ notification.actor.username }}</strong>
                
                <span v-if="notification.notification_type === 'like'"> liked your post.</span>
                <span v-else-if="notification.notification_type === 'comment'"> commented on your post.</span>
                <span v-else-if="notification.notification_type === 'reply'"> replied to your comment.</span>
                <span v-else-if="notification.notification_type === 'mention'"> mentioned you in a 
                  <span class="font-semibold">{{ notification.target?.type.replace('statuspost', 'post') || 'post' }}</span>.
                </span>
                <span v-else> {{ notification.verb }}</span>
              </p>
              <p class="text-xs text-gray-500 mt-1">
                {{ formatDistanceToNowStrict(new Date(notification.timestamp), { addSuffix: true }) }}
              </p>
            </div>
            
            <div v-if="!notification.is_read" class="w-3 h-3 bg-blue-500 rounded-full flex-shrink-0 mt-1 self-center" title="Unread"></div>
          </router-link>
        </li>
      </ul>

      <!-- Pagination (unchanged) -->
      <div v-if="!notificationStore.isLoadingList && notificationStore.pagination.totalPages > 1" class="flex justify-center mt-6">
        <!-- Pagination controls here -->
      </div>
    </div>
  </div>
</template>