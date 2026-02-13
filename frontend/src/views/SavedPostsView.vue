<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed } from 'vue'
import { useFeedStore } from '@/stores/feed'
import { usePostsStore } from '@/stores/posts'
import { useInfiniteScroll } from '@/composables/useInfiniteScroll'
import PostItem from '@/components/PostItem.vue'
import eventBus from '@/services/eventBus'
import { BookmarkIcon } from '@heroicons/vue/24/solid'

const feedStore = useFeedStore()
const postsStore = usePostsStore()
const loadMoreTrigger = ref<HTMLElement | null>(null)

const savedPosts = computed(() => postsStore.getPostsByIds(feedStore.savedPostIds))
const nextSavedPostUrl = computed(() => feedStore.savedPostsNextPageUrl)

useInfiniteScroll(loadMoreTrigger, feedStore.fetchNextPageOfSavedPosts, nextSavedPostUrl)

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(() => {
  if (!feedStore.hasFetchedSavedPosts) {
    feedStore.fetchSavedPosts()
  }
  eventBus.on('scroll-saved-posts-to-top', scrollToTop)
})

onUnmounted(() => {
  eventBus.off('scroll-saved-posts-to-top', scrollToTop)
})
</script>

<template>
  <div class="space-y-4">
    <!-- Enhanced Header Box with Heroicons -->
    <div class="saved-posts-header">
      <div class="header-content">
        <!-- Heroicons Bookmark Icon -->
        <BookmarkIcon class="header-icon" />
        <div class="header-text">
          <h1 class="header-title">Saved Posts</h1>
        </div>
      </div>
    </div>

    <div
      v-if="feedStore.isLoadingSavedPosts && savedPosts.length === 0"
      class="text-center text-gray-500 mt-12"
    >
      Loading saved posts...
    </div>

    <div
      v-else-if="feedStore.savedPostsError"
      class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md"
    >
      Error: {{ feedStore.savedPostsError }}
    </div>

    <div
      v-else-if="savedPosts.length === 0"
      class="text-center text-gray-500 mt-12 p-8 bg-white rounded-lg shadow-sm border border-gray-200"
    >
      <p class="mb-4 text-lg">You haven't saved any posts yet.</p>
      <p>Click the bookmark icon on any post to save it for later!</p>
    </div>

    <div v-else class="space-y-4">
      <PostItem v-for="post in savedPosts" :key="post.id" :post="post" />

      <div v-if="nextSavedPostUrl" ref="loadMoreTrigger" class="h-10"></div>

      <div
        v-if="feedStore.isLoadingSavedPosts && savedPosts.length > 0"
        class="text-center p-4 text-gray-500"
      >
        Loading more posts...
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Scoped styles ensure these rules only apply to this component */
.saved-posts-header {
  background: linear-gradient(135deg, #ea6687 0%, #a24ba2 100%);
  border-radius: 0.75rem;
  padding: 1.5rem;
  color: white;
  box-shadow: 0 10px 25px -5px rgba(102, 126, 234, 0.3);
  border: none;
  margin-bottom: 1rem;
  transition:
    transform 0.3s ease,
    box-shadow 0.3s ease;
}

.saved-posts-header:hover {
  transform: translateY(-2px);
  box-shadow: 0 15px 30px -10px rgba(102, 126, 234, 0.4);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

/* Heroicons styling */
.header-icon {
  width: 2.5rem;
  height: 2.5rem;
  color: #ffffff; /* Gold color */
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
  flex-shrink: 0;
  animation: gentlePulse 3s infinite ease-in-out;
}

@keyframes gentlePulse {
  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.9;
    transform: scale(1.05);
  }
}

.header-text {
  flex-grow: 1;
}

.header-title {
  font-size: 1.75rem;
  font-weight: 800;
  margin-bottom: 0.25rem;
  letter-spacing: -0.025em;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-subtitle {
  font-size: 0.95rem;
  opacity: 0.95;
  font-weight: 300;
  margin: 0;
  line-height: 1.5;
}

/* Responsive adjustments */
@media (max-width: 640px) {
  .header-content {
    flex-direction: column;
    text-align: center;
    gap: 0.75rem;
  }

  .header-icon {
    width: 2rem;
    height: 2rem;
  }

  .header-title {
    font-size: 1.5rem;
  }

  .saved-posts-header {
    padding: 1.25rem;
  }
}

/* Empty state enhancement */
.empty-state-container {
  background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
  border: 2px dashed #d1d5db;
  border-radius: 0.75rem;
}

.empty-state-container p {
  color: #6b7280;
}
</style>
