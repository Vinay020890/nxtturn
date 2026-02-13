<script setup lang="ts">
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { onMounted, computed, ref } from 'vue'
import { useGroupStore } from '@/stores/group'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'
import { formatDistanceToNow } from 'date-fns'
import defaultAvatar from '@/assets/images/default-avatar.svg'
import {
  ArrowLeftIcon,
  UserGroupIcon,
  ShieldCheckIcon,
  ShieldExclamationIcon,
  CheckIcon,
  XMarkIcon,
  ChevronDownIcon,
  EyeSlashIcon,
  EyeIcon,
} from '@heroicons/vue/24/outline'

const route = useRoute()
const router = useRouter()
const groupStore = useGroupStore()
const authStore = useAuthStore()

const activeTab = ref<'requests' | 'blocked'>('requests')
const openDropdowns = ref<Map<number, boolean>>(new Map())

const {
  joinRequests,
  isLoadingRequests,
  requestsError,
  isManagingRequest,
  manageRequestError,
  currentGroup,
  blockedUsers,
  isLoadingBlockedUsers,
  blockedUsersError,
} = storeToRefs(groupStore)

const { currentUser } = storeToRefs(authStore)

const isCreator = computed(() => {
  return (
    currentUser.value &&
    currentGroup.value &&
    currentUser.value.id === currentGroup.value.creator.id
  )
})

onMounted(async () => {
  const slug = route.params.slug as string
  if (!currentGroup.value || currentGroup.value.slug !== slug) {
    await groupStore.fetchGroupDetails(slug)
  }
  if (!isCreator.value) {
    router.push({ name: 'group-detail', params: { slug } })
    return
  }
  await groupStore.fetchJoinRequests(slug)
  await groupStore.fetchBlockedUsers(slug)
})

async function handleApprove(requestId: number) {
  const slug = route.params.slug as string
  await groupStore.manageJoinRequest(slug, requestId, 'approve')
  openDropdowns.value.set(requestId, false)
}

async function handleDeny(requestId: number) {
  const slug = route.params.slug as string
  await groupStore.manageJoinRequest(slug, requestId, 'deny')
  openDropdowns.value.set(requestId, false)
}

async function handleDenyAndBlock(requestId: number) {
  if (
    confirm(
      'Are you sure you want to deny this user and permanently block them from re-requesting?',
    )
  ) {
    const slug = route.params.slug as string
    await groupStore.manageJoinRequest(slug, requestId, 'deny_and_block')
  }
  openDropdowns.value.set(requestId, false)
}

async function handleUnblock(userId: number) {
  if (
    confirm(
      'Are you sure you want to unblock this user? They will be able to request to join the group again.',
    )
  ) {
    const slug = route.params.slug as string
    await groupStore.unblockUser(slug, userId)
  }
}

function toggleDropdown(requestId: number) {
  // Close all other dropdowns
  openDropdowns.value.forEach((_, key) => {
    if (key !== requestId) {
      openDropdowns.value.set(key, false)
    }
  })

  const currentState = openDropdowns.value.get(requestId) || false
  openDropdowns.value.set(requestId, !currentState)
}

function formatTimestamp(dateString: string) {
  return formatDistanceToNow(new Date(dateString), { addSuffix: true })
}
</script>

<template>
  <!-- Added pb-16 for mobile to prevent content hiding behind navbar -->
  <div class="max-w-4xl mx-auto pb-16 sm:pb-0">
    <!-- "Manage Group Members" title with container - Reverted to original styling -->
    <div
      class="bg-gradient-to-r from-blue-700 to-purple-900 rounded-2xl p-6 mb-3 shadow-lg border border-gray-700"
    >
      <div class="flex items-center space-x-4">
        <div class="p-3 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 shadow-md">
          <ShieldCheckIcon class="h-8 w-8 text-white" />
        </div>
        <div>
          <h1 class="text-2xl font-bold text-white mb-1">Manage Group Members</h1>
          <p class="text-gray-300 text-sm">
            Review join requests and manage blocked users for your group
          </p>
        </div>
      </div>

      <div class="flex items-center justify-between mt-6">
        <!-- Back button and Group name containers side by side -->
        <div class="flex items-center space-x-3">
          <!-- Back button with icon -->
          <RouterLink
            v-if="currentGroup"
            :to="{ name: 'group-detail', params: { slug: currentGroup.slug } }"
            class="inline-flex items-center space-x-2 px-3 py-1 rounded-xl bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100 hover:border-blue-200 hover:from-blue-100 hover:to-indigo-100 transition-all duration-300 shadow-sm hover:shadow"
          >
            <ArrowLeftIcon class="h-4 w-4 text-blue-600" />
            <span class="font-semibold text-blue-700 text-sm">Back</span>
          </RouterLink>

          <!-- Group name with icon - All in one row -->
          <div
            v-if="currentGroup"
            class="inline-flex items-center space-x-3 px-5 py-1 rounded-xl bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-100"
          >
            <UserGroupIcon class="h-6 w-6 text-blue-600" />
            <span class="text-gray-800 font-semibold text-sm">{{ currentGroup.name }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Tabs container - Made sticky -->
    <div class="sticky top-0 z-40 mb-3 bg-white sm:bg-transparent">
      <div
        class="bg-white rounded-xl sm:rounded-2xl shadow-sm border border-gray-200 overflow-hidden"
      >
        <div class="flex flex-col sm:flex-row">
          <!-- Pending Requests Tab -->
          <button
            @click="activeTab = 'requests'"
            :class="[
              'flex-1 flex items-center justify-between sm:justify-center py-4 px-4 sm:px-6 transition-all duration-300 border-b sm:border-b-0 sm:border-r border-gray-200',
              activeTab === 'requests'
                ? 'bg-gradient-to-r from-green-50 to-green-100 sm:border-b-2 border-b-green-500 sm:border-b-green-500'
                : 'hover:bg-gray-50',
            ]"
          >
            <div class="flex items-center justify-between w-full sm:w-auto sm:space-x-4">
              <div class="flex items-center space-x-3 sm:space-x-4">
                <div
                  :class="[
                    'p-2 rounded-lg sm:rounded-xl',
                    activeTab === 'requests'
                      ? 'bg-green-100 border border-green-200'
                      : 'bg-gray-100 border border-gray-200',
                  ]"
                >
                  <ShieldCheckIcon
                    class="h-5 w-5"
                    :class="activeTab === 'requests' ? 'text-green-600' : 'text-gray-500'"
                  />
                </div>
                <span
                  :class="[
                    'font-semibold text-sm sm:text-base',
                    activeTab === 'requests' ? 'text-green-700' : 'text-gray-700',
                  ]"
                >
                  Pending Requests
                </span>
              </div>
              <span
                :class="[
                  'px-2 sm:px-3 py-1 rounded-full text-xs sm:text-sm font-bold min-w-8 sm:min-w-10 text-center',
                  activeTab === 'requests'
                    ? 'bg-green-500 text-white shadow-sm'
                    : 'bg-gray-200 text-gray-700',
                ]"
              >
                {{ joinRequests.length }}
              </span>
            </div>
          </button>

          <!-- Blocked Users Tab -->
          <button
            @click="activeTab = 'blocked'"
            :class="[
              'flex-1 flex items-center justify-between sm:justify-center py-4 px-4 sm:px-6 transition-all duration-300',
              activeTab === 'blocked'
                ? 'bg-gradient-to-r from-red-50 to-red-100 sm:border-b-2 border-b-red-500'
                : 'hover:bg-gray-50',
            ]"
          >
            <div class="flex items-center justify-between w-full sm:w-auto sm:space-x-4">
              <div class="flex items-center space-x-3 sm:space-x-4">
                <div
                  :class="[
                    'p-2 rounded-lg sm:rounded-xl',
                    activeTab === 'blocked'
                      ? 'bg-red-100 border border-red-200'
                      : 'bg-gray-100 border border-gray-200',
                  ]"
                >
                  <ShieldExclamationIcon
                    class="h-5 w-5"
                    :class="activeTab === 'blocked' ? 'text-red-600' : 'text-gray-500'"
                  />
                </div>
                <span
                  :class="[
                    'font-semibold text-sm sm:text-base',
                    activeTab === 'blocked' ? 'text-red-700' : 'text-gray-700',
                  ]"
                >
                  Blocked Users
                </span>
              </div>
              <span
                :class="[
                  'px-2 sm:px-3 py-1 rounded-full text-xs sm:text-sm font-bold min-w-8 sm:min-w-10 text-center',
                  activeTab === 'blocked'
                    ? 'bg-red-500 text-white shadow-sm'
                    : 'bg-gray-200 text-gray-700',
                ]"
              >
                {{ blockedUsers.length }}
              </span>
            </div>
          </button>
        </div>
      </div>
    </div>

    <!-- PENDING REQUESTS TAB CONTENT -->
    <div v-if="activeTab === 'requests'">
      <div v-if="isLoadingRequests" class="text-center py-10">Loading...</div>
      <div
        v-else-if="requestsError"
        class="bg-red-100 p-4 rounded-xl sm:rounded-2xl text-red-700 text-sm sm:text-base"
      >
        {{ requestsError }}
      </div>
      <div
        v-else-if="joinRequests.length === 0"
        class="bg-white p-6 sm:p-8 rounded-xl sm:rounded-2xl shadow-md text-center border border-gray-200"
      >
        <div
          class="inline-flex items-center justify-center w-12 h-12 sm:w-16 sm:h-16 rounded-full bg-blue-100 mb-4"
        >
          <ShieldCheckIcon class="h-6 w-6 sm:h-8 sm:w-8 text-blue-500" />
        </div>
        <p class="text-gray-700 text-base sm:text-lg font-medium mb-2">No pending join requests</p>
        <p class="text-gray-500 text-xs sm:text-sm">
          New requests will appear here when users ask to join your group.
        </p>
      </div>
      <!-- MAIN CONTENT CONTAINER -->
      <div
        v-else
        class="bg-white rounded-xl sm:rounded-2xl shadow-md divide-y divide-gray-200 border border-gray-200 max-h-[60vh] sm:max-h-[70vh] overflow-y-auto"
      >
        <div
          v-for="request in joinRequests"
          :key="request.id"
          class="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between hover:bg-gray-50 transition-colors duration-150 relative"
        >
          <div class="flex items-center space-x-3 sm:space-x-4 mb-3 sm:mb-0">
            <img
              :src="request.user.picture || defaultAvatar"
              alt="User avatar"
              class="w-10 h-10 sm:w-14 sm:h-14 rounded-full object-cover border-2 border-gray-200"
            />
            <div class="flex-1 min-w-0">
              <RouterLink
                :to="{ name: 'profile', params: { username: request.user.username } }"
                class="font-bold text-gray-800 hover:text-blue-600 hover:underline transition-colors block truncate"
              >
                {{ request.user.username }}
              </RouterLink>
              <p class="text-xs sm:text-sm text-gray-500 mt-1">
                Requested {{ formatTimestamp(request.created_at) }}
              </p>
            </div>
          </div>
          <div
            class="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3 w-full sm:w-auto"
          >
            <button
              @click="handleApprove(request.id)"
              :disabled="isManagingRequest"
              class="px-4 sm:px-5 py-2.5 bg-gradient-to-r from-green-500 to-green-600 text-white text-xs sm:text-sm font-semibold rounded-xl sm:rounded-2xl hover:from-green-600 hover:to-green-700 disabled:opacity-50 disabled:cursor-wait transition-all duration-200 flex items-center justify-center space-x-2 shadow-sm hover:shadow flex-1 sm:flex-none"
            >
              <CheckIcon class="h-3 w-3 sm:h-4 sm:w-4" />
              <span>Approve</span>
            </button>
            <div class="relative flex-1 sm:flex-none">
              <button
                @click="toggleDropdown(request.id)"
                :disabled="isManagingRequest"
                class="w-full px-4 sm:px-5 py-2.5 bg-gradient-to-r from-red-500 to-red-600 text-white text-xs sm:text-sm font-semibold rounded-xl sm:rounded-2xl hover:from-red-600 hover:to-red-700 disabled:opacity-50 disabled:cursor-wait transition-all duration-200 flex items-center justify-center space-x-2 shadow-sm hover:shadow relative z-10"
              >
                <XMarkIcon class="h-3 w-3 sm:h-4 sm:w-4" />
                <span>Deny</span>
                <ChevronDownIcon class="h-3 w-3 sm:h-4 sm:w-4 ml-1" />
              </button>

              <!-- DROPDOWN - Mobile: full width, Desktop: fixed width -->
              <div
                v-if="openDropdowns.get(request.id)"
                class="absolute left-0 right-0 sm:left-auto sm:right-0 mt-2 w-full sm:w-60 rounded-xl sm:rounded-2xl shadow-xl bg-white ring-1 ring-black ring-opacity-5 border border-gray-200 z-50"
                style="top: calc(100% + 4px)"
              >
                <div class="py-1" role="menu" aria-orientation="vertical">
                  <a
                    href="#"
                    @click.prevent="handleDeny(request.id)"
                    class="block px-4 py-3 text-xs sm:text-sm text-gray-700 hover:bg-gray-100 border-b border-gray-100 rounded-t-xl sm:rounded-t-2xl"
                    role="menuitem"
                  >
                    <div class="font-medium flex items-center">
                      <XMarkIcon class="h-3 w-3 sm:h-4 sm:w-4 mr-2" />
                      Deny Request
                    </div>
                    <p class="text-xs text-gray-500 mt-1 ml-5 sm:ml-6">
                      User can request to join again later.
                    </p>
                  </a>
                  <a
                    href="#"
                    @click.prevent="handleDenyAndBlock(request.id)"
                    class="block px-4 py-3 text-xs sm:text-sm text-red-700 hover:bg-red-50 rounded-b-xl sm:rounded-b-2xl"
                    role="menuitem"
                  >
                    <div class="font-medium flex items-center">
                      <EyeSlashIcon class="h-3 w-3 sm:h-4 sm:w-4 mr-2" />
                      Deny & Block User
                    </div>
                    <p class="text-xs text-red-500 mt-1 ml-5 sm:ml-6">
                      User will be blocked permanently.
                    </p>
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- BLOCKED USERS TAB CONTENT -->
    <div v-if="activeTab === 'blocked'">
      <div v-if="isLoadingBlockedUsers" class="text-center py-10">Loading...</div>
      <div
        v-else-if="blockedUsersError"
        class="bg-red-100 p-4 rounded-xl sm:rounded-2xl text-red-700 text-sm sm:text-base"
      >
        {{ blockedUsersError }}
      </div>
      <div
        v-else-if="blockedUsers.length === 0"
        class="bg-white p-6 sm:p-8 rounded-xl sm:rounded-2xl shadow-md text-center border border-gray-200"
      >
        <div
          class="inline-flex items-center justify-center w-12 h-12 sm:w-16 sm:h-16 rounded-full bg-red-100 mb-4"
        >
          <ShieldExclamationIcon class="h-6 w-6 sm:h-8 sm:w-8 text-red-500" />
        </div>
        <p class="text-gray-700 text-base sm:text-lg font-medium mb-2">No blocked users</p>
        <p class="text-gray-500 text-xs sm:text-sm">
          Blocked users will appear here if you deny and block any join requests.
        </p>
      </div>
      <div
        v-else
        class="bg-white rounded-xl sm:rounded-2xl shadow-md divide-y divide-gray-200 border border-gray-200 max-h-[60vh] sm:max-h-[70vh] overflow-y-auto"
      >
        <div
          v-for="block in blockedUsers"
          :key="block.id"
          class="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between hover:bg-gray-50 transition-colors duration-150"
        >
          <div class="flex items-center space-x-3 sm:space-x-4 mb-3 sm:mb-0">
            <img
              :src="block.user.picture || defaultAvatar"
              alt="User avatar"
              class="w-10 h-10 sm:w-14 sm:h-14 rounded-full object-cover border-2 border-gray-200"
            />
            <div class="flex-1 min-w-0">
              <RouterLink
                :to="{ name: 'profile', params: { username: block.user.username } }"
                class="font-bold text-gray-800 hover:text-blue-600 hover:underline transition-colors block truncate"
              >
                {{ block.user.username }}
              </RouterLink>
              <p class="text-xs sm:text-sm text-gray-500 mt-1">
                Blocked {{ formatTimestamp(block.created_at) }}
              </p>
            </div>
          </div>
          <button
            @click="handleUnblock(block.user.id)"
            class="px-4 sm:px-5 py-2.5 bg-gradient-to-r from-gray-300 to-gray-400 text-gray-800 text-xs sm:text-sm font-semibold rounded-xl sm:rounded-2xl hover:from-gray-400 hover:to-gray-500 transition-all duration-200 flex items-center justify-center space-x-2 shadow-sm hover:shadow w-full sm:w-auto"
          >
            <EyeIcon class="h-3 w-3 sm:h-4 sm:w-4" />
            <span>Unblock</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
