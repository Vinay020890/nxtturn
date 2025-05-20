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
const imagePreviewUrl = ref<string | null>(null);
const selectedVideoFile = ref<File | null>(null);

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
// Still inside <script setup lang="ts"> in CreatePostForm.vue
// Make sure imagePreviewUrl is defined above this:
// const imagePreviewUrl = ref<string | null>(null);

const handleImageFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0]; // Use optional chaining for safety

  if (file) { // If a file is selected
    selectedImageFile.value = file;

    // Create a FileReader to read the image for preview
    const reader = new FileReader();

    reader.onload = (e) => {
      // When the file is successfully read, e.target.result contains the data URL
      imagePreviewUrl.value = e.target?.result as string;
    };

    reader.onerror = (e) => {
      // Optional: Handle file reading errors
      console.error("FileReader error:", e);
      imagePreviewUrl.value = null; // Clear preview on error
    };

    reader.readAsDataURL(file); // Start reading the file as a data URL

    // If there was an error from a previous submission, clear it when a new file is chosen
    if (createPostError.value) {
      feedStore.createPostError = null;
    }
  } else { // If no file is selected (e.g., user cancels file dialog or clears selection)
    selectedImageFile.value = null;
    imagePreviewUrl.value = null; // Clear preview as well
  }
};

// ... (existing handleImageFileChange method) ...

// ---- ADD THIS NEW METHOD FOR VIDEO ----
const handleVideoFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0]; // Get the selected file

  if (file) {
    selectedVideoFile.value = file;
    // If there was an error from a previous submission, clear it when a new file is chosen.
    if (createPostError.value) {
      feedStore.createPostError = null;
    }
  } else {
    selectedVideoFile.value = null; // Clear if no file is selected
  }
};
// ---- END OF NEW METHOD FOR VIDEO ----



// 5. Define the handleSubmit function
// ---- REPLACE EXISTING handleSubmit WITH THIS ----
// ---- REPLACE CURRENT handleSubmit WITH THIS ----
const handleSubmit = async () => {
  const currentContent = postContent.value.trim();
  const currentImageFile = selectedImageFile.value;
  const currentVideoFile = selectedVideoFile.value; // <<<< NEW: Get selected video

  // MODIFIED Validation: ensure either content, an image, OR a video is provided
  if (!currentContent && !currentImageFile && !currentVideoFile) {
    feedStore.createPostError = "Please provide text, an image, or a video for your post.";
    return;
  }
  // Clear any previous error if validation now passes
  if (feedStore.createPostError) {
    feedStore.createPostError = null;
  }

  const formData = new FormData();

  if (currentContent) {
    formData.append('content', currentContent);
  }
  // Note: We don't need an 'else' for content if it's empty.
  // The backend serializer has content as optional.
  // The overall validation (content OR image OR video) is done above and by the backend.

  if (currentImageFile) {
    formData.append('image', currentImageFile);
  }

  if (currentVideoFile) { // <<<< NEW: Append video if selected
    formData.append('video', currentVideoFile);
  }

  const newPost = await feedStore.createPost(formData); // formData now potentially includes video

  if (newPost) {
    console.log("CreatePostForm: Post submitted successfully!", newPost); // Log the newPost for debugging
    postContent.value = '';
    selectedImageFile.value = null;
    imagePreviewUrl.value = null;
    selectedVideoFile.value = null; // <<<< NEW: Clear selected video file state

    // Attempt to reset file inputs visually
    const imageFileInput = document.getElementById('postImageInput') as HTMLInputElement;
    if (imageFileInput) {
      imageFileInput.value = '';
    }
    // We will add an ID "postVideoInput" to the video input in the template
    const videoFileInput = document.getElementById('postVideoInput') as HTMLInputElement;
    if (videoFileInput) {
      videoFileInput.value = ''; // <<<< NEW: Attempt to reset video file input
    }
  } else {
    console.error("CreatePostForm: Failed to submit post. Error should be in store's createPostError.");
  }
};
// ---- END OF REPLACEMENT ----
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

        <!-- 👇👇👇 ADD THIS IMAGE PREVIEW SECTION INSIDE .form-group-image-upload 👇👇👇 -->
        <div v-if="imagePreviewUrl" class="image-preview-container">
          <img :src="imagePreviewUrl" alt="Selected image preview" class="image-preview" />
        </div>
        <!-- END OF IMAGE PREVIEW SECTION -->

      </div>
      <!-- END OF FILE INPUT SECTION -->

      <!-- ---- ADD THIS VIDEO INPUT SECTION ---- -->
      <div class="form-group-video-upload">
        <label for="postVideoInput">Add a video (optional):</label>
        <input
          type="file"
          id="postVideoInput"
          @change="handleVideoFileChange"
          accept="video/mp4, video/webm, video/ogg" 
          :disabled="isCreatingPost"
        />
        <!-- Optional: display selected video file name -->
        <p v-if="selectedVideoFile" class="selected-file-info">
          Selected: {{ selectedVideoFile.name }}
        </p>
      </div>
      <!-- ---- END OF VIDEO INPUT SECTION ---- -->

      <button type="submit" :disabled="isCreatingPost || (postContent.trim() === '' && selectedImageFile === null && selectedVideoFile === null)">
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

.image-preview-container {
  margin-top: 10px;
  text-align: left; /* Or center */
}

.image-preview {
  max-width: 200px;
  max-height: 200px;
  border: 1px solid #ddd;
  border-radius: 4px;
  object-fit: cover;
}

/* In <style scoped> */
.form-group-video-upload { /* Or combine with .form-group-image-upload if styles are identical */
  margin-bottom: 1rem;
}
.form-group-video-upload label {
  display: block;
  margin-bottom: 0.25rem;
  font-weight: 500;
  font-size: 0.9em;
}
.form-group-video-upload input[type="file"] {
  display: block;
  font-size: 0.9em;
}
/* .selected-file-info styles already exist and will apply */
</style>