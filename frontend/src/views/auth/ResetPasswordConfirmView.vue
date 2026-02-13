<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axiosInstance from '@/services/axiosInstance'
import { useToast } from 'vue-toastification'

const route = useRoute()
const router = useRouter()
const toast = useToast()

const newPassword1 = ref('')
const newPassword2 = ref('')
const isLoading = ref(false)
const errorMessage = ref<string | null>(null)
const successMessage = ref<string | null>(null)

// State for the password visibility toggles
const showPassword1 = ref(false)
const showPassword2 = ref(false)

const uid = ref<string | string[]>('')
const token = ref<string | string[]>('')

onMounted(() => {
  uid.value = route.params.uid
  token.value = route.params.token
})

const handleResetConfirm = async () => {
  if (newPassword1.value !== newPassword2.value) {
    errorMessage.value = 'Passwords do not match.'
    toast.error('Passwords do not match.')
    return
  }

  isLoading.value = true
  errorMessage.value = null

  try {
    const payload = {
      uid: uid.value,
      token: token.value,
      new_password1: newPassword1.value,
      new_password2: newPassword2.value,
    }

    await axiosInstance.post('auth/password/reset/confirm/', payload)

    toast.success('Your password has been reset successfully! Redirecting to login...')

    setTimeout(() => {
      router.push({ name: 'login' })
    }, 2000)
  } catch (error: any) {
    const errorData = error.response?.data
    if (errorData) {
      errorMessage.value = Object.values(errorData).flat().join(' ')
    } else {
      errorMessage.value = 'An unexpected error occurred. The link may be invalid or expired.'
    }
    toast.error(errorMessage.value)
  } finally {
    isLoading.value = false
  }
}
</script>

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
        <h2 class="text-lg font-bold text-gray-600 mt-1">Choose a New Password</h2>
      </div>

      <!-- Form Body -->
      <div class="px-6 py-5">
        <form @submit.prevent="handleResetConfirm" class="space-y-4">
          <!-- Success Message -->
          <div
            v-if="successMessage"
            class="bg-green-100 border-l-4 border-green-500 text-green-700 p-3 rounded-lg text-sm"
            role="alert"
          >
            <p class="font-bold">Success!</p>
            <p>
              {{ successMessage }} You can now
              <router-link
                :to="{ name: 'login' }"
                class="font-bold underline text-green-800 hover:text-green-900"
                >log in</router-link
              >.
            </p>
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

          <template v-if="!successMessage">
            <!-- New Password -->
            <div class="relative">
              <label for="new_password1" class="block text-sm font-medium text-gray-700 mb-1"
                >New Password</label
              >
              <input
                :type="showPassword1 ? 'text' : 'password'"
                id="new_password1"
                v-model="newPassword1"
                required
                placeholder="Enter new password"
                class="w-full px-3 py-2 text-sm pr-10 border border-gray-300 rounded-lg placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
              />
              <button
                type="button"
                @click="showPassword1 = !showPassword1"
                class="absolute right-3 top-8 text-gray-400 hover:text-gray-600 transition-colors"
                aria-label="Toggle password visibility"
              >
                <svg
                  v-if="showPassword1"
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a9.97 9.97 0 01-1.563 3.029m-2.177-4.573A3 3 0 0012 9.5m-3.955 3.955A3 3 0 0012 14.5M3 3l18 18"
                  />
                </svg>
                <svg
                  v-else
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                  />
                </svg>
              </button>
            </div>

            <!-- Confirm New Password -->
            <div class="relative">
              <label for="new_password2" class="block text-sm font-medium text-gray-700 mb-1"
                >Confirm New Password</label
              >
              <input
                :type="showPassword2 ? 'text' : 'password'"
                id="new_password2"
                v-model="newPassword2"
                required
                placeholder="Confirm new password"
                class="w-full px-3 py-2 text-sm pr-10 border border-gray-300 rounded-lg placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
              />
              <button
                type="button"
                @click="showPassword2 = !showPassword2"
                class="absolute right-3 top-8 text-gray-400 hover:text-gray-600 transition-colors"
                aria-label="Toggle password visibility"
              >
                <svg
                  v-if="showPassword2"
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a9.97 9.97 0 01-1.563 3.029m-2.177-4.573A3 3 0 0012 9.5m-3.955 3.955A3 3 0 0012 14.5M3 3l18 18"
                  />
                </svg>
                <svg
                  v-else
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                  />
                </svg>
              </button>
            </div>

            <!-- Submit Button -->
            <button
              type="submit"
              :disabled="Boolean(isLoading)"
              class="w-full py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-300 disabled:cursor-not-allowed text-sm"
            >
              {{ isLoading ? 'Resetting...' : 'Reset Password' }}
            </button>
          </template>
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
