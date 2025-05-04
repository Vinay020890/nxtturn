<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import type { Post } from '@/stores/feed';
import { useProfileStore } from '@/stores/profile';
import PostItem from '@/components/PostItem.vue'; // Import PostItem
import { format } from 'date-fns'; // Keep format import
import { storeToRefs } from 'pinia';
import { useAuthStore } from '@/stores/auth';


// --- STORE INSTANCES ---
const route = useRoute(); // Keep route instance
const profileStoreInstance = useProfileStore(); // Instance for profile actions
const authStoreInstance = useAuthStore();     // Instance for auth state/actions

// --- CREATE REACTIVE REFS FROM STORE STATE ---
// Destructure state needed from the profile store
const {
    currentProfile,    // The profile object being viewed
    userPosts,         // The posts list for the profile user
    isLoadingProfile,  // Loading flag for profile details
    isLoadingPosts,    // Loading flag for posts
    errorProfile,      // Error for profile details
    errorPosts,        // Error for posts
    postsPagination,   // Pagination state for posts
    isFollowing,       // Follow status (boolean)
    isLoadingFollow    // Loading flag for follow actions
} = storeToRefs(profileStoreInstance); // Use storeToRefs with the instance

// Destructure state needed from the auth store
const { currentUser, isAuthenticated } = storeToRefs(authStoreInstance); // Use storeToRefs with the instance

// --- COMPONENT LOGIC ---
// Get the username from the route parameters reactively
const username = computed(() => route.params.username as string || '');

// --- ADD isOwnProfile COMPUTED PROPERTY HERE ---
const isOwnProfile = computed(() => {
        
            // --- ADD/MODIFY THESE LINES ---
        // Depend on the trigger ref to force re-evaluation
        const trigger = dataLoadedTrigger.value;
        console.log(`isOwnProfile re-evaluating (trigger=${trigger})`); // Log re-evaluation
        // --- END ADD/MODIFY ---

        const loggedInUser = currentUser.value;
        const profileData = currentProfile.value;

        // Check only after profile data is loaded AND loggedInUser exists
        if (loggedInUser && profileData) {
             const authUsername = loggedInUser.username;
             const profileUsername = profileData.username;
             // --- ADD DETAILED LOGS ---
             console.log(`COMPUTED CHECK: Auth='${authUsername}' (${typeof authUsername}), Profile='${profileUsername}' (${typeof profileUsername})`);
             const result = authUsername === profileUsername;
             console.log(`COMPUTED CHECK: Comparison result (===) is: ${result}`);
             // --- END LOGS ---
             return result; // Return the comparison result
        }
        // --- ADD LOG ---
        console.log('COMPUTED CHECK: Returning false (data missing?)');
        // --- END LOG ---
        return false; // Default to false if data isn't ready
    });

const dataLoadedTrigger = ref(0); // Add this trigger ref

// === REPLACE existing function definitions with these ===

const loadProfileData = async (page = 1) => {
  if (username.value) {
    console.log(`ProfileView: Triggering fetch for ${username.value}, page ${page}`);

    const fetchProfileIfNeeded = (page === 1 || !currentProfile.value)
        ? profileStoreInstance.fetchProfile(username.value)
        : Promise.resolve();
    const fetchPostsPromise = profileStoreInstance.fetchUserPosts(username.value, page);

    try { // Add try block
         await Promise.all([fetchProfileIfNeeded, fetchPostsPromise]);
    } catch(e) {
         console.error("Error during data fetch:", e); // Log potential errors from promises
    } finally { // Use finally to ensure this runs even if one promise fails
        // --- Force reactivity check AFTER fetches ---
        await nextTick(); // Wait for DOM updates potentially triggered by store changes
        console.log(`ProfileView: Fetch promises completed for ${username.value}, page ${page}. Re-checking state.`);
        // Explicitly log the values again AFTER await and nextTick
        console.log(`   -> After nextTick - currentProfile username: ${currentProfile.value?.username}`);
        console.log(`   -> After nextTick - currentUser username: ${currentUser.value?.username}`);
        // --- End force reactivity ---
        // --- ADD THIS LINE ---
        dataLoadedTrigger.value++; // Increment trigger
        console.log('Incremented dataLoadedTrigger to:', dataLoadedTrigger.value); // Optional log
        // --- END ADD ---
    }
  } else {
    console.warn("ProfileView: Username is empty, cannot fetch data.");
    profileStoreInstance.clearProfileData();
  }
};

onMounted(() => { // Keep existing onMounted, it calls loadProfileData which is now corrected
  console.log('ProfileView mounted for username:', username.value);
  loadProfileData(1);
});

watch(username, (newUsername, oldUsername) => { // Keep existing watch
  if (newUsername && newUsername !== oldUsername) {
    console.log(`ProfileView: Username changed to ${newUsername}, reloading data...`);
    loadProfileData(1);
  }
});

onUnmounted(() => { // Update this one
  console.log('ProfileView unmounted, clearing profile data.');
  profileStoreInstance.clearProfileData(); // Use instance for action
});

const fetchPreviousUserPosts = () => { // Update this one
    // Use local ref 'postsPagination' directly
    if (postsPagination.value.currentPage > 1) {
        loadProfileData(postsPagination.value.currentPage - 1);
    }
}
const fetchNextUserPosts = () => { // Update this one
    // Use local ref 'postsPagination' directly
    const hasNext = !!postsPagination.value.next;
    if (hasNext) {
        loadProfileData(postsPagination.value.currentPage + 1);
    }
}




</script>

<template>
  <div class="profile-view">
    <!-- Use local computed 'username' -->
    <h1>Profile Page for: {{ username }}</h1>

    <!-- Loading States - Use local refs -->
    <div v-if="isLoadingProfile || isLoadingPosts">
      <p>Loading profile...</p>
    </div>

    <!-- Error States - Use local refs -->
    <div v-else-if="errorProfile || errorPosts" class="error-message">
      <p v-if="errorProfile">Error loading profile details: {{ errorProfile }}</p>
      <p v-if="errorPosts">Error loading posts: {{ errorPosts }}</p>
    </div>

    <!-- Data Display -->
    <div v-else>
      <!-- Profile Details Section - Use local ref 'currentProfile' -->
      <section class="profile-details" v-if="currentProfile">
        <h2>User Details</h2>
         <!-- Access properties via local ref 'currentProfile' -->
        <p><strong>Username:</strong> {{ currentProfile.username }}</p>
        <p><strong>Name:</strong> {{ currentProfile.first_name }} {{ currentProfile.last_name }}</p>

        <!-- === FOLLOW BUTTON === -->
         <!-- Use local refs 'currentProfile', 'currentUser', 'isFollowing', 'isLoadingFollow' -->
         <!-- NOTE: Still using direct comparison in v-if as computed was problematic -->
         <!-- Use store instance 'profileStoreInstance' for actions -->
        <div class="follow-button-container" v-if="currentProfile && currentUser && username !== currentUser.username">
            <button
                @click="isFollowing ? profileStoreInstance.unfollowUser(username) : profileStoreInstance.followUser(username)"
                :disabled="isLoadingFollow"
                class="follow-button"
                :class="{ 'following': isFollowing }"
            >
                <span v-if="isLoadingFollow">...</span>
                <span v-else>{{ isFollowing ? 'Unfollow' : 'Follow' }}</span>
                
            </button>
        </div>
        <!-- === END FOLLOW BUTTON === -->

        <!-- Use local ref 'currentProfile' -->
        <p v-if="currentProfile.date_joined">
          <strong>Joined:</strong> {{ format(new Date(currentProfile.date_joined), 'PPP') }}
        </p>
        <p v-if="currentProfile.bio"><strong>Bio:</strong> {{ currentProfile.bio }}</p>
        <p v-if="currentProfile.location_city || currentProfile.location_state">
          <strong>Location:</strong> {{ currentProfile.location_city }}{{ currentProfile.location_city && currentProfile.location_state ? ', ' : '' }}{{ currentProfile.location_state }}
        </p>
        <p v-if="currentProfile.college_name"><strong>College:</strong> {{ currentProfile.college_name }}</p>
        <p v-if="currentProfile.major"><strong>Major:</strong> {{ currentProfile.major }}</p>
        <p v-if="currentProfile.graduation_year"><strong>Graduation Year:</strong> {{ currentProfile.graduation_year }}</p>
        <p v-if="currentProfile.linkedin_url"><strong>LinkedIn:</strong> <a :href="currentProfile.linkedin_url" target="_blank" rel="noopener noreferrer">{{ currentProfile.linkedin_url }}</a></p>
        <p v-if="currentProfile.portfolio_url"><strong>Portfolio:</strong> <a :href="currentProfile.portfolio_url" target="_blank" rel="noopener noreferrer">{{ currentProfile.portfolio_url }}</a></p>

        <!-- Use local ref 'currentProfile' -->
        <div v-if="currentProfile.skills?.length > 0">
            <strong>Skills:</strong>
            <ul><li v-for="skill in currentProfile.skills" :key="skill">{{ skill }}</li></ul>
        </div>
         <div v-if="currentProfile.interests?.length > 0">
            <strong>Interests:</strong>
            <ul><li v-for="interest in currentProfile.interests" :key="interest">{{ interest }}</li></ul>
        </div>

        <img v-if="currentProfile.profile_picture_url" :src="currentProfile.profile_picture_url" alt="Profile Picture" width="120">

      </section>
       <section v-else>
            <p>Could not load profile details.</p>
       </section>

      <hr />

      <!-- User Posts Section -->
      <section class="user-posts">
         <!-- Use local computed 'username' -->
        <h2>Posts by {{ username }}</h2>
         <!-- Use local refs -->
         <p v-if="isLoadingPosts && !isLoadingProfile">Loading posts...</p>
        <!-- Use local ref -->
        <div v-else-if="userPosts.length > 0">
           <!-- Use PostItem component -->
           <PostItem v-for="post in userPosts" :key="post.id" :post="post" />

           <!-- PAGINATION CONTROLS - Use local refs -->
           <div class="pagination-controls" v-if="!isLoadingPosts && postsPagination.count > postsPagination.pageSize">
               <button :disabled="!postsPagination.previous" @click="fetchPreviousUserPosts">Previous</button>
               <span>Page {{ postsPagination.currentPage }} of {{ postsPagination.totalPages }}</span>
               <button :disabled="!postsPagination.next" @click="fetchNextUserPosts">Next</button>
           </div>
           <!-- END PAGINATION CONTROLS -->

        </div>
        <p v-else>
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