<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import type { Post } from '@/stores/feed';

import PostItem from '@/components/PostItem.vue'; // Import PostItem
import { format } from 'date-fns'; // Keep format import
import { storeToRefs } from 'pinia';

// import { useProfileStore } from '@/stores/profile';
// import { useAuthStore } from '@/stores/auth';

import { useProfileStore, type UserProfile } from '@/stores/profile'; // Import UserProfile type
import { useAuthStore, type User } from '@/stores/auth';         // Import User type



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

// --- ADD LOCAL REACTIVE STATE FOR ASYNC LOADED DATA ---
const localCurrentProfile = ref<UserProfile | null>(profileStoreInstance.currentProfile);
const localCurrentUser = ref<User | null>(authStoreInstance.currentUser);
// --- END LOCAL REACTIVE STATE ---

// ... after localCurrentProfile and localCurrentUser definitions ...

// --- ADD WATCHERS TO UPDATE LOCAL REFS FROM STORE ---
watch(() => profileStoreInstance.currentProfile, (newProfile) => {
  console.log('ProfileView: profileStore.currentProfile changed in WATCH. New Profile User:', newProfile?.user?.username);
  localCurrentProfile.value = newProfile;
}, { immediate: true, deep: true });

watch(() => authStoreInstance.currentUser, (newUser) => {
  console.log('ProfileView: authStore.currentUser changed in WATCH. New User:', newUser?.username);
  localCurrentUser.value = newUser;
}, { immediate: true });
// --- END WATCHERS ---

// --- ADD NEW STATE FOR PICTURE UPLOAD HERE --- VVVVVV
const selectedFile = ref<File | null>(null);
const picturePreviewUrl = ref<string | null>(null); // For local preview before upload
const isUploadingPicture = ref(false); // Loading state for upload
const uploadError = ref<string | null>(null); // Error state for upload
// --- END NEW STATE --- ^^^^^^

// --- COMPONENT LOGIC ---
// Get the username from the route parameters reactively
const username = computed(() => route.params.username as string || '');

// --- ADD isOwnProfile COMPUTED PROPERTY HERE ---
const isOwnProfile = computed(() => {
  console.log("--- isOwnProfile Evaluation START ---");

  const lCurrentUser = localCurrentUser.value;
  const lCurrentProfile = localCurrentProfile.value;

  console.log("localCurrentUser.value:", JSON.stringify(lCurrentUser, null, 2));
  console.log("localCurrentProfile.value:", JSON.stringify(lCurrentProfile, null, 2));

  if (lCurrentUser && lCurrentUser.username &&
    lCurrentProfile && lCurrentProfile.user && lCurrentProfile.user.username) {

    console.log("Comparing:", lCurrentUser.username, "with", lCurrentProfile.user.username);
    const result = lCurrentUser.username === lCurrentProfile.user.username;
    console.log("Comparison result:", result);
    console.log("--- isOwnProfile Evaluation END (returning result) ---");
    return result;
  } else {
    console.log("One or more required properties are missing for comparison.");
    if (!lCurrentUser) console.log("  - localCurrentUser.value is null/undefined");
    else if (!lCurrentUser.username) console.log("  - localCurrentUser.value.username is missing");

    if (!lCurrentProfile) console.log("  - localCurrentProfile.value is null/undefined");
    else if (!lCurrentProfile.user) console.log("  - localCurrentProfile.value.user is missing");
    else if (!lCurrentProfile.user.username) console.log("  - localCurrentProfile.value.user.username is missing");

    console.log("--- isOwnProfile Evaluation END (returning false) ---");
    return false;
  }
});

// const dataLoadedTrigger = ref(0); // Add this trigger ref

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
    } catch (e) {
      console.error("Error during data fetch:", e); // Log potential errors from promises
    } finally { // Use finally to ensure this runs even if one promise fails
      // --- Force reactivity check AFTER fetches ---
      await nextTick(); // Wait for DOM updates potentially triggered by store changes
      console.log(`ProfileView: Fetch promises completed for ${username.value}, page ${page}. Re-checking state.`);
      // Explicitly log the values again AFTER await and nextTick
      console.log(`   -> After nextTick - currentProfile username: ${currentProfile.value?.user?.username}`); // Added .user
      console.log(`   -> After nextTick - currentUser username: ${currentUser.value?.username}`);
      // --- End force reactivity ---
      // --- ADD THIS LINE ---
      //  dataLoadedTrigger.value++; // Increment trigger
      // console.log('Incremented dataLoadedTrigger to:', dataLoadedTrigger.value); // Optional log
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

watch(username, (newUsername, oldUsername) => {
  if (newUsername && newUsername !== oldUsername) {
    console.log(`ProfileView: Username changed to ${newUsername}, reloading data...`);

    // Clear local refs and store state related to the *previous* profile
    localCurrentProfile.value = null; // Clear the local copy immediately
    // The store's clearProfileData will also be called by onUnmounted if navigating away completely,
    // but calling it here handles direct profile-to-profile navigation.
    profileStoreInstance.clearProfileData(); // This will clear the store's currentProfile, userPosts, pagination etc.
    // and the watcher on profileStoreInstance.currentProfile will update localCurrentProfile again (to null).

    loadProfileData(1); // Fetch data for the new username
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


// --- ADD NEW METHODS FOR FILE HANDLING HERE --- VVVVVV
function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    const file = target.files[0];
    selectedFile.value = file;
    if (picturePreviewUrl.value) {
      URL.revokeObjectURL(picturePreviewUrl.value);
    }
    // ...
    picturePreviewUrl.value = URL.createObjectURL(file);
    console.log('File selected:', file.name); // Log file name first
    console.log('Picture Preview URL created:', picturePreviewUrl.value); // Then log the URL
    uploadError.value = null;
    // ...
  } else {
    selectedFile.value = null;
    if (picturePreviewUrl.value) {
      URL.revokeObjectURL(picturePreviewUrl.value);
    }
    picturePreviewUrl.value = null;
  }
}

// In ProfileView.vue -> <script setup lang="ts">

// ... (all existing imports, store instances, refs, computed properties, other methods) ...

// --- Replace the MOCK uploadProfilePicture with this ---
async function uploadProfilePicture() {
  if (!selectedFile.value) {
    uploadError.value = "Please select an image file first.";
    // console.log('Upload attempt without a file selected.'); // Console log already in handleFileChange indirectly
    return;
  }
  if (!username.value) { // username is the computed route param
    uploadError.value = "Cannot upload picture: Username not available or invalid.";
    return;
  }

  isUploadingPicture.value = true; // Use the local ref for UI feedback
  uploadError.value = null;
  console.log(`ProfileView: Attempting to upload picture for ${username.value}:`, selectedFile.value.name);

  try {
    // Call the store action to upload the picture
    // profileStoreInstance is your instance of useProfileStore()
    const updatedProfile = await profileStoreInstance.updateProfilePicture(username.value, selectedFile.value);

    console.log('ProfileView: Picture upload successful from store action. Updated profile:', updatedProfile);

    // Clear the selection and local preview on success
    selectedFile.value = null;
    if (picturePreviewUrl.value) {
      URL.revokeObjectURL(picturePreviewUrl.value);
    }
    picturePreviewUrl.value = null;

    // --- ADD THIS LINE ---
    await nextTick(); // Wait for DOM to update after picturePreviewUrl is nullified
    // --- END ADD ---

    // The store action updated currentProfile.value, which localCurrentProfile watches.
    // The <img> tag in the template should now reactively display the new currentProfile.picture.
    alert('Profile picture updated successfully!'); // Simple success feedback

  } catch (error: any) {
    console.error('ProfileView: Error during picture upload:', error);
    // The store action re-throws a new Error with a potentially cleaner message
    uploadError.value = error.message || "Failed to upload picture.";
  } finally {
    isUploadingPicture.value = false; // Reset loading state
  }
}
// --- End of updated uploadProfilePicture method ---




</script>

<template>
  <div class="profile-view">
    <h1>Profile Page for: {{ username }}</h1>

    <!-- Loading States -->
    <div v-if="isLoadingProfile || isLoadingPosts">
      <p>Loading profile...</p>
    </div>

    <!-- Error States -->
    <div v-else-if="errorProfile || errorPosts" class="error-message">
      <p v-if="errorProfile">Error loading profile details: {{ errorProfile }}</p>
      <p v-if="errorPosts">Error loading posts: {{ errorPosts }}</p>
    </div>

    <!-- Data Display -->
    <div v-else>
      <!-- Profile Details Section -->
      <section class="profile-details" v-if="currentProfile">
        <h2>User Details</h2>

        <!-- Display Profile Picture (or preview of selected file) -->
        <template v-if="picturePreviewUrl">
          <img :src="picturePreviewUrl" :key="picturePreviewUrl + '-preview'" alt="Profile picture preview"
            class="profile-picture-display" />
        </template>
        <template v-else-if="!picturePreviewUrl && currentProfile && currentProfile.picture">
          <img :src="currentProfile.picture" :key="currentProfile.picture + '-current'" alt="Profile Picture"
            class="profile-picture-display" />
        </template>
        <div v-else class="profile-picture-placeholder">
          <span>No Picture</span>
        </div>

        <!-- File Input and Upload Button (only if own profile) -->
        <div v-if="isOwnProfile" class="profile-picture-upload-form">
          <h3>Update Profile Picture</h3>
          <input type="file" @change="handleFileChange" accept="image/png, image/jpeg, image/gif" />
          <button v-if="selectedFile" @click="uploadProfilePicture" :disabled="isUploadingPicture"
            class="upload-button">
            {{ isUploadingPicture ? 'Uploading...' : 'Upload Selected Picture' }}
          </button>
          <div v-if="uploadError" class="error-message upload-picture-error">
            {{ uploadError }}
          </div>
        </div>

        <!-- Other User Details -->
        <p v-if="currentProfile.user"><strong>Username:</strong> {{ currentProfile.user.username }}</p>
        <p v-if="currentProfile.user"><strong>Name:</strong> {{ currentProfile.user.first_name }} {{
          currentProfile.user.last_name }}</p>
        <div class="follow-button-container" v-if="currentProfile && currentUser && username !== currentUser.username">
          <button
            @click="isFollowing ? profileStoreInstance.unfollowUser(username) : profileStoreInstance.followUser(username)"
            :disabled="isLoadingFollow" class="follow-button" :class="{ 'following': isFollowing }">
            <span v-if="isLoadingFollow">...</span>
            <span v-else>{{ isFollowing ? 'Unfollow' : 'Follow' }}</span>
          </button>
        </div>
        <p v-if="currentProfile.user && currentProfile.user.date_joined">
          <strong>Joined:</strong> {{ format(new Date(currentProfile.user.date_joined), 'PPP') }}
        </p>
        <p v-if="currentProfile.bio"><strong>Bio:</strong> {{ currentProfile.bio }}</p>
        <p v-if="currentProfile.location_city || currentProfile.location_state">
          <strong>Location:</strong> {{ currentProfile.location_city }}{{ currentProfile.location_city &&
            currentProfile.location_state ? ', ' : '' }}{{ currentProfile.location_state }}
        </p>
        <p v-if="currentProfile.college_name"><strong>College:</strong> {{ currentProfile.college_name }}</p>
        <p v-if="currentProfile.major"><strong>Major:</strong> {{ currentProfile.major }}</p>
        <p v-if="currentProfile.graduation_year"><strong>Graduation Year:</strong> {{ currentProfile.graduation_year }}
        </p>
        <p v-if="currentProfile.linkedin_url"><strong>LinkedIn:</strong> <a :href="currentProfile.linkedin_url"
            target="_blank" rel="noopener noreferrer">{{ currentProfile.linkedin_url }}</a></p>
        <p v-if="currentProfile.portfolio_url"><strong>Portfolio:</strong> <a :href="currentProfile.portfolio_url"
            target="_blank" rel="noopener noreferrer">{{ currentProfile.portfolio_url }}</a></p>
        <div v-if="currentProfile.skills?.length > 0">
          <strong>Skills:</strong>
          <ul>
            <li v-for="skill in currentProfile.skills" :key="skill">{{ skill }}</li>
          </ul>
        </div>
        <div v-if="currentProfile.interests?.length > 0">
          <strong>Interests:</strong>
          <ul>
            <li v-for="interest in currentProfile.interests" :key="interest">{{ interest }}</li>
          </ul>
        </div>
      </section>
      <section v-else>
        <p>Could not load profile details.</p>
      </section>

      <hr />

      <!-- User Posts Section -->
      <section class="user-posts">
        <h2>Posts by {{ username }}</h2>
        <p v-if="isLoadingPosts && !isLoadingProfile">Loading posts...</p>
        <div v-else-if="userPosts.length > 0">
          <PostItem v-for="post in userPosts" :key="post.id" :post="post" />
          <div class="pagination-controls" v-if="!isLoadingPosts && postsPagination.count > postsPagination.pageSize">
            <button :disabled="!postsPagination.previous" @click="fetchPreviousUserPosts">Previous</button>
            <span>Page {{ postsPagination.currentPage }} of {{ postsPagination.totalPages }}</span>
            <button :disabled="!postsPagination.next" @click="fetchNextUserPosts">Next</button>
          </div>
        </div>
        <p v-else>This user hasn't posted anything yet.</p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.profile-view {
  padding: 1.5rem;
  /* Slightly more padding */
  max-width: 800px;
  /* Limit max width */
  margin: 1rem auto;
  /* Center the content */
  background-color: #2d2d2d;
  /* Slightly lighter background for contrast */
  border-radius: 8px;
  /* Rounded corners */
  color: #e0e0e0;
  /* Lighter text for dark background */
}

.error-message {
  color: #ff8a80;
  /* Lighter red for dark theme */
  border: 1px solid #ff8a80;
  padding: 0.75rem;
  /* More padding */
  margin-bottom: 1rem;
  background-color: #4e3432;
  /* Dark red background */
  border-radius: 4px;
}

.profile-details,
.user-posts {
  margin-bottom: 2rem;
  /* More space between sections */
}

/* --- Styles for Profile Details --- */
.profile-details h2,
.user-posts h2 {
  border-bottom: 1px solid #555;
  /* Underline section titles */
  padding-bottom: 0.5rem;
  margin-bottom: 1rem;
  color: #ffffff;
  /* White title */
}

.profile-details p,
.profile-details div {
  margin-bottom: 0.6rem;
  /* Consistent spacing */
  line-height: 1.5;
  /* Improve readability */
}

.profile-details strong {
  color: #bdbdbd;
  /* Slightly different color for labels */
  margin-right: 0.5rem;
  display: inline-block;
  /* Ensure consistent alignment */
  min-width: 120px;
  /* Align labels */
}

.profile-details a {
  color: #82b1ff;
  /* Light blue for links */
  text-decoration: none;
}

.profile-details a:hover {
  text-decoration: underline;
}

.profile-details ul {
  list-style: none;
  /* Remove default bullets */
  padding-left: 0;
  /* Remove default padding */
  margin-top: 0.2rem;
  display: inline;
  /* Keep tags mostly inline with label */
}

.profile-details li {
  display: inline-block;
  /* Display skills/interests inline */
  background-color: #424242;
  /* Tag background */
  padding: 0.2rem 0.6rem;
  margin-right: 0.5rem;
  margin-bottom: 0.5rem;
  border-radius: 12px;
  /* Pill shape */
  font-size: 0.9em;
  border: none;
  /* Remove previous border */
}

/* Container for skills/interests to align label correctly */
.profile-details div>strong {
  vertical-align: top;
  /* Align label with top of tags */
}


/* Add these to your existing <style scoped> in ProfileView.vue */
.profile-picture-display {
  width: 120px;
  /* Or your preferred size */
  height: 120px;
  border-radius: 50%;
  /* Make it round */
  object-fit: cover;
  /* Ensures the image covers the area without distortion */
  margin-bottom: 1rem;
  border: 3px solid #444;
  /* Example border */
}

.profile-picture-placeholder {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background-color: #555;
  /* Darker placeholder background */
  color: #aaa;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
  border: 3px solid #444;
  font-size: 0.9em;
}

/* --- End Profile Details Styles --- */

hr {
  margin: 2rem 0;
  /* More spacing around horizontal rule */
  border: none;
  border-top: 1px solid #555;
  /* Style the rule */
}

/* --- Styles for Post List --- */
.user-posts ul {
  list-style: none;
  padding: 0;
}

.user-posts li {
  background-color: #3a3a3a;
  /* Darker background for posts */
  border: 1px solid #555;
  /* Subtle border */
  margin-bottom: 1rem;
  /* More space between posts */
  padding: 1rem;
  border-radius: 4px;
}

.user-posts li p {
  margin-top: 0;
  /* Remove default top margin */
  margin-bottom: 0.5rem;
  /* Space between content and date */
}

.user-posts li small {
  font-size: 0.85em;
  color: #aaa;
  /* Lighter grey for date */
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

.pagination-controls button:disabled {
  /* Style for disabled state */
  cursor: not-allowed;
  opacity: 0.6;
  background-color: #f8f8f8;
}

.pagination-controls button:not(:disabled):hover {
  /* Hover for enabled */
  background-color: #ddd;
}

.pagination-controls span {
  /* Style for the page text */
  margin: 0 1rem;
  color: #555;
}

/* --- END OF ADDED STYLES --- */
</style>