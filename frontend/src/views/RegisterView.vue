<template>
    <div class="register-container">
      <h2>Register for nxtturn</h2>
      <form @submit.prevent="handleRegister" class="register-form">
        <!-- Error message display (will add logic later) -->
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>
  
        <div class="form-group">
          <label for="email">Email:</label>
          <input type="email" id="email" v-model="email" required />
        </div>
  
        <div class="form-group">
          <label for="username">Username:</label>
          <input type="text" id="username" v-model="username" required />
        </div>
  
        <div class="form-group">
          <label for="password">Password:</label>
          <input type="password" id="password" v-model="password" required />
        </div>
  
        <div class="form-group">
          <label for="password2">Confirm Password:</label>
          <input type="password" id="password2" v-model="password2" required />
           <!-- Password mismatch message (will add logic later) -->
          <div v-if="passwordsMismatch" class="error-message small">
            Passwords do not match.
          </div>
        </div>
  
        <!-- UPDATE THIS LINE -->
        <button type="submit" :disabled="isSubmitDisabled">
          <!-- Loading state text (will add logic later) -->
          {{ isLoading ? 'Registering...' : 'Register' }}
        </button>
      </form>
       <!-- Link to Login page (will add later) -->
       <p class="login-link">
         Already have an account? <router-link :to="{ name: 'login' }">Login here</router-link>
       </p>
    </div>
</template>
  
<script setup lang="ts">

import { ref, computed } from 'vue';
import { useAuthStore } from '@/stores/auth'; // <-- Add this line
import { useRouter } from 'vue-router';      // <-- Add this line
import type { AxiosError } from 'axios';     // <-- Add this line

const authStore = useAuthStore();
const router = useRouter();
  

// Temporary reactive refs for form fields and state
const email = ref('');
const username = ref('');
const password = ref('');
const password2 = ref('');
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);

// Temporary computed property for password mismatch (logic is correct)
const passwordsMismatch = computed(() => {
  return password.value && password2.value && password.value !== password2.value;
});

// --- MODIFY THIS COMPUTED PROPERTY ---
const isSubmitDisabled = computed(() => {
  // Explicitly cast the result to boolean
  return Boolean(isLoading.value || passwordsMismatch.value);
});
// --- END OF MODIFICATION ---

// Helper function to parse potential backend errors
const parseError = (error: unknown): string => {
  const axiosError = error as AxiosError<Record<string, string[]>>; // Assume it's an Axios error
  if (axiosError.response && axiosError.response.data && typeof axiosError.response.data === 'object') {
    // Try to join all error messages from the backend response object
    return Object.entries(axiosError.response.data)
      .map(([field, messages]) => `${field}: ${messages.join(', ')}`)
      .join('; ');
  } else if (error instanceof Error) {
    // Fallback for generic errors
    return error.message;
  }
  // Default fallback
  return 'An unexpected error occurred during registration.';
};

// Updated function to handle form submission
const handleRegister = async () => {
  errorMessage.value = null; // Clear previous errors

  // Basic client-side check (button is disabled, but good practice)
  if (passwordsMismatch.value) {
    errorMessage.value = 'Passwords do not match.';
    return;
  }
  if (isSubmitDisabled.value) {
    return; // Don't submit if button should be disabled
  }

  isLoading.value = true; // Show loading indicator

  try {
    // Call the register action in the store using the 'authStore' instance
    await authStore.register({
      email: email.value,
      username: username.value,
      password1: password.value,
      password2: password2.value,
    });

    // If register() doesn't throw an error, it was successful
    console.log('Registration successful!');
    // Show a success message (can be improved later)
    alert('Registration successful! Please log in.');
    // Redirect to the login page using the 'router' instance
    router.push({ name: 'login' });

  } catch (error) {
     // If register() throws an error, catch it here
     console.error("Registration failed in component:", error);
     // Use the helper function to set a readable error message
     errorMessage.value = parseError(error);
  } finally {
    // This runs whether try succeeded or failed
    isLoading.value = false; // Hide loading indicator
  }
};
  
</script>
  
<style scoped>
  /* Styles remain the same */
  .register-container {
    max-width: 400px;
    margin: 50px auto;
    padding: 2rem;
    border: 1px solid #ccc;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  
  h2 {
    text-align: center;
    margin-bottom: 1.5rem;
    color: #333;
  }
  
  .register-form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .form-group {
    display: flex;
    flex-direction: column;
  }
  
  label {
    margin-bottom: 0.5rem;
    font-weight: bold;
    color: #555;
  }
  
  input {
    padding: 0.75rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 1rem;
  }
  
  input:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
  }
  
  button {
    padding: 0.75rem;
    background-color: #28a745; /* Green */
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    cursor: pointer;
    transition: background-color 0.2s ease;
  }
  
  button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
  }
  
  button:not(:disabled):hover {
    background-color: #218838;
  }
  
  .error-message {
    color: #dc3545; /* Red */
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
    padding: 0.75rem;
    border-radius: 4px;
    margin-bottom: 1rem;
    font-size: 0.9rem;
  }
  .error-message.small {
      padding: 0.2rem 0.5rem;
      margin-top: 0.3rem;
      margin-bottom: 0; /* Reset margin if needed */
      background: none;
      border: none;
      text-align: left; /* Align with input */
      color: #dc3545; /* Ensure text color is red */
  }
  
  .login-link {
    margin-top: 1.5rem;
    text-align: center;
    font-size: 0.9rem;
  }
  
  .login-link a {
    color: #007bff;
    text-decoration: none;
  }
  
  .login-link a:hover {
    text-decoration: underline;
  }
</style>