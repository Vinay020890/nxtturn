<script setup lang="ts">
import { ref } from 'vue'
import type { UserProfile, ProfileUpdatePayload } from '@/types'
import { useProfileStore } from '@/stores/profile'
import { UserCircleIcon } from '@heroicons/vue/24/solid'
import { Save, Edit3, MoreVertical } from 'lucide-vue-next'
import BaseModal from '@/components/common/BaseModal.vue'
import BaseButton from '@/components/common/BaseButton.vue'

const props = defineProps<{
  profile: UserProfile
  isOwnProfile: boolean
}>()

const profileStore = useProfileStore()
const isModalOpen = ref(false)
const isLoading = ref(false)

const bioData = ref({
  bio: props.profile.bio || '',
})

async function handleSaveChanges() {
  if (isLoading.value) return
  isLoading.value = true
  try {
    const payload: ProfileUpdatePayload = {
      bio: bioData.value.bio,
    }
    await profileStore.updateProfile(props.profile.user.username, payload)
    isModalOpen.value = false
  } catch (error) {
    console.error('Failed to update bio:', error)
  } finally {
    isLoading.value = false
  }
}

function openModal() {
  bioData.value.bio = props.profile.bio || ''
  isModalOpen.value = true
}
</script>

<template>
  <div
    data-cy="bio-card"
    class="bg-white rounded-xl shadow-lg border border-gray-100 p-4 sm:p-6 relative hover:shadow-xl transition-all duration-300"
  >
    <!-- Header -->
    <div class="flex items-center mb-4 sm:mb-6 pb-4 border-b border-gray-100">
      <div
        class="flex items-center justify-center w-8 h-8 sm:w-8 sm:h-8 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg mr-3"
      >
        <UserCircleIcon class="h-4 w-4 sm:h-6 sm:w-6 text-white" />
      </div>
      <h3 class="text-lg sm:text-xl font-bold text-gray-800">Bio</h3>

      <!-- Three Dots Button - Opens Modal Directly -->
      <button
        data-cy="edit-bio-button"
        v-if="isOwnProfile"
        @click="openModal"
        class="ml-auto flex items-center justify-center w-8 h-8 sm:w-8 sm:h-8 rounded-full hover:bg-gray-100 text-gray-600 hover:text-gray-900 transition-all duration-200"
        aria-label="Edit bio"
      >
        <MoreVertical class="h-4 w-4" />
      </button>
    </div>

    <!-- Bio Content -->
    <div class="text-gray-700">
      <p
        v-if="profile.bio"
        class="whitespace-pre-wrap text-gray-600 leading-relaxed text-base sm:text-lg break-words overflow-hidden"
      >
        {{ profile.bio }}
      </p>
      <p v-else class="text-gray-500 italic">No bio available.</p>
    </div>

    <!-- Modal for Editing -->
    <BaseModal :show="isModalOpen" title="Edit Bio" @close="isModalOpen = false" class="max-w-md">
      <div class="space-y-4">
        <!-- Compact Header with Icon -->
        <div
          class="flex items-center gap-3 p-3 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-100"
        >
          <div
            class="flex items-center justify-center w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg"
          >
            <UserCircleIcon class="h-5 w-5 text-white" />
          </div>
          <div>
            <h3 class="text-base font-semibold text-gray-900">Personal Introduction</h3>
            <p class="text-xs text-gray-600">Share something about yourself</p>
          </div>
        </div>

        <!-- Compact Bio Textarea -->
        <div class="space-y-2">
          <label
            for="bio-textarea"
            class="flex items-center gap-2 text-sm font-medium text-gray-700"
          >
            <Edit3 class="h-3 w-3 text-blue-500" />
            Your Bio
          </label>
          <textarea
            id="bio-textarea"
            v-model="bioData.bio"
            rows="4"
            class="w-full p-3 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 resize-none bg-white"
            placeholder="Tell us about your background, interests, and what you're passionate about..."
          ></textarea>
          <p class="text-xs text-gray-500 flex items-center gap-1">
            <svg
              class="h-3 w-3 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            This will be visible on your public profile
          </p>
        </div>
      </div>

      <template #footer>
        <div class="flex flex-col xs:flex-row justify-end gap-2 pt-4 border-t border-gray-100">
          <BaseButton
            @click="isModalOpen = false"
            variant="secondary"
            class="px-4 py-2.5 text-sm font-medium order-2 xs:order-1"
          >
            Cancel
          </BaseButton>
          <BaseButton
            @click="handleSaveChanges"
            :is-loading="isLoading"
            class="px-4 py-2.5 text-sm font-medium bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white shadow-lg hover:shadow-xl transition-all duration-200 flex items-center gap-2 order-1 xs:order-2"
          >
            <Save class="h-3 w-3" v-if="!isLoading" />
            {{ isLoading ? 'Saving...' : 'Save Changes' }}
          </BaseButton>
        </div>
      </template>
    </BaseModal>
  </div>
</template>
