<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import type { Post } from '@/stores/feed';
import { useFeedStore } from '@/stores/feed';
import { format } from 'date-fns';
import { useCommentStore } from '@/stores/comment';
import CommentItem from '@/components/CommentItem.vue';
import { useAuthStore } from '@/stores/auth';
import { storeToRefs } from 'pinia';
import { useProfileStore } from '@/stores/profile';

// --- Props Definition ---
const props = defineProps<{
  post: Post
}>();



// --- Store Instances ---
const feedStore = useFeedStore();
const commentStore = useCommentStore();
const authStore = useAuthStore();
const profileStore = useProfileStore();

const { currentUser, isAuthenticated } = storeToRefs(authStore);

// --- GET REACTIVE REFS FROM COMMENT STORE FOR CREATION ---
const { isCreatingComment, createCommentError } = storeToRefs(commentStore);

// --- Local State ---
const showComments = ref(false);
const newCommentContent = ref('');

const localDeleteError = ref<string | null>(null); 

// ===========================================
// 👇 ADD THIS COMPUTED PROPERTY
const isOwner = computed(() => {
  // If user is not logged in, or no current user data, or post has no author, they can't be the owner.
  if (!isAuthenticated.value || !currentUser.value || !props.post.author) {
    return false;
  }
  // Compare the logged-in user's ID with the post author's ID.
  // Make sure `currentUser.value.id` and `props.post.author.id` are correct for your setup.
  return currentUser.value.id === props.post.author.id;
});
// ===========================================

// --- HELPER / UTILITY FUNCTIONS (Component-Specific) ---
// 👇👇👇 IDEAL SPOT FOR linkifyContent 👇👇👇
function linkifyContent(text: string | null | undefined): string {
  if (!text) return '';
  const urlRegex = /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])|(\bwww\.[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
  return text.replace(urlRegex, function(url) {
    let fullUrl = url;
    if (!fullUrl.match(/^https?:\/\//i) && fullUrl.startsWith('www.')) {
      fullUrl = 'http://' + fullUrl;
    }
    return `<a href="${fullUrl}" target="_blank" rel="noopener noreferrer">${url}</a>`;
  });
}
// ------------------------------------



// --- Watch for input changes to clear comment creation errors ---
watch(newCommentContent, () => {
  // If the user starts typing and there was a submission error...
  if (createCommentError.value) { // Note: .value is needed here because createCommentError is a ref from storeToRefs
    // ...clear the error in the store.
    commentStore.createCommentError = null; // Directly set the property on the store instance
  }
});

// --- Computed Properties ---
const likeButtonText = computed(() => {
  return props.post.is_liked_by_user ? 'Unlike' : 'Like';
});

const commentPostKey = computed(() => {
  if (!props.post || typeof props.post.post_type === 'undefined' || typeof props.post.object_id === 'undefined') {
    return `invalid_${props.post?.id || 'unknown'}`;
  }
  const key = `${props.post.post_type}_${props.post.object_id}`;
  return key;
});

// In PostItem.vue
const commentsForThisPost = computed(() => { // Consider renaming to topLevelCommentsForPost for clarity
  const key = commentPostKey.value;
  if (!commentStore || 
      typeof commentStore.commentsByPost === 'undefined' || 
      typeof commentStore.commentsByPost !== 'object' || 
      commentStore.commentsByPost === null) {
    return [];
  }
  const allCommentsForPost = commentStore.commentsByPost[key] || [];
  // Filter for comments that do NOT have a 'parent' (i.e., parent is null or undefined)
  return allCommentsForPost.filter(comment => !comment.parent); 
});

const isLoadingComments = computed(() => { // This is for FETCHING comments
  return commentStore.isLoading;
});

const commentError = computed(() => { // This is for FETCHING comments
  return commentStore.error;
});

// --- Methods ---
function loadComments() {
  if (!props.post || typeof props.post.post_type === 'undefined' || typeof props.post.object_id === 'undefined') {
    return;
  }
  commentStore.fetchComments(props.post.post_type, props.post.object_id);
}

function toggleCommentDisplay() {
  showComments.value = !showComments.value;
  const currentComments = commentsForThisPost.value;
  if (showComments.value && Array.isArray(currentComments) && currentComments.length === 0 && !commentError.value) {
    loadComments();
  }
}

async function handleCommentSubmit() {
  if (!newCommentContent.value.trim()) {
    commentStore.createCommentError = "Comment cannot be empty.";
    return;
  }
  if (!props.post || !props.post.post_type || typeof props.post.object_id === 'undefined') {
    commentStore.createCommentError = "Cannot submit comment: Invalid post data.";
    return;
  }

  commentStore.createCommentError = null;

  try {
    await commentStore.createComment(
      props.post.post_type,
      props.post.object_id,
      newCommentContent.value,
      props.post.id
    );
    newCommentContent.value = '';
  } catch (error) {
    console.error("PostItem: createComment action failed (error state should be set in store).");
  }
}

// In PostItem.vue
// This replaces the toggleLike method you just showed me.

const toggleLike = async () => {
  // console.log('[PostItem] toggleLike called for post ID:', props.post.id, 'Type:', props.post.post_type, 'ContentTypeID:', props.post.content_type_id, 'ObjectID:', props.post.object_id);

  if (!authStore.isAuthenticated) {
    alert('Please login to like posts.');
    return;
  }

  // Ensure essential IDs for API call are present on the post prop
   if (typeof props.post.content_type_id !== 'number' || typeof props.post.object_id !== 'number') {
      console.error('[PostItem] CRITICAL: Cannot toggle like because Post prop is missing content_type_id or object_id. Post ID:', props.post.id, 'Post data:', JSON.parse(JSON.stringify(props.post))); // Made log more explicit
      alert('Cannot like this post due to missing information. Please try again later or contact support if the issue persists.'); // Slightly more user-friendly alert
      return;
  }

  try {
    // Step 1: Perform the like/unlike action via feedStore (this makes the API call)
    // console.log('[PostItem] Calling feedStore.toggleLike for post ID:', props.post.id, 'Type:', props.post.post_type);
    await feedStore.toggleLike(props.post.id, props.post.post_type, props.post.content_type_id, props.post.object_id); 
    // console.log('[PostItem] feedStore.toggleLike finished successfully.');

    // Step 2: If this post is being displayed on a profile page, 
    // and its author matches the current profile's user,
    // then also update its state in profileStore.userPosts for UI consistency on that page.
    // console.log('[PostItem] Checking for profile sync. Current profile user:', profileStore.currentProfile?.user?.username,'Post author:', props.post.author.username);

    if (profileStore.currentProfile && 
        profileStore.currentProfile.user.username === props.post.author.username) {
        // Check if the post exists in the userPosts array of the profileStore
        const postExistsInUserPosts = profileStore.userPosts.some(
            (p: Post) => p.id === props.post.id && p.post_type === props.post.post_type
        );

        if (postExistsInUserPosts) {
            // console.log('[PostItem] Post found in profileStore.userPosts. Calling profileStore.toggleLikeInUserPosts for post ID:', props.post.id, 'Type:', props.post.post_type);
            // This new action (toggleLikeInUserPosts) will be added to profile.ts
            // It will ONLY update the local state in profileStore.userPosts.
            profileStore.toggleLikeInUserPosts(props.post.id, props.post.post_type);
        } else {
            // console.log('[PostItem] Post (ID:', props.post.id, ') not found in profileStore.userPosts, or profileStore.userPosts is empty. No sync needed or post list might be stale.');
        }
    } else {
      // console.log('[PostItem] Not on a relevant profile page, or currentProfile/author mismatch. No profileStore sync for like needed.');
    }

  } catch (error: any) { // This catch block primarily catches errors from feedStore.toggleLike
    console.error('[PostItem] Error during toggleLike process (likely from feedStore API call):', error);
    // The alert was here, but feedStore.toggleLike should set its own error state
    // which can be observed by the UI if needed.
    // If you want an alert specifically from PostItem:
    // alert(`An error occurred while trying to like the post: ${error.message || 'Please try again.'}`);
    alert(`An error occurred while trying to like the post.`); 
  }
};
// ---- END OF REPLACEMENT ----

// ===========================================
// === NEW: Method to Handle Post Deletion ===
// ===========================================
// 👇 ADD THIS ASYNC FUNCTION
async function handleDeletePost() {
  localDeleteError.value = null;      // Clear any previous local error for this item
  feedStore.deletePostError = null; // Clear any global error in the store too

  // This check is a safeguard, the button should ideally not even be visible if not owner.
  if (!isOwner.value) {
    alert("You can only delete your own posts."); 
    return;
  }

  // Ask for confirmation before deleting
  const confirmed = window.confirm("Are you sure you want to delete this post? This action cannot be undone.");
  if (!confirmed) {
    return; // User clicked "Cancel"
  }

  try {
    // Call the deletePost action from your feedStore
    // props.post.id is the ID of the post to delete
    // props.post.post_type is its type (e.g., 'statuspost')
    const success = await feedStore.deletePost(props.post.id, props.post.post_type);

    if (success) {
      // The post was deleted successfully. 
      // The feedStore removed it from its list, so the UI should update automatically
      // if this PostItem is part of a v-for loop over feedStore.posts.
      console.log(`PostItem: Post ${props.post.id} successfully deleted.`);
    } else {
      // Deletion failed, the store should have set an error message.
      // Display it locally for this post item.
      localDeleteError.value = feedStore.deletePostError || "Failed to delete post. Please try again.";
      // You could also show an alert here:
      // alert(localDeleteError.value); 
    }
  } catch (error) { 
    // This catch is for unexpected errors if the store action itself throws an unhandled error.
    console.error(`PostItem: Unexpected error during handleDeletePost for post ${props.post.id}:`, error);
    localDeleteError.value = "An unexpected error occurred while trying to delete the post.";
    // alert(localDeleteError.value);
  }
}
// ===========================================

</script>

<template>
  <article class="post-item">
    <header class="post-header">
      <div class="author-info"> 
        <router-link :to="{ name: 'profile', params: { username: post.author.username } }" class="author-link">
          <span class="author-username">{{ post.author.username }}</span>
        </router-link>
        <span class="timestamp" v-if="post.created_at">{{ format(new Date(post.created_at), 'Pp') }}</span>
      </div>

      <div v-if="isOwner" class="post-actions"> 
        <button 
          @click="handleDeletePost"
          :disabled="post.isDeleting"
          class="delete-button">
          {{ post.isDeleting ? 'Deleting...' : 'Delete' }}
        </button>
      </div>
    </header>

    
    
    <div v-if="localDeleteError" class="error-message post-delete-error">
      {{ localDeleteError }}
    </div>

    <div class="post-content">
      
      <div v-if="post.video" class="post-video-container">
        <video controls class="post-video" :src="post.video">
          Your browser does not support the video tag.
        </video>
      </div>

      <div v-if="post.image" class="post-image-container">
        <img :src="post.image" :alt="`Image for post by ${post.author.username}`" class="post-image" />
      </div>

      <p v-if="post.content" class="post-text-content" v-html="linkifyContent(post.content)"></p>
    </div>

    <footer class="post-footer">
      <button @click="toggleLike" :class="{ 'liked': post.is_liked_by_user }" class="like-button"
        :disabled="post.isLiking || post.isDeleting">
        {{ likeButtonText }}
      </button>
      <span>Likes: {{ post.like_count ?? 0 }}</span> |
      <button @click="toggleCommentDisplay" class="comment-toggle-button" 
        :disabled="post.isDeleting">
        Comments: {{ post.comment_count ?? 0 }} {{ showComments ? '(-)' : '(+)' }}
      </button>
    </footer>

    <section v-if="showComments && !post.isDeleting" class="comments-section">
      <div v-if="isLoadingComments" class="comments-loading">
        Loading comments...
      </div>
      <div v-else-if="commentError" class="comments-error"> {/* This v-else-if expects isLoadingComments to be false */}
        Error loading comments: {{ commentError }}
        <button @click="loadComments">Retry</button>
      </div>
      <div v-else-if="Array.isArray(commentsForThisPost)"> {/* This v-else-if expects commentError to be falsey */}
        <template v-if="commentsForThisPost.length > 0">
          <CommentItem v-for="comment in commentsForThisPost" :key="comment.id" :comment="comment"
            :parentPostType="props.post.post_type" :parentObjectId="props.post.object_id"
            :parentPostActualId="props.post.id" />
        </template>
        <div v-else class="no-comments"> {/* This v-else expects commentsForThisPost.length to be 0 */}
          No comments yet.
        </div>
      </div>
      <div v-else class="comments-error"> {/* This v-else is a fallback if commentsForThisPost isn't an array */}
        Could not display comments (unexpected data structure).
      </div>

      <form v-if="isAuthenticated" @submit.prevent="handleCommentSubmit" class="comment-form">
        {/* This v-if for createCommentError is standalone, which is fine */}
        <div v-if="createCommentError" class="error-message comment-submit-error">
          {{ createCommentError }}
        </div>
        <textarea 
            v-model="newCommentContent" 
            placeholder="Add a comment..." 
            rows="2" 
            :disabled="isCreatingComment || post.isDeleting"
            required>
        </textarea>
        <button 
            type="submit" 
            :disabled="isCreatingComment || !newCommentContent.trim() || post.isDeleting">
          {{ isCreatingComment ? 'Submitting...' : 'Submit Comment' }}
        </button>
      </form>
    </section>
  </article>
</template>

<style scoped>
/* ... (all existing styles from PostItem.vue should be here) ... */
.post-item {
  border: 1px solid #ddd;
  padding: 1rem;
  margin-bottom: 1rem;
  background-color: #ffffff;
  border-radius: 4px;
  color: #333;
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.5rem;
  font-size: 0.9em;
}

.author-link {
  text-decoration: none;
  color: #555;
}

.author-username {
  font-weight: bold;
  color: #444;
}

.author-link:hover .author-username {
  text-decoration: underline;
  color: #0056b3;
}

.timestamp {
  color: #666;
  font-size: 0.85em;
}

.post-content {
  margin-bottom: 0.75rem;
  line-height: 1.5;
  color: #333;
}

.post-content p {
  margin-top: 0;
  margin-bottom: 0;
}

.post-footer {
  font-size: 0.9em;
  color: #555;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.like-button {
  padding: 3px 8px;
  cursor: pointer;
  border: 1px solid #ccc;
  background-color: #e9ecef;
  color: #333;
  border-radius: 4px;
  font-size: 0.85em;
  transition: background-color 0.15s ease-in-out, border-color 0.15s ease-in-out;
}

.like-button:hover {
  background-color: #dee2e6;
  border-color: #adb5bd;
}

.like-button.liked {
  background-color: #007bff;
  border-color: #007bff;
  color: white;
}

.like-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.comment-toggle-button {
  background: none;
  border: none;
  color: #555;
  cursor: pointer;
  padding: 0;
  font-size: inherit;
  margin: 0;
  text-decoration: underline;
}

.comment-toggle-button:hover {
  color: #0056b3;
}

.comments-section {
  margin-top: 1rem;
  border-top: 1px solid #f0f0f0;
  padding-top: 1rem;
}

.comments-loading,
.comments-error,
.no-comments {
  color: #888;
  font-style: italic;
  font-size: 0.9em;
  padding: 0.5rem 0;
}

.comments-error {
  color: #dc3545;
}

.comments-error button {
  margin-left: 0.5rem;
  font-size: 0.8em;
  padding: 2px 5px;
  cursor: pointer;
}

/* --- Styles for Comment Form --- */
.comment-form {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px dashed #e0e0e0;
  /* Dashed separator */
}

.comment-form textarea {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 0.95em;
  margin-bottom: 0.5rem;
  resize: vertical;
  box-sizing: border-box;
  min-height: 60px;
  /* Minimum height */
}

.comment-form button {
  padding: 0.4rem 0.8rem;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 0.9em;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.comment-form button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.comment-form button:not(:disabled):hover {
  background-color: #0056b3;
}

.comment-submit-error {
  /* Specific styling for comment submission errors */
  color: #dc3545;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  padding: 0.5rem;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
}

.post-image-container {
  margin-bottom: 10px;
  /* Space between image and content if both exist */
  text-align: center;
  /* Or left, or whatever you prefer */
}

.post-image {
  max-width: 100%;
  /* Make image responsive, not exceed container width */
  max-height: 500px;
  /* Optional: Limit max height to prevent overly tall images */
  border-radius: 8px;
  /* Optional: match post item rounding */
  object-fit: cover;
  /* Optional: how image should resize (cover, contain, etc.) */
  /* Be mindful of aspect ratios with 'cover' */
}

/* Adjust post-content styling if needed */
.post-content p {
  margin-top: 0;
  /* Remove top margin if image is directly above */
  /* Other existing styles for content text */
}

/* In PostItem.vue <style scoped> */

.post-video-container {
  margin-bottom: 10px;
  background-color: #000; /* Optional: black background for video player */
}

.post-video {
  max-width: 100%;
  max-height: 500px; /* Or adjust as you see fit */
  display: block; /* Helps with layout sometimes */
  margin: 0 auto; /* Center if container is text-align:center or if it's block */
  border-radius: 8px; /* Optional */
}

.post-text-content { /* Add a class to specifically style post text if needed */
    /* Your existing styles for post.content p tag can go here or remain as they are */
    /* If content and media are both present, you might want specific margins */
    margin-top: 10px; /* Example: add space if media is above */
}

.post-text-content a { /* Target links within the v-html rendered content */
  color: #007bff;
  text-decoration: underline;
}
.post-text-content a:hover {
  text-decoration: none;
}

/* Ensure your existing .post-image-container and .post-image styles are still there */
/* --- End Comment Form Styles --- */

/* Styles for the container of the delete button, placed in the header */
.post-actions {
  margin-left: auto; /* This will push the delete button to the far right of the header */
  padding-left: 10px; /* Some space between author info and the delete button */
}

/* Styles for the new Delete button */
.delete-button {
  padding: 3px 8px; /* Similar padding to your .like-button */
  background-color: #f0ad4e; /* An orange/warning color, less aggressive than pure red initially */
  color: white;
  border: 1px solid #eea236;
  border-radius: 4px; /* Match your other buttons */
  font-size: 0.85em; /* Match your .like-button */
  cursor: pointer;
  font-weight: normal; /* Or bold if you prefer */
  transition: background-color 0.15s ease-in-out, border-color 0.15s ease-in-out;
}

.delete-button:hover:not(:disabled) {
  background-color: #ec971f; /* Darker orange on hover */
  border-color: #d58512;
}

/* Styles for when the delete button is disabled (e.g., during the API call) */
.delete-button:disabled {
  background-color: #f5d6ab; /* Lighter, muted orange */
  border-color: #f1c688;
  opacity: 0.65; /* Consistent with your .like-button:disabled */
  cursor: not-allowed;
}

/* Styles for the error message specifically for post deletion */
.post-delete-error {
  color: #a94442; /* Text color for errors (often dark red) */
  background-color: #f2dede; /* Background color for error messages (often light pink/red) */
  border: 1px solid #ebccd1; /* Border color for error messages */
  padding: 0.75rem 1rem;   /* Padding inside the error message box */
  margin-top: 0.5rem;      /* Space above the error message */
  margin-bottom: 0.75rem;  /* Space below the error message */
  border-radius: 4px;      /* Rounded corners, matching other elements */
  font-size: 0.9em;        /* Font size for the error text */
  text-align: left;        /* Align text to the left */
}

/*
  Your .post-header currently has 'align-items: baseline;'.
  If the delete button (which might be taller due to padding) doesn't align well
  with the author username/timestamp, you might want to change it to 'flex-start'.
  Try it as is first. If alignment is off, then modify .post-header:
*/
/*
.post-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start; // CHANGED from baseline if vertical alignment is an issue
  margin-bottom: 0.5rem;
  font-size: 0.9em;
}
*/

/*
  You already have good disabled styles for .like-button and .comment-form button.
  The :disabled="... || post.isDeleting" added in the template will use those.
  The .comment-toggle-button doesn't have an explicit :disabled style in your current CSS.
  You might want to add one for consistency if it looks odd when disabled.
  Example:
*/
.comment-toggle-button:disabled {
  color: #aaa; /* Lighter color for disabled state */
  text-decoration: none; /* Remove underline when disabled */
  cursor: not-allowed;
}

</style>