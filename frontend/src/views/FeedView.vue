<script setup lang="ts">
import { useAuthStore } from '@/stores/auth';
import { onMounted, ref } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';
import { useFeedStore } from '@/stores/feed';
import CreatePostForm from '@/components/CreatePostForm.vue';
import PostItem from '@/components/PostItem.vue';
import eventBus from '@/services/eventBus';

const authStore = useAuthStore();
const feedStore = useFeedStore();

const createPostFormKey = ref(0);
const loadMoreTrigger = ref<HTMLElement | null>(null);
let observer: IntersectionObserver | null = null;

function forceFormReset() { 
  createPostFormKey.value++; 
}

onMounted(async () => {
  eventBus.on('reset-feed-form', forceFormReset);
  
  // Fetch initial feed posts only if the list is empty
  if (feedStore.mainFeedPosts.length === 0) {
    await feedStore.fetchFeed();
  }

  observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting && feedStore.mainFeedNextCursor && !feedStore.isLoadingMainFeed) {
      feedStore.fetchNextPageOfMainFeed();
    }
  }, { rootMargin: '200px' });
  
  if (loadMoreTrigger.value) { 
    observer.observe(loadMoreTrigger.value); 
  }
});

onBeforeRouteLeave((to, from) => {
  eventBus.off('reset-feed-form', forceFormReset);
  if (observer) { 
    observer.disconnect(); 
  }
  feedStore.resetMainFeedState();
  console.log('Leaving main feed view, state and observer cleaned up.');
});
</script>

<template>
  <div class="max-w-4xl mx-auto">
    
    <!-- 
      THIS IS THE FINAL STRUCTURE:
      1. The outer div uses space-y-6 to create a larger gap between its direct children:
         - The CreatePostForm
         - The block of posts below it.
    -->
    <div class="space-y-6">
      
      <CreatePostForm :key="createPostFormKey" />

      <!-- Loading/Error/Empty states are now direct children of the outer container -->
      <div v-if="feedStore.isLoadingMainFeed && feedStore.mainFeedPosts.length === 0" class="text-center p-8 text-gray-500">
        Loading feed...
      </div>

      <div v-if="feedStore.mainFeedError" class="bg-red-100 border border-red-300 text-red-700 px-4 py-3 rounded-md text-center p-8" role="alert">
        Error loading feed: {{ feedStore.mainFeedError }}
      </div>
      
      <!-- 
        2. This inner div wraps ONLY the posts and uses space-y-4.
           This creates the tighter, uniform gap *between* each PostItem.
      -->
      <div v-if="feedStore.mainFeedPosts.length > 0" class="space-y-4">
        <PostItem 
          v-for="post in feedStore.mainFeedPosts" 
          :key="post.id" 
          :post="post"
        />
      </div>
      
      <div v-if="!feedStore.isLoadingMainFeed && feedStore.mainFeedPosts.length === 0 && !feedStore.mainFeedError" class="text-center p-8 text-gray-500">
        Your feed is empty. Follow some users or create a post!
      </div>
      
      <!-- Infinite scroll triggers are also direct children -->
      <div v-if="feedStore.mainFeedNextCursor" ref="loadMoreTrigger" class="h-10"></div>
      
      <div v-if="feedStore.isLoadingMainFeed && feedStore.mainFeedPosts.length > 0" class="text-center p-4 text-gray-500">
        Loading more posts...
      </div>
    </div>
    
  </div>
</template>