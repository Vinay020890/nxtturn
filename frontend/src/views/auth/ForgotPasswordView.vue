<template>
  <div
    class="min-h-screen w-full bg-gradient-to-br from-[#667eea] to-[#764ba2] flex items-center justify-center p-4"
  >
    <div class="w-full max-w-sm bg-white rounded-2xl shadow-xl overflow-hidden">
      <!-- Header -->
      <div class="px-6 pt-6 pb-4 text-center border-b border-gray-100">
        <div class="logo flex justify-center mb-2">
          <span
            class="bg-gradient-to-r from-blue-600 to-purple-500 bg-clip-text text-transparent text-2xl font-bold"
            >NxtTurn</span
          >
        </div>
        <h2 class="text-lg font-bold text-gray-600 mt-1">Forgot Your Password?</h2>
        <p class="mt-2 text-center text-xs text-gray-600">
          No problem. Enter your email address below and we'll send you a link to reset it.
        </p>
      </div>

      <!-- Form Body -->
      <div class="px-6 py-5">
        <form @submit.prevent="handleRequestReset" class="space-y-4">
          <!-- Success Message -->
          <div
            v-if="successMessage"
            class="bg-green-100 border-l-4 border-green-500 text-green-700 p-3 rounded-lg text-sm"
            role="alert"
          >
            <p class="font-bold">Success</p>
            <p>{{ successMessage }}</p>
          </div>

          <!-- Error Message -->
          <div
            v-if="errorMessage"
            class="bg-red-100 border-l-4 border-red-500 text-red-700 p-3 rounded-lg text-sm"
            role="alert"
          >
            <p class="font-bold">Error</p>
            <p>{{ errorMessage }}</p>
          </div>

          <!-- Email Input -->
          <div>
            <label for="email" class="block text-sm font-medium text-gray-700 mb-1"
              >Email Address</label
            >
            <input
              type="email"
              id="email"
              v-model="email"
              required
              :disabled="isLoading"
              placeholder="Enter your email address"
              class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors disabled:bg-gray-50"
            />
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            :disabled="Boolean(isLoading)"
            class="w-full py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-300 disabled:cursor-not-allowed text-sm"
          >
            {{ isLoading ? 'Sending...' : 'Send Reset Link' }}
          </button>
        </form>

        <!-- Footer -->
        <div class="text-center text-xs text-gray-600 mt-4">
          <p>
            Remembered your password?
            <router-link
              :to="{ name: 'login' }"
              class="text-indigo-600 hover:text-indigo-500 font-medium hover:underline transition-colors"
            >
              Sign in
            </router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import axiosInstance from '@/services/axiosInstance'
import { useToast } from 'vue-toastification'

const email = ref('')
const isLoading = ref(false)
const errorMessage = ref<string | null>(null)
const successMessage = ref<string | null>(null)
const toast = useToast()

const handleRequestReset = async () => {
  isLoading.value = true
  errorMessage.value = null
  successMessage.value = null

  try {
    const response = await axiosInstance.post('auth/password/reset/', {
      email: email.value,
    })

    // The API always returns a success message for security, as per our pytest test.
    successMessage.value =
      response.data.detail +
      ' If an account with this email exists, you will receive instructions shortly.'
    toast.success('Password reset request sent successfully.')
    email.value = '' // Clear the form on success
  } catch (error: any) {
    errorMessage.value =
      error.response?.data?.detail || 'An unexpected error occurred. Please try again.'
    toast.error(errorMessage.value)
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.logo img {
  filter: drop-shadow(0 2px 5px rgba(0, 0, 0, 0.1));
  border-radius: 6px;
}
</style>
