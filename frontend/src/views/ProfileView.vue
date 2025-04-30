<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'; // Add onUnmounted, watch
import { useRoute } from 'vue-router';
import type { Post } from '@/stores/feed'; // Import Post type
// --- Import the profile store ---
import { useProfileStore } from '@/stores/profile'; // Import the store we just created

const route = useRoute();
// --- Get the profile store instance ---
const profileStore = useProfileStore(); // Use the store

// Get the username from the route parameters (reactively)
const username = computed(() => route.params.username as string || '');

// Function to trigger data fetching
const loadProfileData = async () => {
  if (username.value) {
    console.log(`ProfileView: Triggering fetch for ${username.value}`);
    // Reset previous errors/data before fetching
    profileStore.clearProfileData(); // Optional: Clear before fetch or rely on actions clearing state
    // Use Promise.all to fetch profile and posts concurrently
    await Promise.all([
        profileStore.fetchProfile(username.value),
        profileStore.fetchUserPosts(username.value)
    ]);
    console.log(`ProfileView: Fetch completed for ${username.value}`);
  } else {
      console.warn("ProfileView: Username is empty, cannot fetch data.");
      profileStore.clearProfileData(); // Clear data if username is invalid
  }
};

// Fetch data when the component mounts
onMounted(() => {
  console.log('ProfileView mounted for username:', username.value);
  loadProfileData();
});

// Watch for changes in the username param (if user navigates from one profile to another)
watch(username, (newUsername, oldUsername) => {
  // Only reload if username is valid and actually changed
  if (newUsername && newUsername !== oldUsername) {
    console.log(`ProfileView: Username changed to ${newUsername}, reloading data...`);
    loadProfileData(); // Reload data for the new username
  }
});

// Clear store state when the component is unmounted
onUnmounted(() => {
  console.log('ProfileView unmounted, clearing profile data.');
  profileStore.clearProfileData();
});

</script>

<template>
    <div class="profile-view">
      <h1>Profile Page for: {{ username }}</h1>
  
      <!-- Loading States -->
      <div v-if="profileStore.isLoadingProfile || profileStore.isLoadingPosts">
        <p>Loading profile...</p>
        <!-- Add a spinner or more detailed loading indicator if desired -->
      </div>
  
      <!-- Error States -->
      <div v-else-if="profileStore.errorProfile || profileStore.errorPosts" class="error-message">
        <p v-if="profileStore.errorProfile">Error loading profile details: {{ profileStore.errorProfile }}</p>
        <p v-if="profileStore.errorPosts">Error loading posts: {{ profileStore.errorPosts }}</p>
      </div>
  
      <!-- Data Display -->
      <div v-else>
        <!-- Profile Details Section -->
        <section class="profile-details" v-if="profileStore.currentProfile">
          <h2>User Details</h2>
          <!-- Display actual profile fields -->
          <p><strong>Username:</strong> {{ profileStore.currentProfile.username }}</p>
          <p><strong>Name:</strong> {{ profileStore.currentProfile.first_name }} {{ profileStore.currentProfile.last_name }}</p>
          <p><strong>Joined:</strong> {{ new Date(profileStore.currentProfile.date_joined).toLocaleDateString() }}</p>
          <p v-if="profileStore.currentProfile.bio"><strong>Bio:</strong> {{ profileStore.currentProfile.bio }}</p>
          <p v-if="profileStore.currentProfile.location_city || profileStore.currentProfile.location_state">
            <strong>Location:</strong> {{ profileStore.currentProfile.location_city }}{{ profileStore.currentProfile.location_city && profileStore.currentProfile.location_state ? ', ' : '' }}{{ profileStore.currentProfile.location_state }}
          </p>
          <p v-if="profileStore.currentProfile.college_name"><strong>College:</strong> {{ profileStore.currentProfile.college_name }}</p>
          <p v-if="profileStore.currentProfile.major"><strong>Major:</strong> {{ profileStore.currentProfile.major }}</p>
          <p v-if="profileStore.currentProfile.graduation_year"><strong>Graduation Year:</strong> {{ profileStore.currentProfile.graduation_year }}</p>
          <p v-if="profileStore.currentProfile.linkedin_url"><strong>LinkedIn:</strong> <a :href="profileStore.currentProfile.linkedin_url" target="_blank" rel="noopener noreferrer">{{ profileStore.currentProfile.linkedin_url }}</a></p>
          <p v-if="profileStore.currentProfile.portfolio_url"><strong>Portfolio:</strong> <a :href="profileStore.currentProfile.portfolio_url" target="_blank" rel="noopener noreferrer">{{ profileStore.currentProfile.portfolio_url }}</a></p>
  
          <div v-if="profileStore.currentProfile.skills?.length > 0">
              <strong>Skills:</strong>
              <ul><li v-for="skill in profileStore.currentProfile.skills" :key="skill">{{ skill }}</li></ul>
          </div>
           <div v-if="profileStore.currentProfile.interests?.length > 0">
              <strong>Interests:</strong>
              <ul><li v-for="interest in profileStore.currentProfile.interests" :key="interest">{{ interest }}</li></ul>
          </div>
  
          <!-- Add Profile Picture if URL exists -->
          <img v-if="profileStore.currentProfile.profile_picture_url" :src="profileStore.currentProfile.profile_picture_url" alt="Profile Picture" width="100">
  
        </section>
         <section v-else>
              <!-- Message if profile data couldn't load but no specific error -->
              <p>Could not load profile details.</p>
         </section>
  
        <hr />
  
        <!-- User Posts Section -->
        <section class="user-posts">
          <h2>Posts by {{ username }}</h2>
           <!-- Show loading specifically for posts if profile is already loaded -->
           <p v-if="profileStore.isLoadingPosts && !profileStore.isLoadingProfile">Loading posts...</p>
          <div v-else-if="profileStore.userPosts.length > 0">
            <ul>
              <!-- Loop through posts from the store -->
              <li v-for="post in profileStore.userPosts" :key="post.id">
                <!-- Basic post display -->
                <p>{{ post.content }}</p>
                <small>Posted on: {{ new Date(post.created_at).toLocaleString() }}</small>
                <!-- TODO: Add like button/count here too, using feedStore logic? -->
                <!-- This might require making toggleLike more generic or passing store instance -->
              </li>
            </ul>
            <!-- TODO: Add pagination for user posts -->
          </div>
          <p v-else>
              <!-- Message shown if loading is finished and no posts exist -->
              This user hasn't posted anything yet.
          </p>
        </section>
      </div>
    </div>
  </template>

<style scoped>
.profile-view {
  padding: 1rem;
}

.error-message {
  color: red;
  border: 1px solid red;
  padding: 0.5rem;
  margin-bottom: 1rem;
}

.profile-details, .user-posts {
  margin-bottom: 1.5rem;
}

hr {
  margin: 1.5rem 0;
}

pre {
    background-color: #f4f4f4;
    padding: 10px;
    border-radius: 4px;
    white-space: pre-wrap; /* Allows wrapping */
    word-wrap: break-word; /* Breaks long words */
    color: #333; /* Adjust text color if needed */
}

ul {
    list-style: none;
    padding: 0;
}
li {
    border: 1px solid #ccc;
    margin-bottom: 10px;
    padding: 10px;
    border-radius: 4px;
}
</style>