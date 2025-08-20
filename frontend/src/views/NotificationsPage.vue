// C:\Users\Vinay\Project\frontend\src\views\NotificationsPage.vue

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useNotificationStore } from '@/stores/notification';
import { formatDistanceToNowStrict } from 'date-fns';
import { getAvatarUrl } from '@/utils/avatars';
import type { Notification } from '@/stores/notification';

const notificationStore = useNotificationStore();
const isMarkingAllRead = ref(false);

const getNotificationLink = (notification: Notification) => {
  if (['like', 'comment', 'reply', 'mention'].includes(notification.notification_type)) {
    if (notification.target && notification.target.type.toLowerCase() === 'statuspost') {
      return { name: 'single-post', params: { postId: notification.target.object_id } };
    }
  }
  return { name: 'profile', params: { username: notification.actor.username } };
};

const loadNotifications = (page: number) => {
  if (notificationStore.isLoadingList && page !== 1) return;
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
  await notificationStore.markAllAsRead();
  isMarkingAllRead.value = false;
}

onMounted(() => {
  if (notificationStore.notifications.length === 0) {
      loadNotifications(1);
  }
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

      <div v-if="notificationStore.isLoadingList && notificationStore.notifications.length === 0" class="text-center py-10">
        <p class="text-gray-500">Loading notifications...</p>
      </div>
      <div v-else-if="notificationStore.error" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4">
        <p>{{ notificationStore.error }}</p>
      </div>
      <div v-else-if="notificationStore.notifications.length === 0" class="text-center py-10 text-gray-500">
        <p>You have no notifications yet.</p>
      </div>

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
                <!-- --- THIS IS THE FIX --- -->
                <!-- We add a left margin (ml-1) to create the space. -->
                <span class="ml-1">{{ notification.verb }}</span>
              </p>
              <!-- --- END OF FIX --- -->
              <p class="text-xs text-gray-500 mt-1">
                {{ formatDistanceToNowStrict(new Date(notification.timestamp), { addSuffix: true }) }}
              </p>
            </div>
            
            <div v-if="!notification.is_read" class="w-3 h-3 bg-blue-500 rounded-full flex-shrink-0 mt-1 self-center" title="Unread"></div>
          </router-link>
        </li>
      </ul>
    </div>
  </div>
</template>