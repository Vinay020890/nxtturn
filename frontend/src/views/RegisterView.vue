<script setup lang="ts">
import { ref, computed } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';
import type { AxiosError } from 'axios';

const authStore = useAuthStore();
const router = useRouter();
  
const email = ref('');
const username = ref('');
const password = ref('');
const password2 = ref('');
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);

const passwordsMismatch = computed(() => {
  return password.value && password2.value && password.value !== password2.value;
});

const isSubmitDisabled = computed(() => {
  return isLoading.value || passwordsMismatch.value;
});

const parseError = (error: unknown): string => {
  const axiosError = error as AxiosError<Record<string, string[]>>;
  if (axiosError.response?.data) {
    return Object.entries(axiosError.response.data)
      .map(([field, messages]) => `${field}: ${messages.join(', ')}`)
      .join('; ');
  }
  return 'An unexpected error occurred during registration.';
};

const handleRegister = async () => {
  errorMessage.value = null;

  if (passwordsMismatch.value) {
    errorMessage.value = 'Passwords do not match.';
    return;
  }

  isLoading.value = true;
  try {
    // THIS IS THE CORRECTED PART
    await authStore.register({
      email: email.value,
      username: username.value,
      password1: password.value, // Using password1 as required by the type
      password2: password2.value, // Using password2 as required by the type
    });
    alert('Registration successful! Please log in.');
    router.push({ name: 'login' });
  } catch (error) {
     errorMessage.value = parseError(error);
  } finally {
    isLoading.value = false;
  }
};
</script>

<template>
  <div class="flex items-center justify-center min-h-[calc(100vh-150px)] bg-gray-50">
    <div class="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md">
      <h1 class="text-2xl font-bold text-center text-gray-900">Create your account</h1>
      
      <form @submit.prevent="handleRegister" class="space-y-6">
        
        <div v-if="errorMessage" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4" role="alert">
          <p class="font-bold">Error</p>
          <p>{{ errorMessage }}</p>
        </div>

        <div>
          <label for="email" class="block text-sm font-medium text-gray-700">Email</label>
          <div class="mt-1">
            <input 
              type="email" 
              id="email" 
              v-model="email" 
              required 
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        <div>
          <label for="username" class="block text-sm font-medium text-gray-700">Username</label>
          <div class="mt-1">
            <input 
              type="text" 
              id="username" 
              v-model="username" 
              required 
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-gray-700">Password</label>
          <div class="mt-1">
            <input
              type="password"
              id="password"
              v-model="password"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        <div>
          <label for="password2" class="block text-sm font-medium text-gray-700">Confirm Password</label>
          <div class="mt-1">
            <input
              type="password"
              id="password2"
              v-model="password2"
              required
              class="w-full px-3 py-2 border rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500"
              :class="passwordsMismatch ? 'border-red-500' : 'border-gray-300'"
            />
          </div>
          <p v-if="passwordsMismatch" class="mt-2 text-xs text-red-600">
            Passwords do not match.
          </p>
        </div>

        <div>
          <button 
            type="submit"
            :disabled="isSubmitDisabled"
            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-blue-300 disabled:cursor-not-allowed"
          >
            {{ isLoading ? 'Registering...' : 'Create Account' }}
          </button>
        </div>
      </form>

      <p class="mt-6 text-center text-sm text-gray-600">
        Already have an account?
        <router-link :to="{ name: 'login' }" class="font-medium text-blue-600 hover:text-blue-500">
          Sign in
        </router-link>
      </p>
    </div>
  </div>
</template>