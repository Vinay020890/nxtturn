<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed, nextTick } from 'vue'
import { useNotificationStore } from '@/stores/notification'
import { useInfiniteScroll } from '@/composables/useInfiniteScroll'
import { formatDistanceToNowStrict } from 'date-fns'
import { getAvatarUrl } from '@/utils/avatars'
import type { Notification } from '@/stores/notification'
import {
  HeartIcon,
  ChatBubbleOvalLeftEllipsisIcon,
  ArrowUturnLeftIcon,
  UserPlusIcon,
  AtSymbolIcon,
  UserGroupIcon,
  CheckBadgeIcon,
  BellIcon,
  CheckCircleIcon,
} from '@heroicons/vue/24/solid'
import eventBus from '@/services/eventBus'

const notificationStore = useNotificationStore()
const isMarkingAllRead = ref(false)
const loadMoreTrigger = ref<HTMLElement | null>(null)

const nextNotificationPageUrl = computed(() => notificationStore.pagination.next)
useInfiniteScroll(
  loadMoreTrigger,
  () => notificationStore.fetchNotifications(notificationStore.pagination.currentPage + 1),
  nextNotificationPageUrl,
)

const getNotificationLink = (notification: Notification) => {
  if (notification.notification_type === 'group_join_request' && notification.target?.slug) {
    return { name: 'group-requests', params: { slug: notification.target.slug } }
  }
  if (notification.notification_type === 'group_join_approved' && notification.target?.slug) {
    return { name: 'group-detail', params: { slug: notification.target.slug } }
  }
  if (['like', 'comment', 'reply', 'mention'].includes(notification.notification_type)) {
    if (notification.target && notification.target.type.toLowerCase() === 'statuspost') {
      return { name: 'single-post', params: { postId: notification.target.object_id } }
    }
  }
  return { name: 'profile', params: { username: notification.actor.username } }
}

const markOneAsRead = async (notificationId: number) => {
  const notification = notificationStore.notifications.find((n) => n.id === notificationId)
  if (notification && notification.is_read) return
  await notificationStore.markNotificationsAsRead([notificationId])
}

async function handleMarkAllAsRead() {
  if (isMarkingAllRead.value) return
  isMarkingAllRead.value = true
  await notificationStore.markAllAsRead()
  isMarkingAllRead.value = false
}

// Function to get background color based on notification type and read status
const getNotificationBgColor = (notificationType: string, isRead: boolean) => {
  // For read notifications - very light gray
  if (isRead) {
    return 'bg-gray-50'
  }

  // For unread notifications - very light colors based on type
  switch (notificationType) {
    case 'like':
      return 'bg-pink-50'
    case 'comment':
      return 'bg-blue-50'
    case 'reply':
      return 'bg-gray-50'
    case 'follow':
      return 'bg-green-50'
    case 'mention':
      return 'bg-indigo-50'
    case 'group_join_request':
      return 'bg-purple-50'
    case 'group_join_approved':
      return 'bg-emerald-50'
    default:
      return 'bg-gray-50'
  }
}

// Function to get hover background color based on notification type and read status
const getHoverBgColor = (notificationType: string, isRead: boolean) => {
  // For read notifications - slightly darker gray
  if (isRead) {
    return 'hover:bg-gray-100'
  }

  // For unread notifications - slightly darker version of their color
  switch (notificationType) {
    case 'like':
      return 'hover:bg-pink-100'
    case 'comment':
      return 'hover:bg-blue-100'
    case 'reply':
      return 'hover:bg-gray-100'
    case 'follow':
      return 'hover:bg-green-100'
    case 'mention':
      return 'hover:bg-indigo-100'
    case 'group_join_request':
      return 'hover:bg-purple-100'
    case 'group_join_approved':
      return 'hover:bg-emerald-100'
    default:
      return 'hover:bg-gray-100'
  }
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// Scroll to top when component is mounted/activated
const scrollToTopOnOpen = () => {
  nextTick(() => {
    window.scrollTo({ top: 0, behavior: 'instant' })
  })
}

onMounted(() => {
  // Scroll to top immediately when component is mounted
  scrollToTopOnOpen()

  if (!notificationStore.hasLoadedInitialList) {
    notificationStore.fetchNotifications(1)
  }
  eventBus.on('scroll-notifications-to-top', scrollToTop)
})

onUnmounted(() => {
  eventBus.off('scroll-notifications-to-top', scrollToTop)
})
</script>

<template>
  <div class="container mx-auto max-w-3xl">
    <!-- Changed rounded-lg to rounded-2xl here -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 sm:p-6">
      <!-- Header with Bell Icon -->
      <div class="flex justify-between items-center border-b border-gray-100 pb-4 mb-4">
        <div class="flex items-center gap-3">
          <div class="relative">
            <BellIcon class="w-7 h-7 text-blue-500" />
            <div
              v-if="notificationStore.unreadCount > 0"
              class="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full text-xs text-white flex items-center justify-center"
            >
              {{ notificationStore.unreadCount > 99 ? '99+' : notificationStore.unreadCount }}
            </div>
          </div>
          <h1 class="text-2xl font-bold text-gray-800">Your Notifications</h1>
        </div>
        <button
          v-if="notificationStore.unreadCount > 0"
          @click="handleMarkAllAsRead"
          :disabled="isMarkingAllRead"
          class="text-sm font-medium bg-blue-50 text-blue-600 hover:bg-blue-100 px-4 py-2 rounded-lg transition disabled:opacity-50 border border-blue-100"
        >
          {{ isMarkingAllRead ? 'Processing...' : 'Mark all as read' }}
        </button>
      </div>

      <div
        v-if="notificationStore.isLoadingList && notificationStore.notifications.length === 0"
        class="text-center py-10"
      >
        <div
          class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"
        ></div>
        <p class="text-gray-500">Loading notifications...</p>
      </div>
      <div
        v-else-if="notificationStore.error"
        class="bg-red-50 border-l-4 border-red-400 text-red-700 p-4 rounded"
      >
        <p>{{ notificationStore.error }}</p>
      </div>
      <div
        v-else-if="notificationStore.notifications.length === 0 && !notificationStore.isLoadingList"
        class="text-center py-10 text-gray-500"
      >
        <BellIcon class="w-12 h-12 text-gray-300 mx-auto mb-3" />
        <p class="text-lg">You're all caught up!</p>
        <p class="text-sm">No new notifications</p>
      </div>

      <div v-else>
        <ul class="space-y-2">
          <li
            v-for="notification in notificationStore.notifications"
            :key="notification.id"
            class="block"
          >
            <router-link
              :to="getNotificationLink(notification)"
              @click="markOneAsRead(notification.id)"
              class="flex items-start gap-4 p-4 rounded-lg transition-all duration-200 w-full text-left"
              :class="[
                getNotificationBgColor(notification.notification_type, notification.is_read),
                getHoverBgColor(notification.notification_type, notification.is_read),
              ]"
            >
              <!-- Avatar with Icon Badge -->
              <div class="flex-shrink-0 relative">
                <img
                  v-if="notification.actor"
                  :src="
                    getAvatarUrl(
                      notification.actor.picture,
                      notification.actor.first_name,
                      notification.actor.last_name,
                    )
                  "
                  class="w-12 h-12 rounded-full object-cover border-2 border-white shadow-sm"
                  alt=""
                />
                <div
                  class="absolute -bottom-1 -right-1 w-6 h-6 rounded-full border-2 border-white shadow-sm flex items-center justify-center"
                  :class="{
                    'bg-pink-500': notification.notification_type === 'like',
                    'bg-blue-500': notification.notification_type === 'comment',
                    'bg-gray-500': notification.notification_type === 'reply',
                    'bg-green-500': notification.notification_type === 'follow',
                    'bg-indigo-500': notification.notification_type === 'mention',
                    'bg-purple-500': notification.notification_type === 'group_join_request',
                    'bg-emerald-500': notification.notification_type === 'group_join_approved',
                  }"
                >
                  <HeartIcon
                    v-if="notification.notification_type === 'like'"
                    class="w-3 h-3 text-white"
                  />
                  <ChatBubbleOvalLeftEllipsisIcon
                    v-else-if="notification.notification_type === 'comment'"
                    class="w-3 h-3 text-white"
                  />
                  <ArrowUturnLeftIcon
                    v-else-if="notification.notification_type === 'reply'"
                    class="w-3 h-3 text-white"
                  />
                  <UserPlusIcon
                    v-else-if="notification.notification_type === 'follow'"
                    class="w-3 h-3 text-white"
                  />
                  <AtSymbolIcon
                    v-else-if="notification.notification_type === 'mention'"
                    class="w-3 h-3 text-white"
                  />
                  <UserGroupIcon
                    v-else-if="notification.notification_type === 'group_join_request'"
                    class="w-3 h-3 text-white"
                  />
                  <CheckBadgeIcon
                    v-else-if="notification.notification_type === 'group_join_approved'"
                    class="w-3 h-3 text-white"
                  />
                </div>
              </div>

              <!-- Content -->
              <div class="flex-grow min-w-0 break-words">
                <div class="flex justify-between items-start mb-1">
                  <strong
                    class="font-semibold text-sm"
                    :class="notification.is_read ? 'text-gray-700' : 'text-gray-900'"
                  >
                    <span v-if="notification.notification_type === 'group_join_approved'"
                      >Group Membership Approved</span
                    >
                    <span v-else>{{ notification.actor.username }}</span>
                  </strong>
                  <!-- Time moved to right corner -->
                  <p class="text-xs text-gray-500 flex-shrink-0">
                    {{
                      formatDistanceToNowStrict(new Date(notification.timestamp), {
                        addSuffix: true,
                      })
                    }}
                  </p>
                </div>

                <div class="mt-1 text-sm text-gray-600">
                  <!-- Case 1: Join Request (for owners) -->
                  <div
                    v-if="
                      notification.notification_type === 'group_join_request' && notification.target
                    "
                  >
                    <span>
                      <strong class="font-semibold text-gray-700">{{
                        notification.actor.username
                      }}</strong>
                      {{ notification.verb }}
                      <strong class="font-semibold text-gray-800">{{
                        notification.target.display_text
                      }}</strong>
                    </span>
                  </div>

                  <!-- Case 2: Join Request APPROVED (for requesters) -->
                  <div
                    v-else-if="
                      notification.notification_type === 'group_join_approved' &&
                      notification.target
                    "
                  >
                    <span>
                      You have been accepted into
                      <strong class="font-semibold text-gray-800">{{
                        notification.target.display_text
                      }}</strong
                      >. Welcome!
                    </span>
                  </div>

                  <!-- Fallback for all other types -->
                  <div v-else>
                    <span>{{ notification.verb }}</span>
                  </div>
                </div>

                <p
                  v-if="notification.context_snippet"
                  class="mt-2 text-sm text-gray-500 italic break-words bg-white bg-opacity-50 px-2 py-1 rounded border border-gray-100"
                >
                  {{ notification.context_snippet }}
                </p>
              </div>

              <!-- Unread indicator - more subtle -->
              <div
                v-if="!notification.is_read"
                class="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0 self-center mt-1 animate-pulse"
                title="Unread"
              ></div>
            </router-link>
          </li>
        </ul>

        <div v-if="notificationStore.pagination.next" ref="loadMoreTrigger" class="h-10"></div>
        <div
          v-if="notificationStore.isLoadingList && notificationStore.notifications.length > 0"
          class="text-center py-4 text-gray-500"
        >
          <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mx-auto"></div>
        </div>
      </div>
    </div>
  </div>
</template>
