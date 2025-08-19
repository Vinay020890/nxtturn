<script setup lang="ts">
import { watch, onUnmounted } from 'vue'; // <-- 1. Import 'onUnmounted'
import { useRoute } from 'vue-router';
import { useFeedStore } from '@/stores/feed';
import { storeToRefs } from 'pinia';
import PostItem from '@/components/PostItem.vue';

const route = useRoute();
const feedStore = useFeedStore();

const { singlePost, isLoadingSinglePost, singlePostError } = storeToRefs(feedStore);

// This watcher is the single source of truth for loading data for this page.
watch(
  () => route.params.postId,
  (newPostId) => {
    if (newPostId) {
      feedStore.ensureFullPostData(Number(newPostId));
    }
  },
  { immediate: true }
);

// --- THIS IS THE FIX ---
// 2. Add the onUnmounted hook to clean up the store state.
// This runs automatically whenever the user navigates away from this page.
onUnmounted(() => {
  feedStore.singlePost = null;
  feedStore.singlePostError = null;
  console.log('SinglePostView unmounted. Cleared singlePost state.');
});
// --- END OF FIX ---
</script>

<template>
  <!-- FIX: Removed the "p-4" class from this top-level container -->
  <div class="max-w-4xl mx-auto">
    <div v-if="isLoadingSinglePost" class="text-center py-10 text-gray-500">
      Loading post...
    </div>
    <div v-else-if="singlePostError" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4">
      <p class="font-bold">Error loading post</p>
      <p>{{ singlePostError }}</p>
    </div>
    <div v-else-if="singlePost">
      <!-- We reuse our excellent PostItem component to display the post -->
      <PostItem :post="singlePost" />
    </div>
    <div v-else class="text-center py-10 text-gray-500">
      Post not found.
    </div>
  </div>
</template>