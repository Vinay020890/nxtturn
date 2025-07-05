// C:\Users\Vinay\Project\frontend\src\views\FeedView.vue

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth';
import { onMounted, onUnmounted, ref } from 'vue';
import { useFeedStore } from '@/stores/feed';
import CreatePostForm from '@/components/CreatePostForm.vue';
import PostItem from '@/components/PostItem.vue';
import eventBus from '@/services/eventBus';

const authStore = useAuthStore();
const feedStore = useFeedStore();

// This ref will act as our manual key.
const createPostFormKey = ref(0); 

// This function will be called by the event bus.
// Incrementing the key tells Vue to destroy the old component and create a new one.
function forceFormReset() {
  console.log("Resetting form via event bus...");
  createPostFormKey.value++;
}

onMounted(() => {
  console.log("FeedView: Component mounted, fetching feed...");
  feedStore.fetchFeed();
  // Listen for the event from the header
  eventBus.on('reset-feed-form', forceFormReset);
});

// It's crucial to clean up the listener when the component is destroyed
onUnmounted(() => {
  eventBus.off('reset-feed-form', forceFormReset);
});

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

    <!-- The key is now bound to our manual ref, which is updated by the event bus -->
    <CreatePostForm :key="createPostFormKey" />

    <div v-if="feedStore.isLoading && feedStore.posts.length === 0" class="text-center p-8 text-gray-500">
      Loading feed...
    </div>

    <div v-if="feedStore.error" class="bg-red-100 border border-red-300 text-red-700 px-4 py-3 rounded-md text-center p-8" role="alert">
      Error loading feed: {{ feedStore.error }}
    </div>

    <div v-if="!feedStore.isLoading || feedStore.posts.length > 0" class="mt-4 flex flex-col gap-6">
      <PostItem v-for="post in feedStore.posts" :key="post.id" :post="post" />
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
  </div>
</template>