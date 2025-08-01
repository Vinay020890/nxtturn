<script setup lang="ts">
// VERIFIED: No changes to imports
import { onMounted, watch, computed, ref, nextTick, onUnmounted } from 'vue';
import { useRoute, onBeforeRouteLeave, useRouter } from 'vue-router';
import { useGroupStore } from '@/stores/group';
import { useAuthStore } from '@/stores/auth';
import { storeToRefs } from 'pinia';
import CreatePostForm from '@/components/CreatePostForm.vue';
import PostItem from '@/components/PostItem.vue';
import { useModerationStore } from '@/stores/moderation';
import ReportFormModal from '@/components/ReportFormModal.vue';
import TransferOwnershipModal from '@/components/TransferOwnershipModal.vue';

const route = useRoute();
const router = useRouter();
const groupStore = useGroupStore();
const authStore = useAuthStore();
const moderationStore = useModerationStore();

// --- NO CHANGES IN THIS SECTION ---
const { submissionError } = storeToRefs(moderationStore);
const isReportModalOpen = ref(false);
const contentToReport = ref<{ content_type_id: number; object_id: number; } | null>(null);
const isTransferModalOpen = ref(false);
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
  currentGroup, groupPosts, isLoadingGroup, groupError, isJoiningLeaving,
  joinLeaveError, isLoadingGroupPosts, groupPostsNextCursor, isDeletingGroup,
  deleteGroupError,
  isTransferringOwnership,
  transferOwnershipError,
} = storeToRefs(groupStore);
const { isAuthenticated, currentUser } = storeToRefs(authStore);
const loadMoreGroupPostsTrigger = ref<HTMLElement | null>(null);
let observer: IntersectionObserver | null = null;
const showJoinLeaveButton = computed(() => isAuthenticated.value && currentGroup.value);
const isGroupCreator = computed(() => isAuthenticated.value && currentGroup.value && currentUser.value?.id === currentGroup.value.creator.id);
const showOptionsMenu = ref(false);
const optionsMenuRef = ref<HTMLDivElement | null>(null);
function toggleOptionsMenu() {
  showOptionsMenu.value = !showOptionsMenu.value;
}
const closeOnClickOutside = (event: MouseEvent) => {
  if (optionsMenuRef.value && !optionsMenuRef.value.contains(event.target as Node)) {
    showOptionsMenu.value = false;
  }
};
watch(showOptionsMenu, (isOpen) => {
  if (isOpen) {
    document.addEventListener('click', closeOnClickOutside, true);
  } else {
    document.removeEventListener('click', closeOnClickOutside, true);
  }
});
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
// --- END OF UNCHANGED SECTION ---


// --- THIS SECTION HAS BEEN MODIFIED TO USE SLUGS ---
onMounted(async () => {
  // Use 'slug' from the route params, not 'id'
  await groupStore.fetchGroupDetails(route.params.slug as string);
  setupObserver();
});

onBeforeRouteLeave((to, from) => {
  groupStore.resetGroupFeedState();
  if (observer) {
    observer.disconnect();
  }
  document.removeEventListener('click', closeOnClickOutside, true);
  console.log('Leaving group detail view, state and observers cleaned up.');
});

onUnmounted(() => {
  document.removeEventListener('click', closeOnClickOutside, true);
});

watch(() => route.params.slug, async (newSlug, oldSlug) => { // Watch the 'slug' param
  if (newSlug && newSlug !== oldSlug) {
    // Use the new slug to fetch details
    await groupStore.fetchGroupDetails(newSlug as string);
    setupObserver();
  }
}, { immediate: false });
// --- END OF MODIFIED SECTION ---


// --- NO CHANGES IN THIS SECTION ---
async function handleJoinGroup() {
  if (!currentGroup.value) return;
  const success = await groupStore.joinGroup(currentGroup.value.slug);
  if (success) {
  } else {
    alert(`Failed to join group: ${joinLeaveError.value || 'Unknown error'}`);
  }
}
async function handleLeaveGroup() {
  if (!currentGroup.value) return;
  const success = await groupStore.leaveGroup(currentGroup.value.slug);
  if (success) {
  } else {
    alert(`Failed to leave group: ${joinLeaveError.value || 'Unknown error'}`);
  }
}
function handleTransferOwnership() {
  // First, close the three-dots menu
  showOptionsMenu.value = false;
  // Then, open the transfer modal
  isTransferModalOpen.value = true;
}
async function handleDeleteGroup() {
  if (!currentGroup.value) return;
  if (confirm(`Are you sure you want to permanently delete the group "${currentGroup.value.name}"? This action cannot be undone.`)) {
    const success = await groupStore.deleteGroup(currentGroup.value.slug);
    if (success) {
      alert('Group deleted successfully.');
      router.push({ name: 'group-list' });
    } else {
      alert(`Failed to delete group: ${deleteGroupError.value || 'An unknown error occurred.'}`);
    }
  }
}
async function handleConfirmTransfer(newOwnerId: number) {
  if (!currentGroup.value) return;

  const success = await groupStore.transferOwnership(currentGroup.value.slug, newOwnerId);

  if (success) {
    isTransferModalOpen.value = false;
    alert('Ownership transferred successfully. The page will now update.');
    // The page will automatically update because the store action re-fetches group details.
  } else {
    // Display the error from the store
    alert(`Failed to transfer ownership: ${transferOwnershipError.value || 'An unknown error occurred.'}`);
  }
}
// --- END OF UNCHANGED SECTION ---
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

          <!-- REPLACEMENT: The entire button container is replaced with this new structure -->
          <div class="flex-shrink-0 ml-4 flex space-x-2">
            <!-- Regular Join/Leave button is always visible if not the creator -->
            <button v-if="isAuthenticated && currentGroup && !isGroupCreator"
              @click="currentGroup.is_member ? handleLeaveGroup() : handleJoinGroup()" :disabled="isJoiningLeaving"
              :class="[
                'px-6 py-2 rounded-full font-semibold transition-colors duration-200',
                currentGroup.is_member
                  ? 'bg-gray-200 text-gray-800 hover:bg-gray-300'
                  : 'bg-blue-600 text-white hover:bg-blue-700',
                isJoiningLeaving ? 'opacity-50 cursor-not-allowed' : ''
              ]">
              {{ isJoiningLeaving ? 'Processing...' : (currentGroup.is_member ? 'Leave Group' : 'Join Group') }}
            </button>

            <!-- Creator's Options Menu (Three Dots) -->
            <div v-if="isAuthenticated && isGroupCreator" class="relative" ref="optionsMenuRef">
              <!-- The Three Dots Button -->
              <button @click.stop="toggleOptionsMenu"
                class="p-2 rounded-full text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                  <path
                    d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z">
                  </path>
                </svg>
              </button>

              <!-- The Dropdown Menu -->
              <div v-if="showOptionsMenu"
                class="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-10">
                <div class="py-1" role="menu" aria-orientation="vertical">
                  <a href="#" @click.prevent="handleTransferOwnership"
                    class="text-gray-700 block px-4 py-2 text-sm hover:bg-gray-100" role="menuitem">Transfer
                    Ownership</a>

                  <a href="#" @click.prevent="handleTransferOwnership"
                    class="text-gray-700 block px-4 py-2 text-sm hover:bg-gray-100" role="menuitem">Leave Group</a>

                  <a href="#" @click.prevent="handleDeleteGroup"
                    class="text-red-700 block px-4 py-2 text-sm hover:bg-red-50" role="menuitem">Delete Group</a>
                </div>
              </div>
            </div>
          </div>
          <!-- END OF REPLACEMENT -->

        </div>
        <div class="mt-4 text-sm text-gray-500">
          <span>Created by:
            <router-link :to="{ name: 'profile', params: { username: currentGroup.creator.username } }"
              class="font-semibold hover:underline">
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
        <CreatePostForm :group-slug="currentGroup.slug" />
      </div>
      <div v-else-if="isAuthenticated && !currentGroup.is_member"
        class="bg-white p-6 rounded-lg shadow-md mb-8 text-center text-gray-500">
        <p>You must join this group to create posts.</p>
        <button v-if="!isGroupCreator" @click="handleJoinGroup()" :disabled="isJoiningLeaving"
          class="mt-4 px-6 py-2 bg-blue-600 text-white rounded-full font-semibold hover:bg-blue-700 transition-colors"
          :class="isJoiningLeaving ? 'opacity-50 cursor-not-allowed' : ''">
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
          <PostItem v-for="post in groupPosts" :key="post.id" :post="post" :hide-group-context="true"
            @report-content="handleOpenReportModal" />
        </div>
        <div v-else-if="!isLoadingGroupPosts && groupPosts.length === 0"
          class="bg-white p-6 rounded-lg shadow-md text-center text-gray-500">
          <p>No posts in this group yet. Be the first to create one!</p>
        </div>

        <!-- Infinite Scroll Trigger & Loading Indicator -->
        <div v-if="groupPostsNextCursor" ref="loadMoreGroupPostsTrigger" class="h-10"></div>
        <div v-if="isLoadingGroupPosts && groupPosts.length > 0" class="text-center p-4 text-gray-500">
          Loading more posts...
        </div>
      </main>
    </div>

    <ReportFormModal :is-open="isReportModalOpen" @close="isReportModalOpen = false" @submit="handleReportSubmit" />

    <!-- Transfer Ownership Modal -->
    <TransferOwnershipModal v-if="currentGroup && currentUser" :is-open="isTransferModalOpen"
      :members="currentGroup.members" :creator-id="currentUser.id" :is-submitting="isTransferringOwnership"
      @close="isTransferModalOpen = false" @submit="handleConfirmTransfer" />

  </div>
</template>