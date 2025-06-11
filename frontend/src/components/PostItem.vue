<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import type { Post } from '@/stores/feed';
import { useFeedStore } from '@/stores/feed';
import { format } from 'date-fns';
import { useCommentStore } from '@/stores/comment';
import CommentItem from '@/components/CommentItem.vue';
import { useAuthStore } from '@/stores/auth';
import { storeToRefs } from 'pinia';
import { useProfileStore } from '@/stores/profile';

// --- Props Definition ---
const props = defineProps<{
  post: Post
}>();



// --- Store Instances ---
const feedStore = useFeedStore();
const commentStore = useCommentStore();
const authStore = useAuthStore();
const profileStore = useProfileStore();

const { currentUser, isAuthenticated } = storeToRefs(authStore);

// --- GET REACTIVE REFS FROM COMMENT STORE FOR CREATION ---
const { isCreatingComment, createCommentError } = storeToRefs(commentStore);

// --- Local State ---
const showComments = ref(false);
const newCommentContent = ref('');

const localDeleteError = ref<string | null>(null); 
// 👇 PASTE THESE NEW STATE VARIABLES HERE
const isEditing = ref(false); // To toggle edit mode
const editContent = ref('');
const editImageFile = ref<File | null>(null);
const editImagePreviewUrl = ref<string | null>(null);
const editVideoFile = ref<File | null>(null);
const editVideoFileName = ref<string | null>(null); // To show selected video file name or "Current Video"

const localEditError = ref<string | null>(null); // For errors during edit submission
const isSubmittingEdit = ref(false); // To disable form during submission

// Flags to track if user wants to remove existing media
const removeCurrentImage = ref(false);
const removeCurrentVideo = ref(false);
// END OF NEW STATE VARIABLES


// ===========================================
// 👇 ADD THIS COMPUTED PROPERTY
const isOwner = computed(() => {
  // If user is not logged in, or no current user data, or post has no author, they can't be the owner.
  if (!isAuthenticated.value || !currentUser.value || !props.post.author) {
    return false;
  }
  // Compare the logged-in user's ID with the post author's ID.
  // Make sure `currentUser.value.id` and `props.post.author.id` are correct for your setup.
  return currentUser.value.id === props.post.author.id;
});
// ===========================================

// --- HELPER / UTILITY FUNCTIONS (Component-Specific) ---
// 👇👇👇 IDEAL SPOT FOR linkifyContent 👇👇👇
function linkifyContent(text: string | null | undefined): string {
  if (!text) return '';
  const urlRegex = /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])|(\bwww\.[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
  return text.replace(urlRegex, function(url) {
    let fullUrl = url;
    if (!fullUrl.match(/^https?:\/\//i) && fullUrl.startsWith('www.')) {
      fullUrl = 'http://' + fullUrl;
    }
    return `<a href="${fullUrl}" target="_blank" rel="noopener noreferrer">${url}</a>`;
  });
}
// ------------------------------------



// --- Watch for input changes to clear comment creation errors ---
watch(newCommentContent, () => {
  // If the user starts typing and there was a submission error...
  if (createCommentError.value) { // Note: .value is needed here because createCommentError is a ref from storeToRefs
    // ...clear the error in the store.
    commentStore.createCommentError = null; // Directly set the property on the store instance
  }
});

// --- Computed Properties ---
const likeButtonText = computed(() => {
  return props.post.is_liked_by_user ? 'Unlike' : 'Like';
});

const commentPostKey = computed(() => {
  if (!props.post || typeof props.post.post_type === 'undefined' || typeof props.post.object_id === 'undefined') {
    return `invalid_${props.post?.id || 'unknown'}`;
  }
  const key = `${props.post.post_type}_${props.post.object_id}`;
  return key;
});

// In PostItem.vue
const commentsForThisPost = computed(() => { // Consider renaming to topLevelCommentsForPost for clarity
  const key = commentPostKey.value;
  if (!commentStore || 
      typeof commentStore.commentsByPost === 'undefined' || 
      typeof commentStore.commentsByPost !== 'object' || 
      commentStore.commentsByPost === null) {
    return [];
  }
  const allCommentsForPost = commentStore.commentsByPost[key] || [];
  // Filter for comments that do NOT have a 'parent' (i.e., parent is null or undefined)
  return allCommentsForPost.filter(comment => !comment.parent); 
});

const isLoadingComments = computed(() => { // This is for FETCHING comments
  return commentStore.isLoading;
});

const commentError = computed(() => { // This is for FETCHING comments
  return commentStore.error;
});

// --- Methods ---
function loadComments() {
  if (!props.post || typeof props.post.post_type === 'undefined' || typeof props.post.object_id === 'undefined') {
    return;
  }
  commentStore.fetchComments(props.post.post_type, props.post.object_id);
}

function toggleCommentDisplay() {
  showComments.value = !showComments.value;
  const currentComments = commentsForThisPost.value;
  if (showComments.value && Array.isArray(currentComments) && currentComments.length === 0 && !commentError.value) {
    loadComments();
  }
}

async function handleCommentSubmit() {
  if (!newCommentContent.value.trim()) {
    commentStore.createCommentError = "Comment cannot be empty.";
    return;
  }
  if (!props.post || !props.post.post_type || typeof props.post.object_id === 'undefined') {
    commentStore.createCommentError = "Cannot submit comment: Invalid post data.";
    return;
  }

  commentStore.createCommentError = null;

  try {
    await commentStore.createComment(
      props.post.post_type,
      props.post.object_id,
      newCommentContent.value,
      props.post.id
    );
    newCommentContent.value = '';
  } catch (error) {
    console.error("PostItem: createComment action failed (error state should be set in store).");
  }
}

// In PostItem.vue
// This replaces the toggleLike method you just showed me.

const toggleLike = async () => {
  // console.log('[PostItem] toggleLike called for post ID:', props.post.id, 'Type:', props.post.post_type, 'ContentTypeID:', props.post.content_type_id, 'ObjectID:', props.post.object_id);

  if (!authStore.isAuthenticated) {
    alert('Please login to like posts.');
    return;
  }

  // Ensure essential IDs for API call are present on the post prop
   if (typeof props.post.content_type_id !== 'number' || typeof props.post.object_id !== 'number') {
      console.error('[PostItem] CRITICAL: Cannot toggle like because Post prop is missing content_type_id or object_id. Post ID:', props.post.id, 'Post data:', JSON.parse(JSON.stringify(props.post))); // Made log more explicit
      alert('Cannot like this post due to missing information. Please try again later or contact support if the issue persists.'); // Slightly more user-friendly alert
      return;
  }

  try {
    // Step 1: Perform the like/unlike action via feedStore (this makes the API call)
    // console.log('[PostItem] Calling feedStore.toggleLike for post ID:', props.post.id, 'Type:', props.post.post_type);
    await feedStore.toggleLike(props.post.id, props.post.post_type, props.post.content_type_id, props.post.object_id); 
    // console.log('[PostItem] feedStore.toggleLike finished successfully.');

    // Step 2: If this post is being displayed on a profile page, 
    // and its author matches the current profile's user,
    // then also update its state in profileStore.userPosts for UI consistency on that page.
    // console.log('[PostItem] Checking for profile sync. Current profile user:', profileStore.currentProfile?.user?.username,'Post author:', props.post.author.username);

    if (profileStore.currentProfile && 
        profileStore.currentProfile.user.username === props.post.author.username) {
        // Check if the post exists in the userPosts array of the profileStore
        const postExistsInUserPosts = profileStore.userPosts.some(
            (p: Post) => p.id === props.post.id && p.post_type === props.post.post_type
        );

        if (postExistsInUserPosts) {
            // console.log('[PostItem] Post found in profileStore.userPosts. Calling profileStore.toggleLikeInUserPosts for post ID:', props.post.id, 'Type:', props.post.post_type);
            // This new action (toggleLikeInUserPosts) will be added to profile.ts
            // It will ONLY update the local state in profileStore.userPosts.
            profileStore.toggleLikeInUserPosts(props.post.id, props.post.post_type);
        } else {
            // console.log('[PostItem] Post (ID:', props.post.id, ') not found in profileStore.userPosts, or profileStore.userPosts is empty. No sync needed or post list might be stale.');
        }
    } else {
      // console.log('[PostItem] Not on a relevant profile page, or currentProfile/author mismatch. No profileStore sync for like needed.');
    }

  } catch (error: any) { // This catch block primarily catches errors from feedStore.toggleLike
    console.error('[PostItem] Error during toggleLike process (likely from feedStore API call):', error);
    // The alert was here, but feedStore.toggleLike should set its own error state
    // which can be observed by the UI if needed.
    // If you want an alert specifically from PostItem:
    // alert(`An error occurred while trying to like the post: ${error.message || 'Please try again.'}`);
    alert(`An error occurred while trying to like the post.`); 
  }
};
// ---- END OF REPLACEMENT ----

// ===========================================
// === NEW: Method to Handle Post Deletion ===
// ===========================================
// 👇 ADD THIS ASYNC FUNCTION
async function handleDeletePost() {
  localDeleteError.value = null;      // Clear any previous local error for this item
  feedStore.deletePostError = null; // Clear any global error in the store too

  // This check is a safeguard, the button should ideally not even be visible if not owner.
  if (!isOwner.value) {
    alert("You can only delete your own posts."); 
    return;
  }

  // Ask for confirmation before deleting
  const confirmed = window.confirm("Are you sure you want to delete this post? This action cannot be undone.");
  if (!confirmed) {
    return; // User clicked "Cancel"
  }

  try {
    // Call the deletePost action from your feedStore
    // props.post.id is the ID of the post to delete
    // props.post.post_type is its type (e.g., 'statuspost')
    const success = await feedStore.deletePost(props.post.id, props.post.post_type);

    if (success) {
      // The post was deleted successfully. 
      // The feedStore removed it from its list, so the UI should update automatically
      // if this PostItem is part of a v-for loop over feedStore.posts.
      console.log(`PostItem: Post ${props.post.id} successfully deleted.`);
    } else {
      // Deletion failed, the store should have set an error message.
      // Display it locally for this post item.
      localDeleteError.value = feedStore.deletePostError || "Failed to delete post. Please try again.";
      // You could also show an alert here:
      // alert(localDeleteError.value); 
    }
  } catch (error) { 
    // This catch is for unexpected errors if the store action itself throws an unhandled error.
    console.error(`PostItem: Unexpected error during handleDeletePost for post ${props.post.id}:`, error);
    localDeleteError.value = "An unexpected error occurred while trying to delete the post.";
    // alert(localDeleteError.value);
  }
}
// ===========================================

// ===========================================
// === NEW: Methods for Post Editing ===
// ===========================================

function toggleEditMode() {
  isEditing.value = !isEditing.value;
  localEditError.value = null; // Clear any previous edit error

  if (isEditing.value) {
    // Entering edit mode: pre-fill form data from the current post
    editContent.value = props.post.content || '';
    
    // Reset file inputs and previews for new edit session
    editImageFile.value = null;
    editImagePreviewUrl.value = props.post.image || null; // Show current image initially
    removeCurrentImage.value = false; // Reset flag

    editVideoFile.value = null;
    editVideoFileName.value = props.post.video ? 'Current Video' : null; // Indicate if a video exists by name/URL
    removeCurrentVideo.value = false; // Reset flag

  }
  // No specific action needed when exiting edit mode via "Cancel"
  // Form fields will be re-populated if user clicks "Edit" again.
}

function handleEditImageFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    editImageFile.value = target.files[0];
    editImagePreviewUrl.value = URL.createObjectURL(target.files[0]);
    removeCurrentImage.value = false; // If a new image is selected, we are not trying to remove the (now old) current one
    localEditError.value = null; 
  }
}

function removeEditImage() { // Used when user clicks "Remove Image" for the *newly selected* or *currently displayed* image
  editImageFile.value = null;       // Clear any newly selected file
  editImagePreviewUrl.value = null; // Clear the preview
  removeCurrentImage.value = true;  // Set flag to indicate the original image (if any) should be removed
  
  // Visually clear the file input
  const imageInput = document.getElementById('edit-post-image') as HTMLInputElement;
  if (imageInput) imageInput.value = '';
}


function handleEditVideoFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    editVideoFile.value = target.files[0];
    editVideoFileName.value = target.files[0].name; // Show new file name
    removeCurrentVideo.value = false; // If a new video is selected, we are not trying to remove the (now old) current one
    localEditError.value = null;
  }
}

function removeEditVideo() { // Used when user clicks "Remove Selected Video" for a *newly selected* video
  editVideoFile.value = null;
  editVideoFileName.value = null; // Clear the display name
  // Note: This does NOT set removeCurrentVideo.value to true.
  // This function is for clearing a *newly selected* video before submission.
  // removeExistingVideoForUpdate is for removing a video that's already part of the post.

  const videoInput = document.getElementById('edit-post-video') as HTMLInputElement;
  if (videoInput) videoInput.value = '';
}

function removeExistingVideoForUpdate() { // Used when user clicks "Remove Current Video" for an *existing* video on the post
    editVideoFile.value = null;         // Ensure no new video file is considered
    editVideoFileName.value = null;     // Clear any display of current/new video
    removeCurrentVideo.value = true;    // Set flag to indicate original video should be removed
}


async function handleUpdatePost() {
  localEditError.value = null;
  isSubmittingEdit.value = true;

  // Basic validation: ensure at least one field (content, new image, new video, or keeping existing media) is present.
  const hasContent = editContent.value && editContent.value.trim() !== '';
  const hasNewImage = !!editImageFile.value;
  const hasNewVideo = !!editVideoFile.value;
  
  // Check if existing media is being kept (i.e., not flagged for removal and no new media uploaded to replace it)
  const isKeepingExistingImage = !!props.post.image && !removeCurrentImage.value && !hasNewImage;
  const isKeepingExistingVideo = !!props.post.video && !removeCurrentVideo.value && !hasNewVideo;

  if (!hasContent && !hasNewImage && !hasNewVideo && !isKeepingExistingImage && !isKeepingExistingVideo) {
    localEditError.value = 'Post must have content, an image, or a video.';
    isSubmittingEdit.value = false;
    return;
  }

  const formData = new FormData();
  let contentChanged = editContent.value !== (props.post.content || '');

  // 1. Append content if it has changed from original, or if it's new content.
  // Also append if it was empty and now has content, or had content and is now empty.
  if (contentChanged || (editContent.value && !props.post.content)) {
      formData.append('content', editContent.value);
  } else if (!editContent.value && props.post.content) { // Clearing existing content
      formData.append('content', '');
  } else if (hasContent) { // If content is present and unchanged, but other things might change, send it.
      // Or, if API is PATCH, only send if changed. For simplicity with current structure for StatusPostSerializer validation:
      formData.append('content', editContent.value);
  }


  // 2. Handle Image
  if (editImageFile.value) { // New image uploaded
    formData.append('image', editImageFile.value);
  } else if (removeCurrentImage.value && props.post.image) { // Existing image flagged for removal
    formData.append('image', ''); // Send empty string to clear
  }
  // If no new image and not removing existing, the existing image on server remains untouched with PATCH.

  // 3. Handle Video
  if (editVideoFile.value) { // New video uploaded
    formData.append('video', editVideoFile.value);
  } else if (removeCurrentVideo.value && props.post.video) { // Existing video flagged for removal
    formData.append('video', ''); // Send empty string to clear
  }
  // If no new video and not removing existing, the existing video on server remains untouched with PATCH.


  // Check if any actual data is being sent for update
  // (content changed, new image, new video, or clearing existing image/video)
  let actualChangesMade = false;
  for (const _ of formData.entries()) { // Iterate to see if formData has any entries
      actualChangesMade = true;
      break;
  }
  // Also consider if content was the same but is now explicitly set (even if to same value, to satisfy serializer if media is removed)
  if (!actualChangesMade && hasContent && editContent.value === (props.post.content || '')) {
      // This case handles if only media was removed, and content remained the same (but non-empty)
      // The serializer needs content if media is gone.
      // However, if content was already on formData, this is redundant.
      // Let's refine: if formData is empty but content *should* be there (e.g. media removed)
      if (!formData.has('content') && hasContent) {
          formData.append('content', editContent.value);
          actualChangesMade = true;
      }
  }


  if (!actualChangesMade) {
      // This means content is the same as original, no new files, and no media removal flags.
      isEditing.value = false; // Just exit edit mode
      isSubmittingEdit.value = false;
      return;
  }
  

  try {
    const success = await feedStore.updatePost(
        props.post.id,
        props.post.post_type, // 'statuspost'
        formData
    );

    if (success) {
      isEditing.value = false; // Exit edit mode
      // Reset flags for next edit session on another post or this one later
      removeCurrentImage.value = false;
      removeCurrentVideo.value = false;
    } else {
      localEditError.value = feedStore.updatePostError || 'Failed to update post.';
    }
  } catch (error) {
    console.error('PostItem: Error calling updatePost store action', error);
    localEditError.value = 'An unexpected error occurred while updating the post.';
  } finally {
    isSubmittingEdit.value = false;
  }
}
// ===========================================
// === END OF NEW Methods for Post Editing ===


// ===========================================

// ===========================================
// === NEW: Watchers for Edit Form Previews ===
// ===========================================
watch(() => props.post.image, (newVal, oldVal) => {
    // Only update preview if not currently editing this post,
    // to avoid overwriting user's pending changes in the edit form.
    if (!isEditing.value) {
        editImagePreviewUrl.value = newVal || null;
        // If post.image changes externally, it implies we are no longer trying to remove it
        // based on a previous "Remove Image" click in an old edit session.
        removeCurrentImage.value = false;
    }
});

watch(() => props.post.video, (newVal, oldVal) => {
    if (!isEditing.value) {
        editVideoFileName.value = newVal ? (newVal.substring(newVal.lastIndexOf('/') + 1) || 'Current Video') : null;
        // If post.video changes externally, reset the removal flag.
        removeCurrentVideo.value = false;
    }
});
// ===========================================
// === END OF NEW Watchers ===
// ===========================================

</script>

<template>
  <article class="post-item">
    <header class="post-header">
      <div class="author-info">
        <router-link :to="{ name: 'profile', params: { username: post.author.username } }" class="author-link">
          <span class="author-username">{{ post.author.username }}</span>
        </router-link>
        <span class="timestamp" v-if="post.created_at">{{ format(new Date(post.created_at), 'Pp') }}</span>
      </div>

      <!-- MODIFIED: Post Actions - Edit and Delete Buttons -->
      <div v-if="isOwner" class="post-actions">
        <button
          @click="toggleEditMode"
          :disabled="post.isDeleting || isEditing"
          class="edit-button">
          {{ isEditing ? 'Cancel Edit' : 'Edit' }}
        </button>
        <button
          @click="handleDeletePost"
          :disabled="post.isDeleting || isEditing"
          class="delete-button">
          {{ post.isDeleting ? 'Deleting...' : 'Delete' }}
        </button>
      </div>
      <!-- END OF MODIFIED Post Actions -->
    </header>

    <div v-if="localDeleteError" class="error-message post-delete-error">
      {{ localDeleteError }}
    </div>

    <!-- MODIFIED: Conditional Display - Show Post OR Edit Form -->
    <!-- Display Mode (Not Editing) -->
    <div v-if="!isEditing" class="post-content">
      <div v-if="post.video" class="post-video-container">
        <video controls class="post-video" :src="post.video">
          Your browser does not support the video tag.
        </video>
      </div>
      <div v-if="post.image" class="post-image-container">
        <img :src="post.image" :alt="`Image for post by ${post.author.username}`" class="post-image" />
      </div>
      <p v-if="post.content" class="post-text-content" v-html="linkifyContent(post.content)"></p>
    </div>

    <!-- Edit Mode Form -->
    <div v-if="isEditing" class="edit-post-form">
      <form @submit.prevent="handleUpdatePost">
        <!-- Error Message for Edit -->
        <div v-if="localEditError" class="error-message post-edit-error">
          {{ localEditError }}
        </div>

        <!-- Content Textarea -->
        <div class="form-group">
          <label for="edit-post-content">Content:</label>
          <textarea
            id="edit-post-content"
            v-model="editContent"
            rows="3"
            placeholder="What's on your mind?"
          ></textarea>
        </div>

        <!-- Image Input & Preview -->
        <div class="form-group">
          <label for="edit-post-image">Image:</label>
          <input type="file" id="edit-post-image" @change="handleEditImageFileChange" accept="image/*" />
          <div v-if="editImagePreviewUrl" class="image-preview edit-image-preview">
            <img :src="editImagePreviewUrl" alt="Image preview" />
            <button type="button" @click="removeEditImage" class="remove-media-button">Remove Image</button>
          </div>
        </div>

        <!-- Video Input & Preview/Info -->
        <div class="form-group">
          <label for="edit-post-video">Video:</label>
          <input type="file" id="edit-post-video" @change="handleEditVideoFileChange" accept="video/*" />
          <!-- Show selected new video -->
          <div v-if="editVideoFile" class="video-preview edit-video-preview">
            <p>Selected: {{ editVideoFileName }}</p>
            <button type="button" @click="removeEditVideo" class="remove-media-button">Clear Selection</button>
          </div>
          <!-- Show info about current video if no new one is selected AND not flagged for removal-->
          <div v-else-if="props.post.video && editVideoFileName && !removeCurrentVideo" class="video-preview edit-video-preview">
             <p>Current video: <a :href="props.post.video" target="_blank">{{ editVideoFileName.startsWith('http') ? 'View Current Video' : editVideoFileName }}</a></p>
             <button type="button" @click="removeExistingVideoForUpdate" class="remove-media-button">Remove Current Video</button>
          </div>
        </div>

        <!-- Validation Helper Message for Edit Form -->
        <p v-if="!editContent.trim() && !editImageFile && !editVideoFile && !editImagePreviewUrl && !(props.post.video && editVideoFileName && !removeCurrentVideo)" class="info-message">
            Post must have content, an image, or a video.
        </p>

        <!-- Form Actions (Submit and Cancel) -->
        <div class="form-actions">
          <button type="submit" :disabled="isSubmittingEdit">
            {{ isSubmittingEdit ? 'Saving...' : 'Save Changes' }}
          </button>
          <button type="button" @click="toggleEditMode" :disabled="isSubmittingEdit">Cancel</button>
        </div>
      </form>
    </div>
    <!-- END OF MODIFIED Conditional Display -->


    <footer class="post-footer">
      <button @click="toggleLike" :class="{ 'liked': post.is_liked_by_user }" class="like-button"
        :disabled="post.isLiking || post.isDeleting || isEditing"> <!-- MODIFIED: Disable if editing -->
        {{ likeButtonText }}
      </button>
      <span>Likes: {{ post.like_count ?? 0 }}</span> |
      <button @click="toggleCommentDisplay" class="comment-toggle-button"
        :disabled="post.isDeleting || isEditing"> <!-- MODIFIED: Disable if editing -->
        Comments: {{ post.comment_count ?? 0 }} {{ showComments ? '(-)' : '(+)' }}
      </button>
    </footer>

    <section v-if="showComments && !post.isDeleting && !isEditing" class="comments-section"> <!-- MODIFIED: Hide if editing -->
      <div v-if="isLoadingComments" class="comments-loading">
        Loading comments...
      </div>
      <div v-else-if="commentError" class="comments-error">
        Error loading comments: {{ commentError }}
        <button @click="loadComments">Retry</button>
      </div>
      <div v-else-if="Array.isArray(commentsForThisPost)">
        <template v-if="commentsForThisPost.length > 0">
          <CommentItem v-for="comment in commentsForThisPost" :key="comment.id" :comment="comment"
            :parentPostType="props.post.post_type" :parentObjectId="props.post.object_id"
            :parentPostActualId="props.post.id" />
        </template>
        <div v-else class="no-comments">
          No comments yet.
        </div>
      </div>
      <div v-else class="comments-error">
        Could not display comments (unexpected data structure).
      </div>

      <form v-if="isAuthenticated" @submit.prevent="handleCommentSubmit" class="comment-form">
        <div v-if="createCommentError" class="error-message comment-submit-error">
          {{ createCommentError }}
        </div>
        <textarea
            v-model="newCommentContent"
            placeholder="Add a comment..."
            rows="2"
            :disabled="isCreatingComment || post.isDeleting || isEditing" 
            required>
        </textarea>
        <button
            type="submit"
            :disabled="isCreatingComment || !newCommentContent.trim() || post.isDeleting || isEditing">
          {{ isCreatingComment ? 'Submitting...' : 'Submit Comment' }}
        </button>
      </form>
    </section>
  </article>
</template>

<style scoped>
/* ... (all existing styles from PostItem.vue should be here) ... */
.post-item {
  border: 1px solid #ddd;
  padding: 1rem;
  margin-bottom: 1rem;
  background-color: #ffffff;
  border-radius: 4px;
  color: #333;
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.5rem;
  font-size: 0.9em;
}

.author-link {
  text-decoration: none;
  color: #555;
}

.author-username {
  font-weight: bold;
  color: #444;
}

.author-link:hover .author-username {
  text-decoration: underline;
  color: #0056b3;
}

.timestamp {
  color: #666;
  font-size: 0.85em;
}

.post-content {
  margin-bottom: 0.75rem;
  line-height: 1.5;
  color: #333;
}

.post-content p {
  margin-top: 0;
  margin-bottom: 0;
}

.post-footer {
  font-size: 0.9em;
  color: #555;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.like-button {
  padding: 3px 8px;
  cursor: pointer;
  border: 1px solid #ccc;
  background-color: #e9ecef;
  color: #333;
  border-radius: 4px;
  font-size: 0.85em;
  transition: background-color 0.15s ease-in-out, border-color 0.15s ease-in-out;
}

.like-button:hover {
  background-color: #dee2e6;
  border-color: #adb5bd;
}

.like-button.liked {
  background-color: #007bff;
  border-color: #007bff;
  color: white;
}

.like-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.comment-toggle-button {
  background: none;
  border: none;
  color: #555;
  cursor: pointer;
  padding: 0;
  font-size: inherit;
  margin: 0;
  text-decoration: underline;
}

.comment-toggle-button:hover {
  color: #0056b3;
}

.comments-section {
  margin-top: 1rem;
  border-top: 1px solid #f0f0f0;
  padding-top: 1rem;
}

.comments-loading,
.comments-error,
.no-comments {
  color: #888;
  font-style: italic;
  font-size: 0.9em;
  padding: 0.5rem 0;
}

.comments-error {
  color: #dc3545;
}

.comments-error button {
  margin-left: 0.5rem;
  font-size: 0.8em;
  padding: 2px 5px;
  cursor: pointer;
}

/* --- Styles for Comment Form --- */
.comment-form {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px dashed #e0e0e0;
  /* Dashed separator */
}

.comment-form textarea {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 0.95em;
  margin-bottom: 0.5rem;
  resize: vertical;
  box-sizing: border-box;
  min-height: 60px;
  /* Minimum height */
}

.comment-form button {
  padding: 0.4rem 0.8rem;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 0.9em;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.comment-form button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.comment-form button:not(:disabled):hover {
  background-color: #0056b3;
}

.comment-submit-error {
  /* Specific styling for comment submission errors */
  color: #dc3545;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  padding: 0.5rem;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
}

.post-image-container {
  margin-bottom: 10px;
  /* Space between image and content if both exist */
  text-align: center;
  /* Or left, or whatever you prefer */
}

.post-image {
  max-width: 100%;
  /* Make image responsive, not exceed container width */
  max-height: 500px;
  /* Optional: Limit max height to prevent overly tall images */
  border-radius: 8px;
  /* Optional: match post item rounding */
  object-fit: cover;
  /* Optional: how image should resize (cover, contain, etc.) */
  /* Be mindful of aspect ratios with 'cover' */
}

/* Adjust post-content styling if needed */
.post-content p {
  margin-top: 0;
  /* Remove top margin if image is directly above */
  /* Other existing styles for content text */
}

/* In PostItem.vue <style scoped> */

.post-video-container {
  margin-bottom: 10px;
  background-color: #000; /* Optional: black background for video player */
}

.post-video {
  max-width: 100%;
  max-height: 500px; /* Or adjust as you see fit */
  display: block; /* Helps with layout sometimes */
  margin: 0 auto; /* Center if container is text-align:center or if it's block */
  border-radius: 8px; /* Optional */
}

.post-text-content { /* Add a class to specifically style post text if needed */
    /* Your existing styles for post.content p tag can go here or remain as they are */
    /* If content and media are both present, you might want specific margins */
    margin-top: 10px; /* Example: add space if media is above */
}

.post-text-content a { /* Target links within the v-html rendered content */
  color: #007bff;
  text-decoration: underline;
}
.post-text-content a:hover {
  text-decoration: none;
}

/* Ensure your existing .post-image-container and .post-image styles are still there */
/* --- End Comment Form Styles --- */

/* Styles for the container of the delete button, placed in the header */
.post-actions {
  margin-left: auto; /* This will push the delete button to the far right of the header */
  padding-left: 10px; /* Some space between author info and the delete button */
}

/* Styles for the new Delete button */
.delete-button {
  padding: 3px 8px; /* Similar padding to your .like-button */
  background-color: #f0ad4e; /* An orange/warning color, less aggressive than pure red initially */
  color: white;
  border: 1px solid #eea236;
  border-radius: 4px; /* Match your other buttons */
  font-size: 0.85em; /* Match your .like-button */
  cursor: pointer;
  font-weight: normal; /* Or bold if you prefer */
  transition: background-color 0.15s ease-in-out, border-color 0.15s ease-in-out;
}

.delete-button:hover:not(:disabled) {
  background-color: #ec971f; /* Darker orange on hover */
  border-color: #d58512;
}

/* Styles for when the delete button is disabled (e.g., during the API call) */
.delete-button:disabled {
  background-color: #f5d6ab; /* Lighter, muted orange */
  border-color: #f1c688;
  opacity: 0.65; /* Consistent with your .like-button:disabled */
  cursor: not-allowed;
}

/* Styles for the error message specifically for post deletion */
.post-delete-error {
  color: #a94442; /* Text color for errors (often dark red) */
  background-color: #f2dede; /* Background color for error messages (often light pink/red) */
  border: 1px solid #ebccd1; /* Border color for error messages */
  padding: 0.75rem 1rem;   /* Padding inside the error message box */
  margin-top: 0.5rem;      /* Space above the error message */
  margin-bottom: 0.75rem;  /* Space below the error message */
  border-radius: 4px;      /* Rounded corners, matching other elements */
  font-size: 0.9em;        /* Font size for the error text */
  text-align: left;        /* Align text to the left */
}

/*
  Your .post-header currently has 'align-items: baseline;'.
  If the delete button (which might be taller due to padding) doesn't align well
  with the author username/timestamp, you might want to change it to 'flex-start'.
  Try it as is first. If alignment is off, then modify .post-header:
*/
/*
.post-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start; // CHANGED from baseline if vertical alignment is an issue
  margin-bottom: 0.5rem;
  font-size: 0.9em;
}
*/

/*
  You already have good disabled styles for .like-button and .comment-form button.
  The :disabled="... || post.isDeleting" added in the template will use those.
  The .comment-toggle-button doesn't have an explicit :disabled style in your current CSS.
  You might want to add one for consistency if it looks odd when disabled.
  Example:
*/
.comment-toggle-button:disabled {
  color: #aaa; /* Lighter color for disabled state */
  text-decoration: none; /* Remove underline when disabled */
  cursor: not-allowed;
}

/* In PostItem.vue <style scoped> */
/* --- ADD THESE NEW STYLES --- */

.edit-button {
  padding: 3px 8px;
  background-color: #5bc0de; /* Info blue - or choose another color */
  color: white;
  border: 1px solid #46b8da;
  border-radius: 4px; /* Match your other buttons */
  font-size: 0.85em; /* Match your .like-button */
  cursor: pointer;
  margin-right: 5px; /* Space between edit and delete buttons */
  transition: background-color 0.15s ease-in-out, border-color 0.15s ease-in-out;
}

.edit-button:hover:not(:disabled) {
  background-color: #31b0d5;
  border-color: #269abc;
}

.edit-button:disabled {
  background-color: #a7d9ed; /* Lighter, muted color */
  border-color: #93cfe7;
  opacity: 0.65; /* Consistent with your .like-button:disabled */
  cursor: not-allowed;
}

/* Styles for the Edit Form Container */
.edit-post-form {
  margin-top: 1rem;
  padding: 1rem;
  border: 1px dashed #ccc; /* Dashed border to distinguish from normal post view */
  border-radius: 4px;
  background-color: #f9f9f9; /* Slightly different background */
}

.edit-post-form .form-group {
  margin-bottom: 0.75rem;
}

.edit-post-form label {
  display: block;
  margin-bottom: 0.25rem;
  font-weight: bold;
  font-size: 0.9em;
  color: #333;
}

.edit-post-form textarea,
.edit-post-form input[type="file"] {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 0.95em;
  box-sizing: border-box; /* Important for width 100% and padding */
  margin-top: 0.25rem; /* Space after label if input is not directly part of it */
}

.edit-post-form textarea {
  resize: vertical;
  min-height: 80px;
}

.edit-post-form input[type="file"] {
    font-size: 0.9em; /* Adjust font size for file input text */
}

/* Styles for Image and Video Previews in Edit Form */
.image-preview.edit-image-preview,
.video-preview.edit-video-preview {
  margin-top: 8px;
  padding: 8px;
  border: 1px solid #e0e0e0;
  background-color: #fff;
  border-radius: 4px;
  display: inline-block; /* Or block if you want it full width */
  max-width: 100%;
}

.image-preview.edit-image-preview img {
  max-width: 200px; /* Or your preferred max size */
  max-height: 200px;
  display: block;
  border-radius: 4px;
}

.video-preview.edit-video-preview p {
  font-size: 0.9em;
  color: #555;
  margin: 0;
}
.video-preview.edit-video-preview a {
  color: #007bff;
}

.remove-media-button {
    font-size: 0.8em;
    padding: 3px 6px;
    margin-left: 10px;
    vertical-align: middle; /* Align with text or image */
    background-color: #f8f9fa;
    border: 1px solid #ced4da;
    color: #dc3545; /* Reddish color for remove action */
    border-radius: 3px;
    cursor: pointer;
}
.remove-media-button:hover {
    background-color: #e9ecef;
    border-color: #adb5bd;
    color: #c82333;
}


/* Form Actions (Save, Cancel buttons) */
.edit-post-form .form-actions {
  margin-top: 1rem;
  display: flex;
  gap: 0.5rem; /* Space between buttons */
  justify-content: flex-start; /* Align buttons to the start */
}

.edit-post-form .form-actions button {
  padding: 0.5rem 1rem;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-size: 0.9em;
  font-weight: 500;
  transition: background-color 0.2s ease, opacity 0.2s ease;
}

.edit-post-form .form-actions button[type="submit"] {
  background-color: #28a745; /* Green for save */
  color: white;
}
.edit-post-form .form-actions button[type="submit"]:hover:not(:disabled) {
  background-color: #218838;
}

.edit-post-form .form-actions button[type="button"] { /* Cancel button */
  background-color: #6c757d; /* Standard gray */
  color: white;
}
.edit-post-form .form-actions button[type="button"]:hover:not(:disabled) {
  background-color: #5a6268;
}

.edit-post-form .form-actions button:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

/* Error and Info Messages in Edit Form */
.post-edit-error { /* Using your existing naming convention */
  color: #a94442;
  background-color: #f2dede;
  border: 1px solid #ebccd1;
  padding: 0.75rem 1rem;
  margin-bottom: 0.75rem;
  border-radius: 4px;
  font-size: 0.9em;
}

.info-message { /* For the "Post must have content..." helper text */
    font-size: 0.85em;
    color: #666;
    margin-top: 0.5rem;
    margin-bottom: 0.75rem;
    padding: 0.25rem;
}
/* --- END OF NEW STYLES --- */

</style>