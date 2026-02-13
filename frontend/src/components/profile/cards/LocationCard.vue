<script setup lang="ts">
import { ref, computed } from 'vue'
import type { UserProfile, ProfileUpdatePayload } from '@/types'
import { useProfileStore } from '@/stores/profile'
import { MapPinIcon, BriefcaseIcon, GlobeAltIcon } from '@heroicons/vue/24/solid'
import { Save, MapPin, Building2, Globe, Edit3, MoreVertical } from 'lucide-vue-next'
import BaseModal from '@/components/common/BaseModal.vue'
import BaseButton from '@/components/common/BaseButton.vue'

const props = defineProps<{
  profile: UserProfile
  isOwnProfile: boolean
}>()

const profileStore = useProfileStore()
const isModalOpen = ref(false)
const isLoading = ref(false)

// Form state for the editing modal
const locationData = ref<ProfileUpdatePayload>({
  location_city: props.profile.location_city || '',
  location_administrative_area: props.profile.location_administrative_area || '',
  location_country: props.profile.location_country || '',
  current_work_style: props.profile.current_work_style || '',
  is_open_to_relocation: props.profile.is_open_to_relocation || false,
})

// A computed property to format the location for display, filtering out empty parts.
const displayLocation = computed(() => {
  return [
    props.profile.location_city,
    props.profile.location_administrative_area,
    props.profile.location_country,
  ]
    .filter(Boolean) // Removes any null, undefined, or empty strings
    .join(', ')
})

const workStyleDisplay = computed(() => {
  const styles = {
    on_site: 'On-Site',
    hybrid: 'Hybrid',
    remote: 'Remote',
  }
  const styleKey = props.profile.current_work_style
  return styleKey ? styles[styleKey] : ''
})

async function handleSaveChanges() {
  if (isLoading.value) return
  isLoading.value = true
  try {
    const payload: ProfileUpdatePayload = { ...locationData.value }
    await profileStore.updateProfile(props.profile.user.username, payload)
    isModalOpen.value = false
  } catch (error) {
    console.error('Failed to update location:', error)
  } finally {
    isLoading.value = false
  }
}

function openModal() {
  // Sync form data with the latest profile props when opening the modal
  locationData.value = {
    location_city: props.profile.location_city || '',
    location_administrative_area: props.profile.location_administrative_area || '',
    location_country: props.profile.location_country || '',
    current_work_style: props.profile.current_work_style || '',
    is_open_to_relocation: props.profile.is_open_to_relocation || false,
  }
  isModalOpen.value = true
}
</script>

<template>
  <div
    data-cy="location-card"
    class="bg-white rounded-xl shadow-lg border border-gray-100 p-4 sm:p-6 relative hover:shadow-xl transition-all duration-300"
  >
    <!-- Header -->
    <div class="flex items-center mb-4 sm:mb-6 pb-4 border-b border-gray-100">
      <div
        class="flex items-center justify-center w-6 h-6 sm:w-8 sm:h-8 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg mr-3"
      >
        <MapPinIcon class="h-4 w-4 sm:h-6 sm:w-6 text-white" />
      </div>
      <h3 class="text-lg sm:text-xl font-bold text-gray-800">Location</h3>

      <!-- Three Dots Button - Opens Modal Directly -->
      <button
        data-cy="edit-location-button"
        v-if="isOwnProfile"
        @click="openModal"
        class="ml-auto flex items-center justify-center w-8 h-8 sm:w-8 sm:h-8 rounded-full hover:bg-gray-100 text-gray-600 hover:text-gray-900 transition-all duration-200"
        aria-label="Edit location"
      >
        <MoreVertical class="h-4 w-4" />
      </button>
    </div>

    <!-- Display Section -->
    <div class="space-y-3 sm:space-y-4">
      <!-- Location -->
      <div
        v-if="displayLocation"
        class="flex items-start p-3 sm:p-4 bg-blue-50 rounded-xl border border-blue-100"
      >
        <MapPinIcon class="h-4 w-4 sm:h-5 sm:w-5 text-blue-500 mr-2 sm:mr-3 mt-0.5 flex-shrink-0" />
        <div class="min-w-0 flex-1">
          <p class="font-medium text-gray-900 text-sm sm:text-base">Current Location</p>
          <p class="text-gray-600 text-sm sm:text-base break-words">{{ displayLocation }}</p>
        </div>
      </div>

      <!-- Work Style -->
      <div
        v-if="workStyleDisplay"
        class="flex items-start p-3 sm:p-4 bg-purple-50 rounded-xl border border-purple-100"
      >
        <BriefcaseIcon
          class="h-4 w-4 sm:h-5 sm:w-5 text-purple-500 mr-2 sm:mr-3 mt-0.5 flex-shrink-0"
        />
        <div class="min-w-0 flex-1">
          <p class="font-medium text-gray-900 text-sm sm:text-base">Work Preference</p>
          <div class="flex items-center mt-1">
            <span
              >Currently working <strong>{{ workStyleDisplay }}</strong></span
            >
          </div>
        </div>
      </div>

      <!-- Relocation -->
      <div
        v-if="profile.is_open_to_relocation"
        class="flex items-start p-3 sm:p-4 bg-amber-50 rounded-xl border border-amber-100"
      >
        <GlobeAltIcon
          class="h-4 w-4 sm:h-5 sm:w-5 text-amber-500 mr-2 sm:mr-3 mt-0.5 flex-shrink-0"
        />
        <div class="min-w-0 flex-1">
          <p class="font-medium text-gray-900 text-sm sm:text-base">Relocation</p>
          <p class="text-amber-700 font-medium text-sm sm:text-base">
            Open to relocation opportunities
          </p>
        </div>
      </div>

      <!-- Empty State -->
      <p
        v-if="!displayLocation && !workStyleDisplay && !profile.is_open_to_relocation"
        class="text-gray-500 italic"
      >
        No location information provided.
      </p>
    </div>

    <!-- Ultra Compact Modal for Editing -->
    <BaseModal
      :show="isModalOpen"
      title="Location & Work"
      @close="isModalOpen = false"
      class="max-w-sm"
    >
      <div class="space-y-3">
        <!-- Location Section - Ultra Compact -->
        <div class="space-y-2">
          <div class="flex items-center gap-2 p-2 bg-green-50 rounded border border-green-100">
            <div class="flex items-center justify-center w-7 h-7 bg-green-500 rounded">
              <MapPin class="h-4 w-4 text-white" />
            </div>
            <div>
              <h3 class="text-xs font-semibold text-gray-900">Location</h3>
              <p class="text-xs text-gray-600">Your current location</p>
            </div>
          </div>

          <div class="grid grid-cols-1 gap-1.5">
            <div class="space-y-1">
              <label for="country" class="block text-xs font-medium text-gray-700">Country</label>
              <input
                v-model="locationData.location_country"
                type="text"
                id="country"
                class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded focus:ring-1 focus:ring-green-500 focus:border-green-500 transition-all duration-200 outline-none"
                placeholder="Country"
              />
            </div>
            <div class="grid grid-cols-2 gap-1.5">
              <div class="space-y-1">
                <label for="state" class="block text-xs font-medium text-gray-700">State</label>
                <input
                  v-model="locationData.location_administrative_area"
                  type="text"
                  id="state"
                  class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded focus:ring-1 focus:ring-green-500 focus:border-green-500 transition-all duration-200 outline-none"
                  placeholder="State"
                />
              </div>
              <div class="space-y-1">
                <label for="city" class="block text-xs font-medium text-gray-700">City</label>
                <input
                  v-model="locationData.location_city"
                  type="text"
                  id="city"
                  class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded focus:ring-1 focus:ring-green-500 focus:border-green-500 transition-all duration-200 outline-none"
                  placeholder="City"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Work Preferences - Ultra Compact -->
        <div class="space-y-2">
          <div class="flex items-center gap-2 p-2 bg-purple-50 rounded border border-purple-100">
            <div class="flex items-center justify-center w-7 h-7 bg-purple-500 rounded">
              <Building2 class="h-4 w-4 text-white" />
            </div>
            <div>
              <h3 class="text-xs font-semibold text-gray-900">Work</h3>
              <p class="text-xs text-gray-600">Work preferences</p>
            </div>
          </div>

          <div class="space-y-2">
            <div class="space-y-1">
              <label for="work-style" class="block text-xs font-medium text-gray-700"
                >Work Style</label
              >
              <select
                v-model="locationData.current_work_style"
                id="work-style"
                class="w-full px-2 py-1.5 text-xs border rounded focus:ring-1 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 bg-white outline-none"
              >
                <option value="">Select style</option>
                <option value="on_site">On-Site</option>
                <option value="hybrid">Hybrid</option>
                <option value="remote">Remote</option>
              </select>
            </div>

            <div class="flex items-center gap-2 p-1.5 bg-gray-50 rounded border border-gray-200">
              <input
                v-model="locationData.is_open_to_relocation"
                type="checkbox"
                id="relocation"
                class="h-3 w-3 text-purple-600 border-gray-300 rounded focus:ring-1 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 outline-none"
              />
              <div class="flex items-center gap-1.5 flex-1">
                <Globe class="h-3 w-3 text-amber-500" />
                <div>
                  <label for="relocation" class="text-xs font-medium text-gray-900 cursor-pointer">
                    Open to relocation
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end gap-2 pt-0 border-gray-100">
          <BaseButton
            @click="isModalOpen = false"
            variant="secondary"
            class="px-3 py-1.5 text-xs focus:ring-1 focus:ring-green-500 focus:border-green-500 outline-none"
          >
            Cancel
          </BaseButton>
          <BaseButton
            @click="handleSaveChanges"
            :is-loading="isLoading"
            class="px-3 py-1.5 text-xs bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white transition-all duration-200 flex items-center gap-1 focus:ring-1 focus:ring-green-500 focus:border-green-500 outline-none"
          >
            <Save class="h-3 w-3" v-if="!isLoading" />
            {{ isLoading ? 'Saving...' : 'Save Changes' }}
          </BaseButton>
        </div>
      </template>
    </BaseModal>
  </div>
</template>
