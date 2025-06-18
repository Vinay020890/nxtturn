<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'; // <-- Import computed
import { useNotificationStore } from '@/stores/notification';
import { formatDistanceToNowStrict } from 'date-fns';
import { getAvatarUrl } from '@/utils/avatars'; // <-- Import avatar utility

const notificationStore = useNotificationStore();
const isMarkingAllRead = ref(false);

// --- NEW: Helper function to get the link for a notification target ---
const getNotificationLink = (notification: any) => {
  if (!notification.target) return { name: 'home' }; // Fallback to home

  const targetType = notification.target.type.toLowerCase();
  
  if (targetType === 'statuspost') {
    // For now, we link to the user's profile who made the post.
    // A direct link to a post on the feed page is a more advanced feature.
    return { name: 'profile', params: { username: notification.actor.username } };
  }
  if (targetType === 'comment') {
    // Similarly, we can't easily link to a specific comment, so link to the general area.
    return { name: 'profile', params: { username: notification.actor.username } };
  }
  
  return { name: 'home' };
};


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
      <div v-if="notificationStore.isLoadingList && notificationStore.notifications.length === 0" class="text-center py-10">...</div>
      <div v-else-if="notificationStore.error" class="... ">...</div>
      <div v-else-if="notificationStore.notifications.length === 0" class="text-center py-10">...</div>

      <!-- Notification List -->
      <ul v-else class="space-y-1">
        <li 
          v-for="notification in notificationStore.notifications" 
          :key="notification.id" 
          class="block"
        >
          <!-- Using router-link to make the whole item clickable -->
          <router-link
            :to="getNotificationLink(notification)"
            @click="markOneAsRead(notification.id)"
            class="flex items-start gap-4 p-4 rounded-lg transition-colors w-full text-left"
            :class="notification.is_read ? 'bg-white hover:bg-gray-100' : 'bg-blue-50 hover:bg-blue-100'"
          >
            <!-- Updated icon section to use avatars and mention icon -->
            <div class="flex-shrink-0">
              <img 
                v-if="notification.actor"
                :src="getAvatarUrl(notification.actor.picture, notification.actor.first_name, notification.actor.last_name)"
                class="w-10 h-10 rounded-full object-cover"
              >
            </div>
            
            <div class="flex-grow">
              <p class="text-sm leading-snug">
                <strong class="font-bold" :class="notification.is_read ? 'text-gray-700' : 'text-gray-900'">{{ notification.actor.username }}</strong>
                
                <!-- NEW: Logic to display different notification texts -->
                <span v-if="notification.notification_type === 'like'"> liked your post.</span>
                <span v-else-if="notification.notification_type === 'comment'"> commented on your post.</span>
                <span v-else-if="notification.notification_type === 'reply'"> replied to your comment.</span>
                <span v-else-if="notification.notification_type === 'mention'"> mentioned you in a 
                  <span class="font-semibold">{{ notification.target?.type }}</span>.
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
      <div v-if="!notificationStore.isLoadingList && notificationStore.pagination.totalPages > 1" class="flex justify-center ...">...</div>
    </div>
  </div>
</template>