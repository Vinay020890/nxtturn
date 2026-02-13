<script setup lang="ts">
import { watch, computed, ref, onUnmounted, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGroupStore } from '@/stores/group'
import { useAuthStore } from '@/stores/auth'
import { usePostsStore } from '@/stores/posts'
import { useInfiniteScroll } from '@/composables/useInfiniteScroll'
import { storeToRefs } from 'pinia'
import { useToast } from 'vue-toastification'
import CreatePostForm from '@/components/CreatePostForm.vue'
import PostItem from '@/components/PostItem.vue'
import TransferOwnershipModal from '@/components/TransferOwnershipModal.vue'
import EditGroupModal from '@/components/EditGroupModal.vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import {
  faInfoCircle,
  faNewspaper,
  faUsers,
  faUser,
  faCalendar,
  faLock,
  faUsers as faUsersGroup,
  faEdit,
  faUserClock,
  faUserGroup,
  faRightFromBracket,
  faTrash,
  faCamera,
  faTimes,
  faImage,
} from '@fortawesome/free-solid-svg-icons'

const route = useRoute()
const router = useRouter()
const groupStore = useGroupStore()
const authStore = useAuthStore()
const postsStore = usePostsStore()
const toast = useToast()

const isTransferModalOpen = ref(false)
const isEditModalOpen = ref(false)

// Add description expanded state
const isDescriptionExpanded = ref(false)
const descriptionRef = ref<HTMLParagraphElement | null>(null)
const isDescriptionOverflowing = ref(false)

// Tab state
const activeTab = ref<'about' | 'feed' | 'members'>('feed')

const {
  currentGroup,
  isLoadingGroup,
  groupError,
  isJoiningLeaving,
  joinLeaveError,
  isLoadingGroupPosts,
  isDeletingGroup,
  isTransferringOwnership,
  isUpdatingGroup,
} = storeToRefs(groupStore)

const { isAuthenticated, currentUser } = storeToRefs(authStore)
const loadMoreGroupPostsTrigger = ref<HTMLElement | null>(null)

// Background image upload state
const isUploadingBackground = ref(false)
const backgroundFileInput = ref<HTMLInputElement | null>(null)

// Local state for background image
const groupBackgroundImage = ref<string | null>(null)

const groupSlug = computed(() => route.params.slug as string)
// Group created date label (supports multiple backend keys)
const createdAtLabel = computed(() => {
  const g: any = currentGroup.value as any
  const raw =
    g?.created_at ??
    g?.createdAt ??
    g?.created_on ??
    g?.createdOn ??
    g?.created ??
    g?.created_date ??
    null

  if (!raw) return ''
  const d = new Date(raw)
  if (Number.isNaN(d.getTime())) return String(raw)

  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(d)
})

const privacyLabel = computed(() => {
  const g: any = currentGroup.value as any
  const lvl = (g?.privacy_level ?? g?.privacy ?? '').toString().toLowerCase()
  if (lvl === 'private') return 'Private'
  if (lvl === 'public') return 'Public'
  if (typeof g?.is_private === 'boolean') return g.is_private ? 'Private' : 'Public'
  return lvl ? lvl.charAt(0).toUpperCase() + lvl.slice(1) : ''
})
// Members list for Transfer Ownership modal
// (backend may provide members under different keys depending on serializer)
const transferOwnershipMembers = computed(() => {
  const g: any = currentGroup.value as any
  return (
    g?.members ||
    g?.group_members ||
    g?.memberships ||
    g?.member_list ||
    g?.members_list ||
    g?.users ||
    []
  )
})

// Members list for Members tab display
const membersForDisplay = computed(() => {
  const g: any = currentGroup.value as any
  const list =
    g?.member_list ||
    g?.members_list ||
    g?.members ||
    g?.group_members ||
    g?.memberships ||
    g?.users ||
    []

  // Normalize common backend shapes into { id, username, first_name, last_name, picture }
  const normalized = (Array.isArray(list) ? list : []).map((m: any) => {
    const u = m?.user || m?.member || m?.profile || m
    return {
      id: Number(u?.id ?? m?.id ?? 0),
      username: u?.username ?? u?.user_name ?? u?.handle ?? u?.slug ?? m?.username ?? 'Unknown',
      first_name: u?.first_name ?? u?.firstName ?? m?.first_name ?? '',
      last_name: u?.last_name ?? u?.lastName ?? m?.last_name ?? '',
      picture: u?.picture ?? u?.avatar ?? u?.profile_picture ?? m?.picture ?? null,
      role: m?.role || m?.membership_status || m?.type || 'member',
    }
  })

  // Deduplicate by id/username
  const seen = new Set<string>()
  const unique = normalized.filter((m: any) => {
    const k = String(m.id || '') + '|' + String(m.username || '')
    if (seen.has(k)) return false
    seen.add(k)
    return true
  })

  return unique
})

const otherMembers = computed(() => {
  const creatorId = Number((currentGroup.value as any)?.creator?.id ?? 0)
  const creatorUsername = (currentGroup.value as any)?.creator?.username
  return membersForDisplay.value.filter((m: any) => {
    if (creatorId && m.id === creatorId) return false
    if (creatorUsername && m.username === creatorUsername) return false
    return true
  })
})

const groupCreatorId = computed(() => {
  const g: any = currentGroup.value as any
  return Number(g?.creator?.id ?? g?.creator_id ?? g?.owner?.id ?? g?.owner_id ?? 0)
})

const groupPosts = computed(() => {
  const ids = groupStore.postIdsByGroupSlug[groupSlug.value] || []
  return postsStore.getPostsByIds(ids)
})

const groupPostsNextCursor = computed(() => {
  return groupStore.nextCursorByGroupSlug[groupSlug.value]
})

const isCreator = computed(() => currentGroup.value?.membership_status === 'creator')
const isMember = computed(() =>
  ['creator', 'member'].includes(currentGroup.value?.membership_status || ''),
)
const hasPendingRequest = computed(() => currentGroup.value?.membership_status === 'pending')

/* =========================================================
   ✅ EMOJI-SAFE "FIRST CHARACTER" (GRAPHEME) HELPERS
   - Fixes: emoji / flags / combined emojis not showing
   - Does NOT change any functionality, only display text
   ========================================================= */
function firstGrapheme(text = ''): string {
  const s = (text || '').trim()
  if (!s) return ''

  const AnyIntl = Intl as any
  if (AnyIntl?.Segmenter) {
    const seg = new AnyIntl.Segmenter(undefined, { granularity: 'grapheme' })
    const it = seg.segment(s)[Symbol.iterator]()
    return it.next()?.value?.segment || s[0]
  }

  // Fallback (still better than charAt for emojis)
  return Array.from(s)[0] || ''
}

function profileBadgeText(name = ''): string {
  const g = firstGrapheme(name)
  if (!g) return 'G'
  // Uppercase only if it's a single English letter
  return /^[A-Za-z]$/.test(g) ? g.toUpperCase() : g
}
/* ======================= END HELPERS ======================= */

// Format date function
function formatDate(dateString: string) {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// Check if description needs truncation
function checkDescriptionOverflow() {
  if (descriptionRef.value && currentGroup.value?.description) {
    const lineHeight = 24
    const maxHeight = lineHeight * 2
    isDescriptionOverflowing.value = descriptionRef.value.scrollHeight > maxHeight
  }
}

// Toggle description expansion
function toggleDescription() {
  isDescriptionExpanded.value = !isDescriptionExpanded.value
}

// Reset expanded state when group changes
watch(currentGroup, () => {
  isDescriptionExpanded.value = false
  // Reset background image when group changes
  groupBackgroundImage.value = null
  nextTick(() => {
    checkDescriptionOverflow()
  })
})

async function loadGroupData() {
  const slug = route.params.slug as string
  if (slug) {
    groupStore.joinLeaveError = null
    await groupStore.fetchGroupDetails(slug)

    const canViewPosts =
      groupStore.currentGroup?.membership_status === 'member' ||
      groupStore.currentGroup?.membership_status === 'creator' ||
      groupStore.currentGroup?.privacy_level === 'public'

    if (canViewPosts) {
      groupStore.refreshGroupPosts(slug)
    }
  }
}

watch(
  () => route.params.slug,
  (newSlug, oldSlug) => {
    if (newSlug && newSlug !== oldSlug) {
      groupStore.resetCurrentGroupState()
      loadGroupData()
    }
  },
  { immediate: true },
)

onMounted(() => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
  nextTick(() => {
    checkDescriptionOverflow()
  })
})

onUnmounted(() => {
  document.removeEventListener('click', closeOnClickOutside, true)
  groupStore.resetCurrentGroupState()
  // Clean up object URLs
  if (groupBackgroundImage.value) {
    URL.revokeObjectURL(groupBackgroundImage.value)
  }
})

const joinButtonText = computed(() => {
  if (isJoiningLeaving.value) return 'Processing...'
  switch (currentGroup.value?.membership_status) {
    case 'pending':
      return 'Request Sent'
    case 'blocked':
      return 'Blocked'
    case 'member':
    case 'creator':
      return 'Leave Group'
    default:
      return currentGroup.value?.privacy_level === 'private' ? 'Request to Join' : 'Join Group'
  }
})

const joinButtonClass = computed(() => {
  switch (currentGroup.value?.membership_status) {
    case 'pending':
      return 'bg-yellow-500 text-white cursor-not-allowed'
    case 'blocked':
      return 'bg-red-600 text-white cursor-not-allowed'
    case 'member':
    case 'creator':
      return 'bg-gray-200 text-gray-800 hover:bg-gray-300'
    default:
      return 'bg-blue-600 text-white hover:bg-blue-700'
  }
})

const isJoinButtonDisabled = computed(() => {
  if (isJoiningLeaving.value) return true
  return ['pending', 'blocked'].includes(currentGroup.value?.membership_status || '')
})

async function handleMembershipAction() {
  if (!currentGroup.value || (isJoinButtonDisabled.value && !isMember.value)) return

  if (!isMember.value) {
    await groupStore.joinGroup(currentGroup.value.slug)
    return
  }

  if (isCreator.value) {
    if (currentGroup.value.member_count > 1) {
      alert('As the group creator, you must transfer ownership before you can leave.')
      isTransferModalOpen.value = true
      showOptionsMenu.value = false
      return
    } else {
      alert('As the sole member, leaving the group will permanently delete it.')
      await handleDeleteGroup()
      return
    }
  }

  await groupStore.leaveGroup(currentGroup.value.slug)
}

const showOptionsMenu = ref(false)
const optionsMenuRef = ref<HTMLDivElement | null>(null)
const threeDotsButtonRef = ref<HTMLButtonElement | null>(null)

useInfiniteScroll(
  loadMoreGroupPostsTrigger,
  groupStore.fetchNextPageOfGroupPosts,
  groupPostsNextCursor,
)

function toggleOptionsMenu() {
  showOptionsMenu.value = !showOptionsMenu.value
  // Remove focus from button when closing menu to remove blue ring
  if (!showOptionsMenu.value && threeDotsButtonRef.value) {
    threeDotsButtonRef.value.blur()
  }
}

const closeOnClickOutside = (event: MouseEvent) => {
  if (optionsMenuRef.value && !optionsMenuRef.value.contains(event.target as Node)) {
    showOptionsMenu.value = false
    // Remove focus from button when clicking outside
    if (threeDotsButtonRef.value) {
      threeDotsButtonRef.value.blur()
    }
  }
}

watch(showOptionsMenu, (isOpen) => {
  if (isOpen) {
    document.addEventListener('click', closeOnClickOutside, true)
  } else {
    document.removeEventListener('click', closeOnClickOutside, true)
    // Ensure focus is removed when menu closes
    if (threeDotsButtonRef.value) {
      threeDotsButtonRef.value.blur()
    }
  }
})

function handleTransferOwnership() {
  showOptionsMenu.value = false
  isTransferModalOpen.value = true
  // Remove focus from button
  if (threeDotsButtonRef.value) {
    threeDotsButtonRef.value.blur()
  }
}

async function handleDeleteGroup() {
  if (!currentGroup.value) return
  if (
    confirm(`Are you sure you want to permanently delete the group "${currentGroup.value.name}"?`)
  ) {
    const success = await groupStore.deleteGroup(currentGroup.value.slug)
    if (success) {
      router.push({ name: 'group-list' })
    }
  }
}

function openEditModal() {
  showOptionsMenu.value = false
  isEditModalOpen.value = true
  // Remove focus from button
  if (threeDotsButtonRef.value) {
    threeDotsButtonRef.value.blur()
  }
}

async function handleConfirmTransfer(newOwnerId: number) {
  if (!currentGroup.value) return
  const success = await groupStore.transferOwnership(currentGroup.value.slug, newOwnerId)
  if (success) {
    isTransferModalOpen.value = false
  }
}

async function handleUpdateGroup(data: { name: string; description?: string }) {
  if (!currentGroup.value) return
  const success = await groupStore.updateGroupDetails(currentGroup.value.slug, data)
  if (success) {
    isEditModalOpen.value = false
    toast.success('Group details updated successfully!')
  } else {
    toast.error(groupStore.updateGroupError || 'Failed to update group details.')
  }
}

// Background image upload functions
function triggerBackgroundUpload() {
  if (backgroundFileInput.value) {
    backgroundFileInput.value.click()
    showOptionsMenu.value = false
  }
}

async function handleBackgroundUpload(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files || !input.files[0]) return

  const file = input.files[0]

  // Validate file type
  const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!validTypes.includes(file.type)) {
    toast.error('Please select a valid image file (JPEG, PNG, GIF, or WebP)')
    return
  }

  // Validate file size (max 5MB)
  const maxSize = 5 * 1024 * 1024 // 5MB
  if (file.size > maxSize) {
    toast.error('Image size must be less than 5MB')
    return
  }

  isUploadingBackground.value = true

  try {
    // Clean up previous object URL if exists
    if (groupBackgroundImage.value) {
      URL.revokeObjectURL(groupBackgroundImage.value)
    }

    const objectUrl = URL.createObjectURL(file)
    groupBackgroundImage.value = objectUrl

    // Simulate upload delay
    await new Promise((resolve) => setTimeout(resolve, 1000))

    toast.success('Background image uploaded successfully!')
  } catch (error) {
    console.error('Error uploading background image:', error)
    toast.error('Failed to upload background image. Please try again.')
  } finally {
    isUploadingBackground.value = false
    // Reset the file input
    if (input) input.value = ''
  }
}

async function removeBackgroundImage() {
  if (!groupBackgroundImage.value) return

  if (!confirm('Are you sure you want to remove the background image?')) {
    return
  }

  isUploadingBackground.value = true
  showOptionsMenu.value = false

  try {
    // Simulate API call delay
    await new Promise((resolve) => setTimeout(resolve, 800))

    // Remove the background image
    if (groupBackgroundImage.value) {
      URL.revokeObjectURL(groupBackgroundImage.value)
      groupBackgroundImage.value = null
    }

    toast.success('Background image removed successfully!')
  } catch (error) {
    console.error('Error removing background image:', error)
    toast.error('Failed to remove background image. Please try again.')
  } finally {
    isUploadingBackground.value = false
  }
}
</script>

<template>
  <!-- Increased main container width -->
  <!-- Mobile safe bottom padding so content won't hide behind bottom navbar -->
  <div class="max-w-6xl mx-auto px-0 sm:px-0 pb-6 sm:pb-0">
    <div v-if="isLoadingGroup && !currentGroup" class="text-center py-10 text-gray-500">
      <p>Loading group...</p>
    </div>
    <div v-else-if="groupError" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4">
      <p class="font-bold">Error</p>
      <p>{{ groupError }}</p>
    </div>
    <div v-else-if="currentGroup">
      <!-- Group Header - Increased width -->
      <header class="bg-white rounded-lg shadow-md mb-6 overflow-hidden">
        <!-- Background Photo Area -->
        <div
          class="h-40 relative"
          :class="groupBackgroundImage ? '' : 'bg-gradient-to-r from-blue-500 to-purple-600'"
          :style="
            groupBackgroundImage
              ? {
                  backgroundImage: `url(${groupBackgroundImage})`,
                  backgroundSize: 'cover',
                  backgroundPosition: 'center',
                }
              : {}
          "
        >
          <!-- 3-dot menu for creators -->
          <div
            v-if="isAuthenticated && isCreator"
            class="absolute top-4 right-4 z-10"
            ref="optionsMenuRef"
          >
            <button
              ref="threeDotsButtonRef"
              data-cy="group-options-button"
              @click.stop="toggleOptionsMenu"
              class="p-2 rounded-full bg-white/90 hover:bg-white text-gray-700 focus:outline-none focus:ring-0 shadow-md"
              :class="showOptionsMenu ? 'ring-2 ring-blue-500 ring-offset-2' : ''"
            >
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"
                ></path>
              </svg>
            </button>
            <div
              v-if="showOptionsMenu"
              class="origin-top-right absolute right-0 mt-2 w-48 sm:w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-10"
            >
              <div class="py-1" role="menu" aria-orientation="vertical">
                <a
                  href="#"
                  @click.prevent="openEditModal"
                  class="flex items-center gap-3 text-gray-700 px-4 py-2.5 text-sm hover:bg-gray-100"
                  role="menuitem"
                >
                  <FontAwesomeIcon :icon="faEdit" class="w-4 h-4 text-blue-500" />
                  <span>Edit Group</span>
                </a>
                <router-link
                  :to="{ name: 'group-requests', params: { slug: currentGroup.slug } }"
                  class="flex items-center gap-3 text-gray-700 px-4 py-2.5 text-sm hover:bg-gray-100"
                  role="menuitem"
                >
                  <FontAwesomeIcon :icon="faUserClock" class="w-4 h-4 text-amber-500" />
                  <span>Manage Requests</span>
                </router-link>
                <a
                  href="#"
                  @click.prevent="triggerBackgroundUpload"
                  class="flex items-center gap-3 text-gray-700 px-4 py-2.5 text-sm hover:bg-gray-100"
                  role="menuitem"
                  :disabled="isUploadingBackground"
                >
                  <FontAwesomeIcon :icon="faImage" class="w-4 h-4 text-indigo-500" />
                  <span>{{ groupBackgroundImage ? 'Change Background' : 'Add Background' }}</span>
                </a>
                <a
                  v-if="groupBackgroundImage"
                  href="#"
                  @click.prevent="removeBackgroundImage"
                  class="flex items-center gap-3 text-gray-700 px-4 py-2.5 text-sm hover:bg-gray-100"
                  role="menuitem"
                  :disabled="isUploadingBackground"
                >
                  <FontAwesomeIcon :icon="faTimes" class="w-4 h-4 text-gray-500" />
                  <span>Remove Background</span>
                </a>
                <a
                  href="#"
                  @click.prevent="handleTransferOwnership"
                  class="flex items-center gap-3 text-gray-700 px-4 py-2.5 text-sm hover:bg-gray-100"
                  role="menuitem"
                >
                  <FontAwesomeIcon :icon="faUserGroup" class="w-4 h-4 text-purple-500" />
                  <span>Transfer Ownership</span>
                </a>
                <a
                  href="#"
                  @click.prevent="handleMembershipAction"
                  class="flex items-center gap-3 text-gray-700 px-4 py-2.5 text-sm hover:bg-gray-100"
                  role="menuitem"
                >
                  <FontAwesomeIcon :icon="faRightFromBracket" class="w-4 h-4 text-green-500" />
                  <span>Leave Group</span>
                </a>
                <a
                  href="#"
                  @click.prevent="handleDeleteGroup"
                  class="flex items-center gap-3 text-red-700 px-4 py-2.5 text-sm hover:bg-red-50"
                  role="menuitem"
                >
                  <FontAwesomeIcon :icon="faTrash" class="w-4 h-4 text-red-500" />
                  <span>Delete Group</span>
                </a>
              </div>
            </div>
          </div>

          <!-- 3-dot menu for regular members -->
          <div
            v-if="isAuthenticated && isMember && !isCreator"
            class="absolute top-4 right-4 z-10"
            ref="optionsMenuRef"
          >
            <button
              ref="threeDotsButtonRef"
              data-cy="group-options-button"
              @click.stop="toggleOptionsMenu"
              class="p-2 rounded-full bg-white/90 hover:bg-white text-gray-700 focus:outline-none focus:ring-0 shadow-md"
              :class="showOptionsMenu ? 'ring-2 ring-blue-500 ring-offset-2' : ''"
            >
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"
                ></path>
              </svg>
            </button>
            <div
              v-if="showOptionsMenu"
              class="origin-top-right absolute right-0 mt-2 w-48 sm:w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-10"
            >
              <div class="py-1" role="menu" aria-orientation="vertical">
                <a
                  href="#"
                  data-cy="leave-group-button"
                  @click.prevent="handleMembershipAction"
                  class="flex items-center gap-3 text-gray-700 px-4 py-2.5 text-sm hover:bg-gray-100"
                  role="menuitem"
                >
                  <FontAwesomeIcon :icon="faRightFromBracket" class="w-4 h-4 text-green-500" />
                  <span>Leave Group</span>
                </a>
              </div>
            </div>
          </div>

          <!-- Overlay to ensure text readability when background image is present -->
          <div v-if="groupBackgroundImage" class="absolute inset-0 bg-black/20"></div>

          <!-- Hidden file input for background upload -->
          <input
            ref="backgroundFileInput"
            type="file"
            accept="image/jpeg,image/png,image/gif,image/webp"
            class="hidden"
            @change="handleBackgroundUpload"
            :disabled="isUploadingBackground"
          />
        </div>

        <!-- Content Area with Profile Photo -->
        <div class="relative px-6 sm:px-8 pb-6">
          <!-- Profile Photo -->
          <div class="absolute -top-12 left-6 sm:left-8">
            <div
              class="w-24 h-24 sm:w-28 sm:h-28 rounded-full border-4 border-white bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center shadow-lg"
            >
              <span class="text-white text-3xl sm:text-4xl font-bold leading-none">
                {{ profileBadgeText(currentGroup.name) }}
              </span>
            </div>
          </div>

          <!-- Group Info -->
          <div class="pt-20 sm:pt-16">
            <!-- Group Name and Slug -->
            <div class="mb-4">
              <h1
                data-cy="group-name-header"
                class="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 break-words"
              >
                {{ currentGroup.name }}
              </h1>
              <p class="text-sm text-gray-500 mt-2 break-words">@{{ currentGroup.slug }}</p>
            </div>

            <!-- Description with Show More functionality -->
            <div class="mb-5 text-gray-600">
              <div
                ref="descriptionRef"
                :class="[
                  'transition-all duration-200 break-words text-base',
                  !isDescriptionExpanded && isDescriptionOverflowing
                    ? 'line-clamp-2 overflow-hidden'
                    : '',
                ]"
              >
                <p class="whitespace-pre-wrap">
                  {{ currentGroup.description || 'No description provided.' }}
                </p>
              </div>
              <button
                v-if="isDescriptionOverflowing"
                @click="toggleDescription"
                class="text-blue-600 hover:text-blue-800 text-sm font-medium mt-2 focus:outline-none"
              >
                {{ isDescriptionExpanded ? 'Show less' : 'Show more' }}
              </button>
            </div>

            <!-- Group Metadata and Join Button -->
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <!-- Metadata with creator profile photo -->
              <div
                class="text-sm text-gray-500 flex flex-col gap-1 sm:flex-row sm:items-center sm:gap-2"
              >
                <!-- Created by -->
                <div class="flex items-center min-w-0">
                  <span class="whitespace-nowrap mr-2">Created by:</span>
                  <router-link
                    v-if="currentGroup.creator && currentGroup.creator.username"
                    :to="{ name: 'profile', params: { username: currentGroup.creator.username } }"
                    class="font-semibold hover:underline flex items-center gap-2 min-w-0"
                  >
                    <!-- Creator's profile photo -->
                    <div class="flex items-center min-w-0">
                      <div
                        v-if="currentGroup.creator.picture"
                        class="w-6 h-6 rounded-full overflow-hidden mr-2 shrink-0"
                      >
                        <img
                          :src="currentGroup.creator.picture"
                          :alt="currentGroup.creator.username"
                          class="w-full h-full object-cover"
                        />
                      </div>
                      <div
                        v-else
                        class="w-6 h-6 rounded-full bg-gray-300 flex items-center justify-center mr-2 shrink-0"
                      >
                        <span class="text-xs font-medium text-gray-700 leading-none">
                          {{ profileBadgeText(currentGroup.creator.username) }}
                        </span>
                      </div>
                      <span class="truncate">{{ currentGroup.creator.username }}</span>
                    </div>
                  </router-link>
                </div>
              </div>

              <!-- Join button for NON-MEMBERS ONLY -->
              <div v-if="isAuthenticated && currentGroup && !isMember">
                <button
                  data-cy="group-membership-button"
                  @click="handleMembershipAction()"
                  :disabled="isJoinButtonDisabled"
                  :class="[
                    'px-8 py-3 rounded-full font-semibold transition-colors duration-200 whitespace-nowrap',
                    joinButtonClass,
                    isJoiningLeaving ? 'opacity-50' : '',
                  ]"
                >
                  {{ joinButtonText }}
                </button>
              </div>
            </div>

            <!-- Error message -->
            <div
              v-if="joinLeaveError"
              class="bg-red-100 border-l-4 border-red-500 text-red-700 p-3 text-sm mt-4 rounded"
            >
              <p>{{ joinLeaveError }}</p>
            </div>
          </div>
        </div>
      </header>

      <!-- Tabs Navigation - Mobile: icon above text, Desktop: icon left of text -->
      <!-- Reduced space before & after tabs -->
      <div class="-mt-1 mb-3">
        <div class="border-b border-gray-200">
          <nav class="flex" aria-label="Tabs">
            <!-- About Tab (Soft Blue) -->
            <button
              @click="activeTab = 'about'"
              :class="[
                'group flex-1 flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-2 py-3 px-2 sm:px-4 font-medium text-xs sm:text-sm transition-all duration-200 rounded-t-lg relative',
                activeTab === 'about'
                  ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-500 shadow-sm'
                  : 'bg-gray-50 text-gray-600 hover:bg-blue-50/50 hover:text-blue-600',
              ]"
            >
              <div class="flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-2">
                <font-awesome-icon
                  :icon="faInfoCircle"
                  class="w-4 h-4 sm:w-4 sm:h-4 transition-colors duration-200 mb-1 sm:mb-0"
                  :class="
                    activeTab === 'about'
                      ? 'text-blue-600'
                      : 'text-gray-500 group-hover:text-blue-500'
                  "
                />
                <span>About</span>
              </div>
            </button>

            <!-- Group Feed Tab (Soft Green) -->
            <button
              @click="activeTab = 'feed'"
              :class="[
                'group flex-1 flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-2 py-3 px-2 sm:px-4 font-medium text-xs sm:text-sm transition-all duration-200 rounded-t-lg relative',
                activeTab === 'feed'
                  ? 'bg-green-50 text-green-700 border-b-2 border-green-500 shadow-sm'
                  : 'bg-gray-50 text-gray-600 hover:bg-green-50/50 hover:text-green-600',
              ]"
            >
              <div class="flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-2">
                <font-awesome-icon
                  :icon="faNewspaper"
                  class="w-4 h-4 sm:w-4 sm:h-4 transition-colors duration-200 mb-1 sm:mb-0"
                  :class="
                    activeTab === 'feed'
                      ? 'text-green-600'
                      : 'text-gray-500 group-hover:text-green-500'
                  "
                />
                <span>Group Feed</span>
              </div>
            </button>

            <!-- Members Tab (Soft Purple) -->
            <button
              @click="activeTab = 'members'"
              :class="[
                'group flex-1 flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-2 py-3 px-2 sm:px-4 font-medium text-xs sm:text-sm transition-all duration-200 rounded-t-lg relative',
                activeTab === 'members'
                  ? 'bg-purple-50 text-purple-700 border-b-2 border-purple-500 shadow-sm'
                  : 'bg-gray-50 text-gray-600 hover:bg-purple-50/50 hover:text-purple-600',
              ]"
            >
              <div class="flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-2">
                <font-awesome-icon
                  :icon="faUsers"
                  class="w-4 h-4 sm:w-4 sm:h-4 transition-colors duration-200 mb-1 sm:mb-0"
                  :class="
                    activeTab === 'members'
                      ? 'text-purple-600'
                      : 'text-gray-500 group-hover:text-purple-500'
                  "
                />
                <span>Members</span>
              </div>
            </button>
          </nav>
        </div>
      </div>

      <!-- Tab Content -->
      <div>
        <!-- About Tab - Increased width -->
        <div v-if="activeTab === 'about'" class="bg-white rounded-lg shadow-md p-5">
          <div class="flex items-center gap-3 mb-6">
            <div
              class="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0"
            >
              <font-awesome-icon :icon="faInfoCircle" class="w-6 h-6 text-blue-600" />
            </div>
            <h2 class="text-2xl font-semibold text-gray-800">Group Information</h2>
          </div>

          <!-- Grid layout for group info items -->
          <div class="grid grid-cols-1 gap-3 mb-4">
            <!-- Member Count -->
            <div
              class="flex items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors duration-200"
            >
              <div
                class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center mr-4 flex-shrink-0"
              >
                <font-awesome-icon :icon="faUsersGroup" class="w-5 h-5 text-blue-600" />
              </div>
              <div class="flex-1 min-w-0 flex items-center justify-between">
                <div class="min-w-0">
                  <span class="text-base font-medium text-gray-900 truncate block">Members</span>
                  <p class="text-sm text-gray-500 mt-1 truncate">Total group members</p>
                </div>
                <div class="ml-3 flex items-center justify-center">
                  <span
                    class="inline-flex items-center justify-center px-3 py-1 rounded-full bg-blue-100 text-blue-700 text-sm font-semibold leading-none"
                  >
                    {{ currentGroup.member_count }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Privacy Status -->
            <div
              class="flex items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors duration-200"
            >
              <div
                class="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center mr-4 flex-shrink-0"
              >
                <font-awesome-icon :icon="faLock" class="w-5 h-5 text-purple-600" />
              </div>
              <div class="flex-1 min-w-0 flex items-center justify-between">
                <div class="min-w-0">
                  <span class="text-base font-medium text-gray-900 truncate block">Privacy</span>
                  <p class="text-sm text-gray-500 mt-1 truncate">
                    {{
                      currentGroup.privacy_level === 'private' ? 'Members only' : 'Anyone can view'
                    }}
                  </p>
                </div>
                <div class="ml-3 flex items-center justify-center">
                  <span
                    class="inline-flex items-center justify-center px-3 py-1 rounded-full bg-purple-100 text-purple-700 text-sm font-semibold leading-none"
                  >
                    {{ currentGroup.privacy_level === 'private' ? 'Private' : 'Public' }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Created By -->
            <div
              class="flex items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors duration-200"
            >
              <div
                class="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center mr-4 flex-shrink-0"
              >
                <div
                  v-if="currentGroup.creator.picture"
                  class="w-10 h-10 rounded-full overflow-hidden"
                >
                  <img
                    :src="currentGroup.creator.picture"
                    :alt="currentGroup.creator.username"
                    class="w-full h-full object-cover"
                  />
                </div>
                <div
                  v-else
                  class="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center"
                >
                  <font-awesome-icon :icon="faUser" class="w-5 h-5 text-white" />
                </div>
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex flex-col">
                  <span class="text-base font-medium text-gray-900 truncate">Created by</span>
                  <router-link
                    v-if="currentGroup.creator && currentGroup.creator.username"
                    :to="{ name: 'profile', params: { username: currentGroup.creator.username } }"
                    class="text-base text-blue-600 hover:underline font-medium truncate mt-1"
                  >
                    {{ currentGroup.creator.username }}
                  </router-link>
                </div>
                <p class="text-sm text-gray-500 mt-1 truncate">
                  {{ currentGroup.creator.first_name }} {{ currentGroup.creator.last_name }}
                </p>
              </div>
            </div>

            <!-- Group Created -->
            <div
              class="flex items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors duration-200"
            >
              <div
                class="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center mr-4 flex-shrink-0"
              >
                <font-awesome-icon :icon="faCalendar" class="w-5 h-5 text-amber-600" />
              </div>
              <div class="flex-1 min-w-0 flex items-center justify-between">
                <div class="min-w-0">
                  <span class="text-base font-medium text-gray-900 truncate block"
                    >Group Created</span
                  >
                  <p class="text-sm text-gray-500 mt-1 truncate">Creation date</p>
                </div>
                <div class="ml-3 flex items-center justify-center">
                  <span
                    class="inline-flex items-center justify-center px-3 py-1 rounded-full bg-amber-100 text-amber-700 text-sm font-semibold leading-none"
                  >
                    {{ createdAtLabel || 'N/A' }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Group Description (if exists) -->
          <div v-if="currentGroup.description" class="mt-6 pt-6 border-t border-gray-100">
            <div class="flex items-center gap-3 mb-4">
              <div
                class="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0"
              >
                <font-awesome-icon :icon="faInfoCircle" class="w-6 h-6 text-green-600" />
              </div>
              <h3 class="text-xl font-semibold text-gray-800">About This Group</h3>
            </div>
            <div class="bg-gray-50 rounded-lg p-5 max-h-96 overflow-y-auto">
              <p class="text-gray-600 whitespace-pre-wrap leading-relaxed break-words">
                {{ currentGroup.description }}
              </p>
            </div>
          </div>
        </div>

        <!-- Group Feed Tab -->
        <div v-if="activeTab === 'feed'">
          <!-- Create Post Form for Members -->
          <!-- Small gap (not joint, not too large) between create post and posts -->
          <div v-if="isMember" class="mb-3">
            <CreatePostForm :group-slug="currentGroup.slug" />
          </div>

          <!-- Non-member message -->
          <div
            v-else-if="isAuthenticated && !isMember"
            class="bg-white p-8 rounded-lg shadow-md mb-8 text-center text-gray-500"
          >
            <p v-if="currentGroup.privacy_level === 'private'">
              You must be a member to view and create posts in this private group.
            </p>
            <p v-else>You must join this group to create posts.</p>
            <p v-if="hasPendingRequest" class="mt-6 text-yellow-600">
              Your request to join is pending approval.
            </p>
          </div>

          <!-- Non-authenticated message -->
          <div
            v-else-if="!isAuthenticated"
            class="bg-white p-8 rounded-lg shadow-md mb-8 text-center text-gray-500"
          >
            <p>Please log in to join this group and create posts.</p>
          </div>

          <!-- Group Feed Posts -->
          <div>
            <div v-if="groupPosts.length > 0" class="space-y-6">
              <PostItem
                v-for="post in groupPosts"
                :key="post.id"
                :post="post"
                :hide-group-context="true"
              />
            </div>
            <div
              v-else-if="!isLoadingGroupPosts && groupPosts.length === 0"
              class="bg-white p-8 rounded-lg shadow-md text-center text-gray-500"
            >
              <p v-if="!isMember && currentGroup.privacy_level === 'private'">
                Content is hidden for non-members.
              </p>
              <p v-else>No posts in this group yet. Be the first to create one!</p>
            </div>
            <div v-if="groupPostsNextCursor" ref="loadMoreGroupPostsTrigger" class="h-10"></div>
            <div
              v-if="isLoadingGroupPosts && groupPosts.length > 0"
              class="text-center p-6 text-gray-500"
            >
              Loading more posts...
            </div>
          </div>
        </div>

        <!-- Members Tab -->
        <div v-if="activeTab === 'members'" class="bg-white rounded-lg shadow-md">
          <!-- Members List -->
          <div class="divide-y divide-gray-200">
            <!-- Creator (always first) -->
            <div
              v-if="currentGroup.creator"
              class="px-6 py-4 flex items-center justify-between hover:bg-gray-50"
            >
              <div class="flex items-center">
                <div
                  v-if="currentGroup.creator.picture"
                  class="w-12 h-12 rounded-full overflow-hidden mr-4"
                >
                  <img
                    :src="currentGroup.creator.picture"
                    :alt="currentGroup.creator.username"
                    class="w-full h-full object-cover"
                  />
                </div>
                <div
                  v-else
                  class="w-12 h-12 rounded-full bg-gray-300 flex items-center justify-center mr-4"
                >
                  <span class="text-xl font-medium text-gray-700 leading-none">
                    {{ profileBadgeText(currentGroup.creator.username) }}
                  </span>
                </div>
                <div class="min-w-0">
                  <div class="flex items-center min-w-0">
                    <router-link
                      :to="{ name: 'profile', params: { username: currentGroup.creator.username } }"
                      class="font-medium text-gray-900 hover:text-blue-600 hover:underline text-base truncate"
                    >
                      {{ currentGroup.creator.username }}
                    </router-link>
                  </div>
                  <p class="text-sm text-gray-500 mt-1">
                    {{ currentGroup.creator.first_name }} {{ currentGroup.creator.last_name }}
                  </p>
                </div>
              </div>
              <span
                class="inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 shrink-0"
              >
                Creator
              </span>
            </div>

            <!-- Other members from API (if available) -->
            <div
              v-for="m in otherMembers"
              :key="String(m.id || m.username)"
              class="px-6 py-4 flex items-center justify-between hover:bg-gray-50"
            >
              <div class="flex items-center min-w-0">
                <div v-if="m.picture" class="w-12 h-12 rounded-full overflow-hidden mr-4 shrink-0">
                  <img :src="m.picture" :alt="m.username" class="w-full h-full object-cover" />
                </div>
                <div
                  v-else
                  class="w-12 h-12 rounded-full bg-gray-300 flex items-center justify-center mr-4 shrink-0"
                >
                  <span class="text-lg font-medium text-gray-700 leading-none">
                    {{ profileBadgeText(m.username) }}
                  </span>
                </div>

                <div class="min-w-0">
                  <div class="flex items-center gap-2 min-w-0">
                    <router-link
                      :to="{ name: 'profile', params: { username: m.username } }"
                      class="font-medium text-gray-900 hover:text-blue-600 hover:underline truncate"
                    >
                      {{ m.username }}
                    </router-link>
                  </div>
                  <p
                    v-if="m.first_name || m.last_name"
                    class="text-sm text-gray-500 mt-0.5 truncate"
                  >
                    {{ m.first_name }} {{ m.last_name }}
                  </p>
                </div>
              </div>
              <span
                class="inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800 shrink-0"
              >
                Member
              </span>
            </div>

            <!-- Fallback info when API doesn't provide member list -->
            <div v-if="otherMembers.length === 0" class="px-6 py-4 text-center text-gray-500">
              <p class="text-sm">
                Currently showing {{ currentGroup.member_count }} total members.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <TransferOwnershipModal
      v-if="currentGroup"
      :is-open="isTransferModalOpen"
      :members="transferOwnershipMembers"
      :creator-id="groupCreatorId"
      :is-submitting="isTransferringOwnership"
      @close="isTransferModalOpen = false"
      @submit="handleConfirmTransfer"
    />

    <EditGroupModal
      v-if="currentGroup"
      :is-open="isEditModalOpen"
      :group="currentGroup"
      :is-submitting="isUpdatingGroup"
      @close="isEditModalOpen = false"
      @submit="handleUpdateGroup"
    />
  </div>
</template>
