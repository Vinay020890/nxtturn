<script setup lang="ts">
import { defineProps, computed, watch, ref } from 'vue';
import { format } from 'date-fns';
import type { Comment } from '@/stores/comment'; // Shared type
import { useAuthStore } from '@/stores/auth';
import type { User } from '@/stores/auth'; // Shared type
import { useCommentStore } from '@/stores/comment'; // Import comment store


const MAX_REPLY_DEPTH = 1;

const props = defineProps<{
  comment: Comment;
  parentPostType: string;    // Prop for parent's post_type
  parentObjectId: number;    // Prop for parent's object_id
  parentPostActualId: number; // Prop for parent's actual model ID (for count update)
  currentDepth?: number;
}>();

// Set a default for currentDepth if not provided (for top-level comments)
const effectiveDepth = computed(() => props.currentDepth ?? 0); //

const authStore = useAuthStore();
const commentStore = useCommentStore(); // Get comment store instance
const loggedInUser = ref<User | null>(authStore.currentUser);

const isEditing = ref(false);
const editableContent = ref('');

// ---- ADD THESE REFS FOR REPLY ----
const showReplyForm = ref(false);
const replyContent = ref('');
const isSubmittingReply = ref(false);
const replyError = ref<string | null>(null);
// ---- END OF REFS FOR REPLY ---

// ---- ADD THIS COMPUTED PROPERTY FOR REPLIES ----
const directReplies = computed(() => {
  const postKey = `${props.parentPostType}_${props.parentObjectId}`;
  const allCommentsForPost = commentStore.commentsByPost[postKey] || [];
  // Filter comments whose parent ID matches the current comment's ID
  return allCommentsForPost.filter(reply => reply.parent === props.comment.id);
});
// ---- END OF COMPUTED PROPERTY ---

watch(() => authStore.currentUser, (newUser: User | null) => {
  // console.log(`CommentItem ID ${props.comment.id}: authStore.currentUser changed in WATCH. New User:`, newUser);
  loggedInUser.value = newUser;
}, { immediate: true });

const isCommentAuthor = computed(() => {
  const currentUserVal = loggedInUser.value;
  const commentAuthor = props.comment?.author;
  if (currentUserVal && commentAuthor) {
    return currentUserVal.id === commentAuthor.id;
  }
  return false;
});

// ---- COMPUTED PROPERTY TO CHECK IF REPLIES ARE ALLOWED ----
const canReplyToThisComment = computed(() => {
  return effectiveDepth.value < MAX_REPLY_DEPTH; // <<<< NEW
});
// ---- END ----

// --- MODIFIED editComment function ---
function editComment() {
  console.log('Editing comment ID:', props.comment.id);
  isEditing.value = true;
  editableContent.value = props.comment.content; // Pre-fill textarea
}
// --- END MODIFIED editComment function ---

async function deleteComment() {
  console.log('CommentItem: Attempting to delete comment ID:', props.comment.id);
  if (window.confirm('Are you sure you want to delete this comment?')) {
    console.log('CommentItem: User confirmed deletion for comment ID:', props.comment.id);
    try {
      // Call the actual store action with all necessary parameters
      await commentStore.deleteComment(
        props.comment.id,
        props.parentPostType,
        props.parentObjectId,
        props.parentPostActualId // Pass the parent's actual ID for count updates
      );
      // UI should update reactively when comment is removed from store's list
      // No alert needed here if UI updates correctly
    } catch (error) {
      console.error('CommentItem: Error calling deleteComment store action:', error);
      alert('Failed to delete comment. Please try again.'); // Simple feedback
    }
  } else {
    console.log('CommentItem: User cancelled deletion for comment ID:', props.comment.id);
  }
}

// --- MODIFIED saveEdit function ---
async function saveEdit() {
  console.log(`CommentItem: Attempting to save edit for comment ID: ${props.comment.id}. New content: "${editableContent.value}"`);

  if (editableContent.value.trim() === props.comment.content) {
    console.log('CommentItem: No changes detected, cancelling edit.');
    isEditing.value = false; // Just exit edit mode if no actual change
    return;
  }

  if (!editableContent.value.trim()) {
    alert('Comment content cannot be empty.'); // Simple client-side validation
    return;
  }

  // Optional: Add a local loading state for the save button if desired
  // const isSavingEdit = ref(false);
  // isSavingEdit.value = true;

  try {
    // Call the store action
    // We need parentPostType and parentObjectId to help the store locate the comment list
    await commentStore.editComment(
      props.comment.id,         // ID of the comment to edit
      editableContent.value,    // The new content
      props.parentPostType,     // Parent post's type
      props.parentObjectId      // Parent post's object ID
    );

    console.log('CommentItem: Comment edit saved successfully via store.');
    isEditing.value = false; // Exit editing mode on success

  } catch (error: any) {
    console.error('CommentItem: Error saving comment edit:', error);
    // Display error to user (could be more sophisticated)
    alert(`Failed to save comment: ${error.message || 'Unknown error'}`);
    // Optionally, keep isEditing.value = true so user can retry or cancel
  } finally {
    // isSavingEdit.value = false; // Reset local loading state if used
  }
}
// --- END MODIFIED saveEdit function ---

function cancelEdit() {
  console.log('Cancelled editing comment ID:', props.comment.id);
  isEditing.value = false;
  // No need to reset editableContent, it will be re-initialized if edit is clicked again.
}
// --- END NEW FUNCTIONS ---

// ---- ADD THESE METHODS FOR REPLY ----
function toggleReplyForm() {
  // Check depth BEFORE trying to show the form if it's currently hidden
  if (!showReplyForm.value && !canReplyToThisComment.value) { 
      alert(`Replies are limited to ${MAX_REPLY_DEPTH} level(s).`); // Or handle more gracefully
      return; // Prevent the form from opening
  }

  showReplyForm.value = !showReplyForm.value; // Now toggle the form visibility

  if (showReplyForm.value) {
    isEditing.value = false; 
  }
  replyContent.value = ''; 
  replyError.value = null;
}

async function submitReply() {
  if (!replyContent.value.trim()) {
    replyError.value = "Reply cannot be empty.";
    return;
  }
  if (!props.comment.id) {
      replyError.value = "Cannot reply: Parent comment ID is missing.";
      return;
  }

  isSubmittingReply.value = true;
  replyError.value = null;

  try {
    console.log(`CommentItem: Submitting reply to comment ID ${props.comment.id} on post ${props.parentPostType}/${props.parentObjectId}`);
    // This will initially cause a TypeScript error because createComment doesn't yet accept the 5th argument.
    // We will fix this in commentStore.ts in the next main step.
    await commentStore.createComment(
      props.parentPostType,      // The type of the top-level post (e.g., 'statuspost')
      props.parentObjectId,      // The ID of the top-level post
      replyContent.value,        // The content of the reply
      props.parentPostActualId,  // The actual ID of the parent post (for comment count update)
      props.comment.id           // NEW: The ID of the parent comment we are replying to
    );
    replyContent.value = '';
    showReplyForm.value = false; // Hide form on success
    // TODO later: Handle displaying replies / refreshing the comment list to show the new reply.
    // For now, a full page refresh would show it if the main comment list is re-fetched.
  } catch (error: any) {
    console.error("CommentItem: Error submitting reply:", error);
    replyError.value = error.message || "Failed to submit reply.";
  } finally {
    isSubmittingReply.value = false;
  }
}
// ---- END OF METHODS FOR REPLY ----

// ---- 👇👇👇 ADD THIS NEW METHOD FOR LIKING COMMENTS 👇👇👇 ----
async function handleToggleCommentLike() {
  // Ensure all necessary properties are available on props.comment
  if (
    !props.comment ||
    typeof props.comment.id === 'undefined' ||
    typeof props.comment.comment_content_type_id === 'undefined' // This comes from the updated Comment interface
  ) {
    console.error(
      "CommentItem: Cannot toggle like because comment data is incomplete (id or comment_content_type_id missing). Comment data:",
      JSON.parse(JSON.stringify(props.comment)) // Log a deep copy for inspection
    );
    alert("An error occurred. Required comment information is missing."); // User feedback
    return;
  }

  // Prevent action if not authenticated (though button might be hidden, good safeguard)
  if (!authStore.isAuthenticated) {
    alert("Please log in to like comments.");
    return;
  }

  console.log(
    `CommentItem: Attempting to toggle like for comment ID ${props.comment.id}, ` +
    `ContentTypeID: ${props.comment.comment_content_type_id}, ` +
    `Parent Post: ${props.parentPostType}_${props.parentObjectId}`
  );

  try {
    await commentStore.toggleLikeOnComment(
      props.comment.id,
      props.comment.comment_content_type_id,
      props.parentPostType,
      props.parentObjectId
    );
    // The UI should update reactively because the store's state (comment.is_liked_by_user, comment.like_count)
    // for this specific comment object will be modified by the store action.
    console.log(`CommentItem: Like toggled successfully for comment ID ${props.comment.id} via store.`);
  } catch (error) {
    console.error(`CommentItem: Error calling toggleLikeOnComment store action for comment ID ${props.comment.id}:`, error);
    // Provide user feedback (can be more sophisticated than an alert)
    alert("Failed to update like status. Please try again.");
  }
}
// ---- 👆👆👆 END OF NEW METHOD 👆👆👆 ----

</script>

<template>
  <div class="comment-item" :style="{ 'margin-left': effectiveDepth > 0 ? (effectiveDepth * 20) + 'px' : '0px' }">
    <div class="comment-header">
      <div> <!-- Wrapper for author and timestamp -->
        <span class="comment-author">{{ props.comment.author.username }}</span>
        <span class="comment-timestamp" v-if="props.comment.created_at && !isEditing && !showReplyForm"> <!-- Hide timestamp if editing OR replying -->
          {{ format(new Date(props.comment.created_at), 'Pp') }}
        </span>
      </div>
      
      <!-- Actions: Edit, Delete, Reply -->
      <div class="comment-actions">
        <!-- Show Edit/Delete only if author AND not currently editing this comment AND not showing reply form for this comment -->
        <button v-if="isCommentAuthor && !isEditing && !showReplyForm" @click="editComment" class="action-button edit-button">Edit</button>
        <button v-if="isCommentAuthor && !isEditing && !showReplyForm" @click="deleteComment" class="action-button delete-button">Delete</button>
        
        <!-- MODIFIED: Show Reply button if authenticated, not editing, AND canReplyToThisComment is true -->
        <button 
          v-if="authStore.isAuthenticated && !isEditing && canReplyToThisComment" 
          @click="toggleReplyForm" 
          class="action-button reply-button"
        >
          {{ showReplyForm ? 'Cancel Reply' : 'Reply' }}
        </button>

         <!-- ---- 👇👇👇 ADD LIKE BUTTON AND COUNT HERE (inside .comment-actions) 👇👇👇 ---- -->
        <button 
          v-if="authStore.isAuthenticated && !isEditing && !showReplyForm" 
          @click="handleToggleCommentLike" 
          class="action-button like-comment-button"
          :class="{ 'liked': props.comment.is_liked_by_user }"
          :title="props.comment.is_liked_by_user ? 'Unlike this comment' : 'Like this comment'"
        >
          <!-- Display 'Unlike' or 'Like' text -->
          {{ props.comment.is_liked_by_user ? 'Unlike' : 'Like' }} 
          <!-- Display the like count -->
          ({{ props.comment.like_count ?? 0 }})
        </button>
        <!-- ---- 👆👆👆 END OF LIKE BUTTON AND COUNT 👆👆👆 ---- -->
      </div>
    </div>

    <!-- Display main comment content OR edit form for main comment -->
    <div v-if="!isEditing" class="comment-content">
      <p>{{ props.comment.content }}</p>
    </div>
    <div v-else class="comment-edit-form"> <!-- v-else implies isEditing is true -->
      <textarea v-model="editableContent" rows="3"></textarea>
      <div class="edit-form-actions">
        <button @click="saveEdit" class="action-button save-button">Save</button>
        <button @click="cancelEdit" class="action-button cancel-button">Cancel</button>
      </div>
    </div>

    <!-- Display reply form IF showReplyForm is true (toggleReplyForm already checks depth) -->
    <div v-if="showReplyForm" class="reply-form-container">
      <textarea v-model="replyContent" placeholder="Write a reply..." rows="2" class="reply-textarea"></textarea>
      <div class="reply-form-actions">
        <button @click="submitReply" :disabled="isSubmittingReply || !replyContent.trim()" class="action-button save-button">
          {{ isSubmittingReply ? 'Replying...' : 'Submit Reply' }}
        </button>
        <button @click="toggleReplyForm" class="action-button cancel-button">Cancel</button> <!-- This button will effectively become "Cancel" when form is open -->
      </div>
      <p v-if="replyError" class="error-message reply-error">{{ replyError }}</p>
    </div>

    <!-- Section to display replies -->
    <div v-if="directReplies && directReplies.length > 0" class="replies-container">
      <!-- Recursively render CommentItem for each reply, passing the incremented depth -->
      <CommentItem
        v-for="reply in directReplies"
        :key="reply.id"
        :comment="reply"
        :parentPostType="props.parentPostType"
        :parentObjectId="props.parentObjectId"
        :parentPostActualId="props.parentPostActualId"
        :currentDepth="effectiveDepth + 1"  
      />
    </div>
  </div>
</template>

<style scoped>
/* Scoped styles - CSS will go here */
.comment-item {
  /* Add a little basic style to see it */
  border-bottom: 1px solid #eee;
  padding: 0.75rem 0;
  margin-left: 1rem; /* Indent comments slightly */
}

/* ... (any existing styles for .comment-item, etc.) ... */

.comment-header { /* Modify existing if needed, or ensure it can contain actions */
  display: flex;
  justify-content: space-between; /* This will push actions to the right if they are the last child */
  align-items: flex-start; /* Align items to the top if actions wrap */
  gap: 0.5rem; /* Add some gap between author/timestamp div and actions div */
}

.comment-actions {
  /* No margin-left: auto needed if comment-header is flex and justify-content: space-between */
  display: flex;
  gap: 0.5rem; /* Space between Edit and Delete buttons */
  flex-shrink: 0; /* Prevent action buttons from shrinking if author name is long */
}

.action-button {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.8em; /* Make them a bit smaller */
  padding: 0.1rem 0.3rem; /* Smaller padding */
  border-radius: 3px;
  text-decoration: underline;
  line-height: 1; /* Adjust line height for better vertical alignment */
}

.edit-button {
  color: #007bff; /* Blue */
}
.edit-button:hover {
  background-color: #e7f3ff; /* Light blue background on hover */
  text-decoration: none;
}

.delete-button {
  color: #dc3545; /* Red */
}
.delete-button:hover {
  background-color: #f8d7da; /* Light red background on hover */
  text-decoration: none;
}

/* ... (existing styles) ... */

.comment-edit-form {
  margin-top: 0.5rem;
}
.comment-edit-form textarea {
  width: 100%;
  min-height: 60px;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-family: inherit;
  font-size: 0.95em;
  margin-bottom: 0.5rem;
  box-sizing: border-box;
}
.edit-form-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end; /* Align buttons to the right */
}
.save-button { /* Using action-button as base */
  color: #28a745; /* Green */
  font-weight: bold;
}
.save-button:hover {
  background-color: #eaf6ec;
}
.cancel-button { /* Using action-button as base */
  color: #6c757d; /* Grey */
}
.cancel-button:hover {
  background-color: #f1f1f1;
}

/* ... (your existing styles) ... */

.reply-button { /* Style for the reply button itself */
  color: #17a2b8; /* Example: Teal color */
}
.reply-button:hover {
  background-color: #e2f6f9;
}

.reply-form-container {
  margin-top: 0.75rem;
  margin-left: 1.5rem; /* Indent reply form slightly more */
  padding-top: 0.75rem;
  border-top: 1px dashed #f0f0f0; /* Separator for reply form */
}

.reply-textarea { /* Specific class for reply textarea if needed */
  width: 100%;
  min-height: 50px;
  padding: 0.5rem;
  border: 1px solid #d1d1d1; /* Slightly different border */
  border-radius: 4px;
  font-family: inherit;
  font-size: 0.9em; /* Slightly smaller font for replies */
  margin-bottom: 0.5rem;
  box-sizing: border-box;
}

.reply-form-actions { /* Similar to edit-form-actions */
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

.reply-error { /* Specific error styling if needed */
    margin-top: 0.5rem;
    font-size: 0.8em; /* Smaller error message */
}

/* In CommentItem.vue <style scoped> */
/* ... your existing styles ... */

.comment-item {
  /* Your existing .comment-item styles, e.g.: */
  border-bottom: 1px solid #eee;
  padding: 0.75rem 0;
  /* The margin-left here provides the base indent for ALL comments including replies.
     If you want top-level comments to have no indent and replies to have an indent,
     this margin should be applied more conditionally or to the replies-container.
     For now, let's assume this base indent is okay for all. */
  margin-left: 1rem; 
}

.replies-container {
  margin-top: 8px;         /* Space above the block of replies */
  padding-left: 20px;      /* <<<<----- ADD THIS: Indent the entire block of replies further */
  /* border-left: 1px dashed #ccc; /* Optional: a visual line to indicate threading */
}

/* You might not need extra styling for .comment-item itself if the container provides enough */

/* ---- 👇👇👇 ADD STYLES FOR THE NEW LIKE BUTTON 👇👇👇 ---- */
.like-comment-button {
  color: #6c757d; /* Default: Grey, similar to cancel or a neutral action */
  /* Add any other base styling if different from generic .action-button */
}

.like-comment-button:hover {
  background-color: #f1f1f1; /* Light grey hover */
  text-decoration: none;
}

.like-comment-button.liked {
  color: #007bff;         /* Blue when liked (or your preferred "active" color) */
  font-weight: bold;      /* Optional: make it bold when liked */
}

.like-comment-button.liked:hover {
  background-color: #e7f3ff; /* Light blue hover when liked */
}
/* ---- 👆👆👆 END OF LIKE BUTTON STYLES 👆👆👆 ---- */
</style>