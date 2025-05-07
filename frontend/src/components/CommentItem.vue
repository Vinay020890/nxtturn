<script setup lang="ts">
// Import necessary function from Vue
import { defineProps } from 'vue';
// Import date formatting function (we'll use it in the template later)
import { format } from 'date-fns';

// 1. Define the expected structure of the author data within a comment
interface CommentAuthor {
  id: number;
  username: string;
  // Add other fields like first_name if needed later
}

// 2. Define the expected structure of the comment data object
interface Comment {
  id: number;
  author: CommentAuthor; // Use the interface defined above
  content: string;
  created_at: string; // Expecting ISO date string from API
  // updated_at could be added later if needed
}

// 3. Declare the props the component accepts
// We expect a single prop named 'comment' which must be of type 'Comment'
const props = defineProps<{
  comment: Comment // The prop name is 'comment', its type is the 'Comment' interface
}>();

</script>

<template>
    <div class="comment-item">
      <div class="comment-header">
        <span class="comment-author">{{ props.comment.author.username }}</span>
        <span class="comment-timestamp" v-if="props.comment.created_at">
          {{ format(new Date(props.comment.created_at), 'Pp') }} <!-- Use date-fns format -->
        </span>
      </div>
      <div class="comment-content">
        <p>{{ props.comment.content }}</p>
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
</style>