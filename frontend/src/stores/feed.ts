// C:\Users\Vinay\Project\frontend\src\stores\feed.ts

import { ref } from 'vue';
import { defineStore } from 'pinia';
import axiosInstance from '@/services/axiosInstance';
import { useAuthStore } from './auth';
import { useProfileStore } from './profile';
import { useGroupStore } from './group';

// --- Interfaces ---
interface PostAuthor {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  picture: string | null;
}
export interface PostMedia {
  id: number;
  media_type: 'image' | 'video';
  file_url: string;
}
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
  user_vote: number | null;
}
export interface Post {
  id: number;
  post_type: string;
  author: PostAuthor;
  created_at: string;
  updated_at: string;
  title: string | null;
  content: string | null;
  media: PostMedia[];
  poll: Poll | null; 
  like_count: number;
  comment_count?: number;
  is_liked_by_user: boolean;
  content_type_id: number;
  object_id: number;
  isLiking?: boolean;
  isDeleting?: boolean; 
  isUpdating?: boolean;
  group: { id: number; name: string; } | null;
}
interface PaginatedFeedResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Post[];
}

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
  const singlePost = ref<Post | null>(null);
  const isLoadingSinglePost = ref(false);
  const singlePostError = ref<string | null>(null);

  // --- Actions ---

  async function fetchFeed(page: number = 1) {
    if (isLoading.value && page > 1) return;
    isLoading.value = true;
    error.value = null;

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
      
      if (page === 1) {
        posts.value = fetchedPosts;
      } else {
        posts.value.push(...fetchedPosts);
      }

      currentPage.value = page;
      hasNextPage.value = response.data.next !== null;
      totalPages.value = response.data.count > 0 ? Math.ceil(response.data.count / 10) : 1;
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || 'Failed to fetch feed.';
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchNextPageOfFeed() {
    if (hasNextPage.value && !isLoading.value) {
      await fetchFeed(currentPage.value + 1);
    }
  }

  async function fetchPostById(postId: number) {
    isLoadingSinglePost.value = true;
    singlePostError.value = null;
    singlePost.value = null;
    try {
      const response = await axiosInstance.get<Post>(`/posts/${postId}/`);
      singlePost.value = response.data;
    } catch (err: any) {
      console.error(`FeedStore: Error fetching post ID ${postId}:`, err);
      singlePostError.value = err.response?.data?.detail || `Post with ID ${postId} not found.`;
    } finally {
      isLoadingSinglePost.value = false;
    }
  }

  async function createPost(postData: FormData): Promise<Post | null> {
    isCreatingPost.value = true;
    createPostError.value = null;
    try {
      const authStore = useAuthStore();
      if (!authStore.isAuthenticated) {
        createPostError.value = "User not authenticated. Please login to post.";
        return null;
      }
      const response = await axiosInstance.post<Post>('/posts/', postData);
      const newPost = { ...response.data, isLiking: false, isDeleting: false };
      const groupStore = useGroupStore();

      // Always add the new post to the main feed.
      posts.value.unshift(newPost);

      // AND if the post belongs to the currently viewed group,
      // ALSO add it to the group's post list for an instant update.
      if (newPost.group && newPost.group.id === groupStore.currentGroup?.id) {
        groupStore.addPostToGroupFeed(newPost);
      }
      return newPost;
    } catch (err: any) {
      console.error("FeedStore: Error creating post:", err);
      let errorMessage = 'An unexpected error occurred while creating the post.';
      if (err.response && err.response.data) {
        const errorData = err.response.data;
        if (typeof errorData === 'object' && errorData !== null) {
          const errorKeys = ['images', 'videos', 'content', 'poll_data', 'detail', 'non_field_errors', 'group'];
          const firstErrorKey = errorKeys.find(key => errorData[key]);
          if (firstErrorKey) {
            const errorValue = errorData[firstErrorKey];
            errorMessage = Array.isArray(errorValue) ? errorValue[0] : String(errorValue);
          }
        } else if (typeof errorData === 'string' && errorData) {
          errorMessage = errorData;
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      createPostError.value = errorMessage;
      return null;
    } finally {
      isCreatingPost.value = false;
    }
  }

  async function toggleLike(postId: number, postType: string, contentTypeId: number, objectId: number) {
    const postIndex = posts.value.findIndex(p => p.id === postId && p.post_type === postType);
    let localPostRef: Post | null = null;
    if (postIndex !== -1) {
      localPostRef = posts.value[postIndex];
    } else if (singlePost.value && singlePost.value.id === postId) {
      localPostRef = singlePost.value;
    }
    if (localPostRef) {
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
     if (singlePost.value && singlePost.value.id === postId) {
      singlePost.value.comment_count = (singlePost.value.comment_count || 0) + 1;
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
           if (singlePost.value && singlePost.value.id === postId) {
            singlePost.value = null; 
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
       if (singlePost.value && singlePost.value.id === postId) {
        singlePost.value.isUpdating = true;
      }
      try {
          if (postType.toLowerCase() !== 'statuspost') {
              throw new Error(`Update for post_type '${postType}' is not supported here.`);
          }
          const response = await axiosInstance.patch<Post>(`/posts/${postId}/`, formData);
          const updatedData = { ...response.data, isUpdating: false };
          if (postIndex !== -1) {
              posts.value[postIndex] = { ...posts.value[postIndex], ...updatedData };
          }
          if (singlePost.value && singlePost.value.id === postId) {
            singlePost.value = { ...singlePost.value, ...updatedData };
          }
          const profileStore = useProfileStore();
          profileStore.updateUserPost(response.data);
          return true;
      } catch (err: any) {
          updatePostError.value = err.response?.data?.detail || 'Failed to update post.';
          if (postIndex !== -1 && posts.value[postIndex]) {
              posts.value[postIndex].isUpdating = false;
          }
          if (singlePost.value && singlePost.value.id === postId) {
            singlePost.value.isUpdating = false;
          }
          return false;
      }
  }
  
  async function castVote(pollId: number, optionId: number): Promise<void> {
    const postWithPoll = posts.value.find(p => p.poll?.id === pollId) || (singlePost.value?.poll?.id === pollId ? singlePost.value : null);
    if (!postWithPoll || !postWithPoll.poll) return;
    const poll = postWithPoll.poll;
    const previousVoteId = poll.user_vote;
    const isRetracting = previousVoteId === optionId;
    const originalPollState = JSON.parse(JSON.stringify(poll));
    if (previousVoteId !== null) {
      const prevOption = poll.options.find(o => o.id === previousVoteId);
      if (prevOption) prevOption.vote_count--;
    }
    if (!isRetracting) {
      const newOption = poll.options.find(o => o.id === optionId);
      if (newOption) newOption.vote_count++;
    }
    if (isRetracting) {
      poll.total_votes--;
      poll.user_vote = null;
    } else {
      if (previousVoteId === null) {
        poll.total_votes++;
      }
      poll.user_vote = optionId;
    }
    try {
      let response;
      const apiUrl = `/polls/${pollId}/options/${optionId}/vote/`;
      if (isRetracting) {
        response = await axiosInstance.delete<Post>(apiUrl);
      } else {
        response = await axiosInstance.post<Post>(apiUrl);
      }
      const updatedPost = response.data;
      const postIndex = posts.value.findIndex(p => p.id === updatedPost.id);
      if (postIndex !== -1) {
        posts.value[postIndex] = { ...posts.value[postIndex], ...updatedPost };
      }
       if (singlePost.value && singlePost.value.id === updatedPost.id) {
        singlePost.value = { ...singlePost.value, ...updatedPost };
      }
    } catch (err: any) {
       const postIndexToRevert = posts.value.findIndex(p => p.poll?.id === pollId);
       if (postIndexToRevert !== -1) {
           posts.value[postIndexToRevert].poll = originalPollState;
       }
       if (singlePost.value?.poll?.id === pollId) {
         singlePost.value.poll = originalPollState;
       }
      console.error("Failed to cast/retract vote:", err);
      error.value = err.response?.data?.detail || "Failed to update vote.";
    }
  }

  return {
    // State
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
    singlePost,
    isLoadingSinglePost,
    singlePostError,
    // Actions
    fetchFeed,
    fetchNextPageOfFeed, // Expose the new action
    createPost,
    toggleLike,
    incrementCommentCount, 
    deletePost,
    updatePost,
    castVote,
    fetchPostById,
  };
});