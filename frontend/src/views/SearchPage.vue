<!-- C:\Users\Vinay\Project\frontend\src\views\SearchPage.vue -->
<!-- COMPLETELY FIXED: Clean and working version -->

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { debounce } from 'lodash-es'

import { useSearchStore } from '@/stores/search'
import { useFeedStore } from '@/stores/feed'
import { useGroupStore } from '@/stores/group'
import { usePostsStore } from '@/stores/posts'
import PostItem from '@/components/PostItem.vue'
import { getAvatarUrl } from '@/utils/avatars'

// Font Awesome Icons
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { library } from '@fortawesome/fontawesome-svg-core'
import { faUser, faFileAlt, faUsers, faChevronRight } from '@fortawesome/free-solid-svg-icons'

// Add icons to library
library.add(faUser, faFileAlt, faUsers, faChevronRight)

const route = useRoute()
const router = useRouter()
const searchStore = useSearchStore()
const feedStore = useFeedStore()
const groupStore = useGroupStore()
const postsStore = usePostsStore()

const localQuery = ref((route.query.q as string) || '')
const activeTab = ref<'users' | 'posts' | 'groups'>('users')

// Computed properties
const userResults = computed(() => searchStore.userResults || [])
const isLoadingUsers = computed(() => searchStore.isLoadingUsers || false)
const userError = computed(() => searchStore.userError || null)

const postResultIds = computed(() => feedStore.searchResultPostIds || [])
const postResults = computed(() => {
  if (postsStore.getPostsByIds) {
    return postsStore.getPostsByIds(postResultIds.value) || []
  }
  return []
})
const isLoadingPosts = computed(() => feedStore.isLoadingSearchResults || false)
const postError = computed(() => feedStore.searchError || null)

const groupResults = computed(() => groupStore.groupSearchResults || [])
const isLoadingGroups = computed(() => groupStore.isLoadingGroupSearch || false)
const groupError = computed(() => groupStore.groupSearchError || null)

// Search function
const performSearch = (query: string) => {
  if (!query.trim()) {
    // Clear results if query is empty
    searchStore.clearSearch?.()
    if (feedStore) feedStore.searchResultPostIds = []
    if (groupStore) groupStore.groupSearchResults = []
    return
  }

  // Perform search
  searchStore.searchUsers?.(query)
  feedStore.searchPosts?.(query)
  groupStore.searchGroups?.(query)
}

// Initialize search on component mount
onMounted(() => {
  if (localQuery.value) {
    performSearch(localQuery.value)
  }
})

// Watch for route changes
watch(
  () => route.query.q,
  (newQuery) => {
    const queryStr = (newQuery as string) || ''
    if (localQuery.value !== queryStr) {
      localQuery.value = queryStr
      performSearch(queryStr)
    }
  },
)

// Debounced search
const debouncedSearch = debounce((query: string) => {
  router.push({ name: 'search', query: { q: query } })
}, 500)

// Handle input
const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  const query = target.value
  localQuery.value = query
  debouncedSearch(query)
}

// Handle image error
const handleImageError = (event: Event) => {
  const target = event.target as HTMLImageElement
  target.src = '/default-avatar.png'
}

// Get safe avatar URL
const getSafeAvatarUrl = (picture: string | null, firstName: string, lastName: string) => {
  try {
    return getAvatarUrl(picture, firstName, lastName)
  } catch {
    return '/default-avatar.png'
  }
}
</script>

<template>
  <div class="max-w-4xl mx-auto p-4">
    <!-- Search Header -->
    <h1 class="text-3xl font-bold text-gray-800 mb-6">Search</h1>

    <!-- Search Input -->
    <div class="relative mb-6">
      <input
        type="text"
        :value="localQuery"
        @input="handleInput"
        placeholder="Search for users or content..."
        class="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-full shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      />
      <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <svg class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </div>
    </div>

    <!-- Tabs -->
    <div class="border-b border-gray-200 mb-6">
      <nav class="-mb-px flex space-x-8">
        <button
          @click="activeTab = 'users'"
          :class="[
            'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2',
            activeTab === 'users'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
          ]"
        >
          <font-awesome-icon :icon="['fas', 'user']" class="text-blue-500" />
          Users
        </button>
        <button
          @click="activeTab = 'posts'"
          :class="[
            'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2',
            activeTab === 'posts'
              ? 'border-green-500 text-green-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
          ]"
        >
          <font-awesome-icon :icon="['fas', 'file-alt']" class="text-green-500" />
          Posts
        </button>
        <button
          @click="activeTab = 'groups'"
          :class="[
            'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2',
            activeTab === 'groups'
              ? 'border-purple-500 text-purple-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
          ]"
        >
          <font-awesome-icon :icon="['fas', 'users']" class="text-purple-500" />
          Groups
        </button>
      </nav>
    </div>

    <!-- Results -->
    <div>
      <!-- Users Tab -->
      <div v-if="activeTab === 'users'">
        <div v-if="isLoadingUsers" class="text-center py-8 text-gray-500">
          <div
            class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"
          ></div>
          <p class="mt-2">Searching for users...</p>
        </div>

        <div
          v-else-if="userError"
          class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700"
        >
          <p class="font-medium">Error loading users</p>
          <p class="text-sm">{{ userError }}</p>
        </div>

        <div v-else-if="userResults.length > 0" class="space-y-3">
          <div
            v-for="user in userResults"
            :key="user.id"
            class="bg-white rounded-lg border border-gray-200 hover:border-blue-300 transition-colors duration-200"
          >
            <router-link
              :to="{ name: 'profile', params: { username: user.username } }"
              class="flex items-center gap-4 p-4 hover:bg-blue-50 transition-colors duration-200"
            >
              <img
                :src="getSafeAvatarUrl(user.picture, user.first_name, user.last_name)"
                :alt="`${user.first_name} ${user.last_name}`"
                class="w-12 h-12 rounded-full object-cover bg-gray-200"
                @error="handleImageError"
              />
              <div class="flex-1 min-w-0">
                <h3 class="font-semibold text-gray-900 truncate">
                  {{ user.first_name }} {{ user.last_name }}
                </h3>
                <p class="text-sm text-gray-500 truncate">@{{ user.username }}</p>
              </div>
              <font-awesome-icon
                :icon="['fas', 'chevron-right']"
                class="text-blue-400 text-sm flex-shrink-0"
              />
            </router-link>
          </div>
        </div>

        <div v-else-if="localQuery" class="text-center py-8 text-gray-500">
          <p>No users found for "{{ localQuery }}"</p>
        </div>

        <div v-else class="text-center py-8 text-gray-400">
          <p>Enter a search term to find users</p>
        </div>
      </div>

      <!-- Posts Tab -->
      <div v-if="activeTab === 'posts'">
        <div v-if="isLoadingPosts" class="text-center py-8 text-gray-500">
          <div
            class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-green-500"
          ></div>
          <p class="mt-2">Searching for posts...</p>
        </div>

        <div
          v-else-if="postError"
          class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700"
        >
          <p class="font-medium">Error loading posts</p>
          <p class="text-sm">{{ postError }}</p>
        </div>

        <div v-else-if="postResults.length > 0" class="space-y-4">
          <PostItem v-for="post in postResults" :key="post.id" :post="post" />
        </div>

        <div v-else-if="localQuery" class="text-center py-8 text-gray-500">
          <p>No posts found for "{{ localQuery }}"</p>
        </div>

        <div v-else class="text-center py-8 text-gray-400">
          <p>Enter a search term to find posts</p>
        </div>
      </div>

      <!-- Groups Tab -->
      <div v-if="activeTab === 'groups'">
        <div v-if="isLoadingGroups" class="text-center py-8 text-gray-500">
          <div
            class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"
          ></div>
          <p class="mt-2">Searching for groups...</p>
        </div>

        <div
          v-else-if="groupError"
          class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700"
        >
          <p class="font-medium">Error loading groups</p>
          <p class="text-sm">{{ groupError }}</p>
        </div>

        <div v-else-if="groupResults.length > 0" class="space-y-3">
          <div
            v-for="group in groupResults"
            :key="group.id"
            class="bg-white rounded-lg border border-gray-200 hover:border-purple-300 transition-colors duration-200"
          >
            <router-link
              :to="{ name: 'group-detail', params: { slug: group.slug } }"
              class="block p-4 hover:bg-purple-50 transition-colors duration-200"
            >
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <h3 class="font-semibold text-gray-900 truncate">
                    {{ group.name || 'Unnamed Group' }}
                  </h3>
                  <p class="text-sm text-gray-500 truncate">{{ group.slug || 'No slug' }}</p>
                  <p v-if="group.description" class="text-sm text-gray-600 mt-1 line-clamp-2">
                    {{ group.description }}
                  </p>
                  <p class="text-xs text-gray-500 mt-2">{{ group.member_count || 0 }} members</p>
                </div>
                <font-awesome-icon
                  :icon="['fas', 'chevron-right']"
                  class="text-purple-400 text-sm flex-shrink-0 mt-2"
                />
              </div>
            </router-link>
          </div>
        </div>

        <div v-else-if="localQuery" class="text-center py-8 text-gray-500">
          <p>No groups found for "{{ localQuery }}"</p>
        </div>

        <div v-else class="text-center py-8 text-gray-400">
          <p>Enter a search term to find groups</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Smooth transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
