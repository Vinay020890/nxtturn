// src/stores/feed.ts
import { ref } from 'vue';
import { defineStore } from 'pinia';
import axiosInstance from '@/services/axiosInstance';
import { useAuthStore } from './auth';
import { useProfileStore } from './profile';

// Define the expected shape of an Author object
interface PostAuthor {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  picture: string | null;
}

// --- NEW: Interface for a single media item in a post gallery ---
export interface PostMedia {
  id: number;
  media_type: 'image' | 'video';
  file_url: string;
}

// --- NEW: Interfaces for Polls ---
export interface PollOption {
  id: number;
  text: string;
  vote_count: number;
}

export interface Poll {
  id: number;
  question: string;
  options: PollOption[];
  total_votes: number;
  user_vote: number | null; // The ID of the option the user voted for
}

// ==========================================
// === UPDATED Post Interface Definition ===
// ==========================================
export interface Post {
  id: number;
  post_type: string;
  author: PostAuthor;
  created_at: string;
  updated_at: string;
  title: string | null;
  content: string | null;
  media: PostMedia[];

  // =========================================================
  // v v v ADD THIS LINE TO FIX THE ERROR v v v
  // =========================================================
  poll: Poll | null; 
  // =========================================================
  
  like_count: number;
  comment_count?: number;
  is_liked_by_user: boolean;
  content_type_id: number;
  object_id: number;
  isLiking?: boolean;
  isDeleting?: boolean; 
  isUpdating?: boolean;
}
// ==========================================

// Define the structure of the paginated response from the API
interface PaginatedFeedResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Post[];
}

// Define the store using Setup Store syntax
export const useFeedStore = defineStore('feed', () => {
  // --- State ---
  const posts = ref<Post[]>([]);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const currentPage = ref(1);
  const totalPages = ref(1);
  const hasNextPage = ref(false);
  const createPostError = ref<string | null>(null);
  const isCreatingPost = ref(false);
  const deletePostError = ref<string | null>(null);
  const updatePostError = ref<string | null>(null);

  const ITEMS_PER_PAGE = 10;

  // --- Actions ---

  async function fetchFeed(page: number = 1) {
    if (isLoading.value) return;

    isLoading.value = true;
    error.value = null;

    if (page === 1) {
      posts.value = [];
    }

    try {
      const authStore = useAuthStore();
      if (!authStore.isAuthenticated) {
        isLoading.value = false;
        return;
      }

      const response = await axiosInstance.get<PaginatedFeedResponse>('/feed/', {
        params: { page }
      });

      const fetchedPosts = response.data.results.map(post => ({
          ...post,
          isLiking: false,
          isDeleting: false
      }));

      posts.value = fetchedPosts;
      currentPage.value = page;
      hasNextPage.value = response.data.next !== null;
      totalPages.value = response.data.count > 0 ? Math.ceil(response.data.count / ITEMS_PER_PAGE) : 1;

    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || 'Failed to fetch feed.';
    } finally {
      isLoading.value = false;
    }
  }

  // ==========================================
  // === UPDATED createPost Action ===
  // ==========================================
  async function createPost(postData: FormData): Promise<Post | null> {
    isCreatingPost.value = true;
    createPostError.value = null;

    try {
      const authStore = useAuthStore();
      if (!authStore.isAuthenticated) {
        createPostError.value = "User not authenticated. Please login to post.";
        return null;
      }

      // Axios handles the 'multipart/form-data' Content-Type automatically for FormData
      const response = await axiosInstance.post<Post>('/posts/', postData);

      // Add frontend flags to the newly created post
      const newPostResponseData = { ...response.data, isLiking: false, isDeleting: false };
      
      // Add to the top of the feed
      posts.value.unshift(newPostResponseData);

      return newPostResponseData;

    } catch (err: any) {
      console.error("FeedStore: Error creating post:", err);
      if (err.response && err.response.data) {
          let specificErrorMessage = '';
          if (typeof err.response.data === 'object' && err.response.data !== null) {
              // Handle new 'images' and 'videos' error fields from the backend
              const errorKeys = ['content', 'images', 'videos', 'non_field_errors', 'detail'];
              errorKeys.forEach(key => {
                if (err.response.data[key]) {
                  specificErrorMessage += (Array.isArray(err.response.data[key]) ? err.response.data[key].join(' ') : err.response.data[key]) + ' ';
                }
              });
          }
          
          if (specificErrorMessage.trim()) {
              createPostError.value = specificErrorMessage.trim();
          } else if (typeof err.response.data === 'string') {
              createPostError.value = err.response.data;
          } else { 
              createPostError.value = "Failed to create post. Invalid input or server error.";
          }
      } else if (err.message) {
          createPostError.value = err.message;
      } else {
          createPostError.value = 'An unexpected error occurred while creating the post.';
      }
      return null;
    } finally {
      isCreatingPost.value = false;
    }
  }
  // ==========================================

  async function toggleLike(
    postId: number,
    postType: string,
    contentTypeId: number,
    objectId: number
) {
  const postIndex = posts.value.findIndex(p => p.id === postId && p.post_type === postType);
  let localPostRef: Post | null = null;

  if (postIndex !== -1) {
    localPostRef = posts.value[postIndex];
    if (localPostRef.isLiking) return;
    localPostRef.isLiking = true;
    const originalLikedStatus = localPostRef.is_liked_by_user;
    const originalLikeCount = localPostRef.like_count;
    
    localPostRef.is_liked_by_user = !localPostRef.is_liked_by_user;
    localPostRef.like_count += localPostRef.is_liked_by_user ? 1 : -1;
    
    try {
      const apiUrl = `/content/${contentTypeId}/${objectId}/like/`;
      const response = await axiosInstance.post<{ liked: boolean, like_count: number }>(apiUrl);
      localPostRef.is_liked_by_user = response.data.liked;
      localPostRef.like_count = response.data.like_count;
    } catch (err: any) {
      localPostRef.is_liked_by_user = originalLikedStatus;
      localPostRef.like_count = originalLikeCount;
      error.value = err.response?.data?.detail || err.message || 'Failed to toggle like.';
      throw err;
    } finally {
      localPostRef.isLiking = false;
    }
  } else {
    // If post not in feed, just call the API. Profile store will handle UI on profile page.
    try {
      const apiUrl = `/content/${contentTypeId}/${objectId}/like/`;
      await axiosInstance.post(apiUrl);
    } catch (err: any) {
      console.error(`FeedStore: Error toggling like for non-local object ${objectId}:`, err);
      throw err;
    }
  }
}

function incrementCommentCount(postId: number, postType: string) {
  const postIndex = posts.value.findIndex(p => p.id === postId && p.post_type === postType);
  if (postIndex !== -1) {
    posts.value[postIndex].comment_count = (posts.value[postIndex].comment_count || 0) + 1;
  }
}

async function deletePost(postId: number, postType: string): Promise<boolean> {
    const postIndex = posts.value.findIndex(p => p.id === postId && p.post_type === postType);
    if (postIndex !== -1) {
        posts.value[postIndex].isDeleting = true;
    }

    try {
        if (postType.toLowerCase() !== 'statuspost') {
            throw new Error(`Deletion for post_type '${postType}' is not supported here.`);
        }
        await axiosInstance.delete(`/posts/${postId}/`);
        if (postIndex !== -1) {
            posts.value.splice(postIndex, 1);
        }
        return true;
    } catch (err: any) {
        deletePostError.value = err.response?.data?.detail || err.message || 'Failed to delete post.';
        if (postIndex !== -1 && posts.value[postIndex]) {
            posts.value[postIndex].isDeleting = false;
        }
        return false;
    }
}

async function updatePost(postId: number, postType: string, formData: FormData): Promise<boolean> {
    const postIndex = posts.value.findIndex(p => p.id === postId && p.post_type === postType);
    if (postIndex !== -1) {
        posts.value[postIndex].isUpdating = true;
    }

    try {
        if (postType.toLowerCase() !== 'statuspost') {
            throw new Error(`Update for post_type '${postType}' is not supported here.`);
        }
        const response = await axiosInstance.patch<Post>(`/posts/${postId}/`, formData);
        if (postIndex !== -1) {
            posts.value[postIndex] = { ...posts.value[postIndex], ...response.data, isUpdating: false };
        }
        const profileStore = useProfileStore();
        profileStore.updateUserPost(response.data);
        return true;
    } catch (err: any) {
        updatePostError.value = err.response?.data?.detail || 'Failed to update post.';
        if (postIndex !== -1 && posts.value[postIndex]) {
            posts.value[postIndex].isUpdating = false;
        }
        return false;
    }
}

// In src/stores/feed.ts, inside useFeedStore...

async function castVote(pollId: number, optionId: number): Promise<void> {
  const postWithPoll = posts.value.find(p => p.poll?.id === pollId);
  if (!postWithPoll || !postWithPoll.poll) return;

  const poll = postWithPoll.poll;
  const previousVoteId = poll.user_vote;
  const isRetracting = previousVoteId === optionId;

  // --- Complex Optimistic UI Update ---
  // Store original state for potential rollback
  const originalPollState = JSON.parse(JSON.stringify(poll));

  // 1. If there was a previous vote, decrement its count.
  if (previousVoteId !== null) {
    const prevOption = poll.options.find(o => o.id === previousVoteId);
    if (prevOption) prevOption.vote_count--;
  }

  // 2. If this is a NEW vote (not a retraction), increment the new option's count.
  if (!isRetracting) {
    const newOption = poll.options.find(o => o.id === optionId);
    if (newOption) newOption.vote_count++;
  }

  // 3. Adjust total votes and the user's current vote status.
  if (isRetracting) {
    poll.total_votes--;
    poll.user_vote = null; // User has retracted their vote
  } else {
    if (previousVoteId === null) {
      poll.total_votes++; // Only increment total if it was their first vote
    }
    poll.user_vote = optionId; // Set the new vote
  }
  
  try {
    let response;
    const apiUrl = `/polls/${pollId}/options/${optionId}/vote/`;
    
    if (isRetracting) {
      // Send a DELETE request to retract the vote
      response = await axiosInstance.delete<Post>(apiUrl);
    } else {
      // Send a POST request to cast or change the vote
      response = await axiosInstance.post<Post>(apiUrl);
    }

    // Sync with the authoritative state from the server
    const updatedPost = response.data;
    const postIndex = posts.value.findIndex(p => p.id === updatedPost.id);
    if (postIndex !== -1) {
      posts.value[postIndex] = { ...posts.value[postIndex], ...updatedPost };
    }

  } catch (err: any) {
    // On error, roll back to the original state
    const postIndex = posts.value.findIndex(p => p.poll?.id === pollId);
    if (postIndex !== -1) {
        posts.value[postIndex].poll = originalPollState;
    }
    console.error("Failed to cast/retract vote:", err);
    error.value = err.response?.data?.detail || "Failed to update vote.";
  }
}

  return {
    posts,
    isLoading,
    error,
    currentPage,
    totalPages,
    hasNextPage,
    createPostError,
    isCreatingPost,
    deletePostError,
    updatePostError,
    fetchFeed,
    createPost,
    toggleLike,
    incrementCommentCount, 
    deletePost,
    updatePost,
    castVote,
  };
});