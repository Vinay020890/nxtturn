<script setup lang="ts">
import { useAuthStore } from '@/stores/auth';
import { onMounted } from 'vue';
import { useFeedStore } from '@/stores/feed';
// Import necessary Composition API functions or stores later if needed
// import { onMounted } from 'vue';



const authStore = useAuthStore();
const feedStore = useFeedStore();

// Fetch feed data when the component is mounted
onMounted(() => {
  console.log("FeedView: Component mounted, fetching feed...");
  feedStore.fetchFeed(); // Call the action to fetch page 1
});

</script>

<template>
    <div class="feed-view">
      <!-- Changed h1 to display welcome message -->
      <h1>Welcome, {{ authStore.userDisplay }}!</h1>
      <!-- Added h2 for original title -->
      <h2>Your Feed</h2>
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
    </div>
    </div>
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
/* Add more styles later */
</style>