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

// Template refs for file inputs
const imageInputRef = ref<HTMLInputElement | null>(null); // <<<< NEW
const videoInputRef = ref<HTMLInputElement | null>(null); // <<<< NEW

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
      selectedImageFile.value = null; // Also clear the file if reading fails
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

// ---- 👇👇👇 ADD THIS NEW METHOD FOR REMOVING IMAGE 👇👇👇 ----
const removeSelectedImage = () => {
  if (imagePreviewUrl.value) {
    // Revoke the object URL to free up memory, if you were using URL.createObjectURL
    // Since we are using FileReader and data URLs, this step is not strictly necessary for memory,
    // but good practice if you switch to URL.createObjectURL.
    // For data URLs, simply nullifying is enough.
  }
  selectedImageFile.value = null;
  imagePreviewUrl.value = null;
  // Reset the file input so the user can select the same file again if they wish
  if (imageInputRef.value) {
    imageInputRef.value.value = ''; // This is the key to truly clear the input
  }
};
// ---- END OF NEW METHOD ----

// ---- 👇👇👇 ADD THIS NEW METHOD FOR REMOVING VIDEO 👇👇👇 ----
const removeSelectedVideo = () => {
  selectedVideoFile.value = null;
  // Reset the file input
  if (videoInputRef.value) {
    videoInputRef.value.value = ''; // This is the key to truly clear the input
  }
};
// ---- END OF NEW METHOD ----



// 5. Define the handleSubmit function
// ---- REPLACE EXISTING handleSubmit WITH THIS ----
// ---- REPLACE CURRENT handleSubmit WITH THIS ----
const handleSubmit = async () => {
  const currentContent = postContent.value.trim();
  const currentImageFile = selectedImageFile.value;
  const currentVideoFile = selectedVideoFile.value;

  if (!currentContent && !currentImageFile && !currentVideoFile) {
    feedStore.createPostError = "Please provide text, an image, or a video for your post.";
    return;
  }
  if (feedStore.createPostError) {
    feedStore.createPostError = null;
  }

  const formData = new FormData();

  if (currentContent) {
    formData.append('content', currentContent);
  }
  if (currentImageFile) {
    formData.append('image', currentImageFile);
  }
  if (currentVideoFile) {
    formData.append('video', currentVideoFile);
  }

  const newPost = await feedStore.createPost(formData);

  if (newPost) {
    console.log("CreatePostForm: Post submitted successfully!", newPost);
    postContent.value = '';
    // Call removal functions to ensure inputs are also reset
    removeSelectedImage(); // <<<< MODIFIED
    removeSelectedVideo(); // <<<< MODIFIED

    // The explicit resetting via getElementById can be removed if template refs are used consistently
    // but keeping it for now won't hurt, it's just redundant with the calls above if refs are set up.
    // However, it's better to rely on the `removeSelectedImage/Video` methods for resetting.
    // const imageFileInput = document.getElementById('postImageInput') as HTMLInputElement;
    // if (imageFileInput) {
    //   imageFileInput.value = '';
    // }
    // const videoFileInput = document.getElementById('postVideoInput') as HTMLInputElement;
    // if (videoFileInput) {
    //   videoFileInput.value = '';
    // }
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
      <textarea
        v-model="postContent"
        placeholder="What's on your mind? (Optional if adding image/video)" 
        rows="4"
        :disabled="isCreatingPost"
      ></textarea>

      <div class="form-group-image-upload">
        <label for="postImageInput">Add an image (optional):</label>
        <input
          type="file"
          id="postImageInput"
          ref="imageInputRef" 
          @change="handleImageFileChange"
          accept="image/png, image/jpeg, image/gif"
          :disabled="isCreatingPost"
        />
        
        <!-- Image preview and remove button container -->
        <div v-if="selectedImageFile" class="file-selection-info"> <!-- <<<< ADDED WRAPPER DIV -->
          <p class="selected-file-info">
            Selected: {{ selectedImageFile.name }}
          </p>
          <!-- 👇👇👇 ADD THIS REMOVE BUTTON 👇👇👇 -->
          <button type="button" @click="removeSelectedImage" class="remove-file-button" :disabled="isCreatingPost">
            Remove Image
          </button>
        </div>

        <div v-if="imagePreviewUrl" class="image-preview-container"> <!-- This section structure is the same -->
          <img :src="imagePreviewUrl" alt="Selected image preview" class="image-preview" />
        </div>
      </div>

      <div class="form-group-video-upload">
        <label for="postVideoInput">Add a video (optional):</label>
        <input
          type="file"
          id="postVideoInput"
          ref="videoInputRef" 
          @change="handleVideoFileChange"
          accept="video/mp4, video/webm, video/ogg"
          :disabled="isCreatingPost"
        />

        <!-- Video selection info and remove button container -->
        <div v-if="selectedVideoFile" class="file-selection-info"> <!-- <<<< ADDED WRAPPER DIV -->
          <p class="selected-file-info">
            Selected: {{ selectedVideoFile.name }}
          </p>
          <!-- 👇👇👇 ADD THIS REMOVE BUTTON 👇👇👇 -->
          <button type="button" @click="removeSelectedVideo" class="remove-file-button" :disabled="isCreatingPost">
            Remove Video
          </button>
        </div>
      </div>

      <button
        type="submit"
        :disabled="isCreatingPost || (postContent.trim() === '' && !selectedImageFile && !selectedVideoFile)" 
      >
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
}

.create-post-form h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  font-size: 1.1em;
  font-weight: 600;
}

.create-post-form textarea { /* Made selector more specific */
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1rem;
  margin-bottom: 0.75rem;
  resize: vertical;
  box-sizing: border-box;
}

/* Styles for the main submit button */
.create-post-form button[type="submit"] {
  padding: 0.6rem 1.2rem;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
  float: right;
}

.create-post-form button[type="submit"]:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.create-post-form button[type="submit"]:not(:disabled):hover {
  background-color: #0056b3;
}

/* Consolidated error message style */
.error-message {
  color: red; /* Kept the explicit red from one of the definitions */
  background-color: #ffebee; /* Kept from the same definition */
  border: 1px solid red; /* Kept from the same definition */
  padding: 0.75rem; /* Using rem from the other for consistency */
  border-radius: 4px;
  margin-bottom: 1rem; /* Using rem for consistency */
  font-size: 0.9rem;
}

/* Consolidated styles for file input groups */
.form-group-image-upload,
.form-group-video-upload {
  margin-bottom: 15px; /* Used the 15px value */
}

.form-group-image-upload label,
.form-group-video-upload label {
  display: block;
  margin-bottom: 0.25rem;
  font-weight: 500;
  font-size: 0.9em;
}

.form-group-image-upload input[type="file"],
.form-group-video-upload input[type="file"] {
  display: block; /* Ensures it takes up its own line */
  /* font-size: 0.9em; /* Removed as browser default is usually fine and consistent */
}

/* Styles for the container of selected file name and remove button */
.file-selection-info {
  display: flex;
  align-items: center;
  margin-top: 5px;
}

/* Styles for the selected file name paragraph */
.file-selection-info .selected-file-info { /* More specific selector */
  margin: 0;
  margin-right: 10px;
  font-size: 0.9em; /* Kept this more specific size */
  color: #555;
  font-style: italic; /* Added from one of the original definitions */
}

/* Styles for the "Remove File" buttons */
.remove-file-button { /* General class for both remove buttons */
  padding: 3px 8px;
  font-size: 0.8em;
  background-color: #f8f9fa;
  color: #dc3545;
  border: 1px solid #dc3545;
  border-radius: 4px;
  cursor: pointer;
  /* margin-left: auto; /* Optional: if you want to push it to the right within flex container */
}

.remove-file-button:hover {
  background-color: #dc3545;
  color: white;
}

.remove-file-button:disabled {
  background-color: #e9ecef;
  border-color: #ced4da;
  color: #6c757d;
  cursor: not-allowed;
}

/* Image Preview Styles */
.image-preview-container {
  margin-top: 10px;
  text-align: left; /* Or center, if you prefer */
}

.image-preview {
  max-width: 200px;
  max-height: 200px;
  border: 1px solid #ddd;
  border-radius: 4px;
  object-fit: cover;
}
</style>