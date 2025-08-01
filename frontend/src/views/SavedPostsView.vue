<script setup lang="ts">
import { onMounted } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';
import { useFeedStore } from '@/stores/feed';
import PostItem from '@/components/PostItem.vue';

const feedStore = useFeedStore();

async function fetchMoreSavedPosts() {
  await feedStore.fetchNextPageOfSavedPosts();
}

// Lifecycle Hooks
onMounted(() => {
  // Only fetch if the list is empty to prevent re-fetching on navigation
  if (feedStore.savedPosts.length === 0) {
    feedStore.fetchSavedPosts();
  }
});

onBeforeRouteLeave((to, from) => {
  feedStore.resetSavedPostsState();
  console.log('Leaving saved posts view, state cleaned up.');
});
</script>

<template>
  <div class="space-y-6">
    <!-- Header card for the title -->
    <div class="bg-white rounded-lg shadow-sm p-4 md:p-6 border border-gray-200">
      <div class="flex items-center justify-between">
        <h1 class="text-xl md:text-2xl font-bold text-gray-800">Saved Posts</h1>
      </div>
    </div>

    <!-- Content Area -->
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

    <div v-else class="space-y-6">
      <PostItem
        v-for="post in feedStore.savedPosts"
        :key="post.id"
        :post="post"
      />
      
      <div v-if="feedStore.savedPostsNextPageUrl" class="flex justify-center py-4">
        <button 
          @click="fetchMoreSavedPosts" 
          :disabled="feedStore.isLoadingSavedPosts"
          class="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-full shadow-md transition-transform transform hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ feedStore.isLoadingSavedPosts ? 'Loading...' : 'Load More' }}
        </button>
      </div>
    </div>

    <!-- The ReportFormModal has been removed from here. PostItem now handles it. -->
    
  </div>
</template>