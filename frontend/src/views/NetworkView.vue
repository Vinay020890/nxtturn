<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useNetworkStore } from '@/stores/network'
import { storeToRefs } from 'pinia'
import { Users, UserPlus, UserCheck, Search, MessageSquare, UserCircle } from 'lucide-vue-next'

// 1. Setup the store we created yesterday
const networkStore = useNetworkStore()
const { followers, following, connections, isLoading, error } = storeToRefs(networkStore)

// 2. State for Tabs and Search
const activeTab = ref<'connections' | 'followers' | 'following'>('connections')
const searchQuery = ref('')

// 3. Fetch data whenever the tab changes
const fetchData = async () => {
  if (activeTab.value === 'connections') await networkStore.fetchConnections()
  else if (activeTab.value === 'followers') await networkStore.fetchFollowers()
  else if (activeTab.value === 'following') await networkStore.fetchFollowing()
}

// Watch for tab changes and fetch immediately on load
watch(activeTab, fetchData, { immediate: true })

// 4. Filter the list based on the search bar
const filteredList = computed(() => {
  const list =
    activeTab.value === 'connections'
      ? connections.value
      : activeTab.value === 'followers'
        ? followers.value
        : following.value

  if (!searchQuery.value) return list

  return list.filter(
    (user) =>
      user.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      user.username.toLowerCase().includes(searchQuery.value.toLowerCase()),
  )
})
</script>

<template>
  <div class="space-y-6">
    <!-- Main Container Card -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
      <!-- Header with Title and Search -->
      <div class="p-6 border-b border-gray-100">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <h1 class="text-2xl font-bold text-gray-900">
            {{
              activeTab === 'connections'
                ? 'Your Connections'
                : activeTab === 'followers'
                  ? 'Your Followers'
                  : 'Following'
            }}
          </h1>

          <!-- Search Bar -->
          <div class="relative group">
            <Search
              class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 group-focus-within:text-blue-500 transition-colors"
            />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search people..."
              class="pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm w-full md:w-64 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all"
            />
          </div>
        </div>

        <!-- Tab Buttons -->
        <div class="flex gap-2 mt-6 p-1 bg-gray-100/50 rounded-xl w-fit">
          <button
            v-for="tab in ['connections', 'followers', 'following'] as const"
            :key="tab"
            @click="activeTab = tab"
            :class="[
              'px-5 py-2 text-xs font-bold uppercase tracking-wider rounded-lg transition-all',
              activeTab === tab
                ? 'bg-white text-blue-600 shadow-sm border border-gray-200'
                : 'text-gray-500 hover:text-gray-700',
            ]"
          >
            {{ tab }}
          </button>
        </div>
      </div>

      <!-- List of Users -->
      <div class="min-h-[500px] relative">
        <!-- Loading Spinner -->
        <div
          v-if="isLoading"
          class="absolute inset-0 flex justify-center items-center bg-white/60 z-10 backdrop-blur-[1px]"
        >
          <div
            class="animate-spin rounded-full h-8 w-8 border-2 border-blue-600 border-t-transparent"
          ></div>
        </div>

        <!-- Empty State -->
        <div
          v-if="filteredList.length === 0 && !isLoading"
          class="flex flex-col items-center justify-center py-24 text-gray-400 text-center"
        >
          <Users class="w-12 h-12 opacity-10 mb-4" />
          <p class="text-lg font-medium text-gray-900">No one found</p>
          <p class="text-sm">Try searching for someone else or check another tab.</p>
        </div>

        <!-- User Rows -->
        <div v-else class="divide-y divide-gray-100 px-2">
          <div
            v-for="user in filteredList"
            :key="user.id"
            class="group flex items-center justify-between p-4 hover:bg-blue-50/30 transition-colors rounded-xl"
          >
            <div class="flex items-center gap-4">
              <img
                :src="user.profile_picture || '/img/default-avatar.png'"
                class="w-14 h-14 rounded-2xl object-cover border border-gray-100"
              />
              <div class="min-w-0">
                <RouterLink
                  :to="`/profile/${user.username}`"
                  class="text-base font-bold text-gray-900 hover:text-blue-600 transition-colors block"
                >
                  {{ user.name }}
                </RouterLink>
                <p class="text-xs text-gray-500 truncate max-w-[200px]">
                  {{ user.headline || 'Member at nxtturn' }}
                </p>
                <p class="text-[10px] font-mono text-gray-400">@{{ user.username }}</p>
              </div>
            </div>

            <div class="flex items-center gap-2">
              <button
                class="p-2.5 text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-xl transition-all"
                title="Message"
              >
                <MessageSquare class="w-5 h-5" />
              </button>
              <RouterLink
                :to="`/profile/${user.username}`"
                class="p-2.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-xl transition-all"
              >
                <UserCircle class="w-5 h-5" />
              </RouterLink>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
