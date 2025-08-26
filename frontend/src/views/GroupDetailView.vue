<script setup lang="ts">
import { onMounted, watch, computed, ref, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useGroupStore } from '@/stores/group';
import { useAuthStore } from '@/stores/auth';
import { useInfiniteScroll } from '@/composables/useInfiniteScroll';
import { storeToRefs } from 'pinia';
import CreatePostForm from '@/components/CreatePostForm.vue';
import PostItem from '@/components/PostItem.vue';
import TransferOwnershipModal from '@/components/TransferOwnershipModal.vue';

const route = useRoute();
const router = useRouter();
const groupStore = useGroupStore();
const authStore = useAuthStore();

const isTransferModalOpen = ref(false);

const {
  currentGroup, groupPosts, isLoadingGroup, groupError, isJoiningLeaving,
  joinLeaveError, isLoadingGroupPosts, groupPostsNextCursor, isDeletingGroup,
  deleteGroupError, isTransferringOwnership, transferOwnershipError,
} = storeToRefs(groupStore);

const { isAuthenticated, currentUser } = storeToRefs(authStore);
const loadMoreGroupPostsTrigger = ref<HTMLElement | null>(null);
const isGroupCreator = computed(() => isAuthenticated.value && currentGroup.value && currentUser.value?.id === currentGroup.value.creator.id);
const showOptionsMenu = ref(false);
const optionsMenuRef = ref<HTMLDivElement | null>(null);

// Setup reusable infinite scroll with the CORRECT watcher
const nextGroupPostUrl = computed(() => groupPostsNextCursor.value);
useInfiniteScroll(loadMoreGroupPostsTrigger, groupStore.fetchNextPageOfGroupPosts, nextGroupPostUrl);

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

async function loadGroupData() {
    const slug = route.params.slug as string;
    if (!currentGroup.value || currentGroup.value.slug !== slug) {
        if (currentGroup.value) {
            groupStore.resetGroupFeedState();
        }
        await groupStore.fetchGroupDetails(slug);
    }
}

onMounted(() => {
    loadGroupData();
});

onUnmounted(() => {
  document.removeEventListener('click', closeOnClickOutside, true);
});

watch(() => route.params.slug, async (newSlug, oldSlug) => {
  if (newSlug && newSlug !== oldSlug) {
    loadGroupData();
  }
}, { immediate: false });

async function handleJoinGroup() {
  if (!currentGroup.value) return;
  await groupStore.joinGroup(currentGroup.value.slug);
}
async function handleLeaveGroup() {
  if (!currentGroup.value) return;
  if (isGroupCreator.value) {
    alert('As the group creator, you must transfer ownership before you can leave.');
    isTransferModalOpen.value = true;
    showOptionsMenu.value = false;
    return;
  }
  await groupStore.leaveGroup(currentGroup.value.slug);
}
function handleTransferOwnership() {
  showOptionsMenu.value = false;
  isTransferModalOpen.value = true;
}
async function handleDeleteGroup() {
  if (!currentGroup.value) return;
  if (confirm(`Are you sure you want to permanently delete the group "${currentGroup.value.name}"?`)) {
    const success = await groupStore.deleteGroup(currentGroup.value.slug);
    if (success) {
      router.push({ name: 'group-list' });
    }
  }
}
async function handleConfirmTransfer(newOwnerId: number) {
  if (!currentGroup.value) return;
  const success = await groupStore.transferOwnership(currentGroup.value.slug, newOwnerId);
  if (success) {
    isTransferModalOpen.value = false;
  }
}
</script>

<template>
  <!-- The entire template section remains unchanged -->
  <div class="max-w-4xl mx-auto">
    <div v-if="isLoadingGroup && !currentGroup" class="text-center py-10 text-gray-500">
      <p>Loading group...</p>
    </div>

    <div v-else-if="groupError" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4">
      <p class="font-bold">Error</p>
      <p>{{ groupError }}</p>
    </div>

    <div v-else-if="currentGroup">
      <header class="bg-white p-6 rounded-lg shadow-md mb-8">
        <div class="flex justify-between items-start">
          <div>
            <h1 class="text-3xl font-bold text-gray-900">{{ currentGroup.name }}</h1>
            <p class="text-md text-gray-500 mt-1">@{{ currentGroup.slug }}</p>
            <p class="text-gray-600 mt-2">{{ currentGroup.description }}</p>
          </div>
          <div class="flex-shrink-0 ml-4 flex space-x-2">
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
            <div v-if="isAuthenticated && isGroupCreator" class="relative" ref="optionsMenuRef">
              <button @click.stop="toggleOptionsMenu"
                class="p-2 rounded-full text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20"><path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"></path></svg>
              </button>
              <div v-if="showOptionsMenu"
                class="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-10">
                <div class="py-1" role="menu" aria-orientation="vertical">
                  <a href="#" @click.prevent="handleTransferOwnership" class="text-gray-700 block px-4 py-2 text-sm hover:bg-gray-100" role="menuitem">Transfer Ownership</a>
                  <a href="#" @click.prevent="handleLeaveGroup" class="text-gray-700 block px-4 py-2 text-sm hover:bg-gray-100" role="menuitem">Leave Group</a>
                  <a href="#" @click.prevent="handleDeleteGroup" class="text-red-700 block px-4 py-2 text-sm hover:bg-red-50" role="menuitem">Delete Group</a>
                </div>
              </div>
            </div>
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
      <div v-if="currentGroup.is_member" class="mb-8">
        <CreatePostForm :group-slug="currentGroup.slug" />
      </div>
      <div v-else-if="isAuthenticated && !currentGroup.is_member" class="bg-white p-6 rounded-lg shadow-md mb-8 text-center text-gray-500">
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

      <main class="mt-8">
        <h2 class="text-2xl font-semibold text-gray-800 mb-4">Group Feed</h2>
        <div v-if="groupPosts.length > 0" class="space-y-4">
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
        <div v-if="groupPostsNextCursor" ref="loadMoreGroupPostsTrigger" class="h-10"></div>
        <div v-if="isLoadingGroupPosts && groupPosts.length > 0" class="text-center p-4 text-gray-500">
          Loading more posts...
        </div>
      </main>
    </div>

    <TransferOwnershipModal v-if="currentGroup && currentUser" :is-open="isTransferModalOpen"
      :members="currentGroup.members" :creator-id="currentUser.id" :is-submitting="isTransferringOwnership"
      @close="isTransferModalOpen = false" @submit="handleConfirmTransfer" />
  </div>
</template>