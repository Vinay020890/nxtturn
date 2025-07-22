<script setup lang="ts">
import { getAvatarUrl } from '@/utils/avatars';
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import PostItem from '@/components/PostItem.vue';
import { useProfileStore } from '@/stores/profile';
import { useAuthStore } from '@/stores/auth';
import { storeToRefs } from 'pinia';
import { useModerationStore } from '@/stores/moderation';
import ReportFormModal from '@/components/ReportFormModal.vue';

const route = useRoute();
const profileStore = useProfileStore();
const authStore = useAuthStore();
const moderationStore = useModerationStore();
const { submissionError } = storeToRefs(moderationStore);
const { 
  currentProfile, userPosts, isLoadingProfile, isLoadingPosts, 
  errorProfile, errorPosts, postsPagination, isFollowing, isLoadingFollow 
} = storeToRefs(profileStore);
const { currentUser, isAuthenticated } = storeToRefs(authStore);
const isReportModalOpen = ref(false);
const contentToReport = ref<{ content_type_id: number; object_id: number; } | null>(null);
const selectedFile = ref<File | null>(null);
const picturePreviewUrl = ref<string | null>(null);
const isUploadingPicture = ref(false);
const uploadError = ref<string |null>(null);
const username = computed(() => route.params.username as string || '');
const isOwnProfile = computed(() => isAuthenticated.value && currentUser.value?.username === username.value);

const loadProfileData = async (page = 1) => {
  if (username.value) {
    if(page === 1) {
      await profileStore.fetchProfile(username.value);
    }
    await profileStore.fetchUserPosts(username.value, page);
  }
};

onMounted(() => {
  loadProfileData(1);
});

watch(username, (newUsername, oldUsername) => {
  if (newUsername && newUsername !== oldUsername) {
    profileStore.clearProfileData();
    loadProfileData(1);
  }
});

onUnmounted(() => {
  profileStore.clearProfileData();
});

const handlePageChange = (page: number) => {
  loadProfileData(page);
};

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

function handleFileChange(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (file) {
    selectedFile.value = file;
    picturePreviewUrl.value = URL.createObjectURL(file);
    uploadError.value = null;
    uploadProfilePicture();
  }
}

async function uploadProfilePicture() {
  if (!selectedFile.value || !username.value) return;
  isUploadingPicture.value = true;
  uploadError.value = null;
  try {
    await profileStore.updateProfilePicture(username.value, selectedFile.value);
    selectedFile.value = null;
    picturePreviewUrl.value = null;
  } catch (error: any)
 {
    uploadError.value = error.message || "Failed to upload picture.";
    selectedFile.value = null;
    picturePreviewUrl.value = null;
  } finally {
    isUploadingPicture.value = false;
  }
}
</script>

<template>
  <div>
    <div v-if="isLoadingProfile || (!currentProfile && !errorProfile)" class="text-center p-10 text-gray-500">
      Loading profile...
    </div>
    
    <div v-else-if="errorProfile" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md m-4">
      <p>{{ errorProfile }}</p>
    </div>

    <!-- This container now uses the grid system with sticky positioning for the left column -->
    <div v-else-if="currentProfile" class="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 grid grid-cols-12 gap-8 pt-6">
      
      <!-- Column 1: The Profile Card. Added sticky positioning. -->
      <aside class="col-span-6 sticky top-6 self-start">
        <div class="bg-white rounded-lg shadow-md p-6">
          <div class="flex flex-col items-center text-center">
            <div class="relative w-32 h-32 mb-4">
              <img 
                :src="picturePreviewUrl || getAvatarUrl(currentProfile.picture, currentProfile.user.first_name, currentProfile.user.last_name)" 
                alt="Profile Picture" 
                class="w-full h-full rounded-full object-cover border-4 border-white shadow-lg bg-gray-200"
              >
              <label 
                v-if="isOwnProfile" 
                for="picture-upload" 
                class="absolute bottom-1 right-1 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white cursor-pointer hover:bg-blue-600 border-2 border-white"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                <input id="picture-upload" type="file" @change="handleFileChange" accept="image/*" class="hidden">
              </label>
            </div>
            <h1 class="text-2xl font-bold text-gray-800">{{ currentProfile.user.first_name }} {{ currentProfile.user.last_name }}</h1>
            <p class="text-md text-gray-500">@{{ currentProfile.user.username }}</p>
            <p v-if="currentProfile.bio" class="mt-4 text-sm text-gray-600">{{ currentProfile.bio }}</p>
            <button 
              v-if="!isOwnProfile" 
              @click="isFollowing ? profileStore.unfollowUser(username) : profileStore.followUser(username)" 
              :disabled="isLoadingFollow" 
              class="mt-4 w-full text-white font-bold py-2 px-4 rounded-full transition" 
              :class="isFollowing ? 'bg-gray-400 hover:bg-gray-500' : 'bg-blue-500 hover:bg-blue-600'"
            >
              {{ isLoadingFollow ? '...' : (isFollowing ? 'Following' : 'Follow') }}
            </button>
          </div>
        </div>
      </aside>

      <!-- Column 2: The User's Posts, spanning 6 columns to be identical to the feed -->
      <div class="col-span-6 min-w-0">
        <div v-if="isLoadingPosts && userPosts.length === 0" class="text-center p-10 text-gray-500">
          Loading posts...
        </div>
        <div v-else-if="errorPosts" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md">
          {{ errorPosts }}
        </div>
        <div v-else-if="userPosts.length > 0" class="space-y-6">
          <PostItem 
            v-for="post in userPosts" 
            :key="post.id" 
            :post="post" 
            @report-content="handleOpenReportModal" 
          />
        </div>
        <div v-else class="bg-white rounded-lg shadow-md p-10 text-center text-gray-500">
          This user hasn't posted anything yet.
        </div>
        <!-- Pagination -->
        <div v-if="postsPagination.totalPages > 1" class="mt-8 flex justify-center items-center gap-4">
          <button 
            @click="handlePageChange(postsPagination.currentPage - 1)" 
            :disabled="!postsPagination.previous" 
            class="px-4 py-2 text-sm font-medium bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
          >
            Previous
          </button>
          <span class="text-sm text-gray-700">Page {{ postsPagination.currentPage }} of {{ postsPagination.totalPages }}</span>
          <button 
            @click="handlePageChange(postsPagination.currentPage + 1)" 
            :disabled="!postsPagination.next" 
            class="px-4 py-2 text-sm font-medium bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    </div>
    <ReportFormModal 
      :is-open="isReportModalOpen" 
      @close="isReportModalOpen = false" 
      @submit="handleReportSubmit" 
    />
  </div>
</template>