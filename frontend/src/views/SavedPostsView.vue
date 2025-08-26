<!-- C:\Users\Vinay\Project\frontend\src\views\SavedPostsView.vue -->
<!-- FINAL CORRECTED VERSION -->

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import { useFeedStore } from '@/stores/feed';
import { useInfiniteScroll } from '@/composables/useInfiniteScroll';
import PostItem from '@/components/PostItem.vue';

const feedStore = useFeedStore();
const loadMoreTrigger = ref<HTMLElement | null>(null);

// This is the single source of truth for the next page URL
const nextSavedPostUrl = computed(() => feedStore.savedPostsNextPageUrl);

// We pass it to our composable
useInfiniteScroll(loadMoreTrigger, feedStore.fetchNextPageOfSavedPosts, nextSavedPostUrl);

onMounted(() => {
  if (feedStore.savedPosts.length === 0) {
    feedStore.fetchSavedPosts();
  }
});
</script>

<template>
  <div class="space-y-4">
    <div class="bg-white rounded-lg shadow-sm p-4 md:p-6 border border-gray-200">
      <div class="flex items-center justify-between">
        <h1 class="text-xl md:text-2xl font-bold text-gray-800">Saved Posts</h1>
      </div>
    </div>

    <div v-if="feedStore.isLoadingSavedPosts && feedStore.savedPosts.length === 0" class="text-center text-gray-500 mt-12">
      Loading saved posts...
    </div>

    <div v-else-if="feedStore.savedPostsError" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md">
      Error: {{ feedStore.savedPostsError }}
    </div>

    <div v-else-if="feedStore.savedPosts.length === 0" class="text-center text-gray-500 mt-12 p-8 bg-white rounded-lg shadow-sm border border-gray-200">
      <p class="mb-4 text-lg">You haven't saved any posts yet.</p>
      <p>Click the bookmark icon on any post to save it for later!</p>
    </div>

    <div v-else class="space-y-4">
      <PostItem
        v-for="post in feedStore.savedPosts"
        :key="post.id"
        :post="post"
      />
      
      <!-- THIS IS THE FIX: We now use `nextSavedPostUrl` in the v-if -->
      <div v-if="nextSavedPostUrl" ref="loadMoreTrigger" class="h-10"></div>
      
      <div v-if="feedStore.isLoadingSavedPosts && feedStore.savedPosts.length > 0" class="text-center p-4 text-gray-500">
          Loading more posts...
      </div>

    </div>
  </div>
</template>