<script setup lang="ts">
import { useAuthStore } from '@/stores/auth';
import { onMounted, onUnmounted, ref } from 'vue';
import { useFeedStore } from '@/stores/feed';
import { useModerationStore } from '@/stores/moderation'; // <-- 1. IMPORT the new store
import { storeToRefs } from 'pinia'; // <-- IMPORT storeToRefs

import CreatePostForm from '@/components/CreatePostForm.vue';
import PostItem from '@/components/PostItem.vue';
import ReportFormModal from '@/components/ReportFormModal.vue'; // <-- 2. IMPORT the new modal
import eventBus from '@/services/eventBus';

const authStore = useAuthStore();
const feedStore = useFeedStore();
const moderationStore = useModerationStore(); // <-- 3. INITIALIZE the new store

const { submissionError } = storeToRefs(moderationStore);

// --- State for CreatePostForm reset ---
const createPostFormKey = ref(0); 

// --- 4. NEW STATE for the reporting modal ---
const isReportModalOpen = ref(false);
const contentToReport = ref<{ content_type_id: number; object_id: number; } | null>(null);


// --- Event Handlers ---
function forceFormReset() {
  console.log("Resetting form via event bus...");
  createPostFormKey.value++;
}

// --- 5. NEW HANDLER to open the report modal ---
function handleOpenReportModal(payload: { content_type: string, content_type_id: number, object_id: number }) {
  console.log('Reporting content:', payload);
  contentToReport.value = {
    content_type_id: payload.content_type_id,
    object_id: payload.object_id,
  };
  isReportModalOpen.value = true;
}

// --- 6. NEW HANDLER to submit the report ---
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
    // The error message from the store will be displayed inside the modal,
    // but we can also alert it to make sure the user sees it.
    alert(`Failed to submit report: ${submissionError.value || 'An unknown error occurred.'}`);
  }
}

// --- Lifecycle Hooks ---
onMounted(() => {
  console.log("FeedView: Component mounted, fetching feed...");
  feedStore.fetchFeed();
  eventBus.on('reset-feed-form', forceFormReset);
});

onUnmounted(() => {
  eventBus.off('reset-feed-form', forceFormReset);
});


// --- Pagination Logic (Unchanged) ---
function fetchPreviousPage() {
  if (feedStore.currentPage > 1) {
    feedStore.fetchFeed(feedStore.currentPage - 1);
  }
}

function fetchNextPage() {
  if (feedStore.hasNextPage) {
    feedStore.fetchFeed(feedStore.currentPage + 1);
  }
}
</script>

<template>
  <div class="max-w-4xl mx-auto p-4">
    <h1 class="text-2xl font-bold text-gray-800">Welcome, {{ authStore.userDisplay }}!</h1>
    <h2 class="text-xl text-gray-600 mt-1 mb-6">Your Feed</h2>

    <CreatePostForm :key="createPostFormKey" />

    <div v-if="feedStore.isLoading && feedStore.posts.length === 0" class="text-center p-8 text-gray-500">
      Loading feed...
    </div>

    <div v-if="feedStore.error" class="bg-red-100 border border-red-300 text-red-700 px-4 py-3 rounded-md text-center p-8" role="alert">
      Error loading feed: {{ feedStore.error }}
    </div>

    <div v-if="!feedStore.isLoading || feedStore.posts.length > 0" class="mt-4 flex flex-col gap-6">
      <!-- 7. LISTEN for the 'report-content' event from PostItem -->
      <PostItem 
        v-for="post in feedStore.posts" 
        :key="post.id" 
        :post="post"
        @report-content="handleOpenReportModal"
      />
      <div v-if="!feedStore.isLoading && feedStore.posts.length === 0 && !feedStore.error" class="text-center p-8 text-gray-500">
        Your feed is empty. Follow some users or create a post!
      </div>
    </div>

    <div class="mt-8 text-center">
        <button 
          :disabled="feedStore.currentPage <= 1" 
          @click="fetchPreviousPage"
          class="py-2 px-4 mx-2 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Previous
        </button>
        <span class="mx-4 text-gray-600">Page {{ feedStore.currentPage }} of {{ feedStore.totalPages }}</span>
        <button 
          :disabled="!feedStore.hasNextPage" 
          @click="fetchNextPage"
          class="py-2 px-4 mx-2 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Next
        </button>
    </div>

    <!-- 8. ADD the modal component to the template -->
    <ReportFormModal 
      :is-open="isReportModalOpen" 
      @close="isReportModalOpen = false" 
      @submit="handleReportSubmit"
    />

  </div>
</template>