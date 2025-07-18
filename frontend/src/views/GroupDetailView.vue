// C:\Users\Vinay\Project\frontend\src\views\GroupDetailView.vue

<script setup lang="ts">
import { onMounted, watch, computed, ref } from 'vue';
// ---- [CHANGE 1] ---- Import onBeforeRouteLeave, remove onUnmounted
import { useRoute, onBeforeRouteLeave } from 'vue-router'; 
import { useGroupStore } from '@/stores/group';
import { useAuthStore } from '@/stores/auth';
import { storeToRefs } from 'pinia';
import CreatePostForm from '@/components/CreatePostForm.vue';
import PostItem from '@/components/PostItem.vue';

import { useModerationStore } from '@/stores/moderation';
import ReportFormModal from '@/components/ReportFormModal.vue';

const route = useRoute();
const groupStore = useGroupStore();
const authStore = useAuthStore();

const moderationStore = useModerationStore();
const { submissionError } = storeToRefs(moderationStore);

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

const { 
  currentGroup, 
  groupPosts,
  isLoadingGroup, 
  groupError,
  isJoiningLeaving,
  joinLeaveError,
  isLoadingGroupPosts,
  groupPostsNextCursor
} = storeToRefs(groupStore);

const { isAuthenticated, currentUser } = storeToRefs(authStore);

const loadMoreGroupPostsTrigger = ref<HTMLElement | null>(null);
let observer: IntersectionObserver | null = null;

const showJoinLeaveButton = computed(() => isAuthenticated.value && currentGroup.value);
const isGroupCreator = computed(() => isAuthenticated.value && currentGroup.value && currentUser.value?.id === currentGroup.value.creator.id);

function setupObserver() {
  if (observer) {
    observer.disconnect();
    observer = null;
  }

  observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting && groupPostsNextCursor.value && !isLoadingGroupPosts.value) {
      groupStore.fetchNextPageOfGroupPosts();
    }
  }, { rootMargin: '200px' });

  if (loadMoreGroupPostsTrigger.value) {
    observer.observe(loadMoreGroupPostsTrigger.value);
  }
}

onMounted(async () => {
  await groupStore.fetchGroupDetails(Number(route.params.id));
  setupObserver();
});

// ---- [CHANGE 2] ---- Replace onUnmounted with onBeforeRouteLeave
onBeforeRouteLeave((to, from) => {
  // Call our new, robust reset action from the store
  groupStore.resetGroupFeedState();
  
  // Also clean up the observer here
  if (observer) {
    observer.disconnect();
  }
  console.log('Leaving group detail view, state and observer cleaned up.');
});
// --------------------

watch(() => route.params.id, async (newId, oldId) => {
  if (newId && newId !== oldId) {
    await groupStore.fetchGroupDetails(Number(newId));
    setupObserver();
  }
}, { immediate: false });

async function handleJoinGroup() {
  if (!currentGroup.value) return;
  const success = await groupStore.joinGroup(currentGroup.value.id);
  if (success) {
    // Optional: Use a more subtle notification system in the future
  } else {
    alert(`Failed to join group: ${joinLeaveError.value || 'Unknown error'}`);
  }
}

async function handleLeaveGroup() {
  if (!currentGroup.value) return;
  const success = await groupStore.leaveGroup(currentGroup.value.id);
  if (success) {
    // Optional: Use a more subtle notification system in the future
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
            @report-content="handleOpenReportModal"
          />
        </div>
        <div v-else-if="!isLoadingGroupPosts && groupPosts.length === 0" class="bg-white p-6 rounded-lg shadow-md text-center text-gray-500">
          <p>No posts in this group yet. Be the first to create one!</p>
        </div>
        
        <!-- Infinite Scroll Trigger & Loading Indicator -->
        <div v-if="groupPostsNextCursor" ref="loadMoreGroupPostsTrigger" class="h-10"></div>
        <div v-if="isLoadingGroupPosts && groupPosts.length > 0" class="text-center p-4 text-gray-500">
          Loading more posts...
        </div>
      </main>
    </div>

    <ReportFormModal 
      :is-open="isReportModalOpen" 
      @close="isReportModalOpen = false" 
      @submit="handleReportSubmit"
    />
    
  </div>
</template>