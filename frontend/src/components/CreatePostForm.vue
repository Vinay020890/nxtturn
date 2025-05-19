<script setup lang="ts">
import { ref, watch } from 'vue';
import { useFeedStore } from '@/stores/feed';
import { storeToRefs } from 'pinia';

// 1. Initialize the store instance
const feedStore = useFeedStore();

// 2. Get reactive refs from the store using storeToRefs
//    This makes 'isCreatingPost' and 'createPostError' available as reactive refs
const { isCreatingPost, createPostError } = storeToRefs(feedStore);

// 3. Define local component state
const postContent = ref('');

// 4. ADD THIS WATCH FUNCTION:
// Watch for changes in postContent to clear the error message from the store
watch(postContent, (newValue) => {
  // If there's a post creation error displayed and the user is typing something meaningful
  if (createPostError.value && newValue.trim() !== '') {
    feedStore.createPostError = null; // Clear the error in the store
  } else if (createPostError.value && newValue.trim() === '' && createPostError.value === "Post content cannot be empty.") {
    // If user clears the input after "cannot be empty" error, also clear the error
    feedStore.createPostError = null;
  }
});



// 5. Define the handleSubmit function
const handleSubmit = async () => {
  // Client-side validation for empty content (can also be primarily handled by the store)
  if (!postContent.value.trim()) {
    // Set the error in the store if you want immediate client-side feedback for this
    // The store's createPost action will also perform this check.
    feedStore.createPostError = "Post content cannot be empty.";
    return;
  }
  // The store action (createPost) will clear createPostError at its start.

  const newPost = await feedStore.createPost(postContent.value);

  if (newPost) {
    // Successfully created post
    console.log("CreatePostForm: Post submitted successfully!");
    postContent.value = ''; // Clear the textarea
    // createPostError is already null if successful (cleared in store action or by watcher)
  } else {
    // Failed to create post.
    // The error message is already set in feedStore.createPostError by the action.
    console.error("CreatePostForm: Failed to submit post. Error should be in store's createPostError.");
  }
  // The loading state (isCreatingPost) is managed by the store action.
};
</script>

<template>
  <div class="create-post-form">
    <h3>Create a New Post</h3>
    <form @submit.prevent="handleSubmit">
      <div v-if="createPostError" class="error-message">
  {{ createPostError }}
</div>
      <textarea
        v-model="postContent"
        placeholder="What's on your mind?"
        rows="4"
        required
        :disabled="isCreatingPost"
      ></textarea>
      <button type="submit" :disabled="isCreatingPost  || !postContent.trim()">
        {{ isCreatingPost ? 'Posting...' : 'Post' }}
      </button>
    </form>
  </div>
</template>

<style scoped>
.create-post-form {
  background-color: #f9f9f9;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 1rem 1.5rem;
  margin-bottom: 2rem; /* Space below the form */
}

.create-post-form h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  font-size: 1.1em;
  font-weight: 600;
}

textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1rem;
  margin-bottom: 0.75rem;
  resize: vertical; /* Allow vertical resizing */
  box-sizing: border-box; /* Include padding and border in element's total width and height */
}

button {
  padding: 0.6rem 1.2rem;
  background-color: #007bff; /* Blue */
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
  float: right; /* Align button to the right */
}

button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

button:not(:disabled):hover {
  background-color: #0056b3;
}

.error-message {
  color: #dc3545;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  padding: 0.75rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}
</style>