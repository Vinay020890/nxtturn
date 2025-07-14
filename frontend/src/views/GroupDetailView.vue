// C:\Users\Vinay\Project\frontend\src\views\GroupDetailView.vue

<script setup lang="ts">
import { onMounted, onUnmounted, watch, computed, ref } from 'vue';
import { useRoute } from 'vue-router';
import { useGroupStore } from '@/stores/group';
import { useAuthStore } from '@/stores/auth';
import { storeToRefs } from 'pinia';
import CreatePostForm from '@/components/CreatePostForm.vue';
import PostItem from '@/components/PostItem.vue';

const route = useRoute();
const groupStore = useGroupStore();
const authStore = useAuthStore();

const { 
  currentGroup, 
  groupPosts, // This now holds cursor-paginated posts
  isLoadingGroup, 
  groupError,
  isJoiningLeaving,
  joinLeaveError,
  isLoadingGroupPosts,
  groupPostsNextCursor // NEW: Replaces groupPostsHasNextPage
} = storeToRefs(groupStore);

const { isAuthenticated, currentUser } = storeToRefs(authStore);

const loadMoreGroupPostsTrigger = ref<HTMLElement | null>(null);
let observer: IntersectionObserver | null = null; // Declare observer

const showJoinLeaveButton = computed(() => isAuthenticated.value && currentGroup.value);
const isGroupCreator = computed(() => isAuthenticated.value && currentGroup.value && currentUser.value?.id === currentGroup.value.creator.id);

// === NEW: Function to set up the Intersection Observer ===
function setupObserver() {
  // Disconnect any existing observer first to prevent issues with re-observing
  if (observer) {
    observer.disconnect();
    observer = null; // Clear the old observer
  }

  observer = new IntersectionObserver((entries) => {
    // Trigger fetch if the target is intersecting AND there is a next cursor AND not currently loading
    if (entries[0].isIntersecting && groupPostsNextCursor.value && !isLoadingGroupPosts.value) {
      groupStore.fetchNextPageOfGroupPosts();
    }
  }, { rootMargin: '200px' });

  // Start observing if the target element exists
  if (loadMoreGroupPostsTrigger.value) {
    observer.observe(loadMoreGroupPostsTrigger.value);
  }
}
// ==========================================================

onMounted(async () => {
  // Initial fetch of group details and first page of posts
  await groupStore.fetchGroupDetails(Number(route.params.id));
  setupObserver(); // Setup observer after initial data fetch
});

onUnmounted(() => {
  groupStore.clearCurrentGroup(); // Clears group details and posts
  // Disconnect observer on component unmount
  if (observer) {
    observer.disconnect();
  }
});

// Watch for changes in route.params.id to re-fetch group data and reset observer
watch(() => route.params.id, async (newId, oldId) => {
  if (newId && newId !== oldId) { // Only run if ID actually changes and not on initial load
    await groupStore.fetchGroupDetails(Number(newId)); // This also clears previous posts
    setupObserver(); // Re-setup observer for the new group's content
  }
}, { immediate: false }); // No immediate: true because onMounted handles initial load

// Handlers for Join/Leave are unchanged.
async function handleJoinGroup() {
  if (!currentGroup.value) return;
  const success = await groupStore.joinGroup(currentGroup.value.id);
  if (success) {
    alert(`You have successfully joined ${currentGroup.value.name}!`);
  } else {
    alert(`Failed to join group: ${joinLeaveError.value || 'Unknown error'}`);
  }
}

async function handleLeaveGroup() {
  if (!currentGroup.value) return;
  const success = await groupStore.leaveGroup(currentGroup.value.id);
  if (success) {
    alert(`You have successfully left ${currentGroup.value.name}.`);
  } else {
    alert(`Failed to leave group: ${joinLeaveError.value || 'Unknown error'}`);
  }
}
</script>

<template>
  <div class="max-w-4xl mx-auto p-4">
    <!-- Loading State -->
    <div v-if="isLoadingGroup && !currentGroup" class="text-center py-10 text-gray-500">
      <p>Loading group...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="groupError" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4">
      <p class="font-bold">Error</p>
      <p>{{ groupError }}</p>
    </div>

    <!-- Group Content (Main Display Block) -->
    <div v-else-if="currentGroup">
      <!-- Group Header -->
      <header class="bg-white p-6 rounded-lg shadow-md mb-8">
        <div class="flex justify-between items-start">
          <div>
            <h1 class="text-3xl font-bold text-gray-900">{{ currentGroup.name }}</h1>
            <p class="text-gray-600 mt-2">{{ currentGroup.description }}</p>
          </div>
          <div v-if="showJoinLeaveButton" class="flex-shrink-0">
            <button 
              v-if="!isGroupCreator"
              @click="currentGroup.is_member ? handleLeaveGroup() : handleJoinGroup()"
              :disabled="isJoiningLeaving"
              :class="[
                'ml-4 px-6 py-2 rounded-full font-semibold transition-colors duration-200',
                currentGroup.is_member 
                  ? 'bg-red-500 text-white hover:bg-red-600' 
                  : 'bg-blue-600 text-white hover:bg-blue-700',
                isJoiningLeaving ? 'opacity-50 cursor-not-allowed' : ''
              ]"
            >
              {{ isJoiningLeaving ? 'Processing...' : (currentGroup.is_member ? 'Leave Group' : 'Join Group') }}
            </button>
          </div>
        </div>
        <div class="mt-4 text-sm text-gray-500">
          <span>Created by: 
            <router-link :to="{ name: 'profile', params: { username: currentGroup.creator.username } }" class="font-semibold hover:underline">
              {{ currentGroup.creator.username }}
            </router-link>
          </span>
          <span class="mx-2">|</span>
          <span>{{ currentGroup.member_count }} Members</span>
        </div>
        <div v-if="joinLeaveError" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-3 text-sm mt-3">
          <p>{{ joinLeaveError }}</p>
        </div>
      </header>

      <!-- Create Post Form Section -->
      <div v-if="currentGroup.is_member" class="mb-8">
        <CreatePostForm :group-id="currentGroup.id" />
      </div>
      <div v-else-if="isAuthenticated && !currentGroup.is_member" class="bg-white p-6 rounded-lg shadow-md mb-8 text-center text-gray-500">
        <p>You must join this group to create posts.</p>
        <button v-if="!isGroupCreator" @click="handleJoinGroup()" :disabled="isJoiningLeaving" class="mt-4 px-6 py-2 bg-blue-600 text-white rounded-full font-semibold hover:bg-blue-700 transition-colors" :class="isJoiningLeaving ? 'opacity-50 cursor-not-allowed' : ''">
          {{ isJoiningLeaving ? 'Joining...' : 'Join Group to Post' }}
        </button>
      </div>
      <div v-else-if="!isAuthenticated" class="bg-white p-6 rounded-lg shadow-md mb-8 text-center text-gray-500">
        <p>Please log in to join this group and create posts.</p>
      </div>
      
      <!-- Group Feed Section -->
      <main class="mt-8">
        <h2 class="text-2xl font-semibold text-gray-800 mb-4">Group Feed</h2>
        <div v-if="groupPosts.length > 0" class="space-y-6">
           <PostItem 
             v-for="post in groupPosts" 
             :key="post.id" 
             :post="post" 
             :hide-group-context="true"
           />
        </div>
        <div v-else-if="!isLoadingGroupPosts && groupPosts.length === 0" class="bg-white p-6 rounded-lg shadow-md text-center text-gray-500">
          <p>No posts in this group yet. Be the first to create one!</p>
        </div>
        
        <!-- Infinite Scroll Trigger & Loading Indicator -->
        <!-- Only show the trigger if there's a next cursor to load more posts -->
        <div v-if="groupPostsNextCursor" ref="loadMoreGroupPostsTrigger" class="h-10"></div>
        <div v-if="isLoadingGroupPosts && groupPosts.length > 0" class="text-center p-4 text-gray-500">
          Loading more posts...
        </div>
      </main>
    </div>
  </div>
</template>