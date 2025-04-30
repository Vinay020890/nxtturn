<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import type { Post } from '@/stores/feed';
import { useProfileStore } from '@/stores/profile';
import PostItem from '@/components/PostItem.vue'; // Import PostItem
import { format } from 'date-fns'; // Keep format import

const route = useRoute();
const profileStore = useProfileStore();

const username = computed(() => route.params.username as string || '');

// --- MODIFY loadProfileData to accept page ---
const loadProfileData = async (page = 1) => { // Accept page, default 1
  if (username.value) {
    console.log(`ProfileView: Triggering fetch for ${username.value}, page ${page}`);

    // Fetch profile only if on page 1 or if profile isn't loaded yet
    const fetchProfileIfNeeded = (page === 1 || !profileStore.currentProfile)
        ? profileStore.fetchProfile(username.value)
        : Promise.resolve(); // Don't refetch profile on post pagination

    // Fetch user posts for the requested page
    const fetchPostsPromise = profileStore.fetchUserPosts(username.value, page);

    // Await both (profile fetch might be instant if resolved)
    await Promise.all([fetchProfileIfNeeded, fetchPostsPromise]);

    console.log(`ProfileView: Fetch completed for ${username.value}, page ${page}`);
  } else {
    console.warn("ProfileView: Username is empty, cannot fetch data.");
    profileStore.clearProfileData();
  }
};
// --- END MODIFY loadProfileData ---


onMounted(() => {
  console.log('ProfileView mounted for username:', username.value);
  loadProfileData(1); // Load initial page 1 data
});

watch(username, (newUsername, oldUsername) => {
  if (newUsername && newUsername !== oldUsername) {
    console.log(`ProfileView: Username changed to ${newUsername}, reloading data...`);
    loadProfileData(1); // Load page 1 for new user
  }
});

onUnmounted(() => {
  console.log('ProfileView unmounted, clearing profile data.');
  profileStore.clearProfileData();
});

// --- ADD Pagination Methods ---
const fetchPreviousUserPosts = () => {
    // Check using currentPage directly from the reactive ref
    if (profileStore.postsPagination.currentPage > 1) {
        loadProfileData(profileStore.postsPagination.currentPage - 1);
    }
}
const fetchNextUserPosts = () => {
    // Check using hasNextPage logic derived from 'next' url
    const hasNext = !!profileStore.postsPagination.next;
    if (hasNext) {
        loadProfileData(profileStore.postsPagination.currentPage + 1);
    }
}
// --- END Pagination Methods ---

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
          
          <p v-if="profileStore.currentProfile?.date_joined"> <!-- Check if date_joined exists -->
           <strong>Joined:</strong> {{ format(new Date(profileStore.currentProfile.date_joined), 'PPP') }}
          </p>

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
                      <!-- Loop through posts using the PostItem component -->
          <!-- We can remove the ul/li structure if PostItem renders its own article/div -->
            <PostItem v-for="post in profileStore.userPosts" :key="post.id" :post="post" />
            <!-- TODO: Add pagination for user posts -->
             <!-- === ADD PAGINATION CONTROLS RIGHT HERE === -->
            <div class="pagination-controls" v-if="!profileStore.isLoadingPosts && profileStore.postsPagination.count > profileStore.postsPagination.pageSize">
                <button :disabled="!profileStore.postsPagination.previous" @click="fetchPreviousUserPosts">Previous</button>
                <span>Page {{ profileStore.postsPagination.currentPage }} of {{ profileStore.postsPagination.totalPages }}</span>
                <button :disabled="!profileStore.postsPagination.next" @click="fetchNextUserPosts">Next</button>
            </div>
            <!-- === END PAGINATION CONTROLS === -->
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
  padding: 1.5rem; /* Slightly more padding */
  max-width: 800px; /* Limit max width */
  margin: 1rem auto; /* Center the content */
  background-color: #2d2d2d; /* Slightly lighter background for contrast */
  border-radius: 8px; /* Rounded corners */
  color: #e0e0e0; /* Lighter text for dark background */
}

.error-message {
  color: #ff8a80; /* Lighter red for dark theme */
  border: 1px solid #ff8a80;
  padding: 0.75rem; /* More padding */
  margin-bottom: 1rem;
  background-color: #4e3432; /* Dark red background */
  border-radius: 4px;
}

.profile-details, .user-posts {
  margin-bottom: 2rem; /* More space between sections */
}

/* --- Styles for Profile Details --- */
.profile-details h2, .user-posts h2 {
    border-bottom: 1px solid #555; /* Underline section titles */
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
    color: #ffffff; /* White title */
}

.profile-details p, .profile-details div {
    margin-bottom: 0.6rem; /* Consistent spacing */
    line-height: 1.5; /* Improve readability */
}

.profile-details strong {
    color: #bdbdbd; /* Slightly different color for labels */
    margin-right: 0.5rem;
    display: inline-block; /* Ensure consistent alignment */
    min-width: 120px; /* Align labels */
}

.profile-details a {
    color: #82b1ff; /* Light blue for links */
    text-decoration: none;
}
.profile-details a:hover {
    text-decoration: underline;
}

.profile-details ul {
    list-style: none; /* Remove default bullets */
    padding-left: 0; /* Remove default padding */
    margin-top: 0.2rem;
    display: inline; /* Keep tags mostly inline with label */
}
.profile-details li {
    display: inline-block; /* Display skills/interests inline */
    background-color: #424242; /* Tag background */
    padding: 0.2rem 0.6rem;
    margin-right: 0.5rem;
    margin-bottom: 0.5rem;
    border-radius: 12px; /* Pill shape */
    font-size: 0.9em;
    border: none; /* Remove previous border */
}

/* Container for skills/interests to align label correctly */
.profile-details div > strong {
     vertical-align: top; /* Align label with top of tags */
}


.profile-details img {
    display: block;
    margin-top: 1rem;
    border-radius: 50%; /* Make profile pic round */
    border: 2px solid #555; /* Add a subtle border */
    width: 120px; /* Slightly larger */
    height: 120px;
    object-fit: cover; /* Ensure image covers space nicely */
}
/* --- End Profile Details Styles --- */

hr {
  margin: 2rem 0; /* More spacing around horizontal rule */
  border: none;
  border-top: 1px solid #555; /* Style the rule */
}

/* --- Styles for Post List --- */
.user-posts ul {
    list-style: none;
    padding: 0;
}
.user-posts li {
    background-color: #3a3a3a; /* Darker background for posts */
    border: 1px solid #555; /* Subtle border */
    margin-bottom: 1rem; /* More space between posts */
    padding: 1rem;
    border-radius: 4px;
}
.user-posts li p {
    margin-top: 0; /* Remove default top margin */
    margin-bottom: 0.5rem; /* Space between content and date */
}
.user-posts li small {
    font-size: 0.85em;
    color: #aaa; /* Lighter grey for date */
}

/* Hide old pre tag if not used */
pre {
    display: none;
}

/* --- ADD THESE STYLES --- */
.pagination-controls {
    margin-top: 2rem;
    text-align: center;
}

.pagination-controls button {
    padding: 0.5rem 1rem;
    margin: 0 0.5rem;
    cursor: pointer;
    /* Add basic button styling as needed */
    background-color: #eee;
    border: 1px solid #ccc;
    border-radius: 4px;
}

.pagination-controls button:disabled { /* Style for disabled state */
    cursor: not-allowed;
    opacity: 0.6;
    background-color: #f8f8f8;
}
 .pagination-controls button:not(:disabled):hover { /* Hover for enabled */
    background-color: #ddd;
 }

 .pagination-controls span { /* Style for the page text */
     margin: 0 1rem;
     color: #555;
 }
/* --- END OF ADDED STYLES --- */

</style>