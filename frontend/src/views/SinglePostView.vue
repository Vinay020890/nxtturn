<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { usePostsStore } from '@/stores/posts'
import PostItem from '@/components/PostItem.vue'
import PostItemSkeleton from '@/components/PostItemSkeleton.vue'

const route = useRoute()
const postsStore = usePostsStore()

const postId = computed(() => Number(route.params.postId))
const post = computed(() => postsStore.getPostById(postId.value))

const isLoading = ref(false)
const error = ref<string | null>(null)

// Image preview modal state
const showMediaModal = ref(false)
const modalMediaIndex = ref(0)
const currentPostMedia = computed(() => post.value?.media || [])

// Image preview functions
function openMediaModal(index: number) {
  modalMediaIndex.value = index
  showMediaModal.value = true
}

function closeMediaModal() {
  showMediaModal.value = false
}

function nextMediaModal() {
  modalMediaIndex.value = (modalMediaIndex.value + 1) % currentPostMedia.value.length
}

function prevMediaModal() {
  modalMediaIndex.value =
    (modalMediaIndex.value - 1 + currentPostMedia.value.length) % currentPostMedia.value.length
}

// Close modal on escape key
function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && showMediaModal.value) {
    closeMediaModal()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})

watch(
  postId,
  async (newPostId) => {
    if (!newPostId || isNaN(newPostId)) return

    // Only show the full skeleton if we have no cached version at all
    if (!post.value) {
      isLoading.value = true
    }
    error.value = null

    try {
      await postsStore.fetchPostById(newPostId)
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Post could not be loaded.'
    } finally {
      isLoading.value = false
    }
  },
  { immediate: true },
)
</script>

<template>
  <div class="max-w-4xl mx-auto">
    <div v-if="isLoading && !post">
      <PostItemSkeleton />
    </div>

    <div v-else-if="error" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4">
      <p class="font-bold">Error loading post</p>
      <p>{{ error }}</p>
    </div>

    <div v-else-if="post">
      <PostItem :post="post" @media-click="openMediaModal" />
    </div>

    <div v-else class="text-center py-10 text-gray-500">Post not found.</div>

    <!-- Image Preview Modal for Single Post View -->
    <div
      v-if="showMediaModal && currentPostMedia.length > 0"
      class="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50 p-4"
      @click="closeMediaModal"
    >
      <div class="relative max-w-4xl max-h-full w-full" @click.stop>
        <!-- Close Button -->
        <button
          @click="closeMediaModal"
          class="absolute top-4 right-4 text-white text-2xl z-10 bg-black bg-opacity-50 rounded-full w-10 h-10 flex items-center justify-center hover:bg-opacity-70 transition-all duration-200"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>

        <!-- Navigation Arrows -->
        <button
          v-if="currentPostMedia.length > 1"
          @click="prevMediaModal"
          class="absolute left-4 top-1/2 transform -translate-y-1/2 text-white text-2xl z-10 bg-black bg-opacity-50 rounded-full w-10 h-10 flex items-center justify-center hover:bg-opacity-70 transition-all duration-200"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 19l-7-7 7-7"
            />
          </svg>
        </button>

        <button
          v-if="currentPostMedia.length > 1"
          @click="nextMediaModal"
          class="absolute right-4 top-1/2 transform -translate-y-1/2 text-white text-2xl z-10 bg-black bg-opacity-50 rounded-full w-10 h-10 flex items-center justify-center hover:bg-opacity-70 transition-all duration-200"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 5l7 7-7 7"
            />
          </svg>
        </button>

        <!-- Media Display -->
        <div class="flex items-center justify-center h-full">
          <video
            v-if="currentPostMedia[modalMediaIndex].media_type === 'video'"
            controls
            class="max-w-full max-h-[80vh] object-contain rounded-lg"
            :src="currentPostMedia[modalMediaIndex].file_url"
            autoplay
          ></video>
          <img
            v-else
            :src="currentPostMedia[modalMediaIndex].file_url"
            class="max-w-full max-h-[80vh] object-contain rounded-lg"
          />
        </div>

        <!-- Image Counter -->
        <div
          v-if="currentPostMedia.length > 1"
          class="absolute bottom-4 left-1/2 transform -translate-x-1/2 text-white bg-black bg-opacity-50 rounded-full px-4 py-2 text-sm"
        >
          {{ modalMediaIndex + 1 }} / {{ currentPostMedia.length }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Smooth transitions for modal */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
