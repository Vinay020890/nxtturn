<script setup lang="ts">
import { computed } from 'vue';
import type { Post } from '@/stores/feed'; // Import the Post type
import { useFeedStore } from '@/stores/feed'; // Import feed store for like action
import { format } from 'date-fns'; // Import format for date

// Define the props this component accepts
// We expect a 'post' object matching the Post interface
const props = defineProps<{
  post: Post
}>();

// Get feed store instance to call toggleLike
const feedStore = useFeedStore();

// Optional: Computed property for the like button text
const likeButtonText = computed(() => {
  return props.post.is_liked_by_user ? 'Unlike' : 'Like';
});

</script>

<template>
  <article class="post-item">
    <header class="post-header">
      <!-- Link added around the author username -->
      <router-link :to="{ name: 'profile', params: { username: post.author.username } }" class="author-link">
         <span class="author-username">{{ post.author.username }}</span>
      </router-link>
      <!-- Display post timestamp (format later) -->
      <span class="timestamp" v-if="post.created_at">{{ format(new Date(post.created_at), 'Pp') }}</span>
    </header>
    <div class="post-content">
      <!-- Display post content -->
      <p>{{ post.content }}</p>
    </div>
    <footer class="post-footer">
        <!-- LIKE BUTTON - uses props.post and calls feedStore action -->
    <button
      @click="feedStore.toggleLike(post.id)"
      :class="{ 'liked': post.is_liked_by_user }"
      class="like-button"
      :disabled="post.isLiking" 
    >
      {{ likeButtonText }}
    </button>
      <!-- Likes/Comments count -->
      <span>Likes: {{ post.like_count ?? 0 }}</span> | <!-- Use nullish coalescing for safety -->
      <span>Comments: {{ post.comment_count ?? 0 }}</span> <!-- Use nullish coalescing -->
    </footer>
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
</style>