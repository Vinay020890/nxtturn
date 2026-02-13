<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
    <!-- Top Navigation Bar -->
    <TopNavBar />

    <!-- Main content with padding to account for TopNavBar -->
    <div class="pt-14">
      <!-- Three-column layout: Left sidebar (hidden on mobile), Middle content, Right sidebar (hidden on mobile) -->
      <div class="flex justify-center">
        <!-- Left empty space for alignment (hidden on mobile) -->
        <div class="hidden lg:block w-64 xl:w-72"></div>

        <!-- Middle content section (very slightly decreased) -->
        <div class="w-full max-w-[620px] px-4 py-6">
          <!-- Loading State -->
          <div v-if="isLoading && posts.length === 0" class="text-center p-10 text-gray-500">
            <div
              class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mb-3"
            ></div>
            <p class="text-gray-600">Loading posts...</p>
          </div>

          <!-- Error State -->
          <div
            v-else-if="error"
            class="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 rounded-lg mb-4 shadow-sm"
          >
            <div class="flex">
              <svg class="h-5 w-5 text-red-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fill-rule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clip-rule="evenodd"
                />
              </svg>
              <p>{{ error }}</p>
            </div>
          </div>

          <!-- Posts List -->
          <div v-else-if="posts.length > 0" class="space-y-5">
            <!-- Use computed posts instead of reactive ref -->
            <PostItem v-for="post in computedPosts" :key="post.id" :post="post" />

            <!-- Load More Trigger -->
            <div v-if="nextPageUrl" ref="loadMoreTrigger" class="h-10"></div>

            <!-- Loading More Indicator -->
            <div v-if="isLoading && posts.length > 0" class="text-center p-6">
              <div
                class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mb-2"
              ></div>
              <p class="text-gray-500 text-sm">Loading more posts...</p>
            </div>
          </div>

          <!-- Empty State -->
          <div v-else class="bg-white rounded-xl shadow-sm p-8 sm:p-10 text-center mt-8">
            <div class="mb-4">
              <svg
                class="h-16 w-16 text-gray-300 mx-auto"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="1.5"
                  d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z"
                />
              </svg>
            </div>
            <h3 class="text-lg font-medium text-gray-700 mb-2">No posts yet</h3>
            <p class="text-gray-500">This user hasn't posted anything yet.</p>
          </div>
        </div>

        <!-- Right empty space for alignment (hidden on mobile) -->
        <div class="hidden lg:block w-64 xl:w-72"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick, computed } from 'vue'
import { useRoute } from 'vue-router'
import { usePostsStore } from '@/stores/posts'
import { useProfileStore } from '@/stores/profile'
import PostItem from '@/components/PostItem.vue'
import TopNavBar from '@/components/layout/TopNavBar.vue' // Import TopNavBar
import { useInfiniteScroll } from '@/composables/useInfiniteScroll'

const route = useRoute()
const postsStore = usePostsStore()
const profileStore = useProfileStore()

const posts = ref<any[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)
const loadMoreTrigger = ref<HTMLElement | null>(null)
const nextPageUrl = ref<string | null>(null)

// Get the username from route params
const username = route.params.username as string

// Create computed property for posts to ensure reactivity
const computedPosts = computed(() => {
  if (!username) return []
  const postIds = profileStore.postIdsByUsername[username] || []
  return postsStore.getPostsByIds(postIds)
})

// Function to load user posts
async function loadUserPosts() {
  if (!username) {
    error.value = 'No username provided'
    return
  }

  isLoading.value = true
  error.value = null

  try {
    // Refresh user posts to get the latest
    await profileStore.refreshUserPosts(username)

    // Get post IDs for this user
    const postIds = profileStore.postIdsByUsername[username] || []

    // Get actual post objects from posts store
    posts.value = postsStore.getPostsByIds(postIds)

    // Get next page URL for infinite scroll
    nextPageUrl.value = profileStore.nextPageUrlByUsername[username]
  } catch (err: any) {
    error.value = err.message || 'Failed to load posts'
    console.error('Error loading user posts:', err)
  } finally {
    isLoading.value = false
  }
}

// Function to load more posts
async function loadMorePosts() {
  if (!nextPageUrl.value || isLoading.value) return

  isLoading.value = true
  try {
    await profileStore.fetchNextPageOfUserPosts(username)

    // Update posts list
    const postIds = profileStore.postIdsByUsername[username] || []
    posts.value = postsStore.getPostsByIds(postIds)

    // Update next page URL
    nextPageUrl.value = profileStore.nextPageUrlByUsername[username]
  } catch (err: any) {
    console.error('Error loading more posts:', err)
  } finally {
    isLoading.value = false
  }
}

// Set up infinite scroll
useInfiniteScroll(loadMoreTrigger, loadMorePosts, nextPageUrl)

// Load posts on mount
onMounted(() => {
  loadUserPosts()
})

// Watch for username changes
watch(
  () => route.params.username,
  (newUsername) => {
    if (newUsername) {
      posts.value = []
      loadUserPosts()
    }
  },
)

// Watch for posts store updates to refresh the list
watch(
  () => postsStore.posts, // Watch the entire posts store
  () => {
    // When posts store updates, refresh our posts list
    if (username) {
      const postIds = profileStore.postIdsByUsername[username] || []
      posts.value = postsStore.getPostsByIds(postIds)
    }
  },
  { deep: true },
)
</script>

<style scoped>
/* Fixed header styling */
.fixed {
  position: fixed;
}

/* Smooth scrolling for infinite scroll */
html {
  scroll-behavior: smooth;
}

/* Custom gradient background */
.bg-gradient-to-br {
  background-image: linear-gradient(to bottom right, var(--tw-gradient-stops));
}

.from-gray-50 {
  --tw-gradient-from: #f9fafb;
}

.to-gray-100 {
  --tw-gradient-to: #f3f4f6;
}

/* Ensure header has proper z-index */
.z-50 {
  z-index: 50;
}

/* Truncate long usernames */
.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.min-w-0 {
  min-width: 0;
}

/* Make sure content doesn't get hidden behind fixed header */
.pt-16 {
  padding-top: 4rem; /* Adjust based on your header height */
}

/* Responsive adjustments */
@media (max-width: 1024px) {
  .lg\:block {
    display: none !important;
  }

  .w-full {
    width: 100%;
  }
}

@media (min-width: 1024px) {
  .flex.justify-center {
    justify-content: center;
  }
}
</style>
