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
const selectedImageFile = ref<File | null>(null);

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

// ---- ADD THIS NEW METHOD ----
const handleImageFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    selectedImageFile.value = target.files[0];
    // Optional: You could add a preview of the selected image here if desired
    // For now, we'll just store the file.
    // If there was an error from a previous submission, clear it when a new file is chosen,
    // especially if it was an image-related error (though our current errors are generic)
    if (createPostError.value) {
      feedStore.createPostError = null;
    }
  } else {
    selectedImageFile.value = null;
  }
};
// ---- END OF NEW METHOD ----



// 5. Define the handleSubmit function
// ---- REPLACE EXISTING handleSubmit WITH THIS ----
const handleSubmit = async () => {
  // Validation: ensure either content or an image is provided
  // This client-side check mirrors the backend validation
  const currentContent = postContent.value.trim();
  const currentImageFile = selectedImageFile.value;

  if (!currentContent && !currentImageFile) {
    feedStore.createPostError = "Please provide either text content or an image for your post.";
    return;
  }
  // Clear any previous error if validation passes before submitting
  if (feedStore.createPostError) {
    feedStore.createPostError = null;
  }

  const formData = new FormData();
  if (currentContent) {
    formData.append('content', currentContent);
  } else {
    // If content is empty, backend model allows null/blank,
    // but DRF might expect the field if it's in serializer Meta.fields.
    // Sending an empty string explicitly if no content might be safer
    // if the backend serializer expects 'content' key even if empty.
    // Or, if backend serializer `content` field has `required=False`,
    // we don't need to append it if it's empty.
    // Let's assume for now not appending empty content is fine if an image is present.
    // The serializer's `validate` method checks for at least one.
  }

  if (currentImageFile) {
    formData.append('image', currentImageFile);
  }

  // Call the store action. We'll update the store action in the next step
  // to accept FormData or individual fields. For now, let's pass both.
  const newPost = await feedStore.createPost(formData); // Pass FormData to store action

  if (newPost) {
    console.log("CreatePostForm: Post submitted successfully!");
    postContent.value = ''; // Clear the textarea
    selectedImageFile.value = null; // Clear the selected file
    // Clear the file input visually (this is a bit tricky, often involves resetting the form or input's value)
    const fileInput = document.getElementById('postImageInput') as HTMLInputElement;
    if (fileInput) {
      fileInput.value = ''; // Attempt to reset file input
    }
  } else {
    console.error("CreatePostForm: Failed to submit post. Error should be in store's createPostError.");
    // Error message is already set in feedStore.createPostError by the store action
  }
};
// ---- END OF REPLACED handleSubmit ----
</script>

<template>
  <div class="create-post-form">
    <h3>Create a New Post</h3>
    <form @submit.prevent="handleSubmit">
      <div v-if="createPostError" class="error-message">
        {{ createPostError }}
      </div>
      <textarea v-model="postContent" placeholder="What's on your mind? (Optional if adding an image)" rows="4"
        :disabled="isCreatingPost"></textarea> <!-- 'required' attribute removed -->

      <!-- ADD THIS FILE INPUT SECTION -->
      <div class="form-group-image-upload">
        <label for="postImageInput">Add an image (optional):</label>
        <input type="file" id="postImageInput" @change="handleImageFileChange" accept="image/png, image/jpeg, image/gif"
          :disabled="isCreatingPost" />
        <!-- Optional: display selected file name or a preview -->
        <p v-if="selectedImageFile" class="selected-file-info">
          Selected: {{ selectedImageFile.name }}
        </p>
      </div>
      <!-- END OF FILE INPUT SECTION -->

      <button type="submit" :disabled="isCreatingPost || (postContent.trim() === '' && selectedImageFile === null)">
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
  margin-bottom: 2rem;
  /* Space below the form */
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
  resize: vertical;
  /* Allow vertical resizing */
  box-sizing: border-box;
  /* Include padding and border in element's total width and height */
}

button {
  padding: 0.6rem 1.2rem;
  background-color: #007bff;
  /* Blue */
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
  float: right;
  /* Align button to the right */
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

/* In <style scoped> */
.form-group-image-upload {
  margin-bottom: 1rem;
}

.form-group-image-upload label {
  display: block;
  margin-bottom: 0.25rem;
  font-weight: 500;
  font-size: 0.9em;
}

.form-group-image-upload input[type="file"] {
  display: block;
  font-size: 0.9em;
}

.selected-file-info {
  font-size: 0.85em;
  color: #555;
  margin-top: 0.25rem;
  font-style: italic;
}
</style>