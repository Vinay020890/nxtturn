<script setup lang="ts">
import { useAuthStore } from '@/stores/auth';
// Import necessary Composition API functions or stores later if needed
// import { onMounted } from 'vue';



const authStore = useAuthStore();

// onMounted(() => {
//   // Fetch feed data when component mounts, maybe?
//   console.log('FeedView mounted');
// });

</script>

<template>
    <div class="feed-view">
      <!-- Changed h1 to display welcome message -->
      <h1>Welcome, {{ authStore.userDisplay }}!</h1>
      <!-- Added h2 for original title -->
      <h2>Your Feed</h2>
      <p>Feed content will appear here.</p>
    </div>
  </template>

<style scoped>
.feed-view {
  max-width: 800px; /* Adjust as needed */
  margin: 1rem auto;
  padding: 1rem;
}
/* Add more styles later */
</style>