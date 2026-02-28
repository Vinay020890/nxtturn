<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'
import { getAvatarUrl } from '@/utils/avatars'
import axiosInstance from '@/services/axiosInstance'
import type { UserProfile } from '@/types'
import { HomeIcon, UserGroupIcon, BookmarkIcon } from '@heroicons/vue/24/solid'
import eventBus from '@/services/eventBus'

// Font Awesome Icons
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { faBriefcase, faMapLocationDot } from '@fortawesome/free-solid-svg-icons'

const authStore = useAuthStore()
const { currentUser } = storeToRefs(authStore)
const route = useRoute()

// --- Local State for the Full Profile Data ---
const myProfile = ref<UserProfile | null>(null)
const isLoadingProfile = ref(false)

// --- Fetch the detailed profile (Headline, Location, Display Name) ---
const fetchMyProfile = async () => {
  if (!currentUser.value?.username) return

  isLoadingProfile.value = true
  try {
    const response = await axiosInstance.get<UserProfile>(
      `/profiles/${currentUser.value.username}/`,
    )
    myProfile.value = response.data
  } catch (error) {
    console.error('Failed to load sidebar profile data', error)
  } finally {
    isLoadingProfile.value = false
  }
}

// Fetch on mount, and re-fetch if the logged-in user changes
onMounted(fetchMyProfile)
watch(currentUser, fetchMyProfile)

// --- Helper Functions for Display Logic ---

const displayName = computed(() => {
  if (!myProfile.value) return currentUser.value?.username || 'User'

  // Priority 1: Custom Display Name
  if (myProfile.value.display_name) return myProfile.value.display_name

  // Priority 2: First + Last Name (from Auth Store or Profile)
  const fname = currentUser.value?.first_name || ''
  const lname = currentUser.value?.last_name || ''
  const fullName = `${fname} ${lname}`.trim()
  if (fullName) return fullName

  // Priority 3: Username (Always available)
  return currentUser.value?.username
})

const displayLocation = computed(() => {
  if (!myProfile.value) return null

  const city = myProfile.value.location_city
  const state = myProfile.value.location_administrative_area // State/Province
  const country = myProfile.value.location_country

  // Create an array of the parts that actually exist
  const parts = [city, state, country].filter((part) => part && part.trim())

  // Join them with a comma and space
  if (parts.length === 0) return null
  return parts.join(', ')
})

// --- Navigation Handlers ---
function handleHomeFeedClick(event: MouseEvent) {
  if (route.path === '/') {
    event.preventDefault()
    eventBus.emit('scroll-to-top')
  }
}

function handleMyGroupsClick(event: MouseEvent) {
  if (route.name === 'group-list') {
    event.preventDefault()
    eventBus.emit('scroll-groups-to-top')
  }
}

function handleSavedPostsClick(event: MouseEvent) {
  if (route.name === 'saved-posts') {
    event.preventDefault()
    eventBus.emit('scroll-saved-posts-to-top')
  }
}

// Computed properties for active states
const isHomeRouteActive = computed(() => route.path === '/')
const isGroupsRouteActive = computed(() => route.path.startsWith('/groups'))
const isSavedPostsRouteActive = computed(() => route.name === 'saved-posts')
</script>

<template>
  <div class="space-y-3 translate-x-3 md:block hidden">
    <!-- User Profile Card -->
    <div
      v-if="currentUser"
      class="bg-gradient-to-br from-blue-500 to-purple-500 p-4 rounded-2xl border-0 shadow-lg relative overflow-hidden"
    >
      <!-- Decorative elements -->
      <div
        class="absolute top-0 right-0 w-16 h-16 bg-white/10 rounded-full -translate-y-6 translate-x-6"
      ></div>
      <div
        class="absolute bottom-0 left-0 w-12 h-12 bg-white/10 rounded-full translate-y-2 -translate-x-2"
      ></div>

      <div class="flex flex-col items-center text-center relative z-10">
        <!-- Avatar -->
        <RouterLink :to="`/profile/${currentUser.username}`">
          <img
            :src="getAvatarUrl(currentUser.picture, currentUser.first_name, currentUser.last_name)"
            alt="User Avatar"
            class="h-16 w-16 rounded-full object-cover border-4 border-white/30 shadow-lg mb-3.5 hover:scale-105 transition-transform"
          />
        </RouterLink>

        <!-- Name (Uses the computed logic) -->
        <RouterLink
          :to="`/profile/${currentUser.username}`"
          class="hover:underline decoration-white/50"
        >
          <h2 class="font-bold text-white text-lg leading-tight drop-shadow-sm mb-1">
            {{ displayName }}
          </h2>
        </RouterLink>

        <p class="text-white/80 text-sm font-medium mb-3">@{{ currentUser.username }}</p>

        <!-- Designation (Only shows if headline exists in the fetched profile) -->
        <div v-if="myProfile?.headline" class="flex items-center gap-2 mb-2 justify-center w-full">
          <FontAwesomeIcon :icon="faBriefcase" class="w-3.5 h-3.5 text-yellow-300 flex-shrink-0" />
          <span
            class="text-white/90 text-sm font-medium truncate max-w-[180px]"
            :title="myProfile.headline"
          >
            {{ myProfile.headline }}
          </span>
        </div>

        <!-- Location (Only shows if location exists) -->
        <div v-if="displayLocation" class="flex items-center gap-2 justify-center w-full">
          <FontAwesomeIcon
            :icon="faMapLocationDot"
            class="w-3.5 h-3.5 text-red-300 flex-shrink-0"
          />
          <span class="text-white/90 text-sm font-medium truncate max-w-[180px]">
            {{ displayLocation }}
          </span>
        </div>

        <!-- Fallback: "Complete Profile" Nudge -->
        <!-- Shows if we have loaded the profile, but both headline and location are missing -->
        <div
          v-if="!isLoadingProfile && myProfile && !myProfile.headline && !displayLocation"
          class="mt-2"
        >
          <RouterLink
            :to="`/profile/${currentUser.username}`"
            class="text-xs bg-white/20 hover:bg-white/30 text-white px-3 py-1 rounded-full transition-colors"
          >
            Add details
          </RouterLink>
        </div>
      </div>
    </div>

    <!-- Navigation Card (Unchanged) -->
    <div class="bg-white p-3 rounded-2xl border-0 shadow-lg">
      <nav class="space-y-2.5">
        <RouterLink
          to="/"
          @click="handleHomeFeedClick"
          data-cy="sidebar-home-link"
          class="group flex items-center gap-3 px-3 py-1.5 rounded-xl font-medium transition-all duration-200 ease-out border border-transparent hover:border-orange-100 relative"
          :class="
            isHomeRouteActive
              ? 'bg-gradient-to-r from-orange-100 to-amber-100 text-orange-700 border-orange-200 shadow-md'
              : 'text-gray-800 hover:bg-gradient-to-r hover:from-orange-50 hover:to-amber-50'
          "
        >
          <div
            v-if="isHomeRouteActive"
            class="absolute inset-0 ring-2 ring-orange-300 rounded-xl transition-all duration-200"
          ></div>
          <div
            class="p-1.5 rounded-lg bg-orange-100 group-hover:bg-orange-200 transition-colors duration-200 relative z-10"
            :class="isHomeRouteActive ? 'bg-orange-200' : ''"
          >
            <HomeIcon class="h-5 w-5 text-orange-600" />
          </div>
          <span class="text-base font-semibold relative z-10">Home Feed</span>
        </RouterLink>

        <RouterLink
          to="/groups"
          @click="handleMyGroupsClick"
          data-cy="sidebar-groups-link"
          class="group flex items-center gap-3 px-3 py-1.5 rounded-xl font-medium transition-all duration-200 ease-out border border-transparent hover:border-blue-100 relative"
          :class="
            isGroupsRouteActive
              ? 'bg-gradient-to-r from-blue-100 to-cyan-100 text-blue-700 border-blue-200 shadow-md'
              : 'text-gray-800 hover:bg-gradient-to-r hover:from-blue-50 hover:to-cyan-50'
          "
        >
          <div
            v-if="isGroupsRouteActive"
            class="absolute inset-0 ring-2 ring-blue-300 rounded-xl transition-all duration-200"
          ></div>
          <div
            class="p-1.5 rounded-lg bg-blue-100 group-hover:bg-blue-200 transition-colors duration-200 relative z-10"
            :class="isGroupsRouteActive ? 'bg-blue-200' : ''"
          >
            <UserGroupIcon class="h-5 w-5 text-blue-600" />
          </div>
          <span class="text-base font-semibold relative z-10">My Groups</span>
        </RouterLink>

        <RouterLink
          to="/saved-posts"
          @click="handleSavedPostsClick"
          data-cy="sidebar-saved-posts-link"
          class="group flex items-center gap-3 px-3 py-1.5 rounded-xl font-medium transition-all duration-200 ease-out border border-transparent hover:border-green-100 relative"
          :class="
            isSavedPostsRouteActive
              ? 'bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 border-green-200 shadow-md'
              : 'text-gray-800 hover:bg-gradient-to-r hover:from-green-50 hover:to-emerald-50'
          "
        >
          <div
            v-if="isSavedPostsRouteActive"
            class="absolute inset-0 ring-2 ring-green-300 rounded-xl transition-all duration-200"
          ></div>
          <div
            class="p-1.5 rounded-lg bg-green-100 group-hover:bg-green-200 transition-colors duration-200 relative z-10"
            :class="isSavedPostsRouteActive ? 'bg-green-200' : ''"
          >
            <BookmarkIcon class="h-5 w-5 text-green-600" />
          </div>
          <span class="text-base font-semibold relative z-10">Saved Posts</span>
        </RouterLink>
      </nav>
    </div>
  </div>
</template>
