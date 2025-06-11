<script setup lang="ts">
import { ref } from 'vue';
import { useAuthStore } from '@/stores/auth'; // Import the auth store
import { useRouter } from 'vue-router'; 

const username = ref('');
const password = ref('');
const errorMessage = ref<string | null>(null); // To store potential login errors

const showPassword = ref(false); // Initially password is hidden

const authStore = useAuthStore(); // Get the auth store instance
const router = useRouter();

const togglePasswordVisibility = () => {
  showPassword.value = !showPassword.value;
};


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
        <div class="password-input-wrapper">
          <input
            :type="showPassword ? 'text' : 'password'"
            id="password"
            v-model="password"
            required
          />
          <button type="button" @click="togglePasswordVisibility" class="password-toggle-btn" aria-label="Toggle password visibility">
            <span v-if="showPassword">
              <!-- Bootstrap Icons: eye-slash-fill -->
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" class="bi bi-eye-slash-fill" viewBox="0 0 16 16">
                <path d="m10.79 12.912-1.614-1.615a3.5 3.5 0 0 1-4.474-4.474l-2.06-2.06C.938 6.278 0 8 0 8s3 5.5 8 5.5a7.029 7.029 0 0 0 2.79-.588zM5.21 3.088A7.028 7.028 0 0 1 8 2.5c5 0 8 5.5 8 5.5s-.939 1.721-2.641 3.238l-2.062-2.062a3.5 3.5 0 0 0-4.474-4.474L5.21 3.089z"/>
                <path d="M5.525 7.646a2.5 2.5 0 0 0 2.829 2.829l-2.83-2.829zm4.95.708-2.829-2.83a2.5 2.5 0 0 1 2.829 2.829zm3.171 6-12-12 .708-.708 12 12-.708.708z"/>
              </svg>
            </span>
            <span v-else>
              <!-- Bootstrap Icons: eye-fill -->
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" class="bi bi-eye-fill" viewBox="0 0 16 16">
                <path d="M10.5 8a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0z"/>
                <path d="M0 8s3-5.5 8-5.5S16 8 16 8s-3 5.5-8 5.5S0 8 0 8zm8 3.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z"/>
              </svg>
            </span>
          </button>
        </div>
      </div>

      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>
      <button type="submit">Login</button>
    </form>
    <div class="extra-links">
      <p>
        Don't have an account?
        <router-link :to="{ name: 'register' }" class="link-to-register">Create one</router-link>
      </p>
    </div>
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

.extra-links {
  margin-top: 1.5rem; /* Space above the "Don't have an account?" text */
  text-align: center; /* Center the text */
  font-size: 0.9em;   /* Slightly smaller font */
}

.extra-links p {
  color: #adb5bd; /* Light gray text, adjust to your theme */
  margin-bottom: 0; /* Remove default paragraph bottom margin if not needed */
}

.link-to-register {
  color: #28a745;   /* Green color, similar to your buttons or an accent color */
  text-decoration: none;
  font-weight: 500; /* Make the link text slightly bolder */
}

.link-to-register:hover {
  text-decoration: underline;
  color: #218838; /* Darker green on hover */
}

.password-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.password-input-wrapper input {
  /* Ensure the input takes full width of its parent .form-group minus space for button */
  /* padding-right is crucial if button is positioned absolutely inside */
  padding-right: 4rem; /* Adjust this value based on your button's width + desired spacing */
}

.password-toggle-btn {
  position: absolute;
  right: 0.5rem; /* Adjust for desired position from the right edge */
  top: 50%;
  transform: translateY(-50%);
  background: none; /* Crucial: remove default button background */
  border: none;     /* Crucial: remove default button border */
  color: #adb5bd;    /* Color for the "Show/Hide" text or an icon */
  cursor: pointer;
  padding: 0.25rem 0.5rem; /* Make it easy to click */
  font-size: 0.8em;       /* Adjust font size of "Show/Hide" */
  line-height: 1;         /* Helps with vertical alignment of text */
  
  /* Override general button styles from your component's global button style */
  width: auto;             /* Don't make it full width */
  background-color: transparent !important; /* Force transparent if other styles interfere */
}

.password-toggle-btn:hover {
  color: #e0e0e0; /* Brighter color on hover */
  background-color: transparent !important; /* Ensure no background change on hover */
}
/* END OF ADDED STYLES for password toggle */
</style>