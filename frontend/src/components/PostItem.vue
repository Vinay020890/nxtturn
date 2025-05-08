<script setup lang="ts">
import { ref, computed } from 'vue';
import type { Post } from '@/stores/feed';
import { useFeedStore } from '@/stores/feed';
import { format } from 'date-fns';
import { useCommentStore } from '@/stores/comment';
import CommentItem from '@/components/CommentItem.vue';
import { useAuthStore } from '@/stores/auth'; // Import auth store

// --- Props Definition ---
const props = defineProps<{
  post: Post
}>();
// console.log(`PostItem ${props.post.id}: Setup Start`);

// --- Store Instances ---
const feedStore = useFeedStore();
const commentStore = useCommentStore();
const authStore = useAuthStore(); // Get auth store instance
// console.log(`PostItem ${props.post.id}: commentStore instance:`, commentStore);
// if (!commentStore || typeof commentStore.commentsByPost === 'undefined') {
//   console.error(`PostItem ${props.post.id}: commentStore or commentsByPost is NOT defined immediately after useCommentStore()! Store:`, commentStore);
// }

// --- Local State ---
const showComments = ref(false);
const newCommentContent = ref(''); // Ref for the new comment input
const isSubmittingComment = ref(false); // Loading state for comment submission
const commentSubmitError = ref<string | null>(null); // Error state for comment submission

// --- Computed Properties ---
const likeButtonText = computed(() => {
  return props.post.is_liked_by_user ? 'Unlike' : 'Like';
});

const commentPostKey = computed(() => {
  if (!props.post || typeof props.post.post_type === 'undefined' || typeof props.post.object_id === 'undefined') {
    // console.error(`PostItem ${props.post?.id}: Invalid post prop for computing commentPostKey`, props.post);
    return `invalid_${props.post?.id || 'unknown'}`;
  }
  const key = `${props.post.post_type}_${props.post.object_id}`;
  // console.log(`PostItem ${props.post.id}: Computing commentPostKey: ${key}`);
  return key;
});

const commentsForThisPost = computed(() => {
  // console.log(`PostItem ${props.post?.id}: Computing commentsForThisPost...`);
  const key = commentPostKey.value;
  if (!commentStore || typeof commentStore.commentsByPost === 'undefined') {
    //  console.error(`PostItem ${props.post?.id}: commentStore.commentsByPost is undefined inside computed! Key was: ${key}`);
     return [];
  }
  if (typeof commentStore.commentsByPost !== 'object' || commentStore.commentsByPost === null) {
      // console.error(`PostItem ${props.post?.id}: commentStore.commentsByPost is not an object! Value:`, commentStore.commentsByPost);
      return [];
  }
  return commentStore.commentsByPost[key] || [];
});

const isLoadingComments = computed(() => {
  return commentStore ? commentStore.isLoading : false;
});

const commentError = computed(() => {
  return commentStore ? commentStore.error : null;
});

// --- Methods ---
function loadComments() {
  if (!props.post || typeof props.post.post_type === 'undefined' || typeof props.post.object_id === 'undefined') {
      // console.error(`PostItem ${props.post?.id}: Cannot load comments, invalid post prop.`);
      return;
  }
  // console.log(`PostItem ${props.post.id}: Requesting comments...`);
  commentStore.fetchComments(props.post.post_type, props.post.object_id);
}

function toggleCommentDisplay() {
  // console.log(`PostItem ${props.post?.id}: Toggling comment display`);
  showComments.value = !showComments.value;
  const currentComments = commentsForThisPost.value;
  if (showComments.value && Array.isArray(currentComments) && currentComments.length === 0 && !commentError.value) {
    loadComments();
  }
}

// --- UPDATED: Method to handle comment submission ---
async function handleCommentSubmit() {
  if (!newCommentContent.value.trim()) {
    commentSubmitError.value = "Comment cannot be empty.";
    return;
  }
  // Safety check for post data (already good)
  if (!props.post || !props.post.post_type || typeof props.post.object_id === 'undefined') {
      commentSubmitError.value = "Cannot submit comment: Invalid post data.";
      return;
  }

  isSubmittingComment.value = true;
  commentSubmitError.value = null;

  try {
    // Call the createComment action from the commentStore
    await commentStore.createComment(
      props.post.post_type,      // Pass the post_type (e.g., 'statuspost')
      props.post.object_id,      // Pass the object_id (which is the post's ID)
      newCommentContent.value,   // Pass the comment text
      props.post.id
    );
    
    // If createComment action doesn't throw an error, it succeeded
    newCommentContent.value = ''; // Clear the input field
    console.log('PostItem: Comment submitted successfully and added to store.');
    
    // The comment_count on the PostItem will not update automatically yet.
    // We might address this as a separate improvement.
    // For now, the new comment will appear in the list.

  } catch (error: any) {
    console.error("PostItem: Error submitting comment:", error);
    // The store action re-throws the error, so error.message should be useful
    // If backend sends structured errors (e.g., for content validation):
    if (error.response && error.response.data) {
        if (error.response.data.content) {
            commentSubmitError.value = error.response.data.content.join(' ');
        } else if (error.response.data.detail) {
            commentSubmitError.value = error.response.data.detail;
        } else {
            commentSubmitError.value = "An unexpected error occurred while posting the comment.";
        }
    } else {
        commentSubmitError.value = error.message || "Failed to submit comment.";
    }
  } finally {
    isSubmittingComment.value = false;
  }
}
// --- END: UPDATED Method to handle comment submission ---

// console.log(`PostItem ${props.post.id}: Setup End`);
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
      <p>{{ post.content }}</p>
    </div>
    <footer class="post-footer">
      <button
        @click="feedStore.toggleLike(post.id)"
        :class="{ 'liked': post.is_liked_by_user }"
        class="like-button"
        :disabled="post.isLiking"
      >
        {{ likeButtonText }}
      </button>
      <span>Likes: {{ post.like_count ?? 0 }}</span> |
      <button @click="toggleCommentDisplay" class="comment-toggle-button">
         Comments: {{ post.comment_count ?? 0 }} {{ showComments ? '(-)' : '(+)' }}
      </button>
    </footer>

    <section v-if="showComments" class="comments-section">
      <div v-if="isLoadingComments" class="comments-loading">
        Loading comments...
      </div>
      <div v-else-if="commentError" class="comments-error">
        Error loading comments: {{ commentError }}
        <button @click="loadComments">Retry</button>
      </div>
      <div v-else-if="Array.isArray(commentsForThisPost) && commentsForThisPost.length > 0">
        <CommentItem
          v-for="comment in commentsForThisPost"
          :key="comment.id"
          :comment="comment"
        />
      </div>
      <div v-else class="no-comments">
        No comments yet.
      </div>

      <form v-if="authStore.isAuthenticated" @submit.prevent="handleCommentSubmit" class="comment-form">
        <div v-if="commentSubmitError" class="error-message comment-submit-error">
          {{ commentSubmitError }}
        </div>
        <textarea
          v-model="newCommentContent"
          placeholder="Add a comment..."
          rows="2"
          :disabled="isSubmittingComment"
          required
        ></textarea>
        <button type="submit" :disabled="isSubmittingComment || !newCommentContent.trim()">
          {{ isSubmittingComment ? 'Submitting...' : 'Submit Comment' }}
        </button>
      </form>
    </section>
  </article>
</template>

<style scoped>
/* ... (all existing styles from PostItem.vue) ... */
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
  border-top: 1px dashed #e0e0e0; /* Dashed separator */
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
  min-height: 60px; /* Minimum height */
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
.comment-submit-error { /* Specific styling for comment submission errors */
  color: #dc3545;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  padding: 0.5rem;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
}
/* --- End Comment Form Styles --- */
</style>