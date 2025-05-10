<script setup lang="ts">
import { defineProps, computed, watch, ref } from 'vue';
import { format } from 'date-fns';
import type { Comment } from '@/stores/comment'; // Shared type
import { useAuthStore } from '@/stores/auth';
import type { User } from '@/stores/auth'; // Shared type
import { useCommentStore } from '@/stores/comment'; // Import comment store

const props = defineProps<{
  comment: Comment;
  parentPostType: string;    // Prop for parent's post_type
  parentObjectId: number;    // Prop for parent's object_id
  parentPostActualId: number; // Prop for parent's actual model ID (for count update)
}>();

const authStore = useAuthStore();
const commentStore = useCommentStore(); // Get comment store instance
const loggedInUser = ref<User | null>(authStore.currentUser);

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

function editComment() {
  console.log('TODO: Edit comment ID:', props.comment.id);
}

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
</script>

<template>
  <div class="comment-item">
    <div class="comment-header">
      <div> <!-- Wrapper for author and timestamp -->
        <span class="comment-author">{{ props.comment.author.username }}</span>
        <span class="comment-timestamp" v-if="props.comment.created_at">
          {{ format(new Date(props.comment.created_at), 'Pp') }}
        </span>
      </div>
      <!-- ADD: Edit/Delete Buttons conditionally shown -->
      <div v-if="isCommentAuthor" class="comment-actions">
        <button @click="editComment" class="action-button edit-button">Edit</button>
        <button @click="deleteComment" class="action-button delete-button">Delete</button>
      </div>
      <!-- END: Edit/Delete Buttons -->
    </div>
    <div class="comment-content">
      <p>{{ props.comment.content }}</p>
    </div>
    <!-- Placeholder for an inline editing form, to be added later if editing is active -->
    <!-- 
    <div v-if="isEditing" class="comment-edit-form">
      <textarea v-model="editableContent"></textarea>
      <button @click="saveEdit">Save</button>
      <button @click="cancelEdit">Cancel</button>
    </div> 
    -->
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
</style>