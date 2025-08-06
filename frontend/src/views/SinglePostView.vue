<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { useFeedStore } from '@/stores/feed';
import { storeToRefs } from 'pinia';
import PostItem from '@/components/PostItem.vue';

const route = useRoute();
const feedStore = useFeedStore();

// Get the specific state we need for this view from the feedStore
const { singlePost, isLoadingSinglePost, singlePostError } = storeToRefs(feedStore);

// When the component mounts, get the postId from the URL and fetch the post
onMounted(() => {
  const postId = Number(route.params.postId);
  if (postId) {
    // We will create this 'fetchPostById' action in the next step
    feedStore.fetchPostById(postId);
  }
});
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