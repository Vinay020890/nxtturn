<script setup lang="ts">
import { ref, watch } from 'vue'
import { User, Briefcase, X, Save, Sparkles, Palette } from 'lucide-vue-next'
import type { UserProfile } from '@/types'

type IdentityFormData = {
  display_name: string | null
  headline: string | null
}

const props = defineProps<{
  initialData: UserProfile
}>()

const emit = defineEmits(['save', 'cancel'])

const form = ref<IdentityFormData>({
  display_name: '',
  headline: '',
})

watch(
  () => props.initialData,
  (newData) => {
    if (newData) {
      form.value = {
        display_name: newData.display_name || '',
        headline: newData.headline || '',
      }
    }
  },
  { immediate: true },
)

function handleSubmit() {
  emit('save', form.value)
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="max-w-md mx-auto">
    <!-- Compact Colorful Header Card -->
    <div
      class="bg-gradient-to-br from-purple-500 via-pink-500 to-orange-400 rounded-xl p-4 text-white shadow-lg mb-4 relative overflow-hidden"
    >
      <div class="absolute top-2 right-2 opacity-20">
        <Sparkles :size="32" />
      </div>
      <div class="flex items-center gap-2 mb-1">
        <div class="bg-white/20 p-1.5 rounded-lg backdrop-blur-sm">
          <Palette :size="18" class="text-white" />
        </div>
        <h2 class="text-lg font-bold">Profile Identity</h2>
      </div>
      <p class="text-white/90 text-xs">Make your profile stand out with vibrant colors!</p>
    </div>

    <div class="space-y-4">
      <!-- Display Name -->
      <div class="group">
        <label
          for="display_name"
          class="block text-sm font-semibold text-gray-700 flex items-center gap-2 mb-2"
        >
          <div class="bg-gradient-to-br from-blue-500 to-cyan-400 p-1 rounded-md shadow-sm">
            <User :size="12" class="text-white" />
          </div>
          Display Name
          <span class="text-xs text-blue-500 font-normal">*</span>
        </label>
        <div class="relative transition-all duration-200">
          <input
            v-model="form.display_name"
            type="text"
            id="display_name"
            placeholder="e.g., Vinay S."
            class="w-full px-3 py-2.5 border border-blue-100 rounded-lg shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-400 focus:border-blue-300 transition-all duration-200 text-sm bg-white hover:border-blue-200 bg-gradient-to-r from-blue-50 to-cyan-50"
          />
        </div>
      </div>

      <!-- Headline -->
      <div class="group">
        <label
          for="headline"
          class="block text-sm font-semibold text-gray-700 flex items-center gap-2 mb-2"
        >
          <div class="bg-gradient-to-br from-green-500 to-emerald-400 p-1 rounded-md shadow-sm">
            <Briefcase :size="12" class="text-white" />
          </div>
          Professional Headline
          <span class="text-xs text-green-500 font-normal">*</span>
        </label>
        <div class="relative transition-all duration-200">
          <input
            v-model="form.headline"
            type="text"
            id="headline"
            placeholder="e.g., Computer Science Student | Aspiring AI Engineer"
            class="w-full px-3 py-2.5 border border-green-100 rounded-lg shadow-sm focus:outline-none focus:ring-1 focus:ring-green-400 focus:border-green-300 transition-all duration-200 text-sm bg-white hover:border-green-200 bg-gradient-to-r from-green-50 to-emerald-50"
          />
        </div>
      </div>
    </div>

    <!-- Compact Form Actions -->
    <div class="mt-6 flex flex-col sm:flex-row gap-2 justify-end">
      <button
        type="button"
        @click="$emit('cancel')"
        class="flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-gray-100 to-gray-200 border border-gray-300 rounded-lg shadow-sm text-sm font-semibold text-gray-700 hover:from-gray-200 hover:to-gray-300 transition-all duration-200 flex-1 sm:flex-none order-2 sm:order-1 group"
      >
        <div class="bg-red-500 p-1 rounded-md group-hover:scale-110 transition-transform">
          <X :size="12" class="text-white" />
        </div>
        <span>Cancel</span>
      </button>

      <button
        type="submit"
        class="flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-purple-600 via-pink-500 to-orange-500 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white hover:from-purple-700 hover:via-pink-600 hover:to-orange-600 transition-all duration-200 flex-1 sm:flex-none order-1 sm:order-2 group relative overflow-hidden"
      >
        <div
          class="absolute inset-0 bg-white/20 transform -skew-x-12 -translate-x-full group-hover:translate-x-full transition-transform duration-700"
        ></div>
        <div class="bg-white/20 p-1 rounded-md group-hover:scale-110 transition-transform">
          <Save :size="12" class="text-white" />
        </div>
        <span class="relative">Save Changes</span>
      </button>
    </div>

    <!-- Compact Decorative Elements with Moderate Bounce -->
    <div class="mt-6 text-center">
      <div class="flex justify-center gap-1 mb-1">
        <div
          class="w-1.5 h-1.5 bg-purple-400 rounded-full animate-gentle-bounce"
          style="animation-delay: 0ms"
        ></div>
        <div
          class="w-1.5 h-1.5 bg-pink-400 rounded-full animate-gentle-bounce"
          style="animation-delay: 150ms"
        ></div>
        <div
          class="w-1.5 h-1.5 bg-orange-400 rounded-full animate-gentle-bounce"
          style="animation-delay: 300ms"
        ></div>
        <div
          class="w-1.5 h-1.5 bg-blue-400 rounded-full animate-gentle-bounce"
          style="animation-delay: 450ms"
        ></div>
      </div>
      <p class="text-xs text-gray-500">Make your profile shine! ✨</p>
    </div>
  </form>
</template>

<style scoped>
/* Custom gentle bounce animation - more noticeable than before */
@keyframes gentle-bounce {
  0%,
  100% {
    transform: translateY(0);
    animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
  }
  50% {
    transform: translateY(-4px);
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }
}

.animate-gentle-bounce {
  animation: gentle-bounce 2s infinite;
}
</style>
