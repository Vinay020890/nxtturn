// C:\Users\Vinay\Project\frontend\src\stores\posts.ts
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import axiosInstance from '@/services/axiosInstance';

// --- DEFINITIONS (All are now correctly exported for other files to use) ---
export interface PostAuthor { id: number; username: string; first_name: string; last_name: string; picture: string | null; }
export interface PostMedia { id: number; media_type: 'image' | 'video'; file_url: string; }
export interface PollOption { id: number; text: string; vote_count: number; }
export interface Poll { id: number; question: string; options: PollOption[]; total_votes: number; user_vote: number | null; }
export interface Post { id: number; post_type: string; author: PostAuthor; created_at: string; updated_at: string; title: string | null; content: string | null; media: PostMedia[]; poll: Poll | null; like_count: number; comment_count?: number; is_liked_by_user: boolean; content_type_id: number; object_id: number; isLiking?: boolean; isDeleting?: boolean; isUpdating?: boolean; group: { id: number; name: string; slug: string } | null; is_saved: boolean; }

export const usePostsStore = defineStore('posts', () => {
  const posts = ref<{ [id: number]: Post }>({})

  const getPostById = computed(() => {
    return (postId: number): Post | undefined => posts.value[postId]
  })

  const getPostsByIds = computed(() => {
    return (ids: number[]): Post[] => {
      return ids.map((id) => posts.value[id]).filter((post): post is Post => !!post)
    }
  })

  function addOrUpdatePosts(newPosts: Partial<Post>[]) {
    for (const post of newPosts) {
      if (post && post.id) {
        const existingPost = posts.value[post.id]
        if (existingPost) {
          // Merge new data into the existing post object
          posts.value[post.id] = { ...existingPost, ...post }
        } else {
          // Or add it as a new post
          posts.value[post.id] = post as Post
        }
      }
    }
  }

  // --- NEW FUNCTION TO HANDLE POLL UPDATES ---
  function processVoteUpdate(updatedPost: Post) {
    if (posts.value[updatedPost.id] && updatedPost.poll) {
      // This specifically updates the poll object inside the post,
      // which is crucial for Vue's reactivity to work correctly.
      posts.value[updatedPost.id].poll = updatedPost.poll;
    }
  }

  function removePost(postId: number) {
    console.log(`PostsStore: Deleting post data for ID ${postId} from central cache.`);
    delete posts.value[postId]
  }

  function incrementCommentCount(postId: number) {
    const post = posts.value[postId];
    if (post) {
      post.comment_count = (post.comment_count || 0) + 1;
    }
  }

  function decrementCommentCount(postId: number) {
    const post = posts.value[postId];
    if (post && post.comment_count) {
      post.comment_count = Math.max(0, post.comment_count - 1);
    }
  }

  async function fetchPostById(postId: number) {
    const existingPost = posts.value[postId];
    if (existingPost && typeof existingPost.comment_count !== 'undefined') {
      return existingPost;
    }
    try {
      const response = await axiosInstance.get<Post>(`/posts/${postId}/`);
      addOrUpdatePosts([response.data]);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch post with ID ${postId}`, error);
      throw error;
    }
  }

  // --- UPDATED RETURN STATEMENT ---
  return {
    posts,
    getPostById,
    getPostsByIds,
    addOrUpdatePosts,
    removePost,
    incrementCommentCount,
    decrementCommentCount,
    fetchPostById,
    processVoteUpdate, // Expose the new function
  }
})