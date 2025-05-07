<script setup lang="ts">
import { ref, computed } from 'vue';
import type { Post } from '@/stores/feed';
import { useFeedStore } from '@/stores/feed';
import { format } from 'date-fns';
import { useCommentStore } from '@/stores/comment';
import CommentItem from '@/components/CommentItem.vue';

// --- Props Definition ---
const props = defineProps<{
  post: Post
}>();
console.log(`PostItem ${props.post.id}: Setup Start`); // <-- Log setup start

// --- Store Instances ---
const feedStore = useFeedStore();
const commentStore = useCommentStore();
console.log(`PostItem ${props.post.id}: commentStore instance:`, commentStore); // <-- Log store instance
// Check if commentsByPost exists right after getting the instance
if (!commentStore || typeof commentStore.commentsByPost === 'undefined') { // Check for undefined explicitly
  console.error(`PostItem ${props.post.id}: commentStore or commentsByPost is NOT defined immediately after useCommentStore()! Store:`, commentStore);
}

// --- Local State ---
const showComments = ref(false);

// --- Computed Properties ---
const likeButtonText = computed(() => {
  return props.post.is_liked_by_user ? 'Unlike' : 'Like';
});

const commentPostKey = computed(() => {
  // Add safety check for post prop existence
  if (!props.post || typeof props.post.post_type === 'undefined' || typeof props.post.object_id === 'undefined') {
    console.error(`PostItem ${props.post?.id}: Invalid post prop for computing commentPostKey`, props.post);
    return `invalid_${props.post?.id || 'unknown'}`; // Return a placeholder key
  }
  const key = `${props.post.post_type}_${props.post.object_id}`;
  console.log(`PostItem ${props.post.id}: Computing commentPostKey: ${key}`); // <-- Log key computation
  return key;
});

const commentsForThisPost = computed(() => {
  console.log(`PostItem ${props.post?.id}: Computing commentsForThisPost...`); // <-- Log computed start
  const key = commentPostKey.value; // Get the key

  // --- Add more detailed check ---
  if (!commentStore) {
    console.error(`PostItem ${props.post?.id}: commentStore is undefined/null inside commentsForThisPost computed!`);
    return [];
  }
  if (typeof commentStore.commentsByPost === 'undefined') {
     console.error(`PostItem ${props.post?.id}: commentStore.commentsByPost is undefined inside computed! Key was: ${key}`);
     return [];
  }
  // --- End detailed check ---

  console.log(`PostItem ${props.post?.id}: Accessing commentsByPost[${key}]`);
  // Ensure commentsByPost itself is an object before accessing key
  if (typeof commentStore.commentsByPost !== 'object' || commentStore.commentsByPost === null) {
      console.error(`PostItem ${props.post?.id}: commentStore.commentsByPost is not an object! Value:`, commentStore.commentsByPost);
      return [];
  }
  return commentStore.commentsByPost[key] || [];
});

const isLoadingComments = computed(() => {
  // Add check here too for safety
  return commentStore ? commentStore.isLoading : false;
});

const commentError = computed(() => {
  // Add check here too for safety
  return commentStore ? commentStore.error : null;
});

// --- Methods ---
function loadComments() {
  // Add safety check
  if (!props.post || typeof props.post.post_type === 'undefined' || typeof props.post.object_id === 'undefined') {
      console.error(`PostItem ${props.post?.id}: Cannot load comments, invalid post prop.`);
      return;
  }
  console.log(`PostItem ${props.post.id}: Requesting comments...`);
  commentStore.fetchComments(props.post.post_type, props.post.object_id);
}

function toggleCommentDisplay() {
  console.log(`PostItem ${props.post?.id}: Toggling comment display`); // <-- Log toggle start
  showComments.value = !showComments.value;
   // Add check for commentsForThisPost existence before accessing length
  const currentComments = commentsForThisPost.value;
  if (showComments.value && Array.isArray(currentComments) && currentComments.length === 0 && !commentError.value) {
    loadComments();
  }
}

console.log(`PostItem ${props.post.id}: Setup End`); // <-- Log setup end
</script>

<template>
  <article class="post-item">
    <header class="post-header">
      <!-- Link added around the author username -->
      <router-link :to="{ name: 'profile', params: { username: post.author.username } }" class="author-link">
         <span class="author-username">{{ post.author.username }}</span>
      </router-link>
      <!-- Display post timestamp -->
      <span class="timestamp" v-if="post.created_at">{{ format(new Date(post.created_at), 'Pp') }}</span>
    </header>
    <div class="post-content">
      <!-- Display post content -->
      <p>{{ post.content }}</p>
    </div>
    <footer class="post-footer">
      <!-- LIKE BUTTON -->
      <button
        @click="feedStore.toggleLike(post.id)"
        :class="{ 'liked': post.is_liked_by_user }"
        class="like-button"
        :disabled="post.isLiking"
      >
        {{ likeButtonText }}
      </button>
      <!-- Likes count -->
      <span>Likes: {{ post.like_count ?? 0 }}</span> |
      <!-- Comments count / Toggle Button -->
      <button @click="toggleCommentDisplay" class="comment-toggle-button">
         Comments: {{ post.comment_count ?? 0 }} {{ showComments ? '(-)' : '(+)' }}
      </button>
    </footer>

    <!-- === NEW: Comments Section === -->
    <section v-if="showComments" class="comments-section">
      <!-- Loading state for comments -->
      <div v-if="isLoadingComments" class="comments-loading">
        Loading comments...
      </div>
      <!-- Error state for comments -->
      <div v-else-if="commentError" class="comments-error">
        Error loading comments: {{ commentError }}
        <button @click="loadComments">Retry</button> <!-- Add a retry button -->
      </div>
      <!-- Display comments if loaded and no error -->
      <!-- Add check for commentsForThisPost being an array before using length -->
      <div v-else-if="Array.isArray(commentsForThisPost) && commentsForThisPost.length > 0">
        <CommentItem
          v-for="comment in commentsForThisPost"
          :key="comment.id"
          :comment="comment"
        />
      </div>
      <!-- Message if no comments -->
      <div v-else class="no-comments">
        No comments yet.
      </div>
      <!-- TODO: Add Comment Form later -->
    </section>
    <!-- === END Comments Section === -->

  </article>
</template>

<style scoped>
.post-item {
  border: 1px solid #ddd;        /* Lighter border */
  padding: 1rem;
  margin-bottom: 1rem;
  background-color: #ffffff;    /* WHITE background for the post item */
  border-radius: 4px;
  color: #333;                 /* Default DARK text color for content inside */
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
   color: #555;                 /* Darker color for link */
}
.author-username {
  font-weight: bold;
  color: #444;                 /* DARKER GREY for username */
}
 .author-link:hover .author-username {
     text-decoration: underline;
     color: #0056b3;             /* Standard link blue for hover */
 }

.timestamp {
  color: #666;                 /* Medium grey for timestamp */
  font-size: 0.85em;
}
.post-content {
  margin-bottom: 0.75rem;
  line-height: 1.5;
  color: #333;                 /* DARK GREY for content */
}
.post-content p {
    margin-top: 0;
    margin-bottom: 0;
}
.post-footer {
  font-size: 0.9em;
  color: #555;                 /* Darker grey for footer text */
  display: flex;
  align-items: center;
  gap: 0.75rem;                 /* Add space between button and text */
}

.like-button {
  padding: 3px 8px;
  cursor: pointer;
  border: 1px solid #ccc;      /* Lighter border for button */
  background-color: #e9ecef;   /* Light grey button */
  color: #333;                 /* Dark text on button */
  border-radius: 4px;
  font-size: 0.85em;
  transition: background-color 0.15s ease-in-out, border-color 0.15s ease-in-out; /* Smooth transition */
}
.like-button:hover {
    background-color: #dee2e6; /* Slightly darker hover */
    border-color: #adb5bd;
}
.like-button.liked {
  background-color: #007bff;   /* Standard blue when liked */
  border-color: #007bff;
  color: white;                 /* White text when liked */
}
 .like-button:disabled {
     opacity: 0.6;
     cursor: not-allowed;
 }

 /* --- Add these styles for comments --- */

.comment-toggle-button {
  background: none;
  border: none;
  color: #555; /* Match footer text */
  cursor: pointer;
  padding: 0;
  font-size: inherit; /* Inherit size from footer */
  margin: 0;
  text-decoration: underline;
}
.comment-toggle-button:hover {
  color: #0056b3;
}

.comments-section {
  margin-top: 1rem;
  border-top: 1px solid #f0f0f0; /* Separator line */
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
  color: #dc3545; /* Red */
}
.comments-error button {
   margin-left: 0.5rem;
   font-size: 0.8em;
   padding: 2px 5px;
   cursor: pointer;
}
/* --- End of added styles --- */

</style>