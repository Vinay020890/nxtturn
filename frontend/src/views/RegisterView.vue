<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import type { AxiosError } from 'axios'
import { storeToRefs } from 'pinia'
import { useToast } from 'vue-toastification'

const authStore = useAuthStore()
const router = useRouter()
const toast = useToast()

const { isLoading } = storeToRefs(authStore)
const email = ref('')
const username = ref('')
const password = ref('')
const password2 = ref('')
const errorMessage = ref<string | null>(null)
const showPassword1 = ref(false)
const showPassword2 = ref(false)
const rememberMe = ref(false)

const passwordsMismatch = computed(() => {
  return password.value && password2.value && password.value !== password2.value
})

const isSubmitDisabled = computed(() => {
  return isLoading.value || passwordsMismatch.value
})

const parseError = (error: unknown): string => {
  const axiosError = error as AxiosError<Record<string, string[]>>
  if (axiosError.response?.data) {
    const errorMessages = Object.entries(axiosError.response.data)
      .map(([field, messages]) => `${field}: ${messages.join(', ')}`)
      .join('; ')
    if (axiosError.response.data.non_field_errors) {
      return axiosError.response.data.non_field_errors.join('; ')
    }
    return errorMessages
  }
  return 'An unexpected error occurred during registration.'
}

const handleRegister = async () => {
  errorMessage.value = null

  if (passwordsMismatch.value) {
    errorMessage.value = 'Passwords do not match.'
    return
  }

  try {
    await authStore.register({
      email: email.value,
      username: username.value,
      password1: password.value,
      password2: password2.value,
    })
    toast.success('Registration successful! Please check your email to verify your account.')
    router.push({ name: 'CheckEmail' })
  } catch (error) {
    errorMessage.value = parseError(error)
  }
}

const handleGoogleLogin = () => {
  console.log('Google login')
}
</script>

<template>
  <div
    class="min-h-screen w-full bg-gradient-to-br from-[#667eea] to-[#764ba2] flex items-center justify-center p-4"
  >
    <!-- Responsive Container -->
    <div class="w-full max-w-sm bg-white rounded-2xl shadow-xl overflow-hidden mx-auto">
      <!-- Header - Compact -->
      <div class="px-5 pt-5 pb-3 text-center border-b border-gray-100">
        <div class="logo flex justify-center mb-1">
          <span
            class="bg-gradient-to-r from-blue-600 to-purple-500 bg-clip-text text-transparent text-xl font-bold"
          >
            NxtTurn
          </span>
        </div>
        <h2 class="text-base font-bold text-gray-600 mt-1">Create your account</h2>
      </div>

      <!-- Form Body - Compact -->
      <div class="px-5 py-4">
        <!-- Error Message -->
        <div
          v-if="errorMessage"
          class="bg-red-50 border-l-3 border-red-500 text-red-700 p-3 rounded-md mb-3 text-xs"
          role="alert"
        >
          <p class="font-semibold">Error</p>
          <p>{{ errorMessage }}</p>
        </div>

        <form @submit.prevent="handleRegister" class="space-y-3">
          <!-- Email -->
          <div>
            <label for="email" class="block text-xs font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              id="email"
              v-model="email"
              required
              placeholder="Enter your email"
              class="w-full px-3 py-2 text-xs border border-gray-300 rounded-lg placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
            />
          </div>

          <!-- Username -->
          <div>
            <label for="username" class="block text-xs font-medium text-gray-700 mb-1"
              >Username</label
            >
            <input
              type="text"
              id="username"
              v-model="username"
              required
              placeholder="Enter your username"
              class="w-full px-3 py-2 text-xs border border-gray-300 rounded-lg placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
            />
          </div>

          <!-- Password -->
          <div class="relative">
            <label for="password" class="block text-xs font-medium text-gray-700 mb-1"
              >Password</label
            >
            <input
              :type="showPassword1 ? 'text' : 'password'"
              id="password"
              v-model="password"
              required
              placeholder="Enter your password"
              class="w-full px-3 py-2 text-xs pr-10 border border-gray-300 rounded-lg placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
            />
            <button
              type="button"
              @click="showPassword1 = !showPassword1"
              class="absolute right-3 top-7 text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="Toggle password visibility"
            >
              <svg
                v-if="showPassword1"
                xmlns="http://www.w3.org/2000/svg"
                class="h-3.5 w-3.5"
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
                class="h-3.5 w-3.5"
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

          <!-- Confirm Password -->
          <div class="relative">
            <label for="password2" class="block text-xs font-medium text-gray-700 mb-1"
              >Confirm Password</label
            >
            <input
              :type="showPassword2 ? 'text' : 'password'"
              id="password2"
              v-model="password2"
              required
              placeholder="Confirm your password"
              class="w-full px-3 py-2 text-xs pr-10 border rounded-lg placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
              :class="passwordsMismatch ? 'border-red-500' : 'border-gray-300'"
            />
            <button
              type="button"
              @click="showPassword2 = !showPassword2"
              class="absolute right-3 top-7 text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="Toggle password visibility"
            >
              <svg
                v-if="showPassword2"
                xmlns="http://www.w3.org/2000/svg"
                class="h-3.5 w-3.5"
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
                class="h-3.5 w-3.5"
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
            <p v-if="passwordsMismatch" class="mt-1 text-xs text-red-600">
              Passwords do not match.
            </p>
          </div>

          <!-- Terms Agreement -->
          <div class="flex items-center text-xs">
            <label class="flex items-center gap-1 cursor-pointer">
              <input
                type="checkbox"
                v-model="rememberMe"
                class="w-3 h-3 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
              />
              <span class="text-gray-700">
                I agree to the
                <a href="#" class="text-indigo-600 hover:underline">Terms</a> and
                <a href="#" class="text-indigo-600 hover:underline">Privacy</a>
              </span>
            </label>
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            :disabled="Boolean(isSubmitDisabled)"
            class="w-full py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg transition-colors focus:outline-none focus:ring-1 focus:ring-offset-1 focus:ring-indigo-500 disabled:bg-indigo-300 disabled:cursor-not-allowed text-xs"
          >
            {{ isLoading ? 'Registering...' : 'Create Account' }}
          </button>
        </form>

        <!-- Divider -->
        <div class="my-3 flex items-center">
          <div class="flex-grow border-t border-gray-200"></div>
          <span class="mx-2 text-xs text-gray-500">Or continue with</span>
          <div class="flex-grow border-t border-gray-200"></div>
        </div>

        <!-- Social Login -->
        <p class="text-center text-xs text-gray-600 mb-2">Connect with your favorite platform</p>

        <!-- Google Login -->
        <div class="flex justify-center mb-3">
          <button
            @click="handleGoogleLogin"
            class="w-9 h-9 rounded-lg border border-gray-300 bg-white shadow-sm hover:shadow transition-all duration-200 hover:-translate-y-0.5 flex items-center justify-center"
            title="Sign in with Google"
          >
            <svg class="h-3.5 w-3.5" viewBox="0 0 24 24">
              <path
                fill="#EA4335"
                d="M5.26620003,9.76452941 C6.19878754,6.93863203 8.85444915,4.90909091 12,4.90909091 C13.6909091,4.90909091 15.2181818,5.50909091 16.4181818,6.49090909 L19.9090909,3 C17.7818182,1.14545455 15.0545455,0 12,0 C7.27006974,0 3.1977497,2.69829785 1.23999023,6.65002441 L5.26620003,9.76452941 Z"
              />
              <path
                fill="#34A853"
                d="M16.0407269,18.0125889 C14.9509167,18.7163016 13.5660892,19.0909091 12,19.0909091 C8.86648613,19.0909091 6.21911939,17.076871 5.27698177,14.2678769 L1.23746264,17.3349879 C3.19279051,21.2936293 7.26500293,24 12,24 C14.9328362,24 17.7353462,22.9573905 19.834192,20.9995801 L16.0407269,18.0125889 Z"
              />
              <path
                fill="#4A90E2"
                d="M19.834192,20.9995801 C22.0291676,18.9520994 23.4545455,15.903663 23.4545455,12 C23.4545455,11.2909091 23.3454545,10.5272727 23.1818182,9.81818182 L12,9.81818182 L12,14.4545455 L18.4363636,14.4545455 C18.1187732,16.013626 17.2662994,17.2212117 16.0407269,18.0125889 L19.834192,20.9995801 Z"
              />
              <path
                fill="#FBBC05"
                d="M5.27698177,14.2678769 C5.03832634,13.556323 4.90909091,12.7937589 4.90909091,12 C4.90909091,11.2182781 5.03443647,10.4668121 5.26620003,9.76452941 L1.23999023,6.65002441 C0.43658717,8.26043162 0,10.0753848 0,12 C0,13.9195484 0.444780743,15.7301709 1.23746264,17.3349879 L5.27698177,14.2678769 Z"
              />
            </svg>
          </button>
        </div>

        <!-- Footer -->
        <div class="text-center text-xs text-gray-600">
          <p>
            Already have an account?
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

<style scoped>
/* Ensure form fits within viewport on all devices */
@media (max-height: 600px) {
  .min-h-screen {
    min-height: 100%;
    padding: 1rem 0;
  }
}

/* Prevent any scrolling */
html,
body {
  overflow: hidden;
}

/* Responsive adjustments */
@media (max-width: 640px) {
  .max-w-sm {
    max-width: 100%;
    margin: 0 0.5rem;
  }

  .px-5 {
    padding-left: 1rem;
    padding-right: 1rem;
  }

  .py-4 {
    padding-top: 1rem;
    padding-bottom: 1rem;
  }
}

@media (max-height: 700px) {
  .px-5 {
    padding-left: 1rem;
    padding-right: 1rem;
  }

  .py-4 {
    padding-top: 0.75rem;
    padding-bottom: 0.75rem;
  }

  .space-y-3 > * + * {
    margin-top: 0.5rem;
  }
}
</style>
