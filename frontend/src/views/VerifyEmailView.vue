<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'

const route = useRoute()
const authStore = useAuthStore()
const { isLoading } = storeToRefs(authStore)

const success = ref(false)
const error = ref('')

onMounted(async () => {
  // Get the key from the URL link
  const key = route.params.key as string

  if (!key) {
    error.value = 'Invalid verification link.'
    return
  }

  try {
    // Use the centralized store action we just created
    await authStore.verifyEmail(key)
    success.value = true
  } catch (err: any) {
    // If the backend returns an error (400 or 500)
    error.value = 'The verification link is invalid or has already been used.'
  }
})
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8 text-center">
      <h2 class="text-3xl font-extrabold text-gray-900">NxtTurn Verification</h2>

      <!-- Show while waiting for backend -->
      <div v-if="isLoading" class="mt-4">
        <p class="text-gray-600 animate-pulse">Verifying your account, please wait...</p>
      </div>

      <!-- Show on Success -->
      <div
        v-if="success && !isLoading"
        class="mt-4 p-4 bg-green-100 text-green-700 rounded-md shadow"
      >
        <p class="font-bold text-xl mb-2">Success!</p>
        <p>Your email has been verified. You can now log in to your account.</p>
        <router-link
          to="/login"
          class="mt-4 inline-block px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition"
        >
          Go to Login
        </router-link>
      </div>

      <!-- Show on Error -->
      <div v-if="error && !isLoading" class="mt-4 p-4 bg-red-100 text-red-700 rounded-md shadow">
        <p class="font-bold text-xl mb-2">Verification Failed</p>
        <p>{{ error }}</p>
        <router-link to="/register" class="mt-4 inline-block text-indigo-600 hover:underline">
          Try Registering Again
        </router-link>
      </div>
    </div>
  </div>
</template>
