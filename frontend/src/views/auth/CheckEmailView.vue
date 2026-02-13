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
        <h2 class="text-lg font-bold text-gray-600 mt-1">Please Verify Your Email</h2>
        <p class="mt-2 text-center text-xs text-gray-600">
          We have sent a verification link to your email address. Please click the link to complete
          your registration.
        </p>
      </div>

      <!-- Body -->
      <div class="px-6 py-5">
        <!-- Success/Info Message -->
        <div
          v-if="infoMessage"
          class="bg-blue-100 border-l-4 border-blue-500 text-blue-700 p-3 rounded-lg text-sm mb-4"
          role="alert"
        >
          <p class="font-bold">Information</p>
          <p>{{ infoMessage }}</p>
        </div>

        <div class="text-center">
          <div class="mb-4">
            <svg
              class="w-16 h-16 mx-auto text-indigo-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              ></path>
            </svg>
          </div>

          <p class="text-sm text-gray-600 mb-6">
            Didn't receive the email? Check your spam folder or click below to resend the
            verification link.
          </p>

          <!-- Resend Button -->
          <button
            @click="resendVerification"
            :disabled="isResending"
            class="w-full py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-300 disabled:cursor-not-allowed text-sm mb-4"
          >
            {{ isResending ? 'Sending...' : 'Resend Verification Link' }}
          </button>

          <!-- Footer -->
          <div class="text-center text-xs text-gray-600 mt-4">
            <p>
              Already verified?
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
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useToast } from 'vue-toastification'

const toast = useToast()
const isResending = ref(false)
const infoMessage = ref<string | null>(null)

const resendVerification = () => {
  isResending.value = true
  infoMessage.value = null

  // NOTE: The resend functionality is not yet built in the backend.
  // This is a placeholder for a future feature.
  setTimeout(() => {
    toast.info('Resend functionality is not yet implemented.')
    infoMessage.value =
      "If you didn't receive the email, please check your spam folder or contact support."
    isResending.value = false
  }, 1000)
}
</script>

<style scoped>
.logo img {
  filter: drop-shadow(0 2px 5px rgba(0, 0, 0, 0.1));
  border-radius: 6px;
}
</style>
