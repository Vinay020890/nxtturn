<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';
import { useGroupStore } from '@/stores/group';
import { storeToRefs } from 'pinia';
import { useRouter } from 'vue-router';
import CreateGroupFormModal from '@/components/CreateGroupFormModal.vue';
import type { Group } from '@/stores/group';

const groupStore = useGroupStore();
const router = useRouter();
const { allGroups, isLoadingAllGroups, allGroupsError, allGroupsHasNextPage } = storeToRefs(groupStore);
const isCreateGroupModalOpen = ref(false);

onMounted(() => {
  groupStore.fetchGroups();
});

onBeforeRouteLeave((to, from) => {
  groupStore.resetAllGroupsState();
});

function openCreateGroupModal() {
  isCreateGroupModalOpen.value = true;
}

function handleGroupCreated(newGroup: Group) {
  // THIS IS THE FIX: Corrected variable name
  isCreateGroupModalOpen.value = false;
  router.push({ name: 'group-detail-page', params: { id: newGroup.id } });
}

function loadMoreGroups() {
  groupStore.fetchNextPageOfGroups();
}
</script>

<template>
  <div class="max-w-4xl mx-auto">
    
    <header class="bg-white p-4 rounded-lg shadow-sm border border-gray-200 flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-800">Discover Groups</h1>
      <button 
        @click="openCreateGroupModal"
        class="px-5 py-2 bg-blue-600 text-white rounded-full font-semibold hover:bg-blue-700 transition-colors"
      >
        + Create New Group
      </button>
    </header>

    <!-- Loading State -->
    <div v-if="isLoadingAllGroups && allGroups.length === 0" class="text-center py-10 text-gray-500">
      <p>Loading groups...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="allGroupsError" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4">
      <p class="font-bold">Error</p>
      <p>{{ allGroupsError }}</p>
    </div>

    <!-- Group List -->
    <div v-else-if="allGroups && allGroups.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div v-for="group in allGroups" :key="group.id" class="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow">
        <router-link :to="{ name: 'group-detail-page', params: { id: group.id } }" class="block">
          <h2 class="text-xl font-bold text-gray-900 hover:text-blue-600 transition-colors">{{ group.name }}</h2>
          <p class="text-gray-600 mt-2 text-sm">{{ group.description }}</p>
          <div class="mt-4 text-sm text-gray-500">
            <span>Created by: 
              <router-link :to="{ name: 'profile', params: { username: group.creator?.username } }" class="font-semibold hover:underline" @click.stop>
                {{ group.creator?.username }}
              </router-link>
            </span>
            <span class="mx-2">|</span>
            <span>{{ group.member_count }} Members</span>
            <span class="mx-2">|</span>
            <span v-if="group.privacy_level" :class="group.privacy_level === 'private' ? 'text-red-500' : 'text-green-500'" class="font-semibold">
              {{ group.privacy_level === 'private' ? 'Private' : 'Public' }}
            </span>
            <span v-else class="text-gray-400">Unknown Privacy</span>
            <span class="mx-2" v-if="group.is_member">|</span>
            <span v-if="group.is_member" class="text-blue-500 font-semibold">Member</span>
          </div>
        </router-link>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="bg-white p-6 rounded-lg shadow-md text-center text-gray-500">
      <p>No groups found. Be the first to create one!</p>
    </div>

    <!-- "Load More" button for pagination -->
    <div v-if="allGroupsHasNextPage" class="flex justify-end mt-8">
      <button
        @click="loadMoreGroups"
        :disabled="isLoadingAllGroups"
        class="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2.5 px-6 rounded-full shadow-lg transition-all duration-200 ease-in-out transform hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {{ isLoadingAllGroups ? 'Loading...' : 'Load More' }}
      </button>
    </div>

    <CreateGroupFormModal 
      :is-open="isCreateGroupModalOpen" 
      @close="isCreateGroupModalOpen = false" 
      @group-created="handleGroupCreated" 
    />
  </div>
</template>