<script setup lang="ts">
// --- Imports ---
import { getAvatarUrl, buildMediaUrl } from '@/utils/avatars'
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useFeedStore } from '@/stores/feed'
import { usePostsStore } from '@/stores/posts'
import type { Post, PostMedia, PollOption } from '@/types'
import { formatDistanceToNow } from 'date-fns'
import { useCommentStore } from '@/stores/comment'
import CommentItem from '@/components/CommentItem.vue'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'
import PollDisplay from './PollDisplay.vue'
import MentionAutocomplete from './MentionAutocomplete.vue'
import eventBus from '@/services/eventBus'
import ReportFormModal from './ReportFormModal.vue'
import axiosInstance from '@/services/axiosInstance'

// Font Awesome Setup (Required for Aditya's UI)
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { library } from '@fortawesome/fontawesome-svg-core'
import {
  faEllipsisVertical,
  faBookmark,
  faPenToSquare,
  faTrash,
  faFlag,
  faHeart,
  faComment,
  faCommentDots,
  faPaperPlane,
  faRepeat,
  faImage,
  faVideo,
  faXmark,
  faChevronLeft,
  faChevronRight,
  faPlay,
  faFaceLaughBeam,
  faLightbulb,
  faPlus,
  faGripVertical,
  faChevronDown,
  faChevronUp,
  faSpinner,
  faCompress,
  faCheckCircle,
  faExclamationCircle,
  faCut,
  faHandsClapping,
  faGem,
  faThumbsUp,
} from '@fortawesome/free-solid-svg-icons'

library.add(
  faEllipsisVertical,
  faBookmark,
  faPenToSquare,
  faTrash,
  faFlag,
  faHeart,
  faComment,
  faCommentDots,
  faPaperPlane,
  faRepeat,
  faImage,
  faVideo,
  faXmark,
  faChevronLeft,
  faChevronRight,
  faPlay,
  faFaceLaughBeam,
  faLightbulb,
  faPlus,
  faGripVertical,
  faChevronDown,
  faChevronUp,
  faSpinner,
  faCompress,
  faCheckCircle,
  faExclamationCircle,
  faCut,
  faHandsClapping,
  faGem,
  faThumbsUp,
)

const props = defineProps<{ post: Post; hideGroupContext?: boolean }>()
const feedStore = useFeedStore()
const postsStore = usePostsStore()
const commentStore = useCommentStore()
const authStore = useAuthStore()
const { currentUser, isAuthenticated } = storeToRefs(authStore)
const { isCreatingComment, createCommentError } = storeToRefs(commentStore)

// --- UI State ---
const showComments = ref(false)
const newCommentContent = ref('')
const localDeleteError = ref<string | null>(null)
const isLiking = ref(false)
const activeMediaIndex = ref(0)
const showMediaModal = ref(false)
const modalMediaIndex = ref(0)
const isMobile = ref(false)
const visibleCommentCount = ref(4)
const commentsScrollContainer = ref<HTMLDivElement | null>(null)
const postContainerRef = ref<HTMLElement | null>(null)

// --- Edit Mode State ---
const isEditing = ref(false)
const localEditError = ref<string | null>(null)
const editContent = ref('')
const editableMedia = ref<PostMedia[]>([])
const newImageFiles = ref<File[]>([])
const newVideoFiles = ref<File[]>([])
const mediaToDeleteIds = ref<number[]>([])
const editTextAreaRef = ref<any>(null)
const editPollQuestion = ref('')
const editPollOptions = ref<{ id: number | null; text: string }[]>([])
const deletedOptionIds = ref<number[]>([])
const showOptionsMenu = ref(false)
const optionsMenuRef = ref<HTMLDivElement | null>(null)
const isReportModalOpen = ref(false)
const reportTarget = ref<any>(null)

// --- Computed ---
const isOwner = computed(
  () => isAuthenticated.value && currentUser.value?.id === props.post.author.id,
)
const formattedTimestamp = computed(() =>
  props.post.created_at
    ? formatDistanceToNow(new Date(props.post.created_at), { addSuffix: true })
    : '',
)
const commentPostKey = computed(() => `${props.post.post_type}_${props.post.object_id}`)
const commentsForThisPost = computed(() =>
  (commentStore.commentsByPost[commentPostKey.value] || []).filter((c: any) => !c.parent),
)
const visibleComments = computed(() =>
  commentsForThisPost.value.slice(0, visibleCommentCount.value),
)

// --- Actions ---

function toggleOptionsMenu() {
  showOptionsMenu.value = !showOptionsMenu.value
}
function handleEditClick() {
  toggleEditMode()
  showOptionsMenu.value = false
}
function handleDeleteClick() {
  handleDeletePost()
  showOptionsMenu.value = false
}
function handleReportClick() {
  reportTarget.value = { ct_id: props.post.content_type_id, obj_id: props.post.object_id }
  isReportModalOpen.value = true
  showOptionsMenu.value = false
}
function handleCommentReport(payload: { content_type_id: number; object_id: number }) {
  reportTarget.value = { ct_id: payload.content_type_id, obj_id: payload.object_id }
  isReportModalOpen.value = true
}

// Vinay's Poll Logic
function removePollOptionFromEdit(index: number) {
  localEditError.value = null
  if (editPollOptions.value.length <= 2) {
    localEditError.value = 'A poll must have at least 2 options.'
    return
  }
  const optionToRemove = editPollOptions.value[index]
  if (optionToRemove.id !== null) deletedOptionIds.value.push(optionToRemove.id)
  editPollOptions.value.splice(index, 1)
}

function addPollOptionToEdit() {
  if (editPollOptions.value.length < 5) editPollOptions.value.push({ id: null, text: '' })
}

async function handleUpdatePoll() {
  localEditError.value = null
  if (!editPollQuestion.value.trim()) {
    localEditError.value = 'Poll question cannot be empty.'
    return
  }
  const validOptions = []
  const emptyOptions = []
  for (const opt of editPollOptions.value) {
    if (opt.text.trim() !== '') validOptions.push(opt)
    else emptyOptions.push(opt)
  }
  if (emptyOptions.length > 0) {
    if (validOptions.length < 2) {
      localEditError.value = 'A poll must have at least 2 valid options.'
      return
    }
    if (!window.confirm('You have empty options. They will be discarded if you save. Continue?'))
      return
    emptyOptions.forEach((opt) => {
      if (opt.id !== null) deletedOptionIds.value.push(opt.id)
    })
    editPollOptions.value = validOptions
  } else if (editPollOptions.value.length < 2) {
    localEditError.value = 'A poll must have at least 2 options.'
    return
  }
  postsStore.addOrUpdatePosts([{ id: props.post.id, isUpdating: true }])
  const pollPayload = {
    question: editPollQuestion.value,
    options_to_update: editPollOptions.value.filter((opt) => opt.id !== null),
    options_to_add: editPollOptions.value.filter((opt) => opt.id === null),
    options_to_delete: deletedOptionIds.value,
  }
  const formData = new FormData()
  formData.append('poll_data', JSON.stringify(pollPayload))
  try {
    const response = await axiosInstance.patch<Post>(`/posts/${props.post.id}/`, formData)
    postsStore.addOrUpdatePosts([response.data])
    isEditing.value = false
  } catch (err: any) {
    localEditError.value = err.response?.data?.detail || 'Failed to update poll.'
  } finally {
    postsStore.addOrUpdatePosts([{ id: props.post.id, isUpdating: false }])
  }
}

async function handleUpdatePost() {
  localEditError.value = null
  postsStore.addOrUpdatePosts([{ id: props.post.id, isUpdating: true }])
  const formData = new FormData()
  if (editContent.value !== (props.post.content || ''))
    formData.append('content', editContent.value)
  try {
    const response = await axiosInstance.patch<Post>(`/posts/${props.post.id}/`, formData)
    postsStore.addOrUpdatePosts([response.data])
    isEditing.value = false
  } catch (err: any) {
    localEditError.value = err.response?.data?.detail || 'Failed to update post.'
  } finally {
    postsStore.addOrUpdatePosts([{ id: props.post.id, isUpdating: false }])
  }
}

function toggleEditMode() {
  isEditing.value = !isEditing.value
  if (isEditing.value) {
    if (props.post.poll) {
      editPollQuestion.value = props.post.poll.question
      editPollOptions.value = props.post.poll.options.map((opt) => ({ id: opt.id, text: opt.text }))
      deletedOptionIds.value = []
    } else {
      editContent.value = props.post.content || ''
      editableMedia.value = [...props.post.media]
    }
    nextTick(() => editTextAreaRef.value?.focus())
  }
}

function cancelEdit() {
  isEditing.value = false
}

async function handleCommentSubmit() {
  if (!newCommentContent.value.trim()) return
  await commentStore.createComment(
    props.post.post_type,
    props.post.object_id,
    newCommentContent.value,
    props.post.id,
  )
  newCommentContent.value = ''
}

async function toggleLike() {
  if (!isAuthenticated.value) return alert('Please login to like posts.')
  await feedStore.toggleLike(props.post.id)
}

async function toggleSave() {
  if (!isAuthenticated.value) return alert('Please login to save posts.')
  showOptionsMenu.value = false
  await feedStore.toggleSavePost(props.post.id)
}

async function handleDeletePost() {
  if (!isOwner.value) return
  if (window.confirm('Are you sure you want to delete this post?')) {
    await feedStore.deletePost(props.post.id)
  }
}

function linkifyContent(text: string | null | undefined): string {
  if (!text) return ''
  const urlRegex =
    /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])|(\bwww\.[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/gi
  const mentionRegex = /@([\w.-]+)/g
  return text
    .replace(
      urlRegex,
      (url) =>
        `<a href="${url.startsWith('www.') ? 'http://' + url : url}" target="_blank" class="text-blue-500 hover:underline">${url}</a>`,
    )
    .replace(
      mentionRegex,
      (match, username) =>
        `<a href="/profile/${username}" class="font-semibold text-blue-600 hover:underline">${match}</a>`,
    )
}

onMounted(() => {
  isMobile.value = window.innerWidth <= 768
  document.addEventListener(
    'click',
    (e) => {
      if (optionsMenuRef.value && !optionsMenuRef.value.contains(e.target as Node))
        showOptionsMenu.value = false
    },
    true,
  )
})

function openMediaModal(index: number) {
  modalMediaIndex.value = index
  showMediaModal.value = true
}
function closeMediaModal() {
  showMediaModal.value = false
}
</script>

<template>
  <div class="post-wrapper" ref="postContainerRef">
    <article
      class="bg-white rounded-2xl shadow-sm border border-gray-100 relative overflow-visible"
      data-cy="post-container"
    >
      <!-- Header -->
      <header class="flex items-start justify-between p-3 lg:p-4">
        <div class="flex items-start flex-1 min-w-0">
          <router-link :to="{ name: 'profile', params: { username: post.author.username } }">
            <img
              :src="
                getAvatarUrl(post.author.picture, post.author.first_name, post.author.last_name)
              "
              class="w-10 h-10 rounded-full object-cover mr-3 bg-gray-200"
            />
          </router-link>
          <div class="min-w-0">
            <div class="flex items-center gap-x-2">
              <router-link
                :to="{ name: 'profile', params: { username: post.author.username } }"
                class="font-bold text-gray-900 hover:underline text-sm lg:text-base"
                >{{ post.author.username }}</router-link
              >
              <template v-if="post.group && !hideGroupContext">
                <span class="text-blue-500 text-xs hidden lg:inline">▶</span>
                <router-link
                  :to="{ name: 'group-detail', params: { slug: post.group.slug } }"
                  class="font-semibold text-gray-500 hover:underline text-xs"
                  >{{ post.group.name }}</router-link
                >
              </template>
            </div>
            <p class="text-xs text-gray-500 mt-0.5">{{ formattedTimestamp }}</p>
          </div>
        </div>

        <!-- Options Menu -->
        <div v-if="isAuthenticated" class="relative" ref="optionsMenuRef">
          <button
            @click.stop="toggleOptionsMenu"
            class="w-8 h-8 flex items-center justify-center rounded-full text-gray-500 hover:bg-gray-100 transition-colors"
            data-cy="post-options-button"
          >
            <FontAwesomeIcon :icon="faEllipsisVertical" />
          </button>
          <div
            v-if="showOptionsMenu"
            class="origin-top-right absolute right-0 mt-2 w-44 rounded-lg shadow-lg bg-white z-50 border border-gray-200 py-1"
          >
            <button
              @click="toggleSave"
              class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 flex items-center gap-2 group"
            >
              <FontAwesomeIcon
                :icon="faBookmark"
                :class="post.is_saved ? 'text-blue-500' : 'text-gray-400'"
              />
              <span>{{ post.is_saved ? 'Unsave' : 'Save' }}</span>
            </button>
            <template v-if="isOwner">
              <button
                @click="handleEditClick"
                class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-green-50 flex items-center gap-2 group"
              >
                <FontAwesomeIcon :icon="faPenToSquare" class="text-green-500" /> Edit
              </button>
              <button
                @click="handleDeleteClick"
                class="w-full text-left px-4 py-2 text-sm text-red-700 hover:bg-red-50 flex items-center gap-2 group"
                data-cy="delete-post-button"
              >
                <FontAwesomeIcon :icon="faTrash" class="text-red-500" /> Delete
              </button>
            </template>
          </div>
        </div>
      </header>

      <!-- Content Section -->
      <div v-if="!isEditing" class="px-4 pb-3">
        <div v-if="post.content && !post.poll">
          <div
            class="text-gray-800 whitespace-pre-wrap break-words text-sm md:text-base leading-relaxed"
            v-html="linkifyContent(post.content)"
          ></div>
        </div>
        <PollDisplay v-if="post.poll" :poll="post.poll" :post-id="post.id" />

        <!-- Media Grid -->
        <div
          v-if="post.media?.length"
          class="mt-3 px-3 md:px-4 grid gap-1 rounded-xl overflow-hidden"
          :class="post.media.length > 1 ? 'grid-cols-2' : 'grid-cols-1'"
        >
          <div
            v-for="(mediaItem, index) in post.media.slice(0, 4)"
            :key="mediaItem.id"
            class="relative bg-gray-100 aspect-square overflow-hidden cursor-pointer"
            @click="openMediaModal(index)"
          >
            <video
              v-if="mediaItem.media_type === 'video'"
              class="w-full h-full object-cover"
              :src="buildMediaUrl(mediaItem.file_url)"
            />
            <img
              v-else
              :src="buildMediaUrl(mediaItem.file_url)"
              class="w-full h-full object-cover"
            />
            <div
              v-if="index === 3 && post.media.length > 4"
              class="absolute inset-0 bg-black/60 flex items-center justify-center text-white font-bold text-xl"
            >
              +{{ post.media.length - 3 }}
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <footer v-if="!isEditing" class="px-3 md:px-4 pt-1 pb-2">
        <div
          class="border-t border-gray-200 pt-2 flex items-center justify-between text-gray-600 mobile-actions-grid"
        >
          <button
            @click="toggleLike"
            class="flex flex-1 flex-col md:flex-row items-center justify-center gap-1 hover:text-blue-500"
            :class="{ 'text-blue-500 font-bold': post.is_liked_by_user }"
            data-cy="like-button"
          >
            <FontAwesomeIcon :icon="faThumbsUp" class="mobile-action-icon" />
            <span class="text-xs md:text-sm font-medium">Like {{ post.like_count || '' }}</span>
          </button>
          <button
            @click="showComments = !showComments"
            class="flex flex-1 flex-col md:flex-row items-center justify-center gap-1 hover:text-[#d97706]"
            :class="{ 'text-[#d97706] font-bold': showComments }"
          >
            <FontAwesomeIcon :icon="faCommentDots" class="mobile-action-icon" />
            <span class="text-xs md:text-sm font-medium"
              >Comment {{ post.comment_count || '' }}</span
            >
          </button>
          <button
            class="flex flex-1 flex-col md:flex-row items-center justify-center gap-1 hover:text-rose-500"
          >
            <FontAwesomeIcon :icon="faRepeat" class="mobile-action-icon" />
            <span class="text-xs md:text-sm font-medium">Repost</span>
          </button>
          <button
            class="flex flex-1 flex-col md:flex-row items-center justify-center gap-1 hover:text-purple-600"
          >
            <FontAwesomeIcon :icon="faPaperPlane" class="mobile-action-icon" />
            <span class="text-xs md:text-sm font-medium">Send</span>
          </button>
        </div>
      </footer>

      <!-- Comments -->
      <transition name="comment-slide">
        <section
          v-if="!isEditing && showComments"
          class="bg-gray-50 border-t border-gray-100 rounded-b-2xl overflow-hidden"
        >
          <div class="p-4 space-y-4 max-h-96 overflow-y-auto" ref="commentsScrollContainer">
            <CommentItem
              v-for="comment in visibleComments"
              :key="comment.id"
              :comment="comment"
              :parentPostType="post.post_type"
              :parentObjectId="post.object_id"
              :parentPostActualId="post.id"
              @report-content="handleCommentReport"
            />
            <div
              v-if="commentsForThisPost.length === 0"
              class="text-center py-4 text-gray-500 text-sm"
            >
              Be the first to comment!
            </div>
          </div>
          <form
            v-if="isAuthenticated"
            @submit.prevent="handleCommentSubmit"
            class="p-3 bg-white border-t border-gray-100 flex items-center gap-3"
          >
            <img
              :src="
                getAvatarUrl(currentUser?.picture, currentUser?.first_name, currentUser?.last_name)
              "
              class="w-8 h-8 rounded-full object-cover"
            />
            <input
              v-model="newCommentContent"
              placeholder="Add a comment..."
              class="flex-1 bg-gray-100 text-sm px-4 py-2 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500"
              data-cy="comment-input"
            />
            <button
              type="submit"
              :disabled="!newCommentContent.trim()"
              class="text-blue-600 font-bold p-2 disabled:opacity-50"
              data-cy="comment-submit-button"
            >
              <FontAwesomeIcon :icon="faPaperPlane" />
            </button>
          </form>
        </section>
      </transition>

      <!-- Edit Modal Overlay -->
      <div
        v-if="isEditing"
        class="fixed inset-0 bg-black/60 z-[10000] flex items-center justify-center p-4 backdrop-blur-sm"
        @click.self="cancelEdit"
      >
        <div
          class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden no-scrollbar"
          @click.stop
        >
          <div class="p-6">
            <h3 class="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
              <FontAwesomeIcon :icon="faPenToSquare" class="text-blue-500" />
              {{ post.poll ? 'Edit Poll' : 'Edit Post' }}
            </h3>
            <div
              v-if="localEditError"
              class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm mb-6 flex items-center gap-2"
            >
              <FontAwesomeIcon :icon="faExclamationCircle" /> {{ localEditError }}
            </div>

            <form v-if="!post.poll" @submit.prevent="handleUpdatePost" class="space-y-4">
              <MentionAutocomplete
                ref="editTextAreaRef"
                v-model="editContent"
                placeholder="Edit your post..."
                :rows="4"
                class="w-full border-gray-200 rounded-xl"
              />
              <div class="flex justify-end gap-3 pt-4 border-t">
                <button
                  type="button"
                  @click="cancelEdit"
                  class="px-6 py-2 border border-gray-300 rounded-lg text-sm font-semibold text-gray-700 hover:bg-gray-50 transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  class="px-6 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 transition-all shadow-md"
                >
                  Save Changes
                </button>
              </div>
            </form>

            <form v-else @submit.prevent="handleUpdatePoll" class="space-y-4">
              <div class="space-y-4 bg-gray-50 p-5 rounded-2xl border border-gray-100">
                <input
                  v-model="editPollQuestion"
                  class="w-full p-3 border border-gray-200 rounded-xl text-sm"
                  placeholder="Poll Question"
                />
                <div
                  v-for="(option, index) in editPollOptions"
                  :key="index"
                  class="flex items-center gap-2 mb-2"
                >
                  <input
                    v-model="option.text"
                    class="flex-grow p-3 border border-gray-200 rounded-xl text-sm"
                    :placeholder="`Option ${index + 1}`"
                    maxlength="100"
                  />
                  <button
                    @click.prevent="removePollOptionFromEdit(index)"
                    class="text-gray-400 hover:text-red-500 p-2"
                  >
                    <FontAwesomeIcon :icon="faXmark" />
                  </button>
                </div>
                <button
                  v-if="editPollOptions.length < 5"
                  @click.prevent="addPollOptionToEdit"
                  class="mt-2 text-sm text-blue-600 font-bold hover:text-blue-700 flex items-center gap-1"
                >
                  <FontAwesomeIcon :icon="faPlus" class="w-3" /> Add Option
                </button>
              </div>
              <div class="flex justify-end gap-3 pt-6">
                <button
                  type="button"
                  @click="cancelEdit"
                  class="px-6 py-2 border border-gray-300 rounded-lg text-sm font-semibold text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  class="px-6 py-2 bg-purple-600 text-white rounded-lg text-sm font-semibold hover:bg-purple-700 transition-all shadow-md"
                >
                  Update Poll
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </article>
    <ReportFormModal
      :is-open="isReportModalOpen"
      :target="reportTarget"
      @close="isReportModalOpen = false"
    />
  </div>
</template>

<style scoped>
.post-wrapper {
  margin-bottom: 12px;
  transition: all 0.3s ease;
}
.word-break-fix {
  word-break: break-word;
  overflow-wrap: break-word;
}
@media (max-width: 768px) {
  .mobile-actions-grid {
    display: flex !important;
    width: 100%;
    justify-content: space-between;
    align-items: center;
  }
  .mobile-action-item {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }
  .mobile-action-icon {
    width: 18px;
    height: 18px;
    margin-bottom: 2px;
  }
}
.comment-slide-enter-active,
.comment-slide-leave-active {
  transition: all 0.3s ease;
  max-height: 800px;
}
.comment-slide-enter-from,
.comment-slide-leave-to {
  max-height: 0;
  opacity: 0;
}
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
</style>
