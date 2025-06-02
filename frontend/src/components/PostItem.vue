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

// --- GET REACTIVE REFS FROM COMMENT STORE FOR CREATION ---
const { isCreatingComment, createCommentError } = storeToRefs(commentStore);

// --- Local State ---
const showComments = ref(false);
const newCommentContent = ref('');


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

const commentsForThisPost = computed(() => {
  const key = commentPostKey.value;
  if (!commentStore || typeof commentStore.commentsByPost === 'undefined') {
    return [];
  }
  if (typeof commentStore.commentsByPost !== 'object' || commentStore.commentsByPost === null) {
    return [];
  }
  return commentStore.commentsByPost[key] || [];
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
</script>

<template>
  <article class="post-item">
    <header class="post-header">
      <router-link :to="{ name: 'profile', params: { username: post.author.username } }" class="author-link">
        <span class="author-username">{{ post.author.username }}</span>
      </router-link>
      <span class="timestamp" v-if="post.created_at">{{ format(new Date(post.created_at), 'Pp') }}</span>
    </header>
    <div class="post-content">
      <!-- Display video if it exists -->
      <div v-if="post.video" class="post-video-container">
        <video controls class="post-video">
          <source :src="post.video" type="video/mp4"> <!-- Adjust type if needed, or detect from URL -->
          Your browser does not support the video tag.
        </video>
      </div>
      <!-- Else, display image if it exists (and no video) -->
      <div v-else-if="post.image" class="post-image-container">
        <img :src="post.image" :alt="`Image for post by ${post.author.username}`" class="post-image" />
      </div>

      <!-- Display content if it exists (always show content regardless of media) -->
      <p v-if="post.content" class="post-text-content">{{ post.content }}</p>
    </div>
    <footer class="post-footer">
      <button @click="toggleLike" :class="{ 'liked': post.is_liked_by_user }" class="like-button"
        :disabled="post.isLiking">
        {{ likeButtonText }}
      </button>
      <span>Likes: {{ post.like_count ?? 0 }}</span> |
      <button @click="toggleCommentDisplay" class="comment-toggle-button">
        Comments: {{ post.comment_count ?? 0 }} {{ showComments ? '(-)' : '(+)' }}
      </button>
    </footer>

    <section v-if="showComments" class="comments-section">
      <!-- Loading state for comments -->
      <div v-if="isLoadingComments" class="comments-loading">
        Loading comments...
      </div>
      <!-- Error state for comments -->
      <div v-else-if="commentError" class="comments-error">
        Error loading comments: {{ commentError }}
        <button @click="loadComments">Retry</button>
      </div>
      <!-- Display comments or "no comments" message -->
      <div v-else-if="Array.isArray(commentsForThisPost)">
        <template v-if="commentsForThisPost.length > 0">
          <CommentItem v-for="comment in commentsForThisPost" :key="comment.id" :comment="comment"
            :parentPostType="props.post.post_type" :parentObjectId="props.post.object_id"
            :parentPostActualId="props.post.id" />

        </template>
        <div v-else class="no-comments">
          No comments yet.
        </div>
      </div>
      <!-- Fallback if commentsForThisPost is not an array -->
      <div v-else class="comments-error">
        Could not display comments (unexpected data structure).
      </div>

      <form v-if="authStore.isAuthenticated" @submit.prevent="handleCommentSubmit" class="comment-form">
        <div v-if="createCommentError" class="error-message comment-submit-error">
          {{ createCommentError }}
        </div>
        <textarea v-model="newCommentContent" placeholder="Add a comment..." rows="2" :disabled="isCreatingComment"
          required></textarea>
        <button type="submit" :disabled="isCreatingComment || !newCommentContent.trim()">
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

/* Ensure your existing .post-image-container and .post-image styles are still there */
/* --- End Comment Form Styles --- */
</style>