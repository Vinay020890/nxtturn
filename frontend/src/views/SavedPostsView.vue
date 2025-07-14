// C:\Users\Vinay\Project\frontend\src\views\SavedPostsView.vue

<script setup lang="ts">
// ---- [CHANGE 1] ---- Import onBeforeRouteLeave, remove onUnmounted
import { ref, onMounted } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';
// --------------------
import { useFeedStore } from '@/stores/feed';
import PostItem from '@/components/PostItem.vue';

const feedStore = useFeedStore();

// Reporting state can remain for future use if needed
const showReportModal = ref(false);
const reportPayload = ref({ content_type: '', object_id: 0, content_type_id: 0 });

function prepareReportModal(payload: { content_type: string, object_id: number, content_type_id: number }) {
  reportPayload.value = payload;
  showReportModal.value = true;
}

async function fetchMoreSavedPosts() {
  await feedStore.fetchNextPageOfSavedPosts();
}

// Lifecycle Hooks
onMounted(() => {
  // ---- [CHANGE 2] ---- The manual splice is no longer needed
  // feedStore.savedPosts.splice(0); 
  // --------------------
  feedStore.fetchSavedPosts();
});

// ---- [CHANGE 3] ---- Replace onUnmounted with onBeforeRouteLeave
onBeforeRouteLeave((to, from) => {
  // Call the new, targeted reset action
  feedStore.resetSavedPostsState();
  console.log('Leaving saved posts view, state cleaned up.');
});
// --------------------
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

    <!-- Report Modal can be added here in the future if needed -->
  </div>
</template>