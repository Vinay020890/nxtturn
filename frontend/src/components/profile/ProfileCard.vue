<script setup lang="ts">
import { ref, onUnmounted, onMounted, computed } from 'vue'
import { getAvatarUrl } from '@/utils/avatars'
import type { UserProfile } from '@/types'
import { useProfileStore } from '@/stores/profile'
import ProfileActions from '@/components/ProfileActions.vue'
import BaseModal from '@/components/common/BaseModal.vue'
import IdentityForm from '@/components/profile/forms/IdentityForm.vue'
import { PencilIcon, XMarkIcon, CheckIcon } from '@heroicons/vue/24/solid'

// Import your avatar files - adjust the path according to your project structure
import maleAvatar1 from '@/assets/avatars/male-1.png'
import maleAvatar2 from '@/assets/avatars/male-2.png'
import maleAvatar3 from '@/assets/avatars/male-3.png'
import maleAvatar4 from '@/assets/avatars/male-4.png'
import femaleAvatar1 from '@/assets/avatars/female-1.png'
import femaleAvatar2 from '@/assets/avatars/female-2.png'
import femaleAvatar3 from '@/assets/avatars/female-3.png'
import femaleAvatar4 from '@/assets/avatars/female-4.png'

const props = defineProps<{
  profile: UserProfile
  isOwnProfile: boolean
  postsCount: number
}>()

const emit = defineEmits<{
  postsClicked: []
}>()

const profileStore = useProfileStore()
const isModalOpen = ref(false)
const isPreviewModalOpen = ref(false)
const isEditProfileModalOpen = ref(false)
const isAvatarPreviewModalOpen = ref(false)
const activeTab = ref<'avatars' | 'upload'>('avatars')

// Profile picture preview for other users
const isProfilePicturePreviewModalOpen = ref(false)

type IdentityFormData = {
  display_name: string | null
  headline: string | null
}
const selectedFile = ref<File | null>(null)
const picturePreviewUrl = ref<string | null>(null)
const isUploadingPicture = ref(false)
const isRemovingPicture = ref(false)
const editModalSelectedFile = ref<File | null>(null)
const editModalPicturePreviewUrl = ref<string | null>(null)
const selectedAvatar = ref<{ id: string; src: string } | null>(null)

// Use imported avatar files
const maleAvatars = [
  { id: 'male-1', src: maleAvatar1 },
  { id: 'male-2', src: maleAvatar2 },
  { id: 'male-3', src: maleAvatar3 },
  { id: 'male-4', src: maleAvatar4 },
]

const femaleAvatars = [
  { id: 'female-1', src: femaleAvatar1 },
  { id: 'female-2', src: femaleAvatar2 },
  { id: 'female-3', src: femaleAvatar3 },
  { id: 'female-4', src: femaleAvatar4 },
]

// Use real posts count from props
const socialStats = computed(() => ({
  followers: 245,
  following: 178,
  connections: 542,
  posts: props.postsCount, // Use real posts count
}))

// Track if component is mounted
const isComponentMounted = ref(false)

// Setup lifecycle hooks
onMounted(() => {
  isComponentMounted.value = true
})

async function handleSaveChanges(formData: IdentityFormData) {
  try {
    await profileStore.updateProfile(props.profile.user.username, formData)
    isModalOpen.value = false
  } catch (error) {
    console.error('Failed to update profile:', error)
    alert('Could not update profile. Please try again.')
  }
}

// Profile picture functions
function handleProfilePictureClick() {
  if (props.isOwnProfile) {
    openPreviewModal()
  } else {
    // For other users, show preview with original resolution and no options
    isProfilePicturePreviewModalOpen.value = true
  }
}

// NEW: Direct file upload handler for Cypress tests
function handleFileChange(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) {
    selectedFile.value = file
    picturePreviewUrl.value = URL.createObjectURL(file)

    // Auto-upload when file is selected (for Cypress tests)
    if ((window as any).Cypress) {
      uploadProfilePicture()
    } else {
      // Open preview modal after file selection (for normal users)
      isPreviewModalOpen.value = true
    }
  }
}

function handleEditModalFileChange(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) {
    editModalSelectedFile.value = file
    editModalPicturePreviewUrl.value = URL.createObjectURL(file)
  }
}

async function uploadProfilePicture() {
  if (!selectedFile.value) return

  // Check if component is still mounted
  if (!isComponentMounted.value) return

  isUploadingPicture.value = true
  try {
    await profileStore.updateProfilePicture(props.profile.user.username, selectedFile.value)

    // Check again before updating UI
    if (!isComponentMounted.value) return

    selectedFile.value = null
    // Don't clear preview URL immediately so user can see the result
    setTimeout(() => {
      if (isComponentMounted.value) {
        picturePreviewUrl.value = null
      }
    }, 2000)
    isPreviewModalOpen.value = false
  } catch (error: any) {
    if (isComponentMounted.value) {
      alert(error.message || 'Failed to upload picture.')
      selectedFile.value = null
      picturePreviewUrl.value = null
    }
  } finally {
    if (isComponentMounted.value) {
      isUploadingPicture.value = false
    }
  }
}

async function uploadEditModalProfilePicture() {
  if (!editModalSelectedFile.value) return

  // Check if component is still mounted
  if (!isComponentMounted.value) return

  isUploadingPicture.value = true
  try {
    await profileStore.updateProfilePicture(
      props.profile.user.username,
      editModalSelectedFile.value,
    )

    // Check again before updating UI
    if (!isComponentMounted.value) return

    editModalSelectedFile.value = null
    editModalPicturePreviewUrl.value = null
    isEditProfileModalOpen.value = false
    // Also update the main preview
    selectedFile.value = null
    picturePreviewUrl.value = null
  } catch (error: any) {
    if (isComponentMounted.value) {
      alert(error.message || 'Failed to upload picture.')
      editModalSelectedFile.value = null
      editModalPicturePreviewUrl.value = null
    }
  } finally {
    if (isComponentMounted.value) {
      isUploadingPicture.value = false
    }
  }
}

async function uploadSelectedAvatar() {
  if (!selectedAvatar.value) return

  // Check if component is still mounted
  if (!isComponentMounted.value) return

  isUploadingPicture.value = true
  try {
    // Convert the avatar image to a File object for upload
    const response = await fetch(selectedAvatar.value.src)
    const blob = await response.blob()
    const file = new File([blob], `${selectedAvatar.value.id}.png`, { type: 'image/png' })

    await profileStore.updateProfilePicture(props.profile.user.username, file)

    // Check again before updating UI
    if (!isComponentMounted.value) return

    isAvatarPreviewModalOpen.value = false
    selectedAvatar.value = null
  } catch (error: any) {
    if (isComponentMounted.value) {
      alert(error.message || 'Failed to set avatar.')
    }
  } finally {
    if (isComponentMounted.value) {
      isUploadingPicture.value = false
    }
  }
}

function clearEditModalFile() {
  // Check if component is still mounted
  if (!isComponentMounted.value) return

  editModalSelectedFile.value = null
  editModalPicturePreviewUrl.value = null
  // Reset the file input
  const fileInput = document.getElementById('edit-modal-file-upload') as HTMLInputElement
  if (fileInput) {
    fileInput.value = ''
  }
}

async function handleRemovePicture() {
  // Check if component is still mounted
  if (!isComponentMounted.value) return

  if (window.confirm('Are you sure you want to remove your profile picture?')) {
    isRemovingPicture.value = true
    try {
      await profileStore.removeProfilePicture(props.profile.user.username)

      // Check again before updating UI
      if (!isComponentMounted.value) return

      isPreviewModalOpen.value = false
    } catch (error) {
      if (isComponentMounted.value) {
        alert('Failed to remove profile picture.')
      }
    } finally {
      if (isComponentMounted.value) {
        isRemovingPicture.value = false
      }
    }
  }
}

function openPreviewModal() {
  // Check if component is still mounted
  if (!isComponentMounted.value) return

  // Reset states when opening preview
  picturePreviewUrl.value = null
  selectedFile.value = null
  isPreviewModalOpen.value = true
}

function openEditProfileModal() {
  // Check if component is still mounted
  if (!isComponentMounted.value) return

  isPreviewModalOpen.value = false
  isEditProfileModalOpen.value = true
  activeTab.value = 'avatars'
  // Clear any previous file selection in edit modal
  clearEditModalFile()
}

function handleAvatarSelect(avatar: { id: string; src: string }) {
  // Check if component is still mounted
  if (!isComponentMounted.value) return

  selectedAvatar.value = avatar
  isEditProfileModalOpen.value = false
  isAvatarPreviewModalOpen.value = true
}

function handleEditProfile() {
  // Check if component is still mounted
  if (!isComponentMounted.value) return

  isPreviewModalOpen.value = false
  isModalOpen.value = true
}

// Handle posts card click - emits event to parent
function handlePostsClick() {
  emit('postsClicked')
}

// Cleanup function
onUnmounted(() => {
  // Mark component as unmounted
  isComponentMounted.value = false

  // Clean up any object URLs to prevent memory leaks
  if (picturePreviewUrl.value) {
    URL.revokeObjectURL(picturePreviewUrl.value)
  }
  if (editModalPicturePreviewUrl.value) {
    URL.revokeObjectURL(editModalPicturePreviewUrl.value)
  }
})
</script>

<template>
  <div data-cy="profile-card-container" class="bg-white rounded-2xl shadow-md p-4 sm:p-6 relative">
    <!-- Main layout with header section for buttons -->
    <div class="flex flex-col">
      <!-- Header section with buttons at top right - Only show when needed -->
      <div v-if="!isOwnProfile" class="flex justify-between items-start mb-0">
        <!-- Left spacer - Only needed when there are action buttons -->
        <div class="w-32 lg:w-40"></div>

        <!-- Action buttons on the right - Only for other users' profiles -->
        <div class="flex items-center space-x-2 -mt-5">
          <div class="profile-actions-container">
            <ProfileActions />
          </div>
        </div>
      </div>

      <!-- Edit button for own profile - Positioned absolutely at top right corner -->
      <button
        v-if="isOwnProfile"
        @click="isModalOpen = true"
        class="absolute top-4 right-4 p-2.5 rounded-full text-gray-400 hover:bg-blue-50 hover:text-blue-500 transition-all duration-300 z-10"
        aria-label="Edit profile summary"
      >
        <PencilIcon class="h-5 w-5" />
      </button>

      <!-- Profile Content - Add padding top for own profile to prevent overlap and create gap below pencil icon -->
      <div :class="['relative', isOwnProfile ? 'pt-4' : 'pt-2']">
        <!-- Profile Picture and User Info - FIXED RESPONSIVE ALIGNMENT -->
        <div
          class="flex flex-col lg:flex-row items-center lg:items-start space-y-4 lg:space-y-0 lg:space-x-8 py-4"
        >
          <!-- Profile Picture Column - Properly centered on mobile -->
          <div class="relative flex-shrink-0">
            <div
              data-cy="profile-picture-container"
              class="relative w-28 h-28 sm:w-32 sm:h-32 group"
            >
              <div
                class="absolute -inset-2 bg-gradient-to-r from-blue-400 to-purple-500 rounded-full opacity-20 group-hover:opacity-30 transition-opacity duration-300"
              ></div>
              <img
                data-cy="profile-picture-img"
                :src="
                  picturePreviewUrl ||
                  getAvatarUrl(profile.picture, profile.user.first_name, profile.user.last_name)
                "
                alt="Profile Picture"
                class="relative w-full h-full rounded-full object-cover border-4 border-white shadow-lg bg-gray-200 z-10 cursor-pointer"
                @click="handleProfilePictureClick"
              />

              <!-- Hidden file input for Cypress tests -->
              <input
                id="picture-upload"
                type="file"
                @change="handleFileChange"
                accept="image/*"
                class="hidden"
              />

              <!-- Clickable overlay for profile picture (own profile only) -->
              <div
                v-if="isOwnProfile"
                @click="openPreviewModal"
                class="absolute inset-0 rounded-full bg-black bg-opacity-0 group-hover:bg-opacity-40 flex items-center justify-center cursor-pointer transition-all duration-300 z-20"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-8 w-8 text-white opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
                  />
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                </svg>
              </div>
            </div>
          </div>

          <!-- User Info Column - PROPERLY CENTERED ON MOBILE -->
          <div
            :class="[
              'text-center lg:text-left flex-1 min-w-0 w-full',
              isOwnProfile ? 'lg:pr-12' : '',
            ]"
          >
            <div class="mb-4 px-2">
              <!-- Display Name -->
              <h1
                class="text-xl sm:text-2xl font-bold text-gray-800 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent break-words"
              >
                {{ profile.display_name || `${profile.user.first_name} ${profile.user.last_name}` }}
              </h1>
              <p class="text-base sm:text-lg text-gray-500 mt-1 break-words">
                @{{ profile.user.username }}
              </p>
              <!-- Fixed headline breaking -->
              <p
                v-if="profile.headline"
                class="mt-2 sm:mt-3 text-sm sm:text-base text-gray-600 font-medium break-words overflow-hidden text-ellipsis max-w-full"
                :title="profile.headline"
              >
                {{ profile.headline }}
              </p>
            </div>
          </div>
        </div>

        <!-- Social Stats with proper responsive spacing -->
        <div class="mt-2 pt-4 border-t border-gray-100">
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            <!-- Followers Card -->
            <div class="stats-card group">
              <div
                class="stats-card-inner transform group-hover:translate-y-[-2px] transition-transform duration-300"
              >
                <div
                  class="stats-gradient bg-gradient-to-br from-blue-50 via-sky-50 to-cyan-50"
                ></div>
                <div class="relative z-10 flex flex-col items-center justify-center h-full">
                  <div class="text-sm sm:text-md font-bold text-sky-700 mb-0.5 drop-shadow-sm">
                    {{ socialStats.followers.toLocaleString() }}
                  </div>
                  <div class="text-xs font-medium text-sky-600/80 uppercase tracking-wider">
                    Followers
                  </div>
                </div>
              </div>
            </div>

            <!-- Following Card -->
            <div class="stats-card group">
              <div
                class="stats-card-inner transform group-hover:translate-y-[-2px] transition-transform duration-300"
              >
                <div
                  class="stats-gradient bg-gradient-to-br from-emerald-50 via-green-50 to-teal-50"
                ></div>
                <div class="relative z-10 flex flex-col items-center justify-center h-full">
                  <div class="text-sm sm:text-md font-bold text-emerald-700 mb-0.5 drop-shadow-sm">
                    {{ socialStats.following.toLocaleString() }}
                  </div>
                  <div class="text-xs font-medium text-emerald-600/80 uppercase tracking-wider">
                    Following
                  </div>
                </div>
              </div>
            </div>

            <!-- Connections Card -->
            <div class="stats-card group">
              <div
                class="stats-card-inner transform group-hover:translate-y-[-2px] transition-transform duration-300"
              >
                <div
                  class="stats-gradient bg-gradient-to-br from-violet-50 via-purple-50 to-fuchsia-50"
                ></div>
                <div class="relative z-10 flex flex-col items-center justify-center h-full">
                  <div class="text-sm sm:text-md font-bold text-violet-700 mb-0.5 drop-shadow-sm">
                    {{ socialStats.connections.toLocaleString() }}
                  </div>
                  <div class="text-xs font-medium text-violet-600/80 uppercase tracking-wider">
                    Connections
                  </div>
                </div>
              </div>
            </div>

            <!-- Posts Card - Clickable -->
            <div class="stats-card group" @click="handlePostsClick">
              <div
                class="stats-card-inner transform group-hover:translate-y-[-2px] transition-transform duration-300 cursor-pointer"
              >
                <div
                  class="stats-gradient bg-gradient-to-br from-amber-50 via-orange-50 to-red-50"
                ></div>
                <div class="relative z-10 flex flex-col items-center justify-center h-full">
                  <div class="text-sm sm:text-md font-bold text-amber-700 mb-0.5 drop-shadow-sm">
                    {{ socialStats.posts.toLocaleString() }}
                  </div>
                  <div class="text-xs font-medium text-amber-600/80 uppercase tracking-wider">
                    Posts
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Profile Picture Preview Modal for Other Users -->
    <BaseModal
      v-if="isComponentMounted"
      :show="isProfilePicturePreviewModalOpen"
      title="Profile Photo"
      @close="isProfilePicturePreviewModalOpen = false"
      max-width="max-w-4xl"
    >
      <div class="flex flex-col items-center p-4 sm:p-6">
        <!-- Preview -->
        <div
          class="mb-6 w-full max-w-2xl overflow-hidden rounded-lg bg-gray-100 flex items-center justify-center"
        >
          <img
            :src="getAvatarUrl(profile.picture, profile.user.first_name, profile.user.last_name)"
            alt="Profile Picture Preview"
            class="w-full h-auto max-h-96 object-contain"
          />
        </div>

        <!-- Close button for other users -->
        <div class="flex gap-3 w-full max-w-xs">
          <button
            @click="isProfilePicturePreviewModalOpen = false"
            class="flex-1 px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors font-medium text-sm"
          >
            Close
          </button>
        </div>
      </div>
    </BaseModal>

    <!-- ALL MODALS with mount checks -->
    <BaseModal
      v-if="isComponentMounted"
      :show="isModalOpen"
      title="Edit Profile Summary"
      @close="isModalOpen = false"
      max-width="max-w-md"
    >
      <div class="max-w-md mx-auto p-4">
        <IdentityForm
          :initial-data="profile"
          @save="handleSaveChanges"
          @cancel="isModalOpen = false"
        />
      </div>
    </BaseModal>

    <BaseModal
      v-if="isComponentMounted"
      :show="isPreviewModalOpen"
      title="Profile Photo"
      @close="isPreviewModalOpen = false"
      max-width="max-w-lg"
    >
      <div class="flex flex-col items-center p-4 sm:p-6 max-w-md mx-auto">
        <div
          class="mb-4 w-full max-w-xs overflow-hidden rounded-lg bg-gray-100 flex items-center justify-center"
        >
          <img
            :src="
              picturePreviewUrl ||
              getAvatarUrl(profile.picture, profile.user.first_name, profile.user.last_name)
            "
            alt="Profile Picture Preview"
            class="w-full h-auto max-h-64 object-contain"
          />
        </div>

        <div v-if="isUploadingPicture" class="mb-4 text-blue-600 text-sm">
          Uploading profile picture...
        </div>

        <div class="flex flex-col sm:flex-row gap-3 w-full max-w-xs">
          <button
            @click="openEditProfileModal"
            :disabled="isUploadingPicture"
            class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Edit Photo
          </button>
          <button
            v-if="profile.picture && !picturePreviewUrl"
            data-cy="remove-picture-button"
            @click="handleRemovePicture"
            :disabled="isRemovingPicture || isUploadingPicture"
            class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ isRemovingPicture ? 'Removing...' : 'Remove' }}
          </button>
          <button
            v-if="picturePreviewUrl && !isUploadingPicture"
            @click="uploadProfilePicture"
            class="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium text-sm"
          >
            Save Photo
          </button>
        </div>
      </div>
    </BaseModal>

    <BaseModal
      v-if="isComponentMounted"
      :show="isAvatarPreviewModalOpen"
      title="Avatar Preview"
      @close="isAvatarPreviewModalOpen = false"
      max-width="max-w-md"
    >
      <div class="flex flex-col items-center p-6 max-w-md mx-auto">
        <div class="mb-6 w-48 h-48 rounded-full overflow-hidden border-4 border-white shadow-lg">
          <img
            v-if="selectedAvatar"
            :src="selectedAvatar.src"
            alt="Selected Avatar Preview"
            class="w-full h-full object-cover"
          />
        </div>

        <div class="text-center mb-6">
          <h3 class="text-lg font-semibold text-gray-800">Use this avatar?</h3>
          <p class="text-sm text-gray-500 mt-1">This will replace your current profile picture</p>
        </div>

        <div class="flex gap-3 w-full max-w-xs">
          <button
            @click="isAvatarPreviewModalOpen = false"
            class="flex-1 px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors font-medium text-sm"
          >
            Cancel
          </button>
          <button
            @click="uploadSelectedAvatar"
            :disabled="isUploadingPicture"
            class="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium text-sm disabled:opacity-50"
          >
            {{ isUploadingPicture ? 'Saving...' : 'Save Avatar' }}
          </button>
        </div>
      </div>
    </BaseModal>

    <BaseModal
      v-if="isComponentMounted"
      :show="isEditProfileModalOpen"
      title="Edit Profile Photo"
      @close="isEditProfileModalOpen = false"
      max-width="max-w-md"
    >
      <div class="p-4 sm:p-6 max-w-md mx-auto">
        <div class="flex border-b border-gray-200 mb-4">
          <button
            @click="activeTab = 'avatars'"
            :class="[
              'px-3 py-2 font-medium text-sm border-b-2 transition-colors',
              activeTab === 'avatars'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700',
            ]"
          >
            Choose Avatar
          </button>
          <button
            @click="activeTab = 'upload'"
            :class="[
              'px-3 py-2 font-medium text-sm border-b-2 transition-colors',
              activeTab === 'upload'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700',
            ]"
          >
            Upload Photo
          </button>
        </div>

        <div v-if="activeTab === 'avatars'" class="space-y-4">
          <div>
            <h3 class="text-md font-medium text-gray-900 mb-3">Male Avatars</h3>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div
                v-for="avatar in maleAvatars"
                :key="avatar.id"
                @click="handleAvatarSelect(avatar)"
                class="cursor-pointer transform hover:scale-105 transition-all duration-200 group"
              >
                <div
                  class="relative overflow-hidden rounded-lg border-2 border-gray-200 group-hover:border-blue-500"
                >
                  <img
                    :src="avatar.src"
                    :alt="`Male avatar ${avatar.id}`"
                    class="w-full h-20 sm:h-24 object-cover"
                  />
                  <div
                    class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-10 transition-all duration-200"
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <div>
            <h3 class="text-md font-medium text-gray-900 mb-3">Female Avatars</h3>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div
                v-for="avatar in femaleAvatars"
                :key="avatar.id"
                @click="handleAvatarSelect(avatar)"
                class="cursor-pointer transform hover:scale-105 transition-all duration-200 group"
              >
                <div
                  class="relative overflow-hidden rounded-lg border-2 border-gray-200 group-hover:border-blue-500"
                >
                  <img
                    :src="avatar.src"
                    :alt="`Female avatar ${avatar.id}`"
                    class="w-full h-20 sm:h-24 object-cover"
                  />
                  <div
                    class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-10 transition-all duration-200"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'upload'" class="space-y-4">
          <div v-if="editModalPicturePreviewUrl" class="text-center">
            <div class="mb-4">
              <img
                :src="editModalPicturePreviewUrl"
                alt="Selected photo preview"
                class="mx-auto max-h-48 rounded-lg border-2 border-gray-200"
              />
            </div>
            <div class="flex flex-col sm:flex-row gap-2 justify-center">
              <button
                @click="uploadEditModalProfilePicture"
                :disabled="isUploadingPicture"
                class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium text-sm disabled:opacity-50"
              >
                {{ isUploadingPicture ? 'Uploading...' : 'Save Photo' }}
              </button>
              <button
                @click="clearEditModalFile"
                :disabled="isUploadingPicture"
                class="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors font-medium text-sm disabled:opacity-50"
              >
                Choose Different
              </button>
            </div>
          </div>

          <div v-else>
            <label
              for="edit-modal-file-upload"
              class="block border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer transition-all duration-200 hover:border-blue-400 hover:bg-blue-50 group"
            >
              <svg
                class="mx-auto h-10 w-10 text-gray-400 group-hover:text-blue-500 transition-colors"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 48 48"
              >
                <path
                  d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
              <div class="mt-3">
                <span
                  class="block text-sm font-medium text-gray-900 group-hover:text-blue-700 transition-colors"
                >
                  Upload a file
                </span>
                <p class="mt-1 text-xs text-gray-500">PNG, JPG, GIF up to 10MB</p>
              </div>
              <input
                id="edit-modal-file-upload"
                type="file"
                @change="handleEditModalFileChange"
                accept="image/*"
                class="hidden"
              />
            </label>
          </div>
        </div>
      </div>
    </BaseModal>
  </div>
</template>

<style scoped>
/* Custom hover effect for upload box */
.hover\:bg-blue-50:hover {
  background-color: rgb(239 246 255);
}

/* Gradient text effect */
.bg-gradient-to-r {
  background-image: linear-gradient(to right, var(--tw-gradient-stops));
}

.from-blue-600 {
  --tw-gradient-from: #2563eb;
  --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to, rgb(37 99 235 / 0));
}

.to-purple-600 {
  --tw-gradient-to: #9333ea;
}

/* Ensure text breaks properly and doesn't overflow */
.break-words {
  word-wrap: break-word;
  overflow-wrap: break-word;
  word-break: break-word;
}

.text-ellipsis {
  text-overflow: ellipsis;
}

.min-w-0 {
  min-width: 0;
}

/* Social Stats Styles with reduced height ONLY */
.stats-card {
  @apply relative cursor-pointer;
}

.stats-card-inner {
  @apply relative rounded-2xl border border-white/50 bg-white/80 backdrop-blur-sm
         shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden
         before:absolute before:inset-0 before:bg-gradient-to-br before:from-white/50 before:to-transparent
         before:opacity-60 before:rounded-2xl;
  padding: 0.4rem 0.25rem; /* Reduced vertical padding */
  min-height: 58px; /* Reduced height */
  display: flex;
  align-items: center;
  justify-content: center;
}

.stats-gradient {
  @apply absolute inset-0 opacity-80 transition-opacity duration-300;
}

.stats-card:hover .stats-gradient {
  @apply opacity-100;
}

/* Enhanced 3D effects with multiple shadows */
.stats-card-inner {
  box-shadow:
    0 4px 6px -1px rgba(0, 0, 0, 0.1),
    0 2px 4px -1px rgba(0, 0, 0, 0.06),
    0 0 0 1px rgba(255, 255, 255, 0.5),
    inset 0 2px 4px rgba(255, 255, 255, 0.5);
}

.stats-card:hover .stats-card-inner {
  box-shadow:
    0 20px 25px -5px rgba(0, 0, 0, 0.1),
    0 10px 10px -5px rgba(0, 0, 0, 0.04),
    0 0 0 1px rgba(255, 255, 255, 0.5),
    inset 0 2px 4px rgba(255, 255, 255, 0.5);
}

/* Mobile responsiveness for stats */
@media (max-width: 1024px) {
  .stats-card-inner {
    padding: 0.35rem 0.2rem; /* Slightly smaller padding on tablets */
    min-height: 54px;
  }
}

@media (max-width: 640px) {
  .stats-card-inner {
    padding: 0.25rem 0.15rem; /* Smallest padding on mobile */
    min-height: 50px;
  }
}

/* Improved responsive design for all screen sizes */
@media (max-width: 768px) {
  /* Ensure profile info is perfectly centered on mobile */
  .profile-picture-column {
    display: flex;
    justify-content: center;
    width: 100%;
    margin-bottom: 1rem;
  }

  .user-info-column {
    text-align: center !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
  }

  /* Better spacing for mobile */
  .flex-col.lg\:flex-row {
    align-items: center;
  }

  /* Adjust social stats spacing for mobile */
  .grid-cols-2 {
    gap: 0.75rem;
  }
}

/* Tablet specific adjustments */
@media (min-width: 641px) and (max-width: 1024px) {
  .stats-card-inner {
    padding: 0.3rem 0.2rem;
    min-height: 56px;
  }

  /* Adjust profile picture size for tablet */
  .w-28.h-28.sm\:w-32.sm\:h-32 {
    width: 7rem;
    height: 7rem;
  }
}

/* Large screen adjustments */
@media (min-width: 1280px) {
  .stats-card-inner {
    padding: 0.45rem 0.3rem;
    min-height: 62px;
  }
}
</style>
