<script setup lang="ts">
import { getAvatarUrl } from '@/utils/avatars';
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import PostItem from '@/components/PostItem.vue';
import { useProfileStore } from '@/stores/profile';
import { useAuthStore } from '@/stores/auth';
import { storeToRefs } from 'pinia';

const route = useRoute();
const profileStore = useProfileStore();
const authStore = useAuthStore();

const { 
  currentProfile, userPosts, isLoadingProfile, isLoadingPosts, 
  errorProfile, errorPosts, postsPagination, isFollowing, isLoadingFollow 
} = storeToRefs(profileStore);

const { currentUser, isAuthenticated } = storeToRefs(authStore);

const selectedFile = ref<File | null>(null);
const picturePreviewUrl = ref<string | null>(null);
const isUploadingPicture = ref(false);
const uploadError = ref<string | null>(null);

const username = computed(() => route.params.username as string || '');
const isOwnProfile = computed(() => isAuthenticated.value && currentUser.value?.username === username.value);

const loadProfileData = async (page = 1) => {
  if (username.value) {
    // Only fetch profile details on the first page load for this user
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

function handleFileChange(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (file) {
    selectedFile.value = file;
    picturePreviewUrl.value = URL.createObjectURL(file);
    uploadError.value = null;
    uploadProfilePicture(); // Automatically trigger upload
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
  } catch (error: any) {
    uploadError.value = error.message || "Failed to upload picture.";
    selectedFile.value = null;
    picturePreviewUrl.value = null;
  } finally {
    isUploadingPicture.value = false;
  }
}
</script>

<template>
  <div class="max-w-6xl mx-auto">
    <!-- Loading State -->
    <div v-if="isLoadingProfile" class="text-center p-10 text-gray-500">Loading profile...</div>
    
    <!-- Error State -->
    <div v-else-if="errorProfile" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md">
      <p>{{ errorProfile }}</p>
    </div>

    <!-- Main Profile Layout -->
    <div v-else-if="currentProfile" class="grid grid-cols-1 md:grid-cols-3 gap-8 items-start">
      
      <!-- Left Column (Profile Card - STICKY) -->
      <aside class="md:col-span-1 md:sticky md:top-24">
        <div class="bg-white rounded-lg shadow-md p-6">
          <div class="flex flex-col items-center text-center">
            <!-- Profile Picture -->
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
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                  <input id="picture-upload" type="file" @change="handleFileChange" accept="image/*" class="hidden">
                </label>
            </div>

            <h1 class="text-2xl font-bold text-gray-800">{{ currentProfile.user.first_name }} {{ currentProfile.user.last_name }}</h1>
            <p class="text-md text-gray-500">@{{ currentProfile.user.username }}</p>
            
            <p v-if="currentProfile.bio" class="mt-4 text-sm text-gray-600">{{ currentProfile.bio }}</p>
            
            <!-- Follow/Unfollow Button -->
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
          
          <!-- Details -->
          <div class="mt-6 text-sm text-gray-600 space-y-2 border-t border-gray-200 pt-4">
            <p v-if="currentProfile.location_city" class="flex items-center gap-2">
                <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                <span>{{ currentProfile.location_city }}, {{ currentProfile.location_state }}</span>
              </p>
              <p v-if="currentProfile.college_name" class="flex items-center gap-2">
                <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z"></path></svg>
                <span>{{ currentProfile.college_name }}</span>
              </p>
          </div>
        </div>
      </aside>

      <!-- Right Column (User's Posts) -->
      <div class="md:col-span-2">
        <div v-if="isLoadingPosts && userPosts.length === 0" class="text-center p-10 text-gray-500">Loading posts...</div>
        <div v-else-if="errorPosts" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md">{{ errorPosts }}</div>
        <div v-else-if="userPosts.length > 0" class="space-y-6">
          <PostItem v-for="post in userPosts" :key="post.id" :post="post" />
        </div>
        <div v-else class="bg-white rounded-lg shadow-md p-10 text-center text-gray-500">
          This user hasn't posted anything yet.
        </div>

        <!-- Pagination -->
        <div v-if="postsPagination.totalPages > 1" class="mt-8 flex justify-center items-center gap-4">
          <button @click="handlePageChange(postsPagination.currentPage - 1)" :disabled="!postsPagination.previous" class="px-4 py-2 text-sm font-medium bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50">
            Previous
          </button>
          <span class="text-sm text-gray-700">Page {{ postsPagination.currentPage }} of {{ postsPagination.totalPages }}</span>
          <button @click="handlePageChange(postsPagination.currentPage + 1)" :disabled="!postsPagination.next" class="px-4 py-2 text-sm font-medium bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50">
            Next
          </button>
        </div>
      </div>
    </div>
  </div>
</template>