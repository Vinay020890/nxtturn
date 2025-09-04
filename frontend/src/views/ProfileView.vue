<script setup lang="ts">
import { getAvatarUrl } from '@/utils/avatars';
import { ref, watch, computed } from 'vue';
import { useRoute } from 'vue-router';
import PostItem from '@/components/PostItem.vue';
import { useProfileStore } from '@/stores/profile';
import { useAuthStore } from '@/stores/auth';
import { usePostsStore } from '@/stores/posts';
import { useInfiniteScroll } from '@/composables/useInfiniteScroll';
import { storeToRefs } from 'pinia';

const route = useRoute();
const profileStore = useProfileStore();
const authStore = useAuthStore();
const postsStore = usePostsStore();

const { 
  currentProfile, isLoadingProfile, isLoadingPosts,
  errorProfile, errorPosts,
  isFollowing, isLoadingFollow 
} = storeToRefs(profileStore);

const { currentUser, isAuthenticated } = storeToRefs(authStore);
const username = computed(() => route.params.username as string || '');

// --- THIS IS THE FIX ---
// We access the state directly instead of using the deleted getter functions.
const userPostIds = computed(() => profileStore.postIdsByUsername[username.value] || []);
const userPostsNextPageUrl = computed(() => profileStore.nextPageUrlByUsername[username.value]);

const userPosts = computed(() => postsStore.getPostsByIds(userPostIds.value));
// --- END OF FIX ---


const isOwnProfile = computed(() => isAuthenticated.value && currentUser.value?.username === username.value);
const loadMoreTrigger = ref<HTMLElement | null>(null);

useInfiniteScroll(
  loadMoreTrigger,
  () => profileStore.fetchNextPageOfUserPosts(username.value),
  userPostsNextPageUrl
);

const loadProfileData = () => {
  if (username.value) {
    profileStore.fetchProfile(username.value);
    profileStore.fetchUserPosts(username.value);
  }
};

watch(username, () => {
  loadProfileData();
}, { immediate: true });

const selectedFile = ref<File | null>(null);
const picturePreviewUrl = ref<string | null>(null);
const isUploadingPicture = ref(false);
const uploadError = ref<string |null>(null);

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
  <div>
    <div v-if="isLoadingProfile && !currentProfile" class="text-center p-10 text-gray-500 pt-20">
      Loading profile...
    </div>
    
    <div v-else-if="errorProfile" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md m-4 mt-20">
      <p>{{ errorProfile }}</p>
    </div>

    <div v-else-if="currentProfile" class="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 grid grid-cols-12 gap-6 pt-20">
      
      <aside class="col-span-6 sticky top-20 self-start">
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

      <div class="col-span-6 min-w-0">
        <div v-if="isLoadingPosts && userPosts.length === 0" class="text-center p-10 text-gray-500">
          Loading posts...
        </div>
        <div v-else-if="errorPosts" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md">
          {{ errorPosts }}
        </div>
        <div v-else-if="userPosts.length > 0" class="space-y-4">
          <PostItem 
            v-for="post in userPosts" 
            :key="post.id" 
            :post="post" 
          />
        </div>
        <div v-else class="bg-white rounded-lg shadow-md p-10 text-center text-gray-500">
          This user hasn't posted anything yet.
        </div>
        
        <div v-if="userPostsNextPageUrl" ref="loadMoreTrigger" class="h-10"></div>
        <div v-if="isLoadingPosts && userPosts.length > 0" class="text-center p-4 text-gray-500">
          Loading more posts...
        </div>

      </div>
    </div>
  </div>
</template>