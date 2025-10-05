<script setup lang="ts">
import { getAvatarUrl } from '@/utils/avatars';
import { ref, watch, computed, onMounted, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import PostItem from '@/components/PostItem.vue';
import { useProfileStore } from '@/stores/profile';
import { useAuthStore } from '@/stores/auth';
import { usePostsStore } from '@/stores/posts';
import { useInfiniteScroll } from '@/composables/useInfiniteScroll';
import { storeToRefs } from 'pinia';
import eventBus from '@/services/eventBus';
import ProfileActions from '@/components/ProfileActions.vue';

const route = useRoute();
const profileStore = useProfileStore();
const authStore = useAuthStore();
const postsStore = usePostsStore();

const {
  currentProfile, isLoadingProfile, isLoadingPosts,
  errorProfile, errorPosts,
  isFollowing, isLoadingFollow, relationshipStatus
} = storeToRefs(profileStore);

const { currentUser, isAuthenticated } = storeToRefs(authStore);
const username = computed(() => route.params.username as string || '');

// --- State for Bio Editing ---
const isEditing = ref(false);
const editableBio = ref('');
const isSaving = ref(false);
const editError = ref<string | null>(null);

// --- State for Picture Management ---
const selectedFile = ref<File | null>(null);
const picturePreviewUrl = ref<string | null>(null);
const isUploadingPicture = ref(false);
const uploadError = ref<string | null>(null);
const isRemovingPicture = ref(false);

// --- State for Picture Options Dropdown ---
const showPictureOptions = ref(false);
const pictureOptionsRef = ref<HTMLDivElement | null>(null);

const userPostIds = computed(() => profileStore.postIdsByUsername[username.value] || []);
const userPostsNextPageUrl = computed(() => profileStore.nextPageUrlByUsername[username.value]);
const userPosts = computed(() => postsStore.getPostsByIds(userPostIds.value));
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
    profileStore.refreshUserPosts(username.value);
    profileStore.fetchRelationshipStatus(username.value);
  }
};

watch(username, () => {
  loadProfileData();
}, { immediate: true });

function handleFileChange(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (file) {
    selectedFile.value = file;
    picturePreviewUrl.value = URL.createObjectURL(file);
    uploadError.value = null;
    showPictureOptions.value = false; // Close menu after selecting
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

// In ProfileView.vue -> <script setup>

async function handleRemovePicture() {
  console.log('--- Step 1: handleRemovePicture called! ---');

  if (!username.value) {
    console.error('Error: username is missing.');
    return;
  }

  // Use a confirmation dialog for safety
  if (window.confirm("Are you sure you want to remove your profile picture?")) {
    console.log('--- Step 2: User confirmed. ---');
    isRemovingPicture.value = true;
    try {
      console.log(`--- Step 3: Calling profileStore.removeProfilePicture for user: ${username.value} ---`);

      // This is the line we need to confirm is being executed.
      await profileStore.removeProfilePicture(username.value);

      console.log('--- Step 4: API call successful! ---');
    } catch (error) {
      console.error('--- ERROR: The store action failed! ---', error);
      alert("Failed to remove profile picture.");
    } finally {
      isRemovingPicture.value = false;
      console.log('--- Step 5: Function finished. ---');
    }
  } else {
    console.log('--- User CANCELED the action. ---');
  }
}

function toggleEditMode() {
  isEditing.value = !isEditing.value;
  if (isEditing.value && currentProfile.value) {
    editableBio.value = currentProfile.value.bio || '';
  }
  editError.value = null;
}

async function handleProfileUpdate() {
  if (!isOwnProfile.value || !currentProfile.value) return;
  isSaving.value = true;
  editError.value = null;
  try {
    await profileStore.updateProfile(currentProfile.value.user.username, {
      bio: editableBio.value,
    });
    isEditing.value = false;
  } catch (error: any) {
    editError.value = error.message;
  } finally {
    isSaving.value = false;
  }
}

function togglePictureOptions() {
  showPictureOptions.value = !showPictureOptions.value;
}

const closeOnClickOutside = (event: MouseEvent) => {
  if (pictureOptionsRef.value && !pictureOptionsRef.value.contains(event.target as Node)) {
    showPictureOptions.value = false;
  }
};

watch(showPictureOptions, (isOpen) => {
  if (isOpen) {
    setTimeout(() => document.addEventListener('click', closeOnClickOutside), 0);
  } else {
    document.removeEventListener('click', closeOnClickOutside);
  }
});

// --- ADD THIS BLOCK to handle scrolling ---
function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

onMounted(() => {
  eventBus.on('scroll-profile-to-top', scrollToTop);
});

onUnmounted(() => {
  eventBus.off('scroll-profile-to-top', scrollToTop);
});
// --- END OF NEW BLOCK ---

</script>

<template>
  <div>
    <div v-if="isLoadingProfile && !currentProfile" class="text-center p-10 text-gray-500 pt-20">
      Loading profile...
    </div>

    <div v-else-if="errorProfile" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md m-4 mt-20">
      <p>{{ errorProfile }}</p>
    </div>

    <div v-else-if="currentProfile"
      class="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 grid grid-cols-12 gap-6 pt-20">

      <aside class="col-span-6 sticky top-20 self-start">
        <div class="bg-white rounded-lg shadow-md p-6">

          <div v-if="!isEditing" class="flex flex-col items-center text-center">

            <div data-cy="profile-picture-container" class="relative w-32 h-32 mb-4 group" ref="pictureOptionsRef">
              <img data-cy="profile-picture-img"
                :src="picturePreviewUrl || getAvatarUrl(currentProfile.picture, currentProfile.user.first_name, currentProfile.user.last_name)"
                alt="Profile Picture"
                class="w-full h-full rounded-full object-cover border-4 border-white shadow-lg bg-gray-200">

              <div v-if="isOwnProfile" @click.stop="togglePictureOptions"
                class="absolute inset-0 rounded-full bg-black bg-opacity-0 group-hover:bg-opacity-40 flex items-center justify-center cursor-pointer transition-opacity duration-300">
                <svg xmlns="http://www.w3.org/2000/svg"
                  class="h-8 w-8 text-white opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                  fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round"
                    d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>

              <div v-if="showPictureOptions"
                class="origin-top-left absolute left-1/2 -translate-x-1/2 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-10">
                <ul class="py-1">
                  <li>
                    <label for="picture-upload"
                      class="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 cursor-pointer">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-3 text-gray-500" fill="none"
                        viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round"
                          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                      </svg>
                      Upload a photo
                    </label>
                    <input id="picture-upload" type="file" @change="handleFileChange" accept="image/*" class="hidden">
                  </li>
                  <li v-if="currentProfile.picture">
                    <button data-cy="remove-picture-button" @click.stop="handleRemovePicture"
                      :disabled="isRemovingPicture"
                      class="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 disabled:opacity-50">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-3 text-red-500" fill="none"
                        viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round"
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                      Remove photo
                    </button>
                  </li>
                </ul>
              </div>
            </div>

            <h1 class="text-2xl font-bold text-gray-800">{{ currentProfile.user.first_name }} {{
              currentProfile.user.last_name }}</h1>
            <p class="text-md text-gray-500">@{{ currentProfile.user.username }}</p>
            <p data-cy="profile-bio-display" v-if="currentProfile.bio" class="mt-4 text-sm text-gray-600">{{
              currentProfile.bio }}</p>

            <button v-if="isOwnProfile" @click="toggleEditMode" data-cy="edit-profile-button"
              class="mt-4 w-full bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2 px-4 rounded-full transition">
              Edit Profile
            </button>
            <ProfileActions v-if="!isOwnProfile && relationshipStatus" />
          </div>

          <!-- EDIT MODE: Shown only when isEditing is true -->
          <div v-else>
            <h2 class="text-xl font-bold mb-4">Edit Profile</h2>
            <form @submit.prevent="handleProfileUpdate">
              <div>
                <label for="bio" class="block text-sm font-medium text-gray-700">Bio</label>
                <textarea id="bio" v-model="editableBio" data-cy="bio-textarea" rows="4"
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"></textarea>
              </div>
              <div v-if="editError" class="mt-2 text-sm text-red-600">{{ editError }}</div>
              <div class="mt-4 flex justify-end gap-3">
                <button @click="toggleEditMode" type="button"
                  class="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50">
                  Cancel
                </button>
                <button type="submit" data-cy="save-profile-button" :disabled="isSaving"
                  class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-full disabled:bg-blue-300">
                  {{ isSaving ? 'Saving...' : 'Save Changes' }}
                </button>
              </div>
            </form>
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
          <PostItem v-for="post in userPosts" :key="post.id" :post="post" />
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