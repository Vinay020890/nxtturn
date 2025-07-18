// C:\Users\Vinay\Project\frontend\src\views\SavedPostsView.vue

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';
import { useFeedStore } from '@/stores/feed';
import PostItem from '@/components/PostItem.vue';

// --- ADDED FOR REPORTING ---
import { storeToRefs } from 'pinia';
import { useModerationStore } from '@/stores/moderation';
import ReportFormModal from '@/components/ReportFormModal.vue';
// --- END ADDED ---

const feedStore = useFeedStore();
// --- ADDED FOR REPORTING ---
const moderationStore = useModerationStore();
const { submissionError } = storeToRefs(moderationStore);
// --- END ADDED ---

// --- REPLACED old placeholder logic with new, functional logic ---
const isReportModalOpen = ref(false);
const contentToReport = ref<{ content_type_id: number; object_id: number; } | null>(null);

function handleOpenReportModal(payload: { content_type: string, content_type_id: number, object_id: number }) {
  contentToReport.value = {
    content_type_id: payload.content_type_id,
    object_id: payload.object_id,
  };
  isReportModalOpen.value = true;
}

async function handleReportSubmit(payload: { reason: string; details: string }) {
  if (!contentToReport.value) return;
  const success = await moderationStore.submitReport({
    ct_id: contentToReport.value.content_type_id,
    obj_id: contentToReport.value.object_id,
    reason: payload.reason,
    details: payload.details,
  });
  if (success) {
    isReportModalOpen.value = false;
    contentToReport.value = null;
    alert('Thank you for your report. It has been submitted for review.');
  } else {
    alert(`Failed to submit report: ${submissionError.value || 'An unknown error occurred.'}`);
  }
}
// --- END REPLACED ---

async function fetchMoreSavedPosts() {
  await feedStore.fetchNextPageOfSavedPosts();
}

// Lifecycle Hooks
onMounted(() => {
  feedStore.fetchSavedPosts();
});

onBeforeRouteLeave((to, from) => {
  feedStore.resetSavedPostsState();
  console.log('Leaving saved posts view, state cleaned up.');
});
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
        @report-content="handleOpenReportModal"
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

    <!-- REPLACED MODAL COMMENT WITH ACTUAL COMPONENT -->
    <ReportFormModal 
      :is-open="isReportModalOpen" 
      @close="isReportModalOpen = false" 
      @submit="handleReportSubmit"
    />
  </div>
</template>