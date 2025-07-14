// C:\Users\Vinay\Project\frontend\src\views\FeedView.vue

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth';
// ---- [CHANGE 1] ---- Import onBeforeRouteLeave and remove onUnmounted from vue
import { onMounted, ref } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';
// --------------------
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

// --- Event Handlers ---
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

// --- Lifecycle Hooks ---
onMounted(async () => {
  eventBus.on('reset-feed-form', forceFormReset);
  
  await feedStore.fetchFeed();

  observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting && feedStore.mainFeedNextCursor && !feedStore.isLoadingMainFeed) {
      feedStore.fetchNextPageOfMainFeed();
    }
  }, {
    rootMargin: '200px',
  });

  if (loadMoreTrigger.value) {
    observer.observe(loadMoreTrigger.value);
  }
});

// ---- [CHANGE 2] ---- Replace onUnmounted with onBeforeRouteLeave and call the correct reset function
onBeforeRouteLeave((to, from) => {
  eventBus.off('reset-feed-form', forceFormReset);
  
  if (observer) {
    observer.disconnect();
  }

  // Use the new targeted reset function instead of the aggressive $reset()
  feedStore.resetMainFeedState();
  console.log('Leaving main feed view, state and observer cleaned up.');
});
// --------------------
</script>

<template>
  <div class="max-w-4xl mx-auto p-4">
    <h1 class="text-2xl font-bold text-gray-800">Welcome, {{ authStore.userDisplay }}!</h1>
    <h2 class="text-xl text-gray-600 mt-1 mb-6">Your Feed</h2>

    <CreatePostForm :key="createPostFormKey" />

    <!-- Initial Loading State -->
    <div v-if="feedStore.isLoadingMainFeed && feedStore.mainFeedPosts.length === 0" class="text-center p-8 text-gray-500">
      Loading feed...
    </div>

    <!-- Error State -->
    <div v-if="feedStore.mainFeedError" class="bg-red-100 border border-red-300 text-red-700 px-4 py-3 rounded-md text-center p-8" role="alert">
      Error loading feed: {{ feedStore.mainFeedError }}
    </div>

    <!-- Posts List -->
    <div v-if="feedStore.mainFeedPosts.length > 0" class="mt-4 flex flex-col gap-6">
      <PostItem 
        v-for="post in feedStore.mainFeedPosts" 
        :key="post.id" 
        :post="post"
        @report-content="handleOpenReportModal"
      />
    </div>

    <!-- Empty Feed State -->
    <div v-if="!feedStore.isLoadingMainFeed && feedStore.mainFeedPosts.length === 0 && !feedStore.mainFeedError" class="text-center p-8 text-gray-500">
      Your feed is empty. Follow some users or create a post!
    </div>

    <!-- Infinite Scroll Trigger & Loading Indicator -->
    <div v-if="feedStore.mainFeedNextCursor" ref="loadMoreTrigger" class="h-10"></div>
    <div v-if="feedStore.isLoadingMainFeed && feedStore.mainFeedPosts.length > 0" class="text-center p-4 text-gray-500">
      Loading more posts...
    </div>

    <!-- Report Modal -->
    <ReportFormModal 
      :is-open="isReportModalOpen" 
      @close="isReportModalOpen = false" 
      @submit="handleReportSubmit"
    />
  </div>
</template>