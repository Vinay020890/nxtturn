<script setup lang="ts">
import { getAvatarUrl } from '@/utils/avatars';
import { ref, computed, watch } from 'vue';
import type { Post, PostMedia } from '@/stores/feed';
import { useFeedStore } from '@/stores/feed';
import { format } from 'date-fns';
import { useCommentStore } from '@/stores/comment';
import CommentItem from '@/components/CommentItem.vue';
import { useAuthStore } from '@/stores/auth';
import { storeToRefs } from 'pinia';
import { useProfileStore } from '@/stores/profile';

// --- Props, Stores, and Basic State ---
const props = defineProps<{ post: Post }>();
const feedStore = useFeedStore();
const commentStore = useCommentStore();
const authStore = useAuthStore();
const profileStore = useProfileStore();
const { currentUser, isAuthenticated } = storeToRefs(authStore);
const { isCreatingComment, createCommentError } = storeToRefs(commentStore);
const showComments = ref(false);
const newCommentContent = ref('');
const localDeleteError = ref<string | null>(null);

// --- State for Media Gallery Display ---
const activeMediaIndex = ref(0);
watch(() => props.post.id, () => { activeMediaIndex.value = 0; });

// --- State for Edit Mode ---
const isEditing = ref(false);
const localEditError = ref<string | null>(null);
const editContent = ref('');
const editableMedia = ref<PostMedia[]>([]);
const newImageFiles = ref<File[]>([]);
const newVideoFiles = ref<File[]>([]);
const mediaToDeleteIds = ref<number[]>([]);

// --- Computed Properties ---
const isOwner = computed(() => isAuthenticated.value && currentUser.value?.id === props.post.author.id);
const likeButtonText = computed(() => props.post.is_liked_by_user ? 'Unlike' : 'Like');
const commentPostKey = computed(() => `${props.post.post_type}_${props.post.object_id}`);
const commentsForThisPost = computed(() => (commentStore.commentsByPost[commentPostKey.value] || []).filter(c => !c.parent));
const isLoadingComments = computed(() => commentStore.isLoading);
const commentError = computed(() => commentStore.error);
const activeMedia = computed(() => props.post.media?.[activeMediaIndex.value]);
const hasMultipleMedia = computed(() => (props.post.media?.length ?? 0) > 1);

// --- Methods ---
function toggleCommentDisplay() {
  showComments.value = !showComments.value;
  if (showComments.value && commentsForThisPost.value.length === 0 && !commentError.value) {
    commentStore.fetchComments(props.post.post_type, props.post.object_id);
  }
}
async function toggleLike() {
  if (!isAuthenticated.value) return alert('Please login to like posts.');
  await feedStore.toggleLike(props.post.id, props.post.post_type, props.post.content_type_id, props.post.object_id);
  if (profileStore.currentProfile?.user.username === props.post.author.username) {
    profileStore.toggleLikeInUserPosts(props.post.id, props.post.post_type);
  }
}
async function handleDeletePost() {
  if (!isOwner.value) return;
  if (window.confirm("Are you sure you want to delete this post? This action cannot be undone.")) {
    const success = await feedStore.deletePost(props.post.id, props.post.post_type);
    if (!success) {
      localDeleteError.value = feedStore.deletePostError || "Failed to delete post.";
    }
  }
}
function nextMedia() { activeMediaIndex.value = (activeMediaIndex.value + 1) % props.post.media.length; }
function prevMedia() { activeMediaIndex.value = (activeMediaIndex.value - 1 + props.post.media.length) % props.post.media.length; }
function setActiveMedia(index: number) { activeMediaIndex.value = index; }
function toggleEditMode() {
  isEditing.value = !isEditing.value;
  localEditError.value = null;

  if (isEditing.value) {
    editContent.value = props.post.content || '';
    editableMedia.value = [...props.post.media];
    newImageFiles.value = [];
    newVideoFiles.value = [];
    mediaToDeleteIds.value = [];
  }
}
function handleNewFiles(event: Event, type: 'image' | 'video') {
  const files = (event.target as HTMLInputElement).files;
  if (!files) return;
  const targetArray = type === 'image' ? newImageFiles : newVideoFiles;
  for (const file of Array.from(files)) {
    targetArray.value.push(file);
  }
  (event.target as HTMLInputElement).value = '';
}
function flagExistingMediaForRemoval(mediaId: number) {
  mediaToDeleteIds.value.push(mediaId);
  editableMedia.value = editableMedia.value.filter(m => m.id !== mediaId);
}
function removeNewFile(index: number, type: 'image' | 'video') {
  const targetArray = type === 'image' ? newImageFiles : newVideoFiles;
  targetArray.value.splice(index, 1);
}
function getObjectURL(file: File): string {
  return URL.createObjectURL(file);
}
async function handleUpdatePost() {
  localEditError.value = null;
  feedStore.updatePostError = null;
  const finalMediaCount = editableMedia.value.length + newImageFiles.value.length + newVideoFiles.value.length;
  if (!editContent.value.trim() && finalMediaCount === 0) {
    localEditError.value = "A post cannot be empty. It must have text or at least one media file.";
    return;
  }
  const formData = new FormData();
  if (editContent.value !== (props.post.content || '')) {
      formData.append('content', editContent.value);
  }
  newImageFiles.value.forEach(file => formData.append('images', file));
  newVideoFiles.value.forEach(file => formData.append('videos', file));
  if (mediaToDeleteIds.value.length > 0) {
      formData.append('media_to_delete', JSON.stringify(mediaToDeleteIds.value));
  }
  let hasChanges = false;
  for (const _ of formData.entries()) {
      hasChanges = true;
      break;
  }
  if (!hasChanges) {
      toggleEditMode();
      return;
  }
  const success = await feedStore.updatePost(props.post.id, props.post.post_type, formData);
  if (success) {
    isEditing.value = false;
  } else {
    localEditError.value = feedStore.updatePostError || 'Failed to update post.';
  }
}
function linkifyContent(text: string | null | undefined): string {
  if (!text) return '';
  const urlRegex = /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])|(\bwww\.[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
  return text.replace(urlRegex, url => `<a href="${url.startsWith('www.') ? 'http://' + url : url}" target="_blank" rel="noopener noreferrer" class="text-blue-500 hover:underline">${url}</a>`);
}
async function handleCommentSubmit() {
  if (!newCommentContent.value.trim()) return;
  await commentStore.createComment(props.post.post_type, props.post.object_id, newCommentContent.value, props.post.id);
  newCommentContent.value = '';
}
</script>

<template>
  <article class="bg-white border border-gray-200 rounded-lg shadow-md mb-6">
    <!-- Post Header -->
    <header class="flex items-center justify-between p-4 border-b border-gray-200">
      <div class="flex items-center">
        <img 
          :src="getAvatarUrl(post.author.picture, post.author.first_name, post.author.last_name)" 
          alt="author avatar" 
          class="w-10 h-10 rounded-full object-cover mr-3 bg-gray-200"
    >
        <div>
          <router-link :to="{ name: 'profile', params: { username: post.author.username } }" class="font-bold text-gray-800 hover:underline">
            {{ post.author.username }}
          </router-link>
          <p class="text-sm text-gray-500">{{ format(new Date(post.created_at), 'Pp') }}</p>
        </div>
      </div>
      <div v-if="isOwner" class="flex gap-2">
        <button @click="toggleEditMode" :disabled="post.isDeleting" class="text-sm font-medium text-gray-500 hover:text-blue-500 px-3 py-1 rounded-full hover:bg-gray-100 transition">
          {{ isEditing ? 'Cancel' : 'Edit' }}
        </button>
        <button @click="handleDeletePost" :disabled="post.isDeleting || isEditing" class="text-sm font-medium text-gray-500 hover:text-red-500 px-3 py-1 rounded-full hover:bg-gray-100 transition">
          {{ post.isDeleting ? 'Deleting...' : 'Delete' }}
        </button>
      </div>
    </header>

    <div v-if="localDeleteError" class="m-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md">{{ localDeleteError }}</div>

    <!-- Display Mode -->
    <div v-if="!isEditing">
      <div v-if="post.content" class="p-4">
        <p class="text-gray-800 whitespace-pre-wrap" v-html="linkifyContent(post.content)"></p>
      </div>
      <div v-if="post.media && post.media.length > 0" class="relative bg-gray-100">
        <div class="relative">
          <template v-if="activeMedia">
            <video v-if="activeMedia.media_type === 'video'" controls class="w-full max-h-[70vh] object-contain" :key="activeMedia.id" :src="activeMedia.file_url"></video>
            <img v-else :src="activeMedia.file_url" class="w-full max-h-[70vh] object-contain" />
          </template>
        </div>
        <template v-if="hasMultipleMedia">
          <button @click="prevMedia" class="absolute left-2 top-1/2 -translate-y-1/2 bg-gray-800 bg-opacity-50 text-white rounded-full w-8 h-8 flex items-center justify-center hover:bg-opacity-75"><</button>
          <button @click="nextMedia" class="absolute right-2 top-1/2 -translate-y-1/2 bg-gray-800 bg-opacity-50 text-white rounded-full w-8 h-8 flex items-center justify-center hover:bg-opacity-75">></button>
        </template>
      </div>
      <div v-if="hasMultipleMedia" class="p-2 flex flex-wrap gap-2 justify-center bg-gray-100">
        <div v-for="(mediaItem, index) in post.media" :key="mediaItem.id" @click="setActiveMedia(index)" class="w-16 h-16 rounded-md cursor-pointer border-2" :class="index === activeMediaIndex ? 'border-blue-500' : 'border-transparent'">
          <span v-if="mediaItem.media_type === 'video'" class="w-full h-full bg-gray-200 flex items-center justify-center text-2xl text-gray-500 rounded-md">▶</span>
          <img v-else :src="mediaItem.file_url" class="w-full h-full object-cover rounded-md" />
        </div>
      </div>
    </div>

    <!-- Edit Mode -->
    <div v-else class="p-4">
      <form @submit.prevent="handleUpdatePost" novalidate>
        <div v-if="localEditError" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md mb-4">{{ localEditError }}</div>
        <textarea v-model="editContent" rows="3" class="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-none"></textarea>
        <div class="mt-2 flex flex-wrap gap-2">
          <div v-for="media in editableMedia" :key="`edit-${media.id}`" class="relative w-20 h-20">
            <span v-if="media.media_type === 'video'" class="w-full h-full bg-gray-200 flex items-center justify-center text-2xl text-gray-500 rounded-md">▶</span>
            <img v-else :src="media.file_url" class="w-full h-full object-cover rounded-md" />
            <button @click="flagExistingMediaForRemoval(media.id)" type="button" class="absolute top-1 right-1 bg-gray-800 bg-opacity-50 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs hover:bg-red-500">×</button>
          </div>
          <div v-for="(file, index) in newImageFiles" :key="`new-img-${index}`" class="relative w-20 h-20">
            <img :src="getObjectURL(file)" class="w-full h-full object-cover rounded-md" />
            <button @click="removeNewFile(index, 'image')" type="button" class="absolute top-1 right-1 bg-gray-800 bg-opacity-50 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs hover:bg-red-500">×</button>
          </div>
        </div>
        <div class="mt-4 flex justify-between items-center">
          <div class="flex gap-4">
            <label for="add-images-edit" class="text-gray-500 hover:text-blue-500 cursor-pointer"><svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg></label>
            <input type="file" id="add-images-edit" @change="handleNewFiles($event, 'image')" multiple accept="image/*" class="hidden">
            <label for="add-videos-edit" class="text-gray-500 hover:text-blue-500 cursor-pointer"><svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg></label>
            <input type="file" id="add-videos-edit" @change="handleNewFiles($event, 'video')" multiple accept="video/*" class="hidden">
          </div>
          <button type="submit" :disabled="post.isUpdating" class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-full">Save Changes</button>
        </div>
      </form>
    </div>

    <!-- Footer and Comments -->
    <footer v-if="!isEditing" class="p-4 border-t border-gray-200 flex items-center gap-6 text-gray-500">
      <button @click="toggleLike" class="flex items-center gap-2 hover:text-red-500 transition-colors" :class="{'text-red-500 font-bold': post.is_liked_by_user}" :disabled="post.isLiking">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" :fill="post.is_liked_by_user ? 'currentColor' : 'none'" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 016.364 0L12 7.5l1.318-1.182a4.5 4.5 0 116.364 6.364L12 20.364l-7.682-7.682a4.5 4.5 0 010-6.364z" /></svg>
        <span>{{ post.like_count }}</span>
      </button>
      <button @click="toggleCommentDisplay" class="flex items-center gap-2 hover:text-blue-500 transition-colors">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
        <span>{{ post.comment_count }}</span>
      </button>
    </footer>
    <section v-if="!isEditing && showComments" class="bg-gray-50 p-4 border-t border-gray-200">
      <div v-if="isLoadingComments">Loading...</div>
      <div v-else-if="commentError" class="text-red-600">Error: {{ commentError }}</div>
      <div v-else>
        <CommentItem v-for="comment in commentsForThisPost" :key="comment.id" :comment="comment" :parentPostType="props.post.post_type" :parentObjectId="props.post.object_id" :parentPostActualId="props.post.id" />
        <p v-if="commentsForThisPost.length === 0" class="text-sm text-gray-500 py-4 text-center">No comments yet.</p>
      </div>
      <form v-if="isAuthenticated" @submit.prevent="handleCommentSubmit" class="mt-4 flex items-start gap-2">
        <div class="w-8 h-8 bg-gray-300 rounded-full flex-shrink-0"></div>
        <div class="flex-grow">
          <textarea v-model="newCommentContent" placeholder="Add a comment..." rows="1" class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm"></textarea>
          <div v-if="createCommentError" class="text-red-600 text-sm mt-1">{{ createCommentError }}</div>
          <button type="submit" :disabled="isCreatingComment || !newCommentContent.trim()" class="mt-2 bg-blue-500 hover:bg-blue-600 text-white text-sm font-bold py-1 px-4 rounded-full float-right disabled:bg-blue-300">Submit</button>
        </div>
      </form>
    </section>
  </article>
</template>