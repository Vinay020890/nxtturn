<script setup lang="ts">
import { useAuthStore } from '@/stores/auth';
import { onMounted } from 'vue';
import { useFeedStore } from '@/stores/feed';
import CreatePostForm from '@/components/CreatePostForm.vue';

const authStore = useAuthStore();
const feedStore = useFeedStore();

// Fetch feed data when the component is mounted
onMounted(() => {
  console.log("FeedView: Component mounted, fetching feed...");
  feedStore.fetchFeed(); // Call the action to fetch page 1
});

// Method to fetch the previous page
function fetchPreviousPage() {
  // Check if we are not on the first page
  if (feedStore.currentPage > 1) {
    // If not, call the store's fetchFeed action with the previous page number
    console.log("FeedView: Fetching previous page..."); // Log click
    feedStore.fetchFeed(feedStore.currentPage - 1);
  } else {
    console.log("FeedView: Already on first page."); // Log if disabled logic fails
  }
}

// Method to fetch the next page
function fetchNextPage() {
  // Check if the store indicates there is a next page
  if (feedStore.hasNextPage) {
    // If yes, call the store's fetchFeed action with the next page number
    console.log("FeedView: Fetching next page..."); // Log click
    feedStore.fetchFeed(feedStore.currentPage + 1);
  } else {
     console.log("FeedView: Already on last page."); // Log if disabled logic fails
  }
}

</script>

<template>
  <div class="feed-view">
    <!-- Changed h1 to display welcome message -->
    <h1>Welcome, {{ authStore.userDisplay }}!</h1>
    <!-- Added h2 for original title -->
    <h2>Your Feed</h2>

    <CreatePostForm />

    <!-- Loading State -->
    <div v-if="feedStore.isLoading && feedStore.posts.length === 0" class="loading">
      Loading feed...
    </div>

    <!-- Error State -->
    <div v-if="feedStore.error" class="error-message">
      Error loading feed: {{ feedStore.error }}
    </div>

    <!-- Posts List -->
    <div v-if="!feedStore.isLoading || feedStore.posts.length > 0" class="posts-list">
      <article v-for="post in feedStore.posts" :key="post.id" class="post-item">
        <header class="post-header">
          <!-- Display author username (add link later) -->
          <span class="author-username">{{ post.author.username }}</span>
          <!-- Display post timestamp (format later) -->
          <span class="timestamp">{{ post.created_at }}</span>
        </header>
        <div class="post-content">
          <!-- Display post content -->
          <p>{{ post.content }}</p>
        </div>
        <footer class="post-footer">
            <!-- ADD LIKE BUTTON HERE -->
        <button
          @click="feedStore.toggleLike(post)"
          :class="{ 'liked': post.is_liked_by_user }"
          class="like-button"
        >
          {{ post.is_liked_by_user ? 'Unlike' : 'Like' }}
        </button>
        <!-- END OF LIKE BUTTON -->
          <!-- Placeholder for likes/comments count -->
          <!-- Make sure fields exist in Post interface in feed.ts -->
          <span>Likes: {{ post.like_count || 0 }}</span> |
          <span>Comments: {{ post.comment_count || 0 }}</span>
        </footer>
      </article>

      <!-- Message if feed is empty -->
      <div v-if="!feedStore.isLoading && feedStore.posts.length === 0 && !feedStore.error" class="empty-feed">
        Your feed is empty. Follow some users or create a post!
      </div>
    </div> <!-- End of posts-list -->

    <!-- Pagination Controls -->
    <div class="pagination-controls">
        <button :disabled="feedStore.currentPage <= 1" @click="fetchPreviousPage">Previous</button>
        <span>Page {{ feedStore.currentPage }} of {{ feedStore.totalPages }}</span>
        <button :disabled="!feedStore.hasNextPage" @click="fetchNextPage">Next</button>
    </div>

  </div> <!-- End of feed-view -->
</template>

<style scoped>
.feed-view {
  max-width: 800px; /* Adjust as needed */
  margin: 1rem auto;
  padding: 1rem;
}

.loading,
.error-message,
.empty-feed {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.error-message {
  color: #dc3545; /* Red */
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
}

.posts-list {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem; /* Space between posts */
}

.post-item {
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 1rem 1.5rem;
  background-color: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  color: #555;
  font-size: 0.9em;
}

.author-username {
  font-weight: bold;
  color: #333;
}

.timestamp {
  color: #888;
}

.post-content {
  margin-bottom: 1rem;
  line-height: 1.6;
  /* Handle long words/links */
  word-wrap: break-word;
  overflow-wrap: break-word;
  color: #333;
}

.post-footer {
    font-size: 0.85em;
    color: #777;
    border-top: 1px solid #f0f0f0;
    padding-top: 0.75rem;
    margin-top: 1rem;
}

.post-footer span {
    margin-right: 1rem;
}

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

 /* Add these styles */
.like-button {
  background-color: transparent;
  border: 1px solid #ccc;
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
  cursor: pointer;
  margin-right: 1rem;
  color: #337ab7; /* Default blue-ish */
  transition: background-color 0.2s ease, color 0.2s ease;
}

.like-button:hover {
  background-color: #f0f0f0;
}

.like-button.liked { /* Style when liked */
  background-color: #007bff; /* Blue background */
  color: white;
  border-color: #0056b3;
}

.like-button.liked:hover {
    background-color: #0056b3;
}
/* Add more styles later */
</style>