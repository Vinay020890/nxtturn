<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { useFeedStore } from '@/stores/feed';
import { useAuthStore } from '@/stores/auth'; // <-- NEW: Import auth store
import { storeToRefs } from 'pinia';
import { getAvatarUrl } from '@/utils/avatars'; // <-- NEW: Import avatar utility
import MentionAutocomplete from './MentionAutocomplete.vue';

// --- Stores and State ---
const feedStore = useFeedStore();
const authStore = useAuthStore(); // <-- NEW: Initialize auth store
const { isCreatingPost, createPostError } = storeToRefs(feedStore);
const { currentUser } = storeToRefs(authStore); // <-- NEW: Get current user for avatar

// --- Form State ---
const postContent = ref('');
const selectedImageFiles = ref<File[]>([]);
const selectedVideoFiles = ref<File[]>([]);
const imagePreviewUrls = ref<string[]>([]);
const showPollCreator = ref(false);
const pollQuestion = ref('');
const pollOptions = ref<string[]>(['', '']);

// --- Computed Properties ---
const isSubmittable = computed(() => {
  const hasContent = postContent.value.trim() !== '';
  const hasMedia = selectedImageFiles.value.length > 0 || selectedVideoFiles.value.length > 0;
  const isPollValid = showPollCreator.value && pollQuestion.value.trim() !== '' && pollOptions.value.length >= 2 && pollOptions.value.every(opt => opt.trim() !== '');
  return hasContent || hasMedia || isPollValid;
});

// --- Watchers ---
watch([postContent, selectedImageFiles, selectedVideoFiles, pollQuestion, pollOptions], () => {
  if (createPostError.value) {
    feedStore.createPostError = null;
  }
}, { deep: true });

// --- Methods (remain the same) ---
const handleFileChange = (event: Event, type: 'image' | 'video') => {
  const target = event.target as HTMLInputElement;
  const files = target.files;
  if (!files) return;

  // --- NEW VALIDATION LOGIC ---
  if (type === 'image') {
    for (const file of Array.from(files)) {
      const fileName = file.name.toLowerCase();
      if (fileName.endsWith('.avif') || fileName.endsWith('.heic')) {
        // Use the existing error display to give the user feedback
        feedStore.createPostError = `Unsupported file format: '${file.name}'. Please use JPG, PNG, or WEBP.`;
        target.value = ''; // Clear the input so the invalid file is not kept
        return; // Stop the function here
      }
    }
  }
  // --- END OF NEW LOGIC ---

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
  showPollCreator.value = false;
  pollQuestion.value = '';
  pollOptions.value = ['', ''];
};
const handleSubmit = async () => {
  if (!isSubmittable.value) return;
  if (createPostError.value) feedStore.createPostError = null;

  const formData = new FormData();
  if (postContent.value.trim()) {
    formData.append('content', postContent.value.trim());
  }
  selectedImageFiles.value.forEach(file => formData.append('images', file));
  selectedVideoFiles.value.forEach(file => formData.append('videos', file));
  
  if (showPollCreator.value && pollQuestion.value.trim() && pollOptions.value.length >= 2) {
    const validOptions = pollOptions.value.map(o => o.trim()).filter(Boolean);
    if (validOptions.length >= 2) {
      const pollPayload = {
        question: pollQuestion.value.trim(),
        options: validOptions
      };
      formData.append('poll_data', JSON.stringify(pollPayload));
    }
  }

  const newPost = await feedStore.createPost(formData);
  if (newPost) {
    clearForm();
  }
};
const addPollOption = () => {
  if (pollOptions.value.length < 5) {
    pollOptions.value.push('');
  }
};
const removePollOption = (index: number) => {
  if (pollOptions.value.length > 2) {
    pollOptions.value.splice(index, 1);
  }
};
</script>

<template>
  <div class="bg-white p-4 rounded-lg shadow-md mb-8">
    <form @submit.prevent="handleSubmit" novalidate>
      <!-- Main container with avatar and input -->
      <div class="flex items-start gap-4">
       <img 
            :src="getAvatarUrl(currentUser?.picture, currentUser?.first_name, currentUser?.last_name)" 
            alt="Your avatar" 
            class="w-10 h-10 rounded-full object-cover bg-gray-200 flex-shrink-0"
          >
        <div class="w-full">
          <MentionAutocomplete
            v-model="postContent"
            placeholder="What's on your mind? Mention users with @"
            :rows="3"
            :disabled="isCreatingPost"
          />
        </div>
      </div>

      <!-- Error Message Styling -->
      <div v-if="createPostError" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md relative my-4" role="alert">
        <span class="block sm:inline">{{ createPostError }}</span>
      </div>

      <!-- Previews Section -->
      <div v-if="selectedImageFiles.length > 0 || selectedVideoFiles.length > 0" class="mt-4 pl-14 flex flex-wrap gap-4">
        <div v-for="(url, index) in imagePreviewUrls" :key="`img-${index}`" class="relative w-24 h-24">
          <img :src="url" alt="Selected image preview" class="w-full h-full object-cover rounded-md" />
          <button @click="removeSelectedFile(index, 'image')" type="button" class="absolute top-1 right-1 bg-gray-800 bg-opacity-50 text-white rounded-full w-6 h-6 flex items-center justify-center hover:bg-red-500 transition">×</button>
        </div>
        <div v-for="(file, index) in selectedVideoFiles" :key="`vid-${index}`" class="relative w-24 h-24 bg-gray-200 rounded-md flex flex-col items-center justify-center text-center p-1">
          <span class="text-3xl">🎬</span>
          <span class="text-xs text-gray-600 truncate w-full">{{ file.name }}</span>
          <button @click="removeSelectedFile(index, 'video')" type="button" class="absolute top-1 right-1 bg-gray-800 bg-opacity-50 text-white rounded-full w-6 h-6 flex items-center justify-center hover:bg-red-500 transition">×</button>
        </div>
      </div>
      
      <!-- Poll Creator Section -->
      <div v-if="showPollCreator" class="mt-4 pl-14 p-4 border border-gray-200 rounded-md bg-gray-50">
        <input type="text" v-model="pollQuestion" placeholder="Poll Question" class="w-full p-2 border border-gray-300 rounded-md mb-3" maxlength="255">
        <div v-for="(option, index) in pollOptions" :key="index" class="flex items-center gap-2 mb-2">
          <input type="text" v-model="pollOptions[index]" :placeholder="`Option ${index + 1}`" class="flex-grow p-2 border border-gray-300 rounded-md" maxlength="100">
          <button @click="removePollOption(index)" type="button" class="text-gray-400 hover:text-red-500 disabled:opacity-50" :disabled="pollOptions.length <= 2">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
          </button>
        </div>
        <button @click="addPollOption" type="button" class="text-sm text-blue-500 hover:text-blue-700 disabled:opacity-50" :disabled="pollOptions.length >= 5">Add Option</button>
      </div>
      
      <!-- Form Actions: File Inputs and Submit Button -->
      <div class="mt-4 flex justify-between items-center pl-14">
        <div class="flex gap-4">
          <label for="postImageInput" class="text-gray-500 hover:text-blue-500 cursor-pointer transition p-2 rounded-full hover:bg-blue-100">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
            <input type="file" id="postImageInput" @change="handleFileChange($event, 'image')" multiple accept="image/*" class="hidden">
          </label>
          <label for="postVideoInput" class="text-gray-500 hover:text-blue-500 cursor-pointer transition p-2 rounded-full hover:bg-blue-100">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
            <input type="file" id="postVideoInput" @change="handleFileChange($event, 'video')" multiple accept="video/*" class="hidden">
          </label>
          <button @click="showPollCreator = !showPollCreator" type="button" class="text-gray-500 hover:text-blue-500 cursor-pointer transition p-2 rounded-full hover:bg-blue-100" :class="{'text-blue-500 bg-blue-100': showPollCreator}">
             <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
          </button>
        </div>
        
        <button
          type="submit"
          :disabled="isCreatingPost || !isSubmittable"
          class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded-full transition-all duration-200 shadow-sm hover:shadow-md disabled:bg-blue-300 disabled:cursor-not-allowed disabled:shadow-none"
        >
          {{ isCreatingPost ? 'Posting...' : 'Post' }}
        </button>
      </div>
    </form>
  </div>
</template>