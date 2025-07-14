<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'; // 'watch' is no longer needed
import { useFeedStore } from '@/stores/feed';
import PostItem from '@/components/PostItem.vue';

// Stores
const feedStore = useFeedStore();

// State for reporting (keeping them for future potential re-introduction of ReportModal if desired)
const showReportModal = ref(false);
const reportPayload = ref({ content_type: '', object_id: 0, content_type_id: 0 });

// Methods
function prepareReportModal(payload: { content_type: string, object_id: number, content_type_id: number }) {
  reportPayload.value = payload;
  showReportModal.value = true;
}

function handleReportSuccess() {
  showReportModal.value = false;
  // Optionally, show a toast notification or some other feedback
}

async function fetchMoreSavedPosts() {
  await feedStore.fetchNextPageOfSavedPosts();
}

// Lifecycle Hooks
onMounted(() => {
  // Clear any existing posts and fetch the first page of saved posts
  feedStore.savedPosts.splice(0); // Ensure the list is empty before fetching
  feedStore.fetchSavedPosts();
});

onUnmounted(() => {
  // Clear the saved posts data when leaving the view
  feedStore.$reset(); // Resets all feed store state including savedPosts
});

// Removed: Intersection Observer related state (observerTarget, observer) and its setup/watch logic
// No need for 'watch' import as it's not used here anymore.
</script>

<template>
  <div class="max-w-3xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
    <h1 class="text-3xl font-bold text-gray-900 mb-6">Saved Posts</h1>
    
    <div v-if="feedStore.isLoadingSavedPosts && feedStore.savedPosts.length === 0" class="text-center text-gray-500 mt-12">
      Loading saved posts...
    </div>

    <div v-else-if="feedStore.savedPostsError" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md mx-auto max-w-lg">
      Error: {{ feedStore.savedPostsError }}
    </div>

    <div v-else-if="feedStore.savedPosts.length === 0" class="text-center text-gray-500 mt-12 p-8 bg-white rounded-lg shadow-sm">
      <p class="mb-4 text-lg">You haven't saved any posts yet.</p>
      <p>Click the bookmark icon on any post to save it for later!</p>
    </div>

    <div v-else class="space-y-6">
      <PostItem
        v-for="post in feedStore.savedPosts"
        :key="post.id"
        :post="post"
        @report-content="prepareReportModal"
      />
      
      <!-- "Load More" button for pagination -->
      <!-- MODIFIED: Container uses flex and justify-end for right alignment -->
      <div v-if="feedStore.savedPostsNextPageUrl" class="flex justify-end py-4">
        <button 
          @click="fetchMoreSavedPosts" 
          :disabled="feedStore.isLoadingSavedPosts"
          class="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2.5 px-6 rounded-full shadow-lg transition-all duration-200 ease-in-out transform hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ feedStore.isLoadingSavedPosts ? 'Loading...' : 'Load More' }}
        </button>
      </div>

    </div>

    <!-- Report Modal is not included here -->
  </div>
</template>