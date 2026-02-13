<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed } from 'vue'
import { useFeedStore } from '@/stores/feed'
import { usePostsStore } from '@/stores/posts'
import { useInfiniteScroll } from '@/composables/useInfiniteScroll'
import CreatePostForm from '@/components/CreatePostForm.vue'
import PostItem from '@/components/PostItem.vue'
import eventBus from '@/services/eventBus'
import {
  ArrowUpIcon,
  ExclamationTriangleIcon,
  ChatBubbleLeftRightIcon,
  UserGroupIcon,
  SparklesIcon,
  ArrowPathIcon,
} from '@heroicons/vue/24/solid'
import PostItemSkeleton from '@/components/PostItemSkeleton.vue'

const feedStore = useFeedStore()
const postsStore = usePostsStore()

const createPostFormKey = ref(0)
const loadMoreTrigger = ref<HTMLElement | null>(null)

const mainFeedPosts = computed(() => {
  return postsStore.getPostsByIds(feedStore.mainFeedPostIds)
})

const nextFeedPageUrl = computed(() => feedStore.mainFeedNextCursor)
useInfiniteScroll(loadMoreTrigger, feedStore.fetchNextPageOfMainFeed, nextFeedPageUrl)

function forceFormReset() {
  createPostFormKey.value++
}

function scrollToTop() {
  window.scrollTo({
    top: 0,
    behavior: 'smooth',
  })
}

function handleShowNewPosts() {
  feedStore.showNewPosts()
  scrollToTop()
}

onMounted(() => {
  eventBus.on('reset-feed-form', forceFormReset)
  eventBus.on('scroll-to-top', scrollToTop)

  feedStore.refreshMainFeed()
})

onUnmounted(() => {
  eventBus.off('reset-feed-form', forceFormReset)
  eventBus.off('scroll-to-top', scrollToTop)
})
</script>

<template>
  <div class="max-w-4xl mx-auto min-h-[calc(100vh-12rem)]">
    <div class="space-y-3">
      <CreatePostForm :key="createPostFormKey" />

      <!-- New Posts Notification - Floating Overlap with lower stop point -->
      <div
        v-if="feedStore.newPostIdsFromRefresh.length > 0"
        class="sticky top-24 z-30 pointer-events-none"
        :class="feedStore.newPostIdsFromRefresh.length === 0 ? 'hidden' : ''"
        style="height: 0"
      >
        <div class="absolute left-1/2 transform -translate-x-1/2 -translate-y-1/2">
          <button
            @click="handleShowNewPosts"
            class="flex items-center gap-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold px-3 py-1 rounded-full shadow-xl hover:shadow-2xl hover:scale-105 transition-all duration-300 transform pointer-events-auto"
          >
            <SparklesIcon class="w-5 h-5" />
            Show {{ feedStore.newPostIdsFromRefresh.length }} new post(s)
            <ArrowUpIcon class="w-5 h-5 ml-1" />
          </button>
        </div>
      </div>

      <div v-if="feedStore.isLoadingMainFeed && mainFeedPosts.length === 0" class="space-y-6">
        <PostItemSkeleton v-for="n in 3" :key="n" />
      </div>

      <!-- Error Message -->
      <div
        v-if="feedStore.mainFeedError"
        class="bg-gradient-to-r from-red-50 to-orange-50 border-l-4 border-red-500 rounded-r-lg p-6 shadow-md"
        role="alert"
      >
        <div class="flex items-center gap-3">
          <div class="flex-shrink-0">
            <div class="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
              <ExclamationTriangleIcon class="w-6 h-6 text-red-600" />
            </div>
          </div>
          <div>
            <p class="text-lg font-semibold text-red-800">
              Error loading feed: {{ feedStore.mainFeedError }}
            </p>
            <button
              @click="feedStore.refreshMainFeed"
              class="mt-2 inline-flex items-center gap-2 text-sm font-medium text-red-700 hover:text-red-800 transition"
            >
              <ArrowPathIcon class="w-4 h-4" />
              Try again
            </button>
          </div>
        </div>
      </div>

      <div v-if="mainFeedPosts.length > 0" class="space-y-4">
        <PostItem v-for="post in mainFeedPosts" :key="post.id" :post="post" />
      </div>

      <!-- Empty Feed Message -->
      <div
        v-if="
          !feedStore.isLoadingMainFeed && mainFeedPosts.length === 0 && !feedStore.mainFeedError
        "
        class="text-center py-12 px-4"
        data-cy="empty-feed-message"
      >
        <div class="max-w-md mx-auto">
          <div
            class="w-24 h-24 mx-auto bg-gradient-to-br from-blue-100 to-purple-100 rounded-full flex items-center justify-center mb-6"
          >
            <ChatBubbleLeftRightIcon class="w-12 h-12 text-gray-400" />
          </div>
          <h3 class="text-2xl font-bold text-gray-800 mb-2">Your feed is empty</h3>
          <p class="text-gray-600 mb-6">Follow some users or create a post!</p>
          <div class="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              @click="eventBus.emit('scroll-to-top')"
              class="px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white font-medium rounded-lg hover:from-blue-600 hover:to-blue-700 transition shadow-md hover:shadow-lg"
            >
              Create a post
            </button>
            <button
              class="px-6 py-3 bg-gradient-to-r from-gray-100 to-gray-200 text-gray-800 font-medium rounded-lg hover:from-gray-200 hover:to-gray-300 transition shadow-md hover:shadow-lg flex items-center justify-center gap-2"
            >
              <UserGroupIcon class="w-5 h-5" />
              Explore users
            </button>
          </div>
        </div>
      </div>

      <div v-if="feedStore.mainFeedNextCursor" ref="loadMoreTrigger" class="h-10"></div>

      <!-- Loading More Posts -->
      <div v-if="feedStore.isLoadingMainFeed && mainFeedPosts.length > 0" class="text-center py-8">
        <div class="inline-flex flex-col items-center gap-3">
          <div class="relative">
            <div class="w-12 h-12 border-4 border-blue-100 rounded-full"></div>
            <div
              class="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full absolute top-0 left-0 animate-spin"
            ></div>
          </div>
          <div>
            <p class="text-gray-700 font-medium">Loading more posts...</p>
          </div>
        </div>
      </div>

      <!-- Add extra spacing at the bottom for mobile -->
      <div class="h-4 md:h-0"></div>
    </div>
  </div>
</template>
