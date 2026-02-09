<script setup lang="ts">
import { computed } from 'vue'
import { useProfileStore } from '@/stores/profile'
import { useAuthStore } from '@/stores/auth'
import ResumeCard from '../cards/ResumeCard.vue'

const profileStore = useProfileStore()
const authStore = useAuthStore()

// We get the profile data directly from the central store
const profile = computed(() => profileStore.currentProfile)

// Security: Check if the logged-in user is the one viewing their own profile
const isOwner = computed(() => authStore.currentUser?.username === profile.value?.user.username)
</script>

<template>
  <div v-if="profile" class="max-w-2xl mx-auto py-10 px-4">
    <!-- Presentational component for the UI -->
    <ResumeCard
      :resume-url="profile.resume"
      :username="profile.user.username"
      :is-owner="isOwner"
    />

    <!-- Professional Footer -->
    <p class="mt-8 text-center text-sm text-gray-400">
      Your resume is visible to logged-in users. Keep it updated for better visibility.
    </p>
  </div>

  <div v-else class="text-center py-12 text-gray-500 italic">Loading profile data...</div>
</template>
