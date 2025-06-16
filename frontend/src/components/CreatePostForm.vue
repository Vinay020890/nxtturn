<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { useFeedStore } from '@/stores/feed';
import { storeToRefs } from 'pinia';

const feedStore = useFeedStore();
const { isCreatingPost, createPostError } = storeToRefs(feedStore);

const postContent = ref('');
const selectedImageFiles = ref<File[]>([]);
const selectedVideoFiles = ref<File[]>([]);
const imagePreviewUrls = ref<string[]>([]);

const isSubmittable = computed(() => {
  return postContent.value.trim() !== '' || selectedImageFiles.value.length > 0 || selectedVideoFiles.value.length > 0;
});

watch([postContent, selectedImageFiles, selectedVideoFiles], () => {
  if (createPostError.value) {
    feedStore.createPostError = null;
  }
}, { deep: true });

const handleFileChange = (event: Event, type: 'image' | 'video') => {
  const target = event.target as HTMLInputElement;
  const files = target.files;
  if (!files) return;

  const targetFilesRef = type === 'image' ? selectedImageFiles : selectedVideoFiles;
  const targetPreviewsRef = imagePreviewUrls;

  for (const file of Array.from(files)) {
    targetFilesRef.value.push(file);
    if (type === 'image') {
      const reader = new FileReader();
      reader.onload = (e) => {
        if (e.target?.result) {
          targetPreviewsRef.value.push(e.target.result as string);
        }
      };
      reader.readAsDataURL(file);
    }
  }
  target.value = '';
};

const removeSelectedFile = (index: number, type: 'image' | 'video') => {
  if (type === 'image') {
    selectedImageFiles.value.splice(index, 1);
    imagePreviewUrls.value.splice(index, 1);
  } else {
    selectedVideoFiles.value.splice(index, 1);
  }
};

const clearForm = () => {
    postContent.value = '';
    selectedImageFiles.value = [];
    selectedVideoFiles.value = [];
    imagePreviewUrls.value = [];
};

const handleSubmit = async () => {
  if (!isSubmittable.value) {
    feedStore.createPostError = "Please provide text or at least one media file for your post.";
    return;
  }
  if (createPostError.value) {
    feedStore.createPostError = null;
  }

  const formData = new FormData();
  if (postContent.value.trim()) {
    formData.append('content', postContent.value.trim());
  }
  selectedImageFiles.value.forEach(file => {
    formData.append('images', file);
  });
  selectedVideoFiles.value.forEach(file => {
    formData.append('videos', file);
  });

  const newPost = await feedStore.createPost(formData);
  if (newPost) {
    clearForm();
  }
};
</script>

<template>
  <!-- Main container card with padding, background, border, shadow, etc. -->
  <div class="bg-white p-6 rounded-lg shadow-md mb-8">
    <h3 class="text-xl font-bold text-gray-800 mb-4">Create a New Post</h3>
    
    <form @submit.prevent="handleSubmit" novalidate>
      <!-- Error Message Styling -->
      <div v-if="createPostError" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md relative mb-4" role="alert">
        <span class="block sm:inline">{{ createPostError }}</span>
      </div>
      
      <!-- Textarea Styling -->
      <textarea
        v-model="postContent"
        placeholder="What's on your mind?"
        rows="4"
        :disabled="isCreatingPost"
        class="w-full p-3 text-gray-700 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
      ></textarea>

      <!-- Previews Section -->
      <div v-if="selectedImageFiles.length > 0 || selectedVideoFiles.length > 0" class="mt-4 flex flex-wrap gap-4">
        <!-- Image Previews -->
        <div v-for="(url, index) in imagePreviewUrls" :key="`img-${index}`" class="relative w-24 h-24">
          <img :src="url" alt="Selected image preview" class="w-full h-full object-cover rounded-md" />
          <button @click="removeSelectedFile(index, 'image')" type="button" class="absolute top-1 right-1 bg-gray-800 bg-opacity-50 text-white rounded-full w-6 h-6 flex items-center justify-center hover:bg-red-500 transition">×</button>
        </div>
        <!-- Video 'Previews' (File Names) -->
        <div v-for="(file, index) in selectedVideoFiles" :key="`vid-${index}`" class="relative w-24 h-24 bg-gray-200 rounded-md flex flex-col items-center justify-center text-center p-1">
          <span class="text-3xl">🎬</span>
          <span class="text-xs text-gray-600 truncate w-full">{{ file.name }}</span>
          <button @click="removeSelectedFile(index, 'video')" type="button" class="absolute top-1 right-1 bg-gray-800 bg-opacity-50 text-white rounded-full w-6 h-6 flex items-center justify-center hover:bg-red-500 transition">×</button>
        </div>
      </div>
      
      <!-- Form Actions: File Inputs and Submit Button -->
      <div class="mt-4 flex justify-between items-center">
        <!-- File Input Icons -->
        <div class="flex gap-4">
          <label for="postImageInput" class="text-gray-500 hover:text-blue-500 cursor-pointer transition">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
            <input type="file" id="postImageInput" @change="handleFileChange($event, 'image')" multiple accept="image/*" class="hidden">
          </label>
          <label for="postVideoInput" class="text-gray-500 hover:text-blue-500 cursor-pointer transition">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
            <input type="file" id="postVideoInput" @change="handleFileChange($event, 'video')" multiple accept="video/*" class="hidden">
          </label>
        </div>
        
        <!-- Submit Button -->
        <button
          type="submit"
          :disabled="isCreatingPost || !isSubmittable"
          class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-6 rounded-full transition disabled:bg-blue-300 disabled:cursor-not-allowed"
        >
          {{ isCreatingPost ? 'Posting...' : 'Post' }}
        </button>
      </div>
    </form>
  </div>
</template>

<!-- The <style scoped> block has been completely removed -->