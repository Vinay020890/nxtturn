<script setup lang="ts">
// Import RouterView for displaying pages, useRouter for navigation
import { RouterView, useRouter, RouterLink } from 'vue-router';
// Import the Pinia store to check authentication status and call logout
import { useAuthStore } from '@/stores/auth';

// Get instances of the store and router
const authStore = useAuthStore();
const router = useRouter();

// Method to handle the logout process
const handleLogout = () => {
  console.log('Logout button clicked');
  authStore.logout(); // Call the store action to clear token/user state
  router.push({ name: 'login' }); // Redirect to the login page
};
</script>

<template>
  <header>
    <nav>
      <!-- Left side: Basic Branding/Home Link (Example) -->
      <div>
        <!-- RouterLink creates navigation links -->
        <RouterLink to="/">Loopline</RouterLink>
      </div>

      <!-- Right side: Auth Section -->
      <div>
        <!-- Show different content based on authentication status -->
        <span v-if="authStore.isAuthenticated">
          Welcome, {{ authStore.userDisplay }}!
          <button @click="handleLogout">Logout</button>
        </span>
        <span v-else>
          <!-- Show Login/Register links if not logged in -->
          <RouterLink to="/login" style="margin-right: 10px;">Login</RouterLink>
          <!-- We'll add a Register link later -->
          <!-- <RouterLink to="/register">Register</RouterLink> -->
        </span>
      </div>
    </nav>
  </header>

  <!-- Main content area where the router renders the current page -->
  <main>
    <RouterView />
  </main>
</template>

<style scoped>
header {
  background-color: #f8f8f8;
  padding: 0.5rem 1rem;
  border-bottom: 1px solid #eee;
  line-height: 1.5;
}
nav {
  display: flex; /* Use flexbox for layout */
  justify-content: space-between; /* Space out left/right sides */
  align-items: center; /* Vertically align items */
  max-width: 1200px; /* Max width for content */
  margin: 0 auto; /* Center the nav content */
}
nav button { /* Style logout button */
   margin-left: 1rem;
   padding: 0.3rem 0.6rem;
   cursor: pointer;
   /* Add basic button styles if needed */
   background-color: #eee;
   border: 1px solid #ccc;
   border-radius: 4px;
}
nav button:hover {
    background-color: #ddd;
}
main {
  /* Keep padding, adjust as needed */
  padding: 1rem; /* Consistent padding */
  max-width: 1200px; /* Optional: Max width for main content */
  margin: 1rem auto; /* Optional: Center main content */
}
/* Add basic link styling */
a {
    text-decoration: none;
    color: #007bff; /* Example link color */
    font-weight: 500;
}
a:hover {
    text-decoration: underline;
}
/* Style for the brand link */
nav > div:first-child a {
    font-weight: bold;
    color: #333; /* Example brand color */
}
</style>