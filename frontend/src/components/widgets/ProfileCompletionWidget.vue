<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useProfileStore } from '@/stores/profile'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'

const profileStore = useProfileStore()
const authStore = useAuthStore()
const { currentProfile } = storeToRefs(profileStore)
const { currentUser } = storeToRefs(authStore)

onMounted(async () => {
  if (currentUser.value?.username && !currentProfile.value) {
    await profileStore.fetchProfile(currentUser.value.username)
  }
})

const completionData = computed(() => {
  if (!currentProfile.value) return { percentage: 0, isComplete: false, firstMissing: null }

  const p = currentProfile.value
  let score = 0
  const totalSteps = 5

  // PREFERENCE ORDER:
  // 1. Photo (Target: photo)
  // 2. Display Name (Target: basic-info)
  // 3. Headline (Target: basic-info)
  // 4. Location (Target: basic-info)
  // 5. Education (Target: education)
  const steps = [
    { key: 'picture', value: p.picture, target: 'photo' },
    { key: 'display_name', value: p.display_name, target: 'basic-info' },
    { key: 'headline', value: p.headline, target: 'basic-info' },
    { key: 'location_city', value: p.location_city, target: 'basic-info' },
    { key: 'education', value: p.education && p.education.length > 0, target: 'education' },
  ]

  // This explicit type fixes the ts-plugin(7034) error you saw
  let firstMissing: string | null = null

  steps.forEach((step) => {
    if (step.value) {
      score++
    } else if (!firstMissing) {
      firstMissing = step.target
    }
  })

  const percentage = Math.round((score / totalSteps) * 100)

  return {
    percentage,
    isComplete: percentage === 100,
    firstMissing,
  }
})
</script>

<template>
  <!-- Only show if the profile is NOT 100% complete and we have a user -->
  <div
    v-if="!completionData.isComplete && currentUser"
    class="bg-white p-5 rounded-2xl border border-blue-100 shadow-sm transition-all hover:shadow-md"
  >
    <div class="flex items-center justify-between mb-3">
      <div class="flex flex-col">
        <h3 class="font-bold text-gray-800 text-sm tracking-tight">Profile Strength</h3>
        <p class="text-[10px] text-blue-500 font-bold uppercase tracking-widest">Connect more</p>
      </div>
      <div class="flex items-baseline gap-0.5">
        <span class="text-xl font-black text-blue-600">{{ completionData.percentage }}</span>
        <span class="text-[10px] font-bold text-blue-400">%</span>
      </div>
    </div>

    <!-- Progress Bar -->
    <div class="w-full bg-gray-100 rounded-full h-2 mb-4 overflow-hidden shadow-inner">
      <div
        class="bg-gradient-to-r from-blue-500 to-indigo-600 h-full transition-all duration-1000 ease-out"
        :style="{ width: `${completionData.percentage}%` }"
      ></div>
    </div>

    <p class="text-[11px] text-gray-500 mb-5 leading-relaxed">
      A strong profile helps <span class="font-bold text-gray-700">alumni and peers</span> find you.
      Set your display name and photo to build trust!
    </p>

    <!-- The link now prioritizes Location over Education -->
    <RouterLink
      :to="{
        name: 'profile',
        params: { username: currentUser.username },
        query: { edit: completionData.firstMissing },
      }"
      class="group flex items-center justify-center gap-2 w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl transition-all shadow-sm active:scale-95"
    >
      Complete Profile
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="h-3 w-3 group-hover:translate-x-1 transition-transform"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M9 5l7 7-7 7" />
      </svg>
    </RouterLink>
  </div>
</template>
