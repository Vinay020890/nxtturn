<script setup lang="ts">
import { ref } from 'vue';
import { useFeedStore } from '@/stores/feed';

// Ref to hold the content of the new post
const postContent = ref('');
const isLoading = ref(false); // To disable button during submission
const errorMessage = ref<string | null>(null); // To show errors
const feedStore = useFeedStore();

// Placeholder for the submit handler
// Updated submit handler
const handleSubmit = async () => {
  // Basic validation
  if (!postContent.value.trim()) {
    errorMessage.value = "Post content cannot be empty.";
    return;
  }
  errorMessage.value = null; // Clear previous errors
  isLoading.value = true;    // Set loading state

  try {
    // Call the store action to create the post
    await feedStore.createPost(postContent.value);

    // If successful:
    console.log("CreatePostForm: Post submitted successfully!");
    postContent.value = ''; // Clear the textarea

    // Optional: Notify parent component or show success message?
    // For now, clearing the form is enough. The store handles adding the post to the feed list.

  } catch (error: any) {
    // If store action throws an error:
    console.error("CreatePostForm: Failed to submit post:", error);
    // Display the error message from the store action
    errorMessage.value = error.message || "An unknown error occurred.";

  } finally {
    // Always run this:
    isLoading.value = false; // Reset loading state
  }
};

</script>

<template>
  <div class="create-post-form">
    <h3>Create a New Post</h3>
    <form @submit.prevent="handleSubmit">
      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>
      <textarea
        v-model="postContent"
        placeholder="What's on your mind?"
        rows="4"
        required
        :disabled="isLoading"
      ></textarea>
      <button type="submit" :disabled="isLoading || !postContent.trim()">
        {{ isLoading ? 'Posting...' : 'Post' }}
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