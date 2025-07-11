// C:\Users\Vinay\Project\frontend\src\views\FeedView.vue

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth';
import { onMounted, onUnmounted, ref } from 'vue';
import { useFeedStore } from '@/stores/feed';
import { useModerationStore } from '@/stores/moderation';
import { storeToRefs } from 'pinia';

import CreatePostForm from '@/components/CreatePostForm.vue';
import PostItem from '@/components/PostItem.vue';
import ReportFormModal from '@/components/ReportFormModal.vue';
import eventBus from '@/services/eventBus';

const authStore = useAuthStore();
const feedStore = useFeedStore();
const moderationStore = useModerationStore();

const { submissionError } = storeToRefs(moderationStore);
const createPostFormKey = ref(0);

const isReportModalOpen = ref(false);
const contentToReport = ref<{ content_type_id: number; object_id: number; } | null>(null);

const loadMoreTrigger = ref<HTMLElement | null>(null);
let observer: IntersectionObserver | null = null;

// --- Event Handlers (Unchanged) ---
function forceFormReset() {
  createPostFormKey.value++;
}

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

// --- Lifecycle Hooks (THIS IS THE FIX) ---
onMounted(async () => {
  eventBus.on('reset-feed-form', forceFormReset);
  
  // 1. AWAIT the first page to load. This pauses execution here until the
  //    network request is done and the store's state (like hasNextPage) is updated.
  await feedStore.fetchFeed(1);

  // 2. Now that we know for sure if there is a next page, set up the observer.
  observer = new IntersectionObserver((entries) => {
    // The check is the same, but now it's guaranteed to have the correct state.
    if (entries[0].isIntersecting && feedStore.hasNextPage) {
      feedStore.fetchNextPageOfFeed();
    }
  }, {
    rootMargin: '200px', // Start loading when 200px away
  });

  // 3. If the trigger element exists, start observing it.
  if (loadMoreTrigger.value) {
    observer.observe(loadMoreTrigger.value);
  }
});

onUnmounted(() => {
  eventBus.off('reset-feed-form', forceFormReset);
  // Clean up the observer when the component is destroyed to prevent memory leaks.
  if (observer) {
    observer.disconnect();
  }
});
</script>

<template>
  <div class="max-w-4xl mx-auto p-4">
    <h1 class="text-2xl font-bold text-gray-800">Welcome, {{ authStore.userDisplay }}!</h1>
    <h2 class="text-xl text-gray-600 mt-1 mb-6">Your Feed</h2>

    <CreatePostForm :key="createPostFormKey" />

    <!-- Initial Loading State (for the very first load) -->
    <div v-if="feedStore.isLoading && feedStore.posts.length === 0" class="text-center p-8 text-gray-500">
      Loading feed...
    </div>

    <!-- Error State -->
    <div v-if="feedStore.error" class="bg-red-100 border border-red-300 text-red-700 px-4 py-3 rounded-md text-center p-8" role="alert">
      Error loading feed: {{ feedStore.error }}
    </div>

    <!-- Posts List -->
    <div v-if="feedStore.posts.length > 0" class="mt-4 flex flex-col gap-6">
      <PostItem 
        v-for="post in feedStore.posts" 
        :key="post.id" 
        :post="post"
        @report-content="handleOpenReportModal"
      />
    </div>

    <!-- Empty Feed State -->
    <div v-if="!feedStore.isLoading && feedStore.posts.length === 0 && !feedStore.error" class="text-center p-8 text-gray-500">
      Your feed is empty. Follow some users or create a post!
    </div>

    <!-- --- REMOVED PAGINATION BUTTONS --- -->

    <!-- --- NEW INFINITE SCROLL TRIGGER & LOADING INDICATOR --- -->
    <div ref="loadMoreTrigger" class="h-10"></div>
    <div v-if="feedStore.isLoading && feedStore.posts.length > 0" class="text-center p-4 text-gray-500">
      Loading more posts...
    </div>
    <!-- --- END OF NEW SECTION --- -->

    <!-- Report Modal (Unchanged) -->
    <ReportFormModal 
      :is-open="isReportModalOpen" 
      @close="isReportModalOpen = false" 
      @submit="handleReportSubmit"
    />
  </div>
</template>