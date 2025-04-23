<script setup lang="ts">
import { ref } from 'vue';
import { useAuthStore } from '@/stores/auth'; // Import the auth store
import { useRouter } from 'vue-router'; 

const username = ref('');
const password = ref('');
const errorMessage = ref<string | null>(null); // To store potential login errors

const authStore = useAuthStore(); // Get the auth store instance
const router = useRouter();

const handleLogin = async () => {
  errorMessage.value = null; // Clear previous errors
  console.log('Login attempt:', username.value);

  try {
    // Call the login action from the Pinia store
    // The action currently mocks success or throws an error
    await authStore.login({
      username: username.value,
      password: password.value,
    });

    // If the above line doesn't throw an error, it succeeded (in our mock)
    console.log('LoginView: Login action succeeded.');
    // --- WE WILL ADD REDIRECTION LATER ---
    router.push({ name: 'feed' }); // <-- ADD THIS LINE to redirect

  } catch (error: any) {
    // Handle errors thrown by the authStore.login action
    console.error('LoginView: Login action failed:', error);

    // Basic error display for now (we'll refine later)
    // Attempt to get DRF non_field_errors first
    if (error?.response?.data?.non_field_errors) {
         errorMessage.value = error.response.data.non_field_errors.join(' ');
    } else {
         // If no specific error, show a generic one
         errorMessage.value = 'Login failed. Please check credentials or try again.';
    }
  }
};
</script>

<template>
  <div class="login-view">
    <h1>Login</h1>
    <form @submit.prevent="handleLogin">
      <div class="form-group">
        <label for="username">Username:</label>
        <input type="text" id="username" v-model="username" required />
      </div>
      <div class="form-group">
        <label for="password">Password:</label>
        <input type="password" id="password" v-model="password" required />
      </div>
      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>
      <button type="submit">Login</button>
    </form>
    <!-- Add link to registration page later -->
    <!-- <p>Don't have an account? <router-link to="/register">Register</router-link></p> -->
  </div>
</template>

<style scoped>
.login-view {
  max-width: 400px;
  margin: 2rem auto;
  padding: 1.5rem;
  border: 1px solid #ccc;
  border-radius: 8px;
  /* Add more mobile-first styles */
}
.form-group {
  margin-bottom: 1rem;
}
.form-group label {
  display: block;
  margin-bottom: 0.3rem;
}
.form-group input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box; /* Include padding and border in the element's total width and height */
}
button {
  padding: 0.6rem 1.2rem;
  background-color: #4CAF50; /* Example color */
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  width: 100%; /* Make button full width */
}
button:hover {
  background-color: #45a049;
}
.error-message {
  color: red;
  margin-bottom: 1rem;
  font-size: 0.9em;
}
</style>