<script setup lang="ts">
// --- Imports ---
import { getAvatarUrl, buildMediaUrl } from '@/utils/avatars';
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue';
import type { Post, PostMedia } from '@/stores/feed';
import { useFeedStore } from '@/stores/feed';
import { format } from 'date-fns';
import { useCommentStore } from '@/stores/comment';
import CommentItem from '@/components/CommentItem.vue';
import { useAuthStore } from '@/stores/auth';
import { storeToRefs } from 'pinia';
// We no longer need useProfileStore for this component's actions
// import { useProfileStore } from '@/stores/profile'; 
import PollDisplay from './PollDisplay.vue';
import MentionAutocomplete from './MentionAutocomplete.vue';
import eventBus from '@/services/eventBus';

// --- Props, Stores, and Basic State ---
const props = defineProps<{ post: Post; hideGroupContext?: boolean; }>();
const emit = defineEmits(['report-content']);
const feedStore = useFeedStore();
const commentStore = useCommentStore();
const authStore = useAuthStore();
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
const editTextAreaRef = ref<{ blur: () => void; focus: () => void; } | null>(null);
const editPollQuestion = ref('');
const editPollOptions = ref<{ id: number | null, text: string }[]>([]);
const deletedOptionIds = ref<number[]>([]);

// --- State for Options Dropdown Menu ---
const showOptionsMenu = ref(false);
const optionsMenuRef = ref<HTMLDivElement | null>(null);
const postArticleRef = ref<HTMLElement | null>(null);

// --- Computed Properties ---
const isOwner = computed(() => isAuthenticated.value && currentUser.value?.id === props.post.author.id);
const commentPostKey = computed(() => `${props.post.post_type}_${props.post.object_id}`);
const commentsForThisPost = computed(() => (commentStore.commentsByPost[commentPostKey.value] || []).filter(c => !c.parent));
const isLoadingComments = computed(() => commentStore.isLoading);
const commentError = computed(() => commentStore.error);
const activeMedia = computed(() => props.post.media?.[activeMediaIndex.value]);
const hasMultipleMedia = computed(() => (props.post.media?.length ?? 0) > 1);

// --- Methods ---
function toggleOptionsMenu() { showOptionsMenu.value = !showOptionsMenu.value; }
function handleEditClick() { toggleEditMode(); showOptionsMenu.value = false; }
function handleDeleteClick() { handleDeletePost(); showOptionsMenu.value = false; }

function handleReportClick() {
  emit('report-content', {
    content_type: props.post.post_type,
    object_id: props.post.object_id,
    content_type_id: props.post.content_type_id
  });
  showOptionsMenu.value = false;
}

function reEmitReportEvent(payload: { content_type: string, content_type_id: number, object_id: number }) {
  emit('report-content', payload);
}

const closeOnClickOutside = (event: MouseEvent) => { if (optionsMenuRef.value && !optionsMenuRef.value.contains(event.target as Node)) showOptionsMenu.value = false; };
watch(showOptionsMenu, (isOpen) => {
  if (isOpen) document.addEventListener('click', closeOnClickOutside, true);
  else document.removeEventListener('click', closeOnClickOutside, true);
});

const handleNavigation = () => {
  if (isEditing.value) {
    isEditing.value = false;
  }
};
onMounted(() => {
  eventBus.on('navigation-started', handleNavigation);
});
onUnmounted(() => { 
  document.removeEventListener('click', closeOnClickOutside, true); 
  eventBus.off('navigation-started', handleNavigation);
});

function toggleCommentDisplay() {
  showComments.value = !showComments.value;
  if (showComments.value && commentsForThisPost.value.length === 0 && !commentError.value) {
    commentStore.fetchComments(props.post.post_type, props.post.object_id);
  }
}

// === THIS IS THE ONLY FUNCTIONAL CHANGE ===
// It is now simplified to only call the central store action.
async function toggleLike() {
  if (!isAuthenticated.value) {
    return alert('Please login to like posts.');
  }
  await feedStore.toggleLike(
    props.post.id, 
    props.post.post_type, 
    props.post.content_type_id, 
    props.post.object_id
  );
}
// === END OF CHANGE ===

async function toggleSave() {
  if (!isAuthenticated.value) {
    showOptionsMenu.value = false;
    return alert('Please login to save posts.');
  }
  showOptionsMenu.value = false;
  await feedStore.toggleSavePost(props.post.id);
}

async function handleDeletePost() {
  if (!isOwner.value) return;
  if (window.confirm("Are you sure you want to delete this post? This action cannot be undone.")) {
    // This correctly calls the central feedStore action.
    const success = await feedStore.deletePost(props.post.id, props.post.post_type);
    if (!success) localDeleteError.value = feedStore.deletePostError || "Failed to delete post.";
  }
}
function nextMedia() { activeMediaIndex.value = (activeMediaIndex.value + 1) % props.post.media.length; }
function prevMedia() { activeMediaIndex.value = (activeMediaIndex.value - 1 + props.post.media.length) % props.post.media.length; }
function setActiveMedia(index: number) { activeMediaIndex.value = index; }

function toggleEditMode() {
  isEditing.value = !isEditing.value;
  localEditError.value = null;

  if (isEditing.value) {
    if (props.post.poll) {
      editPollQuestion.value = props.post.poll.question;
      editPollOptions.value = props.post.poll.options.map(opt => ({ id: opt.id, text: opt.text }));
      deletedOptionIds.value = [];
      editContent.value = '';
      editableMedia.value = [];
    } else {
      editContent.value = props.post.content || '';
      editableMedia.value = [...props.post.media];
      editPollQuestion.value = '';
      editPollOptions.value = [];
    }
    newImageFiles.value = [];
    newVideoFiles.value = [];
    mediaToDeleteIds.value = [];
    nextTick(() => {
      editTextAreaRef.value?.focus(); 
    });
  }
}

function addPollOptionToEdit() {
  if (editPollOptions.value.length < 5) {
    editPollOptions.value.push({ id: null, text: '' });
  }
}

function removePollOptionFromEdit(index: number) {
  if (editPollOptions.value.length <= 2) {
    return;
  }
  const optionToRemove = editPollOptions.value[index];
  if (optionToRemove.id !== null) {
    deletedOptionIds.value.push(optionToRemove.id);
  }
  editPollOptions.value.splice(index, 1);
}

function handleNewFiles(event: Event, type: 'image' | 'video') {
  const files = (event.target as HTMLInputElement).files;
  if (!files) return;
  const targetArray = type === 'image' ? newImageFiles : newVideoFiles;
  for (const file of Array.from(files)) targetArray.value.push(file);
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

function getObjectURL(file: File): string { return URL.createObjectURL(file); }

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
    if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
    isEditing.value = false;
    return;
  }
  // This correctly calls the central feedStore action.
  const success = await feedStore.updatePost(props.post.id, props.post.post_type, formData);
  if (success) {
    if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
    window.getSelection()?.removeAllRanges();
    postArticleRef.value?.focus();
    isEditing.value = false;
  } else {
    localEditError.value = feedStore.updatePostError || 'Failed to update post.';
  }
}

async function handleUpdatePoll() {
  localEditError.value = null;
  feedStore.updatePostError = null;
  if (!editPollQuestion.value.trim()) {
    localEditError.value = "Poll question cannot be empty.";
    return;
  }
  if (editPollOptions.value.some(opt => !opt.text.trim())) {
    localEditError.value = "Poll options cannot be empty.";
    return;
  }
  const pollPayload = {
    question: editPollQuestion.value,
    options_to_update: editPollOptions.value.filter(opt => opt.id !== null),
    options_to_add: editPollOptions.value.filter(opt => opt.id === null),
    options_to_delete: deletedOptionIds.value
  };
  const formData = new FormData();
  formData.append('poll_data', JSON.stringify(pollPayload));
  // This correctly calls the central feedStore action.
  const success = await feedStore.updatePost(props.post.id, props.post.post_type, formData);
  if (success) {
    isEditing.value = false;
  } else {
    localEditError.value = feedStore.updatePostError || 'Failed to update poll.';
  }
}

function linkifyContent(text: string | null | undefined): string {
  if (!text) return '';
  const urlRegex = /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])|(\bwww\.[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
  const mentionRegex = /@(\w+)/g;
  let linkedText = text.replace(urlRegex, url => `<a href="${url.startsWith('www.') ? 'http://' + url : url}" target="_blank" rel="noopener noreferrer" class="text-blue-500 hover:underline">${url}</a>`);
  linkedText = linkedText.replace(mentionRegex, (match, username) => {
    const profileUrl = `/profile/${username}`;
    return `<a href="${profileUrl}" class="font-semibold text-blue-600 hover:underline">${match}</a>`;
  });
  return linkedText;
}

async function handleCommentSubmit() {
  if (!newCommentContent.value.trim()) return;
  await commentStore.createComment(props.post.post_type, props.post.object_id, newCommentContent.value, props.post.id);
  newCommentContent.value = '';
}
</script>

<template>
  <article ref="postArticleRef" tabindex="-1" class="bg-white border border-gray-200 rounded-lg shadow-md mb-6 focus:outline-none">
    <header class="flex items-center justify-between p-4 border-b border-gray-200">
      <div class="flex items-center">
        <img :src="getAvatarUrl(post.author.picture, post.author.first_name, post.author.last_name)" alt="author avatar" class="w-10 h-10 rounded-full object-cover mr-3 bg-gray-200">
        <div>
          <div class="flex items-center gap-1">
            <router-link :to="{ name: 'profile', params: { username: post.author.username } }" class="font-bold text-gray-800 hover:underline">{{ post.author.username }}</router-link>
            <template v-if="post.group && !hideGroupContext">
              <span class="text-gray-500 text-sm">▶</span>
              <router-link
                :to="{ name: 'group-detail-page', params: { id: post.group.id } }"
                class="font-bold text-gray-800 hover:underline"
              >
                {{ post.group.name }}
              </router-link>
            </template>
          </div>
          <p class="text-sm text-gray-500">{{ format(new Date(post.created_at), 'Pp') }}</p>
        </div>
      </div>
      <div v-if="isAuthenticated" class="relative" ref="optionsMenuRef">
        <button @click.stop="toggleOptionsMenu" class="p-2 rounded-full text-gray-500 hover:bg-gray-100 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"></path></svg>
        </button>
        <div v-if="showOptionsMenu" class="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-10">
          <div class="py-1" role="menu" aria-orientation="vertical" aria-labelledby="options-menu">
            <button
              @click.prevent="toggleSave"
              class="w-full text-left flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
              role="menuitem"
            >
              <svg class="w-5 h-5 mr-3 text-gray-400" :fill="post.is_saved ? 'currentColor' : 'none'" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
              </svg>
              <span>{{ post.is_saved ? 'Unsave Post' : 'Save Post' }}</span>
            </button>
            <template v-if="isOwner">
              <button
                @click="handleEditClick"
                :disabled="post.isDeleting"
                class="w-full text-left flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
                role="menuitem"
              >
                <svg class="w-5 h-5 mr-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.5L15.232 5.232z"></path></svg>
                <span>{{ isEditing ? 'Cancel Edit' : 'Edit Post' }}</span>
              </button>
              <button @click="handleDeleteClick" :disabled="post.isDeleting || isEditing" class="w-full text-left flex items-center px-4 py-2 text-sm text-red-700 hover:bg-red-50 hover:text-red-900" role="menuitem">
                <svg class="w-5 h-5 mr-3 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                <span>{{ post.isDeleting ? 'Deleting...' : 'Delete Post' }}</span>
              </button>
            </template>
            <template v-else>
              <button @click="handleReportClick" class="w-full text-left flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900" role="menuitem">
                <svg class="w-5 h-5 mr-3 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6H8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9" />
                </svg>
                <span>Report Post</span>
              </button>
            </template>
          </div>
        </div>
      </div>
    </header>

    <div v-if="localDeleteError" class="m-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md">{{ localDeleteError }}</div>
    <div v-if="!isEditing">
      <div v-if="post.content" class="p-4"><p class="text-gray-800 whitespace-pre-wrap" v-html="linkifyContent(post.content)"></p></div>
      <PollDisplay v-if="post.poll" :poll="post.poll" />
      <div v-if="post.media && post.media.length > 0" class="relative bg-gray-100">
        <div class="relative">
          <template v-if="activeMedia">
            <video v-if="activeMedia.media_type === 'video'" controls class="w-full max-h-[70vh] object-contain" :key="activeMedia.id" :src="buildMediaUrl(activeMedia.file_url)"></video>
            <img v-else :src="buildMediaUrl(activeMedia.file_url)" class="w-full max-h-[70vh] object-contain">
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
          <img v-else :src="buildMediaUrl(mediaItem.file_url)" class="w-full h-full object-cover rounded-md">
        </div>
      </div>
    </div>
    <div v-else class="p-4">
      <form v-if="!post.poll" @submit.prevent="handleUpdatePost" novalidate>
        <div v-if="localEditError" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md mb-4">{{ localEditError }}</div>
        <MentionAutocomplete ref="editTextAreaRef" v-model="editContent" placeholder="Edit your post..." :rows="3" class="text-base"/>
        <div class="mt-2 flex flex-wrap gap-2">
          <div v-for="media in editableMedia" :key="`edit-${media.id}`" class="relative w-20 h-20">
            <span v-if="media.media_type === 'video'" class="w-full h-full bg-gray-200 flex items-center justify-center text-2xl text-gray-500 rounded-md">▶</span>
            <img v-else :src="buildMediaUrl(media.file_url)" class="w-full h-full object-cover rounded-md">
            <button @click="flagExistingMediaForRemoval(media.id)" type="button" class="absolute top-1 right-1 bg-gray-800 bg-opacity-50 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs hover:bg-red-500">×</button>
          </div>
          <div v-for="(file, index) in newImageFiles" :key="`new-img-${index}`" class="relative w-20 h-20">
            <img :src="getObjectURL(file)" class="w-full h-full object-cover rounded-md">
            <button @click="removeNewFile(index, 'image')" type="button" class="absolute top-1 right-1 bg-gray-800 bg-opacity-50 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs hover:bg-red-500">×</button>
          </div>
          <div v-for="(file, index) in newVideoFiles" :key="`new-vid-${index}`" class="relative w-20 h-20 bg-gray-200 rounded-md flex flex-col items-center justify-center text-center p-1">
              <span class="text-3xl">🎬</span>
              <span class="text-xs text-gray-600 truncate w-full">{{ file.name }}</span>
              <button @click="removeNewFile(index, 'video')" type="button" class="absolute top-1 right-1 bg-gray-800 bg-opacity-50 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs hover:bg-red-500">×</button>
          </div>
        </div>
        <div class="mt-4 flex justify-between items-center">
          <div class="flex gap-4">
            <label for="add-images-edit" class="text-gray-500 hover:text-blue-500 cursor-pointer"><svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg></label>
            <input id="add-images-edit" type="file" @change="handleNewFiles($event, 'image')" multiple accept="image/*" class="hidden">
            <label for="add-videos-edit" class="text-gray-500 hover:text-blue-500 cursor-pointer"><svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg></label>
            <input id="add-videos-edit" type="file" @change="handleNewFiles($event, 'video')" multiple accept="video/*" class="hidden">
          </div>
          <button type="submit" :disabled="post.isUpdating" class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-full">Save Changes</button>
        </div>
      </form>
      <form v-else @submit.prevent="handleUpdatePoll" novalidate>
          <div v-if="localEditError" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md mb-4">{{ localEditError }}</div>
          <div class="p-4 border border-gray-200 rounded-md bg-gray-50">
            <input 
              type="text" 
              v-model="editPollQuestion" 
              placeholder="Poll Question"
              class="w-full p-2 border border-gray-300 rounded-md mb-3" 
              maxlength="255"
            >
            <div v-for="(option, index) in editPollOptions" :key="option.id || `new-${index}`" class="flex items-center gap-2 mb-2">
              <input 
                type="text" 
                v-model="option.text" 
                :placeholder="`Option ${index + 1}`"
                class="flex-grow p-2 border border-gray-300 rounded-md" 
                maxlength="100"
              >
              <button 
                @click.prevent="removePollOptionFromEdit(index)" 
                :disabled="editPollOptions.length <= 2" 
                class="text-gray-400 hover:text-red-500 disabled:opacity-50 flex-shrink-0"
                type="button"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              </button>
            </div>
            <button 
              @click.prevent="addPollOptionToEdit" 
              :disabled="editPollOptions.length >= 5" 
              class="text-sm text-blue-500 hover:text-blue-700 disabled:opacity-50 mt-1"
              type="button"
            >
              Add Option
            </button>
          </div>
          <div class="mt-4 flex justify-end">
            <button 
              type="submit" 
              :disabled="post.isUpdating" 
              class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-full disabled:bg-blue-300"
            >
              {{ post.isUpdating ? 'Saving...' : 'Save Changes' }}
            </button>
          </div>
      </form>
      <div v-if="localEditError" class="text-red-600 mt-2">{{ localEditError }}</div>
    </div>
    <footer v-if="!isEditing" class="p-4 border-t border-gray-200 flex items-center gap-6 text-gray-500">
      <button @click="toggleLike" class="flex items-center gap-2 hover:text-red-500 transition-colors" :class="{'text-red-500 font-bold': post.is_liked_by_user}" :disabled="post.isLiking">
        <svg class="h-6 w-6" :fill="post.is_liked_by_user ? 'currentColor' : 'none'" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 016.364 0L12 7.5l1.318-1.182a4.5 4.5 0 116.364 6.364L12 20.364l-7.682-7.682a4.5 4.5 0 010-6.364z"></path></svg>
        <span>{{ post.like_count }}</span>
      </button>
      <button @click="toggleCommentDisplay" class="flex items-center gap-2 hover:text-blue-500 transition-colors">
        <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path></svg>
        <span>{{ post.comment_count }}</span>
      </button>
    </footer>
    <section v-if="!isEditing && showComments" class="bg-gray-50 p-4 border-t border-gray-200">
      <div v-if="isLoadingComments">Loading...</div>
      <div v-else-if="commentError" class="text-red-600">Error: {{ commentError }}</div>
      <div v-else>
        <CommentItem 
          v-for="comment in commentsForThisPost" 
          :key="comment.id" 
          :comment="comment" 
          :parentPostType="props.post.post_type" 
          :parentObjectId="props.post.object_id" 
          :parentPostActualId="props.post.id"
          @report-content="reEmitReportEvent" 
        />
        <p v-if="commentsForThisPost.length === 0" class="text-sm text-gray-500 py-4 text-center">No comments yet.</p>
      </div>
      <form v-if="isAuthenticated" @submit.prevent="handleCommentSubmit" class="mt-4 flex items-start gap-3">
          <img :src="getAvatarUrl(authStore.currentUser?.picture, authStore.currentUser?.first_name, authStore.currentUser?.last_name)" alt="your avatar" class="w-8 h-8 rounded-full object-cover flex-shrink-0 bg-gray-200">
          <div class="flex-grow">
              <MentionAutocomplete v-model="newCommentContent" placeholder="Add a comment... Mention with @" :rows="1" class="text-sm"/>
              <div v-if="createCommentError" class="text-red-600 text-sm mt-1">{{ createCommentError }}</div>
              <button type="submit" :disabled="isCreatingComment || !newCommentContent.trim()" class="mt-2 bg-blue-500 hover:bg-blue-600 text-white text-sm font-bold py-1 px-4 rounded-full float-right disabled:bg-blue-300">Submit</button>
          </div>
      </form>
    </section>
  </article>
</template>