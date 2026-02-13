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

// Font Awesome Icons
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
  faBrain,
  faRocket,
  faStar,
  faFire,
  faThumbsUp,
  faHandsClapping,
  faGem,
  faExpand,
  faPlus,
  faGripVertical,
  faChevronDown,
  faChevronUp,
  faChevronUp as faAngleUp,
  faChevronDown as faAngleDown,
  faArrowLeft,
  faSpinner,
  faCompress,
  faCheckCircle,
  faExclamationCircle,
  faCut,
  faExclamationTriangle,
} from '@fortawesome/free-solid-svg-icons'

// Add icons to library
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
  faBrain,
  faRocket,
  faStar,
  faFire,
  faThumbsUp,
  faHandsClapping,
  faGem,
  faExpand,
  faPlus,
  faGripVertical,
  faChevronDown,
  faChevronUp,
  faAngleUp,
  faAngleDown,
  faArrowLeft,
  faSpinner,
  faCompress,
  faCheckCircle,
  faExclamationCircle,
  faCut,
  faExclamationTriangle,
)

// --- Media Processing Interfaces and Constants ---
interface ProcessedFile extends File {
  trimmed?: boolean
  compressed?: boolean
  originalDuration?: number
  originalSize?: number
  finalSize?: number
}

const MAX_IMAGES = 10
const MAX_VIDEOS = 5
const MAX_TOTAL_POINTS = 10
const IMAGE_POINTS = 1
const VIDEO_POINTS = 2
const MAX_IMAGE_SIZE_KB = 400
const MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_KB * 1024
const MAX_VIDEO_SIZE_MB = 50
const MAX_VIDEO_SIZE_BYTES = MAX_VIDEO_SIZE_MB * 1024 * 1024
const MAX_VIDEO_DURATION_SECONDS = 30
const SUPPORTED_IMAGE_MIME_TYPES = [
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp',
  'image/avif',
]
const SUPPORTED_VIDEO_MIME_TYPES = [
  'video/mp4',
  'video/webm',
  'video/quicktime',
  'video/x-matroska',
]

// --- Props, Stores, and Basic State ---
const props = defineProps<{ post: Post; hideGroupContext?: boolean }>()

const feedStore = useFeedStore()
const postsStore = usePostsStore()
const commentStore = useCommentStore()
const authStore = useAuthStore()
const { currentUser, isAuthenticated } = storeToRefs(authStore)
const { isCreatingComment, createCommentError } = storeToRefs(commentStore)
const showComments = ref(false)
const newCommentContent = ref('')
const localDeleteError = ref<string | null>(null)
const isLiking = ref(false)
const activeMediaIndex = ref(0)
const showMediaModal = ref(false)
const modalMediaIndex = ref(0)

// Mobile-specific states
const isMobile = ref(false)

// Comment pagination
const visibleCommentCount = ref(4)
const commentsScrollContainer = ref<HTMLDivElement | null>(null)

// Refs for scrolling
const actionsFooterRef = ref<HTMLElement | null>(null)
const postContainerRef = ref<HTMLElement | null>(null)

// Text expansion state
const isContentExpanded = ref(false)
const contentElementRef = ref<HTMLElement | null>(null)
const isContentOverflowing = ref(false)

// Edit mode state
const isEditing = ref(false)
const localEditError = ref<string | null>(null)
const editContent = ref('')
const editableMedia = ref<PostMedia[]>([])
const newImageFiles = ref<ProcessedFile[]>([])
const newVideoFiles = ref<ProcessedFile[]>([])
const mediaToDeleteIds = ref<number[]>([])
const editTextAreaRef = ref<{ blur: () => void; focus: () => void } | null>(null)
const editPollQuestion = ref('')
const editPollOptions = ref<{ id: number | null; text: string }[]>([])
const deletedOptionIds = ref<number[]>([])
const showOptionsMenu = ref(false)
const optionsMenuRef = ref<HTMLDivElement | null>(null)
const postArticleRef = ref<HTMLElement | null>(null)
const isReportModalOpen = ref(false)
const reportTarget = ref<{ ct_id: number; obj_id: number } | null>(null)

// Modal-specific report state
const isModalReportModalOpen = ref(false)
const modalReportTarget = ref<{ ct_id: number; obj_id: number } | null>(null)

// Media processing state for edit mode
const isCompressing = ref(false)
const compressionProgress = ref(0)
const processingMessages = ref<string[]>([])
const editProcessingError = ref<string | null>(null)
const newImagePreviewUrls = ref<string[]>([])
const newVideoPreviewUrls = ref<string[]>([])

// Drag and drop state
const dragItemIndex = ref<number | null>(null)
const dragOverItemIndex = ref<number | null>(null)
const isDragging = ref(false)

// Define types for combined media
interface ExistingMediaItem {
  type: 'existing'
  media: PostMedia
  index: number
  id: number
}

interface NewImageItem {
  type: 'new-image'
  file: ProcessedFile
  index: number
  id: string
}

interface NewVideoItem {
  type: 'new-video'
  file: ProcessedFile
  index: number
  id: string
}

type CombinedMediaItem = ExistingMediaItem | NewImageItem | NewVideoItem

// Combined media for drag & drop
const combinedMedia = computed((): CombinedMediaItem[] => {
  const existing: ExistingMediaItem[] = editableMedia.value.map((media, index) => ({
    type: 'existing',
    media,
    index,
    id: media.id,
  }))

  const newImages: NewImageItem[] = newImageFiles.value.map((file, index) => ({
    type: 'new-image',
    file,
    index,
    id: `new-image-${index}`,
  }))

  const newVideos: NewVideoItem[] = newVideoFiles.value.map((file, index) => ({
    type: 'new-video',
    file,
    index,
    id: `new-video-${index}`,
  }))

  return [...existing, ...newImages, ...newVideos]
})

// Calculate current points for edit mode
const editCurrentPoints = computed(() => {
  let points = 0

  // Points from existing media
  editableMedia.value.forEach((media) => {
    points += media.media_type === 'image' ? IMAGE_POINTS : VIDEO_POINTS
  })

  // Points from new files
  points += newImageFiles.value.length * IMAGE_POINTS
  points += newVideoFiles.value.length * VIDEO_POINTS

  return points
})

const editRemainingPoints = computed(() => {
  return MAX_TOTAL_POINTS - editCurrentPoints.value
})

// Get media type for display
function getMediaType(item: CombinedMediaItem): string {
  if (item.type === 'existing') {
    return item.media.media_type === 'image' ? 'Image' : 'Video'
  } else {
    return item.type === 'new-image' ? 'Image' : 'Video'
  }
}

// Get file for new media items (type-safe)
function getProcessedFile(item: CombinedMediaItem): ProcessedFile | null {
  if (item.type === 'new-image' || item.type === 'new-video') {
    return item.file
  }
  return null
}

// Reaction system
const showReactions = ref(false)
const currentReaction = ref<string | null>(null)
const reactionHideTimeout = ref<number | null>(null)
const hoveredReaction = ref<string | null>(null)
const reactions = [
  { name: 'like', icon: faThumbsUp, label: 'Like', color: 'text-blue-500' },
  { name: 'love', icon: faHeart, label: 'Love', color: 'text-red-500' },
  { name: 'happy', icon: faFaceLaughBeam, label: 'Happy', color: 'text-yellow-500' },
  { name: 'celebrate', icon: faHandsClapping, label: 'Celebrate', color: 'text-purple-500' },
  { name: 'insightful', icon: faLightbulb, label: 'Insightful', color: 'text-blue-400' },
  { name: 'brilliant', icon: faGem, label: 'Brilliant', color: 'text-teal-500' },
]

const isOwner = computed(
  () => isAuthenticated.value && currentUser.value?.id === props.post.author.id,
)
const commentPostKey = computed(() => `${props.post.post_type}_${props.post.object_id}`)
const commentsForThisPost = computed(() =>
  (commentStore.commentsByPost[commentPostKey.value] || []).filter((c: any) => !c.parent),
)

// Comment pagination
const visibleComments = computed(() => {
  return commentsForThisPost.value.slice(0, visibleCommentCount.value)
})

const isLoadingComments = computed(() => commentStore.isLoading)
const commentError = computed(() => commentStore.error)
const activeMedia = computed(() => props.post.media?.[activeMediaIndex.value])
const hasMultipleMedia = computed(() => (props.post.media?.length ?? 0) > 1)
const formattedTimestamp = computed(() =>
  props.post.created_at
    ? formatDistanceToNow(new Date(props.post.created_at), { addSuffix: true })
    : '',
)

// Media grid layout
const mediaGridClass = computed(() => {
  const mediaCount = props.post.media?.length || 0
  if (mediaCount === 1) return 'grid-cols-1'
  if (mediaCount === 2) return 'grid-cols-2'
  if (mediaCount === 3) return 'grid-cols-2 grid-rows-2'
  if (mediaCount >= 4) return 'grid-cols-2 grid-rows-2'
  return 'grid-cols-1'
})

// --- Media Processing Functions ---
const getErrorMessage = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message
  } else if (typeof error === 'string') {
    return error
  } else if (error && typeof error === 'object' && 'message' in error) {
    return String((error as any).message)
  }
  return 'An unknown error occurred'
}

const compressImageFast = (file: File): Promise<ProcessedFile> => {
  return new Promise((resolve, reject) => {
    if (file.size <= MAX_IMAGE_SIZE_BYTES) {
      const processedFile = Object.assign(new File([file], file.name, { type: file.type }), {
        finalSize: file.size,
      }) as ProcessedFile
      return resolve(processedFile)
    }

    const img = new Image()
    const url = URL.createObjectURL(file)

    img.onload = () => {
      URL.revokeObjectURL(url)

      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      if (!ctx) {
        reject(new Error('Canvas context not available'))
        return
      }

      let width = img.width
      let height = img.height

      const sizeRatio = file.size / MAX_IMAGE_SIZE_BYTES
      let maxDimension = 1200

      if (sizeRatio > 10) maxDimension = 800
      else if (sizeRatio > 5) maxDimension = 1000

      if (width > maxDimension || height > maxDimension) {
        const ratio = Math.min(maxDimension / width, maxDimension / height)
        width = Math.floor(width * ratio)
        height = Math.floor(height * ratio)
      }

      canvas.width = width
      canvas.height = height

      ctx.imageSmoothingEnabled = true
      ctx.imageSmoothingQuality = 'high'
      ctx.drawImage(img, 0, 0, width, height)

      let quality = 0.7

      const compressAttempt = (attemptQuality: number): void => {
        canvas.toBlob(
          (blob) => {
            if (!blob) {
              reject(new Error('Compression failed'))
              return
            }

            if (blob.size > MAX_IMAGE_SIZE_BYTES && attemptQuality > 0.1) {
              compressAttempt(attemptQuality - 0.1)
            } else {
              if (blob.size > MAX_IMAGE_SIZE_BYTES && width > 400 && height > 400) {
                width = Math.floor(width * 0.8)
                height = Math.floor(height * 0.8)
                canvas.width = width
                canvas.height = height
                ctx.drawImage(img, 0, 0, width, height)
                compressAttempt(0.5)
              } else {
                const compressedFile = Object.assign(
                  new File([blob], file.name, { type: 'image/jpeg' }),
                  {
                    compressed: true,
                    originalSize: file.size,
                    finalSize: blob.size,
                  },
                ) as ProcessedFile
                resolve(compressedFile)
              }
            }
          },
          'image/jpeg',
          attemptQuality,
        )
      }

      compressAttempt(quality)
    }

    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('Error loading image'))
    }

    img.src = url
  })
}

const getVideoDuration = (file: File): Promise<number> => {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video')
    video.preload = 'metadata'

    const timeout = setTimeout(() => {
      reject(new Error('Video duration check timeout'))
      URL.revokeObjectURL(video.src)
    }, 5000)

    video.onloadedmetadata = () => {
      clearTimeout(timeout)
      const duration = video.duration
      URL.revokeObjectURL(video.src)
      resolve(duration)
    }

    video.onerror = () => {
      clearTimeout(timeout)
      URL.revokeObjectURL(video.src)
      reject(new Error('Could not get video duration'))
    }

    video.src = URL.createObjectURL(file)
  })
}

const trimVideoToDuration = (file: File, maxDurationSeconds: number): Promise<ProcessedFile> => {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video')
    video.src = URL.createObjectURL(file)
    video.muted = true
    video.playsInline = true

    video.onloadedmetadata = async () => {
      const originalDuration = video.duration
      const targetDuration = Math.min(originalDuration, maxDurationSeconds)

      if (originalDuration <= maxDurationSeconds) {
        URL.revokeObjectURL(video.src)
        const unchangedFile = Object.assign(new File([file], file.name, { type: file.type }), {
          originalDuration: originalDuration,
          finalSize: file.size,
        }) as ProcessedFile
        resolve(unchangedFile)
        return
      }

      try {
        const stream = await (video as any).captureStream()
        const mediaRecorder = new MediaRecorder(stream, {
          mimeType: 'video/webm; codecs=vp9',
          videoBitsPerSecond: 2500000,
        })

        const chunks: Blob[] = []

        mediaRecorder.ondataavailable = (e) => {
          if (e.data.size > 0) {
            chunks.push(e.data)
          }
        }

        mediaRecorder.onstop = () => {
          const trimmedBlob = new Blob(chunks, { type: 'video/webm' })

          if (trimmedBlob.size > MAX_VIDEO_SIZE_BYTES) {
            compressVideoFile(new File([trimmedBlob], file.name, { type: 'video/webm' }))
              .then((compressedFile) => {
                const finalFile = Object.assign(
                  new File([compressedFile], file.name, { type: compressedFile.type }),
                  {
                    trimmed: true,
                    originalDuration: originalDuration,
                    originalSize: file.size,
                    finalSize: compressedFile.size,
                  },
                ) as ProcessedFile

                URL.revokeObjectURL(video.src)
                stream.getTracks().forEach((track: MediaStreamTrack) => track.stop())
                resolve(finalFile)
              })
              .catch((error) => {
                URL.revokeObjectURL(video.src)
                stream.getTracks().forEach((track: MediaStreamTrack) => track.stop())
                reject(error)
              })
          } else {
            const trimmedFile = Object.assign(
              new File([trimmedBlob], file.name, { type: 'video/webm' }),
              {
                trimmed: true,
                originalDuration: originalDuration,
                originalSize: file.size,
                finalSize: trimmedBlob.size,
              },
            ) as ProcessedFile

            URL.revokeObjectURL(video.src)
            stream.getTracks().forEach((track: MediaStreamTrack) => track.stop())
            resolve(trimmedFile)
          }
        }

        mediaRecorder.onerror = (e: any) => {
          URL.revokeObjectURL(video.src)
          stream.getTracks().forEach((track: MediaStreamTrack) => track.stop())
          reject(new Error(`MediaRecorder error: ${e}`))
        }

        mediaRecorder.start()
        video.currentTime = 0
        await video.play()

        setTimeout(() => {
          if (mediaRecorder.state === 'recording') {
            mediaRecorder.stop()
            video.pause()
          }
        }, targetDuration * 1000)
      } catch (error) {
        URL.revokeObjectURL(video.src)
        reject(new Error(`Video trimming failed: ${getErrorMessage(error)}`))
      }
    }

    video.onerror = () => {
      URL.revokeObjectURL(video.src)
      reject(new Error('Error loading video for trimming'))
    }
  })
}

const compressVideoFile = (file: File): Promise<File> => {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video')
    video.src = URL.createObjectURL(file)
    video.muted = true
    video.playsInline = true

    video.onloadedmetadata = () => {
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')

      if (!ctx) {
        URL.revokeObjectURL(video.src)
        reject(new Error('Canvas context not available'))
        return
      }

      let targetWidth = video.videoWidth
      let targetHeight = video.videoHeight

      if (targetWidth > 1280 || targetHeight > 720) {
        const ratio = Math.min(1280 / targetWidth, 720 / targetHeight)
        targetWidth = Math.floor(targetWidth * ratio)
        targetHeight = Math.floor(targetHeight * ratio)
      }

      canvas.width = targetWidth
      canvas.height = targetHeight

      const stream = canvas.captureStream(30)
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'video/webm; codecs=vp9',
        videoBitsPerSecond: 1500000,
      })

      const chunks: Blob[] = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.push(e.data)
        }
      }

      mediaRecorder.onstop = () => {
        const compressedBlob = new Blob(chunks, { type: 'video/webm' })
        const compressedFile = new File([compressedBlob], file.name, {
          type: 'video/webm',
          lastModified: Date.now(),
        })

        URL.revokeObjectURL(video.src)
        stream.getTracks().forEach((track: MediaStreamTrack) => track.stop())
        resolve(compressedFile)
      }

      mediaRecorder.onerror = () => {
        URL.revokeObjectURL(video.src)
        stream.getTracks().forEach((track: MediaStreamTrack) => track.stop())
        reject(new Error('Video compression failed'))
      }

      let startTime = Date.now()
      const captureFrame = () => {
        if (
          Date.now() - startTime < MAX_VIDEO_DURATION_SECONDS * 1000 &&
          video.currentTime < video.duration
        ) {
          ctx.drawImage(video, 0, 0, targetWidth, targetHeight)
          requestAnimationFrame(captureFrame)
        } else {
          mediaRecorder.stop()
          video.pause()
        }
      }

      mediaRecorder.start()
      video.currentTime = 0
      video
        .play()
        .then(() => {
          captureFrame()
        })
        .catch((error) => {
          URL.revokeObjectURL(video.src)
          reject(new Error(`Video play failed: ${getErrorMessage(error)}`))
        })
    }

    video.onerror = () => {
      URL.revokeObjectURL(video.src)
      reject(new Error('Error loading video for compression'))
    }
  })
}

const generateVideoPreview = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video')
    video.preload = 'metadata'

    const timeout = setTimeout(() => {
      URL.revokeObjectURL(video.src)
      resolve('')
    }, 2000)

    video.onloadedmetadata = () => {
      clearTimeout(timeout)
      video.currentTime = Math.min(1, video.duration / 2)

      video.onseeked = () => {
        const canvas = document.createElement('canvas')
        canvas.width = 120
        canvas.height = 68

        const ctx = canvas.getContext('2d')
        if (!ctx) {
          URL.revokeObjectURL(video.src)
          resolve('')
          return
        }

        ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
        const dataUrl = canvas.toDataURL('image/jpeg', 0.5)
        URL.revokeObjectURL(video.src)
        resolve(dataUrl)
      }
    }

    video.onerror = () => {
      clearTimeout(timeout)
      URL.revokeObjectURL(video.src)
      resolve('')
    }

    video.src = URL.createObjectURL(file)
  })
}

const processImage = async (file: File): Promise<ProcessedFile> => {
  try {
    const processedFile = await compressImageFast(file)
    return processedFile
  } catch (error) {
    throw new Error(`Image processing error: ${getErrorMessage(error)}`)
  }
}

const processVideo = async (file: File): Promise<ProcessedFile> => {
  try {
    const duration = await getVideoDuration(file)
    const sizeMB = file.size / (1024 * 1024)

    let processedFile: ProcessedFile = Object.assign(
      new File([file], file.name, { type: file.type }),
      {
        originalDuration: duration,
        finalSize: file.size,
      },
    ) as ProcessedFile
    let needsProcessing = false

    if (duration > MAX_VIDEO_DURATION_SECONDS) {
      needsProcessing = true
    }

    if (sizeMB > MAX_VIDEO_SIZE_MB) {
      needsProcessing = true
    }

    if (!needsProcessing) {
      return processedFile
    }

    if (duration > MAX_VIDEO_DURATION_SECONDS) {
      processedFile = await trimVideoToDuration(file, MAX_VIDEO_DURATION_SECONDS)
    }

    const currentSizeMB = processedFile.size / (1024 * 1024)
    if (currentSizeMB > MAX_VIDEO_SIZE_MB || sizeMB > MAX_VIDEO_SIZE_MB) {
      const compressedBlob = await compressVideoFile(processedFile)

      const finalFile = Object.assign(
        new File([compressedBlob], file.name, { type: compressedBlob.type }),
        {
          trimmed: processedFile.trimmed || duration > MAX_VIDEO_DURATION_SECONDS,
          compressed: true,
          originalDuration: duration,
          originalSize: file.size,
          finalSize: compressedBlob.size,
        },
      ) as ProcessedFile

      processedFile = finalFile
    }

    return processedFile
  } catch (error) {
    throw new Error(`Video processing error: ${getErrorMessage(error)}`)
  }
}

// Enhanced handleNewFiles for edit mode
const handleNewFilesEdit = async (event: Event, type: 'image' | 'video') => {
  const target = event.target as HTMLInputElement
  const files = target.files
  if (!files) return

  editProcessingError.value = null

  // Calculate current counts
  const existingImages = editableMedia.value.filter((m) => m.media_type === 'image').length
  const existingVideos = editableMedia.value.filter((m) => m.media_type === 'video').length
  const currentNewImages = newImageFiles.value.length
  const currentNewVideos = newVideoFiles.value.length

  const totalImages = existingImages + currentNewImages
  const totalVideos = existingVideos + currentNewVideos

  const filesToAdd = files.length
  const filePoints = type === 'image' ? IMAGE_POINTS : VIDEO_POINTS
  const potentialPoints = editCurrentPoints.value + filesToAdd * filePoints

  // Check individual limits
  if (type === 'image') {
    const remainingSlots = MAX_IMAGES - totalImages
    if (filesToAdd > remainingSlots) {
      editProcessingError.value = `You can only upload ${MAX_IMAGES} images maximum.`
      target.value = ''
      return
    }
  } else {
    const remainingSlots = MAX_VIDEOS - totalVideos
    if (filesToAdd > remainingSlots) {
      editProcessingError.value = `You can only upload ${MAX_VIDEOS} videos maximum.`
      target.value = ''
      return
    }
  }

  // Check point limit
  if (potentialPoints > MAX_TOTAL_POINTS) {
    const maxFiles = Math.floor(editRemainingPoints.value / filePoints)
    if (maxFiles <= 0) {
      editProcessingError.value = `You have reached the maximum upload limit.`
    } else {
      editProcessingError.value = `You can only upload ${maxFiles} more ${type}${maxFiles > 1 ? 's' : ''}.`
    }
    target.value = ''
    return
  }

  const filesToProcess = Array.from(files)

  // Start processing
  isCompressing.value = true
  compressionProgress.value = 10
  processingMessages.value = []

  try {
    for (const [index, file] of filesToProcess.entries()) {
      try {
        let processedFile: ProcessedFile
        const originalSizeMB = (file.size / (1024 * 1024)).toFixed(2)

        if (type === 'image') {
          if (!SUPPORTED_IMAGE_MIME_TYPES.includes(file.type)) {
            throw new Error(
              `Unsupported image format: '${file.name}'. Please use JPG, PNG, GIF, WEBP, or AVIF.`,
            )
          }

          processingMessages.value.push(
            `Processing image ${index + 1}/${filesToProcess.length} (${originalSizeMB}MB)`,
          )
          processedFile = await processImage(file)

          const finalSizeKB = ((processedFile.finalSize || file.size) / 1024).toFixed(1)
          processingMessages.value.push(
            `✓ Image ${index + 1}: ${originalSizeMB}MB → ${finalSizeKB}KB`,
          )

          // Add to new files and generate preview
          newImageFiles.value.push(processedFile)
          const reader = new FileReader()
          reader.onload = (e) => {
            if (e.target?.result) {
              newImagePreviewUrls.value.push(e.target.result as string)
            }
          }
          reader.readAsDataURL(processedFile)
        } else {
          if (!SUPPORTED_VIDEO_MIME_TYPES.includes(file.type)) {
            throw new Error(
              `Unsupported video format: '${file.name}'. Please use MP4, WebM, or MOV.`,
            )
          }

          processingMessages.value.push(
            `Processing video ${index + 1}/${filesToProcess.length} (${originalSizeMB}MB)`,
          )
          processedFile = await processVideo(file)

          const finalSizeMB = ((processedFile.finalSize || file.size) / (1024 * 1024)).toFixed(2)
          const durationInfo = processedFile.originalDuration
            ? `${Math.round(processedFile.originalDuration)}s → ${MAX_VIDEO_DURATION_SECONDS}s`
            : 'duration optimized'

          processingMessages.value.push(
            `✓ Video ${index + 1}: ${originalSizeMB}MB → ${finalSizeMB}MB, ${durationInfo}`,
          )

          newVideoFiles.value.push(processedFile)

          // Generate and add video preview
          try {
            const previewUrl = await generateVideoPreview(processedFile)
            newVideoPreviewUrls.value.push(previewUrl)
          } catch (previewError) {
            console.warn('Failed to generate video preview:', getErrorMessage(previewError))
            newVideoPreviewUrls.value.push('')
          }
        }
      } catch (error) {
        const errorMessage = getErrorMessage(error)
        editProcessingError.value = `Failed to process ${type}: ${errorMessage}`
        target.value = ''
        isCompressing.value = false
        compressionProgress.value = 0
        return
      }
    }

    processingMessages.value.push(
      `✓ All ${filesToProcess.length} ${type}(s) processed successfully`,
    )

    setTimeout(() => {
      processingMessages.value = []
      isCompressing.value = false
      compressionProgress.value = 0
    }, 3000)
  } catch (error) {
    editProcessingError.value = getErrorMessage(error)
    isCompressing.value = false
    compressionProgress.value = 0
    processingMessages.value = []
  }

  target.value = ''
}

// Check if mobile on mount
onMounted(() => {
  checkIfMobile()
  window.addEventListener('resize', checkIfMobile)
  nextTick(() => {
    checkContentOverflow()
  })

  // Add body class watcher for isEditing
  watch(isEditing, (newVal) => {
    if (newVal) {
      document.body.classList.add('modal-open', 'overflow-hidden')
    } else {
      document.body.classList.remove('modal-open', 'overflow-hidden')
    }
  })
})

onUnmounted(() => {
  window.removeEventListener('resize', checkIfMobile)
  window.removeEventListener('video-play', handleGlobalVideoPlay as EventListener)
  document.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('click', closeOnClickOutside, true)
  eventBus.off('navigation-started', handleNavigation)
  document.body.classList.remove('modal-open', 'overflow-hidden')

  // Clean up object URLs
  newImagePreviewUrls.value.forEach((url) => {
    if (url.startsWith('blob:')) {
      URL.revokeObjectURL(url)
    }
  })
  newVideoPreviewUrls.value.forEach((url) => {
    if (url.startsWith('blob:')) {
      URL.revokeObjectURL(url)
    }
  })
})

function checkIfMobile() {
  isMobile.value = window.innerWidth <= 768
}

watch(
  () => props.post.id,
  () => {
    activeMediaIndex.value = 0
    visibleCommentCount.value = 4
    isContentExpanded.value = false
    nextTick(() => {
      checkContentOverflow()
    })
  },
)

function checkContentOverflow() {
  if (!contentElementRef.value) return

  isContentOverflowing.value = false
  const element = contentElementRef.value
  const lineHeight = parseInt(getComputedStyle(element).lineHeight) || 24
  const maxHeight = lineHeight * 4

  element.classList.remove('line-clamp-4')
  const actualHeight = element.scrollHeight
  element.classList.add('line-clamp-4')

  isContentOverflowing.value = actualHeight > maxHeight
}

function toggleContentExpansion() {
  isContentExpanded.value = !isContentExpanded.value
}

function loadMoreComments() {
  const oldCount = visibleCommentCount.value
  visibleCommentCount.value = Math.min(
    visibleCommentCount.value + 4,
    commentsForThisPost.value.length,
  )

  nextTick(() => {
    const container = commentsScrollContainer.value
    if (!container || oldCount <= 0) return

    const commentItems = container.querySelectorAll<HTMLElement>('.comment-item')
    if (commentItems.length <= oldCount) return

    // Scroll ONLY inside the comments container (avoid moving the whole post/page)
    const target = commentItems[oldCount]
    const containerRect = container.getBoundingClientRect()
    const targetRect = target.getBoundingClientRect()
    const delta = targetRect.top - containerRect.top

    container.scrollTo({
      top: container.scrollTop + delta,
      behavior: 'smooth',
    })
  })
}

function showLessComments() {
  visibleCommentCount.value = 4
  nextTick(() => {
    if (commentsScrollContainer.value) {
      commentsScrollContainer.value.scrollTo({ top: 0, behavior: 'smooth' })
    }
  })
}

watch(commentsForThisPost, () => {
  visibleCommentCount.value = 4
})

function pauseOtherVideos(event: Event) {
  const currentVideo = event.target as HTMLVideoElement

  const allVideosInPost = postArticleRef.value?.querySelectorAll('video') || []
  allVideosInPost.forEach((video) => {
    const videoElement = video as HTMLVideoElement
    if (videoElement !== currentVideo && !videoElement.paused) {
      videoElement.pause()
    }
  })

  window.dispatchEvent(
    new CustomEvent('video-play', {
      detail: {
        postId: props.post.id,
        video: currentVideo,
      },
    }),
  )
}

function handleGlobalVideoPlay(event: Event) {
  const customEvent = event as CustomEvent<{ postId: number; video: HTMLVideoElement }>

  if (!customEvent.detail) return

  if (customEvent.detail.postId !== props.post.id) {
    const allVideosInPost = postArticleRef.value?.querySelectorAll('video') || []
    allVideosInPost.forEach((video) => {
      const videoElement = video as HTMLVideoElement
      if (!videoElement.paused) {
        videoElement.pause()
      }
    })

    if (showMediaModal.value) {
      const modalVideos = document.querySelectorAll('.fixed.inset-0 video') || []
      modalVideos.forEach((video) => {
        const videoElement = video as HTMLVideoElement
        if (!videoElement.paused) {
          videoElement.pause()
        }
      })
    }
  }
}

// Drag and Drop Functions
function handleDragStart(index: number) {
  dragItemIndex.value = index
  isDragging.value = true
  setTimeout(() => {
    const element = document.querySelector(`[data-drag-index="${index}"]`) as HTMLElement
    if (element) {
      element.classList.add('opacity-50')
    }
  }, 0)
}

function handleDragOver(event: DragEvent, index: number) {
  event.preventDefault()
  dragOverItemIndex.value = index
}

function handleDragLeave(event: DragEvent) {
  const relatedTarget = event.relatedTarget as HTMLElement
  if (!relatedTarget || !relatedTarget.closest('.drag-container')) {
    dragOverItemIndex.value = null
  }
}

function handleDrop(event: DragEvent, index: number) {
  event.preventDefault()

  if (dragItemIndex.value === null || dragItemIndex.value === index) {
    resetDragState()
    return
  }

  const newCombinedMedia = [...combinedMedia.value]

  const [draggedItem] = newCombinedMedia.splice(dragItemIndex.value, 1)
  newCombinedMedia.splice(index, 0, draggedItem)

  const updatedExisting: PostMedia[] = []
  const updatedNewImages: ProcessedFile[] = []
  const updatedNewVideos: ProcessedFile[] = []

  newCombinedMedia.forEach((item) => {
    if (item.type === 'existing') {
      updatedExisting.push(item.media)
    } else if (item.type === 'new-image') {
      updatedNewImages.push(item.file)
    } else if (item.type === 'new-video') {
      updatedNewVideos.push(item.file)
    }
  })

  editableMedia.value = updatedExisting
  newImageFiles.value = updatedNewImages
  newVideoFiles.value = updatedNewVideos

  resetDragState()
}

function handleDragEnd() {
  resetDragState()
}

function resetDragState() {
  dragItemIndex.value = null
  dragOverItemIndex.value = null
  isDragging.value = false
  document.querySelectorAll('[data-drag-index]').forEach((element) => {
    element.classList.remove('opacity-50')
  })
}

// Handle media removal - FIXED TYPE ISSUES
function handleRemoveMedia(item: CombinedMediaItem) {
  if (item.type === 'existing') {
    flagExistingMediaForRemoval(item.media.id)
  } else if (item.type === 'new-image') {
    // Find the actual index in the newImageFiles array
    const actualIndex = newImageFiles.value.findIndex((file) => file === item.file)
    if (actualIndex !== -1) {
      newImageFiles.value.splice(actualIndex, 1)
      newImagePreviewUrls.value.splice(actualIndex, 1)
    }
  } else if (item.type === 'new-video') {
    // Find the actual index in the newVideoFiles array
    const actualIndex = newVideoFiles.value.findIndex((file) => file === item.file)
    if (actualIndex !== -1) {
      newVideoFiles.value.splice(actualIndex, 1)
      newVideoPreviewUrls.value.splice(actualIndex, 1)
    }
  }
}

// Enhanced media modal functions
function openMediaModal(index: number) {
  modalMediaIndex.value = index
  showMediaModal.value = true
  if (commentsForThisPost.value.length === 0 && !commentError.value) {
    commentStore.fetchComments(props.post.post_type, props.post.object_id)
  }
}

function closeMediaModal() {
  showMediaModal.value = false
}

function nextMediaModal() {
  modalMediaIndex.value = (modalMediaIndex.value + 1) % props.post.media.length
}

function prevMediaModal() {
  modalMediaIndex.value =
    (modalMediaIndex.value - 1 + props.post.media.length) % props.post.media.length
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    if (showMediaModal.value) {
      closeMediaModal()
    }
    if (isEditing.value) {
      cancelEdit()
    }
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

// Reaction methods for main post
function showReactionPicker() {
  if (reactionHideTimeout.value) {
    clearTimeout(reactionHideTimeout.value)
    reactionHideTimeout.value = null
  }
  showReactions.value = true
}

function hideReactionPicker() {
  reactionHideTimeout.value = window.setTimeout(() => {
    showReactions.value = false
    hoveredReaction.value = null
  }, 300)
}

function cancelHideReactionPicker() {
  if (reactionHideTimeout.value) {
    clearTimeout(reactionHideTimeout.value)
    reactionHideTimeout.value = null
  }
}

function setHoveredReaction(reactionName: string | null) {
  hoveredReaction.value = reactionName
}

// Reaction methods for modal
const showModalReactions = ref(false)
const modalReactionHideTimeout = ref<number | null>(null)
const hoveredModalReaction = ref<string | null>(null)

function showModalReactionPicker() {
  if (modalReactionHideTimeout.value) {
    clearTimeout(modalReactionHideTimeout.value)
    modalReactionHideTimeout.value = null
  }
  showModalReactions.value = true
}

function hideModalReactionPicker() {
  modalReactionHideTimeout.value = window.setTimeout(() => {
    showModalReactions.value = false
    hoveredModalReaction.value = null
  }, 300)
}

function cancelHideModalReactionPicker() {
  if (modalReactionHideTimeout.value) {
    clearTimeout(modalReactionHideTimeout.value)
    modalReactionHideTimeout.value = null
  }
}

function setHoveredModalReaction(reactionName: string | null) {
  hoveredModalReaction.value = reactionName
}

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

function handleModalCommentReport(payload: { content_type_id: number; object_id: number }) {
  modalReportTarget.value = { ct_id: payload.content_type_id, obj_id: payload.object_id }
  isModalReportModalOpen.value = true
}

const closeOnClickOutside = (event: MouseEvent) => {
  if (optionsMenuRef.value && !optionsMenuRef.value.contains(event.target as Node))
    showOptionsMenu.value = false
}
watch(showOptionsMenu, (isOpen) => {
  if (isOpen) document.addEventListener('click', closeOnClickOutside, true)
  else document.removeEventListener('click', closeOnClickOutside, true)
})
const handleNavigation = () => {
  if (isEditing.value) isEditing.value = false
}
onMounted(() => eventBus.on('navigation-started', handleNavigation))

// MODIFIED: toggleCommentDisplay function for both desktop and mobile
async function toggleCommentDisplay() {
  const wasShowingComments = showComments.value
  showComments.value = !showComments.value

  if (showComments.value) {
    if (commentsForThisPost.value.length === 0 && !commentError.value) {
      await commentStore.fetchComments(props.post.post_type, props.post.object_id)
    }

    nextTick(() => {
      if (actionsFooterRef.value) {
        const footerRect = actionsFooterRef.value.getBoundingClientRect()
        const currentScroll = window.pageYOffset || document.documentElement.scrollTop
        const targetScroll = currentScroll + footerRect.top - 80

        window.scrollTo({
          top: targetScroll,
          behavior: 'smooth',
        })
      }
    })
  } else if (wasShowingComments) {
    if (postContainerRef.value) {
      const postRect = postContainerRef.value.getBoundingClientRect()
      const viewportHeight = window.innerHeight
      const currentScroll = window.pageYOffset || document.documentElement.scrollTop
      const targetScroll = currentScroll + postRect.top - viewportHeight / 4

      setTimeout(() => {
        window.scrollTo({
          top: targetScroll,
          behavior: 'smooth',
        })
      }, 100)
    }
  }
}

async function toggleLike() {
  if (!isAuthenticated.value) return alert('Please login to like posts.')
  if (props.post.isLiking) return
  await feedStore.toggleLike(props.post.id)
}

async function handleReaction(reactionType: string) {
  if (!isAuthenticated.value) return alert('Please login to react to posts.')
  if (reactionType === 'like') {
    await feedStore.toggleLike(props.post.id)
  } else {
    console.log(`${reactionType} reaction clicked`)
  }
  showReactions.value = false
  hoveredReaction.value = null
}

async function handleModalReaction(reactionType: string) {
  if (!isAuthenticated.value) return alert('Please login to react to posts.')
  if (reactionType === 'like') {
    await feedStore.toggleLike(props.post.id)
  } else {
    console.log(`${reactionType} reaction clicked`)
  }
  showModalReactions.value = false
  hoveredModalReaction.value = null
}

async function toggleSave() {
  if (!isAuthenticated.value) {
    showOptionsMenu.value = false
    return alert('Please login to save posts.')
  }
  showOptionsMenu.value = false
  await feedStore.toggleSavePost(props.post.id)
}

async function handleDeletePost() {
  if (!isOwner.value) return
  if (window.confirm('Are you sure you want to delete this post? This action cannot be undone.')) {
    const success = await feedStore.deletePost(props.post.id)
    if (!success) localDeleteError.value = 'Failed to delete post.'
  }
}

function nextMedia() {
  activeMediaIndex.value = (activeMediaIndex.value + 1) % props.post.media.length
}
function prevMedia() {
  activeMediaIndex.value =
    (activeMediaIndex.value - 1 + props.post.media.length) % props.post.media.length
}
function setActiveMedia(index: number) {
  activeMediaIndex.value = index
}
function toggleEditMode() {
  isEditing.value = !isEditing.value
  localEditError.value = null
  editProcessingError.value = null
  if (isEditing.value) {
    if (props.post.poll) {
      editPollQuestion.value = props.post.poll.question
      editPollOptions.value = props.post.poll.options.map((opt: PollOption) => ({
        id: opt.id,
        text: opt.text,
      }))
      deletedOptionIds.value = []
      editContent.value = ''
      editableMedia.value = []
    } else {
      editContent.value = props.post.content || ''
      editableMedia.value = [...props.post.media]
      editPollQuestion.value = ''
      editPollOptions.value = []
    }
    newImageFiles.value = []
    newVideoFiles.value = []
    newImagePreviewUrls.value = []
    newVideoPreviewUrls.value = []
    mediaToDeleteIds.value = []
    nextTick(() => {
      if (editTextAreaRef.value) {
        editTextAreaRef.value.focus()
      }
    })
  } else {
    // Clean up when canceling edit
    cancelEdit()
  }
}
function addPollOptionToEdit() {
  if (editPollOptions.value.length < 5) editPollOptions.value.push({ id: null, text: '' })
}
function removePollOptionFromEdit(index: number) {
  if (editPollOptions.value.length <= 2) return
  const optionToRemove = editPollOptions.value[index]
  if (optionToRemove.id !== null) deletedOptionIds.value.push(optionToRemove.id)
  editPollOptions.value.splice(index, 1)
}
function flagExistingMediaForRemoval(mediaId: number) {
  mediaToDeleteIds.value.push(mediaId)
  editableMedia.value = editableMedia.value.filter((m: PostMedia) => m.id !== mediaId)
}
function getObjectURL(file: File): string {
  return URL.createObjectURL(file)
}

// Add this method to handle cancel edit
function cancelEdit() {
  isEditing.value = false
  isCompressing.value = false
  compressionProgress.value = 0
  processingMessages.value = []

  // Clean up object URLs
  newImagePreviewUrls.value.forEach((url) => {
    if (url.startsWith('blob:')) {
      URL.revokeObjectURL(url)
    }
  })
  newVideoPreviewUrls.value.forEach((url) => {
    if (url.startsWith('blob:')) {
      URL.revokeObjectURL(url)
    }
  })

  newImageFiles.value = []
  newVideoFiles.value = []
  newImagePreviewUrls.value = []
  newVideoPreviewUrls.value = []

  // Center the post in viewport
  nextTick(() => {
    centerPostInViewport()
  })
}

async function handleUpdatePost() {
  localEditError.value = null
  editProcessingError.value = null

  postsStore.addOrUpdatePosts([{ id: props.post.id, isUpdating: true }])
  const formData = new FormData()
  if (editContent.value !== (props.post.content || ''))
    formData.append('content', editContent.value)
  newImageFiles.value.forEach((file) => formData.append('images', file))
  newVideoFiles.value.forEach((file) => formData.append('videos', file))
  if (mediaToDeleteIds.value.length > 0)
    formData.append('media_to_delete', JSON.stringify(mediaToDeleteIds.value))

  try {
    const response = await axiosInstance.patch<Post>(`/posts/${props.post.id}/`, formData)
    postsStore.addOrUpdatePosts([response.data])
    isEditing.value = false

    // Clean up
    newImageFiles.value = []
    newVideoFiles.value = []
    newImagePreviewUrls.value = []
    newVideoPreviewUrls.value = []
    isCompressing.value = false
    compressionProgress.value = 0
    processingMessages.value = []

    nextTick(() => {
      centerPostInViewport()
    })
  } catch (err: any) {
    localEditError.value = err.response?.data?.detail || 'Failed to update post.'
  } finally {
    postsStore.addOrUpdatePosts([{ id: props.post.id, isUpdating: false }])
  }
}

async function handleUpdatePoll() {
  localEditError.value = null
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

    nextTick(() => {
      centerPostInViewport()
    })
  } catch (err: any) {
    localEditError.value = err.response?.data?.detail || 'Failed to update poll.'
  } finally {
    postsStore.addOrUpdatePosts([{ id: props.post.id, isUpdating: false }])
  }
}

function centerPostInViewport() {
  if (!postContainerRef.value) return

  const postRect = postContainerRef.value.getBoundingClientRect()
  const viewportHeight = window.innerHeight
  const currentScroll = window.pageYOffset || document.documentElement.scrollTop
  const targetScroll = currentScroll + postRect.top - viewportHeight / 2 + postRect.height / 2

  window.scrollTo({
    top: targetScroll,
    behavior: 'smooth',
  })
}

function linkifyContent(text: string | null | undefined): string {
  if (!text) return ''
  const urlRegex =
    /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])|(\bwww\.[-A-Z0+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/gi
  const mentionRegex = /@([\w.-]+)/g
  let linkedText = text.replace(
    urlRegex,
    (url) =>
      `<a href="${url.startsWith('www.') ? 'http://' + url : url}" target="_blank" rel="noopener noreferrer" class="text-blue-500 hover:underline">${url}</a>`,
  )
  linkedText = linkedText.replace(
    mentionRegex,
    (match, username) =>
      `<a href="/profile/${username}" class="font-semibold text-blue-600 hover:underline">${match}</a>`,
  )
  return linkedText
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

// GIF functionality placeholder
function handleGifClick() {
  console.log('GIF picker would open here')
  alert('GIF functionality would be implemented here with a GIF picker')
}

// Emoji functionality placeholder
function handleEmojiClick() {
  console.log('Emoji picker would open here')
  alert('Emoji functionality would be implemented here with an emoji picker')
}
</script>

<template>
  <div class="post-wrapper" ref="postContainerRef">
    <!-- Compression Progress Overlay for Edit Mode -->
    <div
      v-if="isCompressing"
      class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
    >
      <div class="bg-white rounded-xl p-4 lg:p-6 max-w-sm w-full">
        <div class="flex items-center gap-3 mb-4">
          <FontAwesomeIcon
            :icon="['fas', 'compress']"
            class="text-blue-500 text-xl animate-pulse"
          />
          <div>
            <h3 class="font-bold text-gray-800 text-sm lg:text-base">Optimizing Media</h3>
            <p class="text-xs text-gray-600">Please wait...</p>
          </div>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-2">
          <div
            class="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-300"
            :style="{ width: `${compressionProgress}%` }"
          ></div>
        </div>
        <p class="text-xs text-gray-500 mt-2 text-center">{{ compressionProgress }}%</p>

        <!-- Processing Messages -->
        <div v-if="processingMessages.length > 0" class="mt-4 space-y-2 max-h-40 overflow-y-auto">
          <div
            v-for="(message, index) in processingMessages"
            :key="index"
            class="text-xs p-2 rounded-lg flex items-start gap-2"
            :class="{
              'bg-green-50 text-green-700': message.startsWith('✓'),
              'bg-blue-50 text-blue-700': !message.startsWith('✓'),
            }"
          >
            <FontAwesomeIcon
              :icon="message.startsWith('✓') ? ['fas', 'check-circle'] : ['fas', 'spinner']"
              class="mt-0.5 flex-shrink-0"
              :class="[
                message.startsWith('✓') ? 'text-green-500' : 'text-blue-500',
                { 'animate-spin': !message.startsWith('✓') },
              ]"
            />
            <span class="text-xs">{{ message }}</span>
          </div>
        </div>
      </div>
    </div>

    <article
      ref="postArticleRef"
      tabindex="-1"
      class="bg-white rounded-2xl shadow-sm focus:outline-none border border-gray-100 relative overflow-visible"
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
              alt="author avatar"
              class="w-9 h-9 lg:w-11 lg:h-11 rounded-full object-cover mr-3 lg:mr-4 bg-gray-200"
              data-cy="post-author-avatar"
            />
          </router-link>
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-x-1 lg:gap-x-2 flex-wrap">
              <router-link
                :to="{ name: 'profile', params: { username: post.author.username } }"
                class="font-semibold text-gray-900 hover:underline text-sm lg:text-base truncate max-w-[120px] lg:max-w-[150px]"
                >{{ post.author.username }}</router-link
              >
              <template v-if="post.group && !hideGroupContext">
                <span class="text-blue-500 text-xs hidden lg:inline">▶</span>
                <router-link
                  :to="{ name: 'group-detail', params: { slug: post.group.slug } }"
                  class="font-semibold text-gray-500 hover:underline text-xs lg:text-sm truncate max-w-[100px] lg:max-w-[130px]"
                >
                  {{ post.group.name }}
                </router-link>
              </template>
            </div>
            <p class="text-xs md:text-sm text-gray-500 mt-0.5">{{ formattedTimestamp }}</p>
          </div>
        </div>
        <div v-if="isAuthenticated" class="relative" ref="optionsMenuRef">
          <button
            @click.stop="toggleOptionsMenu"
            class="w-7 h-7 md:w-8 md:h-8 flex items-center justify-center rounded-full text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
            data-cy="post-options-button"
          >
            <FontAwesomeIcon :icon="faEllipsisVertical" class="w-3 h-3 md:w-4 md:h-4" />
          </button>
          <div
            v-if="showOptionsMenu"
            class="origin-top-right absolute right-0 mt-2 w-40 md:w-44 rounded-lg shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-50 border border-gray-200"
          >
            <div
              class="py-2"
              role="menu"
              aria-orientation="vertical"
              aria-labelledby="options-menu"
            >
              <button
                @click.prevent="toggleSave"
                class="w-full text-left flex items-center px-3 py-2 md:py-3 text-sm text-gray-700 hover:bg-blue-50 transition-colors duration-200 group"
                role="menuitem"
              >
                <FontAwesomeIcon
                  :icon="faBookmark"
                  class="w-3 h-3 md:w-4 md:h-4 mr-2 text-blue-500 group-hover:text-blue-600"
                  :class="post.is_saved ? 'fill-current' : ''"
                />
                <span class="group-hover:text-blue-600 text-xs md:text-sm">{{
                  post.is_saved ? 'Unsave Post' : 'Save Post'
                }}</span>
              </button>

              <template v-if="isOwner">
                <button
                  @click="handleEditClick"
                  :disabled="post.isDeleting"
                  class="w-full text-left flex items-center px-3 py-2 md:py-3 text-sm text-gray-700 hover:bg-green-50 transition-colors duration-200 group disabled:opacity-50"
                  role="menuitem"
                >
                  <FontAwesomeIcon
                    :icon="faPenToSquare"
                    class="w-3 h-3 md:w-4 md:h-4 mr-2 text-green-500 group-hover:text-green-600"
                  />
                  <span class="group-hover:text-green-600 text-xs md:text-sm">{{
                    isEditing ? 'Cancel Edit' : 'Edit Post'
                  }}</span>
                </button>

                <button
                  @click="handleDeleteClick"
                  :disabled="post.isDeleting || isEditing"
                  class="w-full text-left flex items-center px-3 py-2 md:py-3 text-sm text-red-700 hover:bg-red-50 transition-colors duration-200 group"
                  role="menuitem"
                  data-cy="delete-post-button"
                >
                  <FontAwesomeIcon
                    :icon="faTrash"
                    class="w-3 h-3 md:w-4 md:h-4 mr-2 text-red-500 group-hover:text-red-600"
                  />
                  <span class="group-hover:text-red-600 text-xs md:text-sm">{{
                    post.isDeleting ? 'Deleting...' : 'Delete Post'
                  }}</span>
                </button>
              </template>

              <template v-else>
                <button
                  @click="handleReportClick"
                  class="w-full text-left flex items-center px-3 py-2 md:py-3 text-sm text-gray-700 hover:bg-orange-50 transition-colors duration-200 group"
                  role="menuitem"
                >
                  <FontAwesomeIcon
                    :icon="faFlag"
                    class="w-3 h-3 md:w-4 md:h-4 mr-2 text-orange-500 group-hover:text-orange-600"
                  />
                  <span class="group-hover:text-orange-600 text-xs md:text-sm">Report Post</span>
                </button>
              </template>
            </div>
          </div>
        </div>
      </header>

      <!-- Post Body & Media Section -->
      <div v-if="!isEditing" class="pb-3">
        <!-- MODIFIED: Post content with expand/collapse functionality -->
        <div v-if="post.content && !post.poll" class="px-3 md:px-4">
          <div
            ref="contentElementRef"
            :class="[!isContentExpanded && isContentOverflowing ? 'line-clamp-4' : '']"
            class="text-gray-800 whitespace-pre-wrap break-words text-sm md:text-base word-break-fix transition-all duration-200"
            v-html="linkifyContent(post.content)"
          ></div>

          <!-- "See more/See less" button -->
          <div v-if="isContentOverflowing" class="mt-1">
            <button
              @click="toggleContentExpansion"
              class="text-blue-500 hover:text-blue-600 text-sm font-medium flex items-center gap-1 transition-colors duration-200"
            >
              <FontAwesomeIcon
                :icon="isContentExpanded ? faAngleUp : faAngleDown"
                class="w-3 h-3"
              />
              <span>{{ isContentExpanded ? 'See less' : 'See more' }}</span>
            </button>
          </div>
        </div>

        <!-- Original Poll Display -->
        <PollDisplay v-if="post.poll" :poll="post.poll" :post-id="post.id" />

        <!-- Media Grid Layout -->
        <div v-if="post.media && post.media.length > 0" class="mt-3 px-3 md:px-4">
          <!-- Single video -->
          <div v-if="post.media.length === 1" class="relative overflow-hidden rounded-xl">
            <div class="cursor-pointer" @click="openMediaModal(0)">
              <video
                v-if="post.media[0].media_type === 'video'"
                controls
                class="w-full h-auto max-h-[500px] object-contain rounded-xl mx-auto"
                :src="buildMediaUrl(post.media[0].file_url)"
                @play="pauseOtherVideos"
              ></video>
              <img
                v-else
                :src="buildMediaUrl(post.media[0].file_url)"
                class="w-full h-auto object-contain rounded-xl max-h-[300px] mx-auto"
              />
            </div>
          </div>

          <!-- Multiple media -->
          <div
            v-else
            class="grid gap-[1px] rounded-xl overflow-hidden max-h-[300px]"
            :class="mediaGridClass"
          >
            <!-- Two photos -->
            <template v-if="post.media.length === 2">
              <div
                v-for="(mediaItem, index) in post.media"
                :key="mediaItem.id"
                class="relative bg-gray-100 overflow-hidden aspect-square cursor-pointer"
                :class="index === 0 ? 'rounded-l-xl' : 'rounded-r-xl'"
                @click="openMediaModal(index)"
              >
                <video
                  v-if="mediaItem.media_type === 'video'"
                  controls
                  class="w-full h-full object-cover"
                  :src="buildMediaUrl(mediaItem.file_url)"
                  @play="pauseOtherVideos"
                ></video>
                <img
                  v-else
                  :src="buildMediaUrl(mediaItem.file_url)"
                  class="w-full h-full object-cover"
                />
              </div>
            </template>

            <!-- Three photos -->
            <template v-else-if="post.media.length === 3">
              <div
                class="row-span-2 relative bg-gray-100 overflow-hidden rounded-l-xl cursor-pointer"
                @click="openMediaModal(0)"
              >
                <video
                  v-if="post.media[0].media_type === 'video'"
                  controls
                  class="w-full h-full object-cover"
                  :src="buildMediaUrl(post.media[0].file_url)"
                  @play="pauseOtherVideos"
                ></video>
                <img
                  v-else
                  :src="buildMediaUrl(post.media[0].file_url)"
                  class="w-full h-full object-cover"
                />
              </div>
              <div
                class="relative bg-gray-100 overflow-hidden rounded-tr-xl cursor-pointer"
                @click="openMediaModal(1)"
              >
                <video
                  v-if="post.media[1].media_type === 'video'"
                  controls
                  class="w-full h-full object-cover"
                  :src="buildMediaUrl(post.media[1].file_url)"
                  @play="pauseOtherVideos"
                ></video>
                <img
                  v-else
                  :src="buildMediaUrl(post.media[1].file_url)"
                  class="w-full h-full object-cover"
                />
              </div>
              <div
                class="relative bg-gray-100 overflow-hidden rounded-br-xl cursor-pointer"
                @click="openMediaModal(2)"
              >
                <video
                  v-if="post.media[2].media_type === 'video'"
                  controls
                  class="w-full h-full object-cover"
                  :src="buildMediaUrl(post.media[2].file_url)"
                  @play="pauseOtherVideos"
                ></video>
                <img
                  v-else
                  :src="buildMediaUrl(post.media[2].file_url)"
                  class="w-full h-full object-cover"
                />
              </div>
            </template>

            <!-- Four or more photos -->
            <template v-else-if="post.media.length >= 4">
              <div
                class="row-span-2 relative bg-gray-100 overflow-hidden rounded-l-xl cursor-pointer"
                @click="openMediaModal(0)"
              >
                <video
                  v-if="post.media[0].media_type === 'video'"
                  controls
                  class="w-full h-full object-cover"
                  :src="buildMediaUrl(post.media[0].file_url)"
                  @play="pauseOtherVideos"
                ></video>
                <img
                  v-else
                  :src="buildMediaUrl(post.media[0].file_url)"
                  class="w-full h-full object-cover"
                />
              </div>

              <div
                class="relative bg-gray-100 overflow-hidden rounded-tr-xl cursor-pointer"
                @click="openMediaModal(1)"
              >
                <video
                  v-if="post.media[1].media_type === 'video'"
                  controls
                  class="w-full h-full object-cover"
                  :src="buildMediaUrl(post.media[1].file_url)"
                  @play="pauseOtherVideos"
                ></video>
                <img
                  v-else
                  :src="buildMediaUrl(post.media[1].file_url)"
                  class="w-full h-full object-cover"
                />
              </div>

              <div
                class="relative bg-gray-100 overflow-hidden rounded-br-xl cursor-pointer"
                @click="openMediaModal(2)"
              >
                <video
                  v-if="post.media[2].media_type === 'video'"
                  controls
                  class="w-full h-full object-cover"
                  :src="buildMediaUrl(post.media[2].file_url)"
                  @play="pauseOtherVideos"
                ></video>
                <img
                  v-else
                  :src="buildMediaUrl(post.media[2].file_url)"
                  class="w-full h-full object-cover"
                />

                <!-- More overlay for 4+ images -->
                <div
                  v-if="post.media.length > 3"
                  class="absolute bottom-2 right-2 bg-black bg-opacity-80 text-white rounded-lg px-3 py-1 flex items-center justify-center cursor-pointer"
                  @click.stop="openMediaModal(3)"
                >
                  <span class="text-lg font-bold">+{{ post.media.length - 3 }}</span>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- FIXED: Actions Footer with mobile layout showing counts next to text -->
      <footer
        v-if="!isEditing"
        ref="actionsFooterRef"
        class="px-3 md:px-4 pt-1 pb-2"
        :id="`actions-footer-${post.id}`"
      >
        <div
          class="border-t border-gray-200 pt-2 md:pt-3 flex items-center justify-between text-gray-600 mobile-actions-grid"
        >
          <!-- Like Button with Reactions -->
          <div class="relative flex-1 min-w-0 flex justify-center mobile-action-item">
            <div
              class="flex items-center justify-center w-full"
              @mouseenter="showReactionPicker"
              @mouseleave="hideReactionPicker"
            >
              <button
                @click="handleReaction('like')"
                :disabled="isLiking"
                class="flex flex-col md:flex-row items-center justify-center transition-all duration-200 hover:text-blue-500 disabled:opacity-50 group w-full mobile-action-button"
                :class="{ 'text-blue-500 font-semibold': post.is_liked_by_user }"
                data-cy="like-button"
              >
                <!-- Mobile: Icon on one line, Text + Count below -->
                <div class="flex items-center justify-center mb-0.5 md:mb-0">
                  <FontAwesomeIcon
                    :icon="faThumbsUp"
                    class="w-4 h-4 md:w-4 md:h-4 group-hover:scale-110 transition-transform duration-200 group-hover:text-blue-500 mobile-action-icon"
                    :class="post.is_liked_by_user ? 'text-blue-500 fill-current' : 'text-gray-400'"
                  />
                </div>

                <!-- Mobile: Text + Count in one line below the icon -->
                <div
                  class="md:hidden flex items-center justify-center gap-1 mobile-text-count-container"
                >
                  <span class="text-xs font-medium mobile-action-text">Like</span>
                  <span
                    data-cy="like-count"
                    class="text-xs font-medium mobile-action-count"
                    :class="{ 'text-blue-500': post.is_liked_by_user }"
                    >{{ post.like_count ?? 0 }}</span
                  >
                </div>

                <!-- Desktop: Text + Count in one line with icon -->
                <div class="hidden md:flex items-center gap-1">
                  <span class="text-sm font-medium mobile-action-label">Like</span>
                  <span
                    data-cy="like-count"
                    class="text-sm font-medium mobile-action-count"
                    :class="{ 'text-blue-500': post.is_liked_by_user }"
                    >{{ post.like_count ?? 0 }}</span
                  >
                </div>
              </button>
            </div>

            <!-- Reaction Picker with Tooltips -->
            <div
              v-if="showReactions"
              @mouseenter="cancelHideReactionPicker"
              @mouseleave="hideReactionPicker"
              class="absolute bottom-full left-1/2 transform -translate-x-1/4 mb-2 bg-white rounded-full shadow-xl border border-gray-200 px-2 md:px-3 py-1.5 md:py-2 flex items-center gap-1 md:gap-2 z-30 mobile-reaction-picker"
              :style="{ transform: 'translateX(calc(-25% - 1px))' }"
            >
              <div
                v-for="reaction in reactions"
                :key="reaction.name"
                class="relative"
                @mouseenter="setHoveredReaction(reaction.name)"
                @mouseleave="setHoveredReaction(null)"
              >
                <button
                  @click="handleReaction(reaction.name)"
                  class="p-1 md:p-1.5 rounded-full hover:scale-125 transform transition-all duration-200 hover:bg-gray-100 relative"
                  :class="reaction.color"
                >
                  <FontAwesomeIcon :icon="reaction.icon" class="w-4 h-4 md:w-5 md:h-5" />

                  <!-- Tooltip -->
                  <div
                    v-if="hoveredReaction === reaction.name"
                    class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-1 md:mb-2 bg-gray-900 text-white text-xs font-medium py-1 px-2 rounded-md whitespace-nowrap z-50"
                  >
                    {{ reaction.label }}
                    <div
                      class="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"
                    ></div>
                  </div>
                </button>
              </div>
            </div>
          </div>

          <!-- Comment Button -->
          <button
            @click="toggleCommentDisplay"
            class="flex flex-col md:flex-row items-center justify-center transition-all duration-200 group flex-1 min-w-0 mobile-action-item mobile-action-button"
            :class="{ 'text-[#d97706] font-semibold': showComments }"
          >
            <!-- Mobile: Icon on one line, Text + Count below -->
            <div class="flex items-center justify-center mb-0.5 md:mb-0">
              <FontAwesomeIcon
                :icon="faCommentDots"
                class="w-4 h-4 md:w-4 md:h-4 group-hover:scale-110 transition-transform duration-200 mobile-action-icon"
                :class="
                  showComments
                    ? 'text-[#d97706] fill-current'
                    : 'text-gray-400 group-hover:text-[#d97706]'
                "
              />
            </div>

            <!-- Mobile: Text + Count in one line below the icon -->
            <div
              class="md:hidden flex items-center justify-center gap-1 mobile-text-count-container"
            >
              <span class="text-xs font-medium mobile-action-text">Comment</span>
              <span
                class="text-xs font-medium mobile-action-count group-hover:text-[#d97706]"
                :class="{ 'text-[#d97706]': showComments }"
                >{{ post.comment_count ?? 0 }}</span
              >
            </div>

            <!-- Desktop: Text + Count in one line with icon -->
            <div class="hidden md:flex items-center gap-1">
              <span
                class="text-sm font-medium group-hover:text-[#d97706] mobile-action-label"
                :class="{ 'text-[#d97706]': showComments }"
                >Comment</span
              >
              <span
                class="text-sm font-medium mobile-action-count group-hover:text-[#d97706]"
                :class="{ 'text-[#d97706]': showComments }"
                >{{ post.comment_count ?? 0 }}</span
              >
            </div>
          </button>

          <!-- Repost Button (Placeholder) -->
          <button
            class="flex flex-col md:flex-row items-center justify-center transition-all duration-200 hover:text-rose-500 group flex-1 min-w-0 mobile-action-item mobile-action-button"
          >
            <!-- Mobile: Icon on one line, Text below -->
            <div class="flex items-center justify-center mb-0.5 md:mb-0">
              <FontAwesomeIcon
                :icon="faRepeat"
                class="w-4 h-4 md:w-4 md:h-4 group-hover:scale-110 transition-transform duration-200 text-gray-400 group-hover:text-rose-500 mobile-action-icon"
              />
            </div>

            <!-- Mobile: Text only below the icon -->
            <div class="md:hidden">
              <span class="text-xs font-medium mobile-action-text">Repost</span>
            </div>

            <!-- Desktop: Text only with icon -->
            <div class="hidden md:flex items-center gap-1">
              <span class="text-sm font-medium mobile-action-label">Repost</span>
            </div>
          </button>

          <!-- Send Button (Placeholder) -->
          <button
            class="flex flex-col md:flex-row items-center justify-center transition-all duration-200 hover:text-purple-600 group flex-1 min-w-0 mobile-action-item mobile-action-button"
          >
            <!-- Mobile: Icon on one line, Text below -->
            <div class="flex items-center justify-center mb-0.5 md:mb-0">
              <FontAwesomeIcon
                :icon="faPaperPlane"
                class="w-4 h-4 md:w-4 md:h-4 group-hover:scale-110 transition-transform duration-200 text-gray-400 group-hover:text-purple-600 mobile-action-icon"
              />
            </div>

            <!-- Mobile: Text only below the icon -->
            <div class="md:hidden">
              <span class="text-xs font-medium mobile-action-text">Send</span>
            </div>

            <!-- Desktop: Text only with icon -->
            <div class="hidden md:flex items-center gap-1">
              <span class="text-sm font-medium mobile-action-label">Send</span>
            </div>
          </button>
        </div>
      </footer>

      <!-- IMPROVED Comment Section with NEW LAYOUT -->
      <transition name="comment-slide">
        <section
          v-if="!isEditing && showComments"
          class="bg-white border-t border-gray-100 rounded-b-2xl overflow-hidden comment-section"
        >
          <!-- Comments List on TOP -->
          <div
            ref="commentsScrollContainer"
            class="max-h-64 md:max-h-96 overflow-y-auto p-2 md:p-4 border-b border-gray-200"
          >
            <div v-if="isLoadingComments" class="text-sm text-gray-500 text-center py-4">
              Loading comments...
            </div>
            <div v-else-if="commentError" class="text-red-600 text-sm text-center py-4">
              Error loading comments: {{ commentError }}
            </div>
            <div v-else>
              <!-- Display visible comments (paginated) -->
              <div v-for="comment in visibleComments" :key="comment.id" class="comment-item">
                <CommentItem
                  :comment="comment"
                  :parentPostType="props.post.post_type"
                  :parentObjectId="props.post.object_id"
                  :parentPostActualId="props.post.id"
                  @report-content="handleCommentReport"
                  data-cy="comment-container"
                />
              </div>

              <!-- Show More / Show Less Buttons -->
              <div v-if="commentsForThisPost.length > 4" class="flex justify-center mt-3">
                <button
                  v-if="visibleCommentCount < commentsForThisPost.length"
                  @click="loadMoreComments"
                  class="flex items-center gap-2 px-3 md:px-4 py-2 text-xs md:text-sm font-medium text-blue-600 hover:text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg transition-all duration-200 border border-blue-200 shadow-sm"
                >
                  <FontAwesomeIcon :icon="faChevronDown" class="w-3 h-3 md:w-4 md:h-4" />
                  Show More ({{ commentsForThisPost.length - visibleCommentCount }}
                  remaining)
                </button>

                <button
                  v-else-if="visibleCommentCount > 4"
                  @click="showLessComments"
                  class="flex items-center gap-2 px-3 md:px-4 py-2 text-xs md:text-sm font-medium text-gray-600 hover:text-gray-700 bg-gray-50 hover:bg-gray-100 rounded-lg transition-all duration-200 border border-gray-200 shadow-sm"
                >
                  <FontAwesomeIcon :icon="faChevronUp" class="w-3 h-3 md:w-4 md:h-4" />
                  Show Less Comments
                </button>
              </div>

              <!-- Updated No Comments Box -->
              <div
                v-if="commentsForThisPost.length === 0"
                class="flex flex-col items-center justify-center py-2 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border border-blue-100 mx-1 md:mx-2 my-2"
              >
                <div
                  class="w-6 h-6 md:w-7 md:h-7 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center mb-1 shadow-sm"
                >
                  <FontAwesomeIcon :icon="faComment" class="w-3 h-3 md:w-3 md:h-3 text-white" />
                </div>
                <p class="text-[11px] font-medium text-blue-700 leading-tight">
                  Be first to comment
                </p>
              </div>
            </div>
          </div>

          <!-- Simple Comment Input (FB / Instagram style) -->
          <form
            v-if="isAuthenticated"
            @submit.prevent="handleCommentSubmit"
            class="comment-input-form flex items-center gap-2 px-3 py-2 bg-white border-t border-gray-100"
            data-cy="comment-input"
          >
            <!-- User Avatar -->
            <img
              :src="
                getAvatarUrl(
                  authStore.currentUser?.picture,
                  authStore.currentUser?.first_name,
                  authStore.currentUser?.last_name,
                )
              "
              alt="your avatar"
              class="w-8 h-8 rounded-full object-cover flex-shrink-0 bg-gray-200"
            />

            <!-- Input + inline actions -->
            <div class="relative flex-1">
              <input
                v-model="newCommentContent"
                type="text"
                placeholder="Add a comment..."
                class="w-full text-sm px-4 py-2 pr-20 rounded-full bg-gray-100 border border-transparent focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white"
              />

              <!-- Right-side actions (inside input) -->
              <div class="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
                <button
                  type="button"
                  @click="handleGifClick"
                  class="text-purple-600 hover:text-purple-700 flex items-center justify-center"
                  title="Add GIF"
                >
                  <span class="text-[10px] font-bold leading-none">GIF</span>
                </button>

                <button
                  type="button"
                  @click="handleEmojiClick"
                  class="text-yellow-500 hover:text-yellow-600 flex items-center justify-center"
                  title="Add emoji"
                >
                  <FontAwesomeIcon :icon="faFaceLaughBeam" class="w-4 h-4" />
                </button>
              </div>
            </div>

            <!-- Send Button -->
            <button
              type="submit"
              data-cy="comment-submit-button"
              :disabled="isCreatingComment || !newCommentContent.trim()"
              class="text-blue-600 hover:text-blue-700 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center"
              title="Post"
            >
              <FontAwesomeIcon :icon="faPaperPlane" class="w-5 h-5" />
            </button>
          </form>
        </section>
      </transition>
    </article>

    <!-- EDIT MODE MODAL - Centered overlay -->
    <div
      v-if="isEditing"
      class="fixed inset-0 bg-black/50 z-[10000] flex items-center justify-center p-0 md:p-4 backdrop-blur-sm overflow-hidden"
      @click.self="cancelEdit"
    >
      <div
        class="bg-white rounded-none md:rounded-2xl shadow-2xl w-full h-full md:h-auto md:max-h-[90vh] overflow-y-auto md:max-w-2xl mx-auto no-scrollbar"
        @click.stop
      >
        <!-- FORM FOR EDITING A REGULAR TEXT/MEDIA POST -->
        <div v-if="!post.poll" class="p-4 pb-28 md:p-6 md:pb-6">
          <form @submit.prevent="handleUpdatePost" novalidate class="space-y-4">
            <!-- Error Display -->
            <div
              v-if="localEditError || editProcessingError"
              class="bg-red-50 border border-red-200 text-red-700 px-3 py-2 md:px-4 md:py-3 rounded-xl relative mb-4 flex items-center gap-2 md:gap-3 text-sm md:text-base"
            >
              <FontAwesomeIcon
                :icon="['fas', 'exclamation-circle']"
                class="text-red-500 flex-shrink-0"
              />
              <span class="block md:inline">{{ localEditError || editProcessingError }}</span>
            </div>

            <div class="bg-white rounded-lg border border-gray-200 p-3">
              <MentionAutocomplete
                ref="editTextAreaRef"
                v-model="editContent"
                placeholder="What's on your mind?"
                :rows="2"
                class="text-sm md:text-base w-full border-0 focus:ring-0 p-0 resize-none word-break-fix"
              />
            </div>

            <!-- Media Preview Section with Drag & Drop -->
            <div
              v-if="combinedMedia.length > 0"
              class="bg-white rounded-lg border border-gray-200 p-4 drag-container"
            >
              <h4 class="text-sm font-medium text-gray-700 mb-3 flex items-center justify-between">
                <div class="flex items-center">
                  <FontAwesomeIcon :icon="faImage" class="text-blue-500 mr-2" />
                  Media Attachments
                  <span class="ml-2 text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                    {{ combinedMedia.length }} item{{ combinedMedia.length > 1 ? 's' : '' }}
                  </span>
                </div>
                <div class="text-xs text-gray-500 flex items-center">
                  <FontAwesomeIcon :icon="faGripVertical" class="mr-1" />
                  Drag to reorder
                </div>
              </h4>

              <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                <!-- Combined Media with Drag & Drop -->
                <div
                  v-for="(item, index) in combinedMedia"
                  :key="item.id"
                  :data-drag-index="index"
                  draggable="true"
                  @dragstart="handleDragStart(index)"
                  @dragover="handleDragOver($event, index)"
                  @dragleave="handleDragLeave"
                  @drop="handleDrop($event, index)"
                  @dragend="handleDragEnd"
                  class="relative group transition-all duration-200"
                  :class="{
                    'scale-105 border-2 border-blue-400 shadow-md': dragOverItemIndex === index,
                    'cursor-grab': !isDragging,
                    'cursor-grabbing': isDragging,
                  }"
                >
                  <div
                    class="w-full h-24 rounded-lg overflow-hidden border border-gray-200 bg-gray-50 flex items-center justify-center"
                  >
                    <!-- Existing Image -->
                    <div
                      v-if="item.type === 'existing' && item.media.media_type === 'image'"
                      class="relative w-full h-full"
                    >
                      <img
                        :src="buildMediaUrl(item.media.file_url)"
                        class="w-full h-full object-cover"
                      />
                    </div>

                    <!-- Existing Video -->
                    <div
                      v-else-if="item.type === 'existing' && item.media.media_type === 'video'"
                      class="relative w-full h-full"
                    >
                      <video
                        class="w-full h-full object-cover"
                        :src="buildMediaUrl(item.media.file_url)"
                        preload="metadata"
                        @play="pauseOtherVideos"
                      ></video>
                      <div
                        class="absolute inset-0 bg-black bg-opacity-20 flex items-center justify-center"
                      >
                        <FontAwesomeIcon :icon="faPlay" class="text-white text-lg" />
                      </div>
                    </div>

                    <!-- New Image -->
                    <div v-else-if="item.type === 'new-image'" class="relative w-full h-full">
                      <img :src="getObjectURL(item.file)" class="w-full h-full object-cover" />
                    </div>

                    <!-- New Video -->
                    <div v-else-if="item.type === 'new-video'" class="relative w-full h-full">
                      <video
                        v-if="newVideoPreviewUrls[item.index]"
                        class="w-full h-full object-cover"
                        :src="getObjectURL(item.file)"
                        preload="metadata"
                        @play="pauseOtherVideos"
                      ></video>
                      <div
                        v-else
                        class="w-full h-full flex flex-col items-center justify-center p-2 text-center bg-gradient-to-br from-blue-50 to-purple-50"
                      >
                        <FontAwesomeIcon
                          :icon="['fas', 'video']"
                          class="text-purple-500 text-sm mb-1"
                        />
                        <span class="text-xs text-gray-700 font-medium truncate w-full px-1">{{
                          item.file.name
                        }}</span>
                      </div>
                      <div
                        class="absolute inset-0 bg-black bg-opacity-20 flex items-center justify-center"
                      >
                        <FontAwesomeIcon :icon="faPlay" class="text-white text-lg" />
                      </div>
                    </div>

                    <!-- Drag Handle -->
                    <div
                      class="absolute top-1 left-1 bg-black bg-opacity-50 text-white rounded p-1 cursor-grab"
                    >
                      <FontAwesomeIcon :icon="faGripVertical" class="w-2 h-2" />
                    </div>

                    <!-- Processing Badges for New Files -->
                    <div
                      v-if="
                        (item.type === 'new-image' || item.type === 'new-video') &&
                        item.file.compressed
                      "
                      class="absolute top-1 right-1 bg-green-500 text-white text-xs rounded-full px-2 py-0.5"
                      title="Compressed"
                    >
                      <FontAwesomeIcon :icon="['fas', 'compress']" class="w-2 h-2" />
                    </div>
                    <div
                      v-if="
                        (item.type === 'new-image' || item.type === 'new-video') &&
                        item.file.trimmed
                      "
                      class="absolute top-1 right-1 bg-blue-500 text-white text-xs rounded-full px-2 py-0.5"
                      title="Trimmed"
                    >
                      <FontAwesomeIcon :icon="['fas', 'cut']" class="w-2 h-2" />
                    </div>
                  </div>

                  <button
                    @click="handleRemoveMedia(item)"
                    type="button"
                    class="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs hover:bg-red-600 transition-all duration-200 opacity-0 group-hover:opacity-100 shadow-md"
                  >
                    <FontAwesomeIcon :icon="faXmark" class="w-3 h-3" />
                  </button>

                  <!-- Labels below the media -->
                  <div class="text-xs text-center mt-1">
                    <span
                      v-if="item.type === 'existing'"
                      class="text-gray-600 bg-gray-100 px-2 py-0.5 rounded-full"
                    >
                      Current
                    </span>
                    <span v-else class="text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">
                      New
                    </span>
                    <div class="mt-0.5 text-gray-500">
                      {{ getMediaType(item) }}
                    </div>
                    <!-- Size info for new files -->
                    <div
                      v-if="
                        (item.type === 'new-image' || item.type === 'new-video') &&
                        item.file.finalSize
                      "
                      class="text-xs text-green-600 mt-0.5"
                    >
                      {{ (item.file.finalSize! / 1024 / 1024).toFixed(2) }}MB
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="flex flex-col md:flex-row justify-between items-center gap-3 pt-2">
              <div class="flex gap-2 w-full md:w-auto">
                <!-- Image Upload Button with enhanced validation -->
                <div class="relative group flex-1 md:flex-none">
                  <label
                    for="add-images-edit"
                    class="flex items-center justify-center gap-2 px-3 md:px-4 py-2 bg-white border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 cursor-pointer transition-all duration-200 text-sm font-medium shadow-sm w-full"
                    :class="{
                      'cursor-not-allowed opacity-50':
                        newImageFiles.length >= MAX_IMAGES || editRemainingPoints < IMAGE_POINTS,
                    }"
                  >
                    <FontAwesomeIcon :icon="['fas', 'image']" class="w-4 h-4 text-green-500" />
                    <span class="hidden md:inline">Add Images</span>
                    <span class="md:hidden">Images</span>
                    <span
                      v-if="newImageFiles.length > 0"
                      class="ml-1 bg-green-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center"
                    >
                      {{ newImageFiles.length }}
                    </span>
                  </label>
                  <input
                    id="add-images-edit"
                    type="file"
                    @change="handleNewFilesEdit($event, 'image')"
                    multiple
                    :accept="SUPPORTED_IMAGE_MIME_TYPES.join(',')"
                    class="hidden"
                    :disabled="
                      newImageFiles.length >= MAX_IMAGES || editRemainingPoints < IMAGE_POINTS
                    "
                  />
                  <!-- Updated Tooltip -->
                  <div
                    class="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xs rounded-lg py-1 px-2 opacity-0 group-hover:opacity-100 transition-all duration-200 pointer-events-none whitespace-nowrap shadow-lg z-50 upload-tooltip"
                  >
                    {{
                      newImageFiles.length >= MAX_IMAGES
                        ? `Maximum ${MAX_IMAGES} images allowed`
                        : editRemainingPoints < IMAGE_POINTS
                          ? 'Limit exceeded'
                          : `Add Images (up to ${MAX_IMAGES - newImageFiles.length})`
                    }}
                  </div>
                </div>

                <!-- Video Upload Button with enhanced validation -->
                <div class="relative group flex-1 md:flex-none">
                  <label
                    for="add-videos-edit"
                    class="flex items-center justify-center gap-2 px-3 md:px-4 py-2 bg-white border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 cursor-pointer transition-all duration-200 text-sm font-medium shadow-sm w-full"
                    :class="{
                      'cursor-not-allowed opacity-50':
                        newVideoFiles.length >= MAX_VIDEOS || editRemainingPoints < VIDEO_POINTS,
                    }"
                  >
                    <FontAwesomeIcon :icon="['fas', 'video']" class="w-4 h-4 text-blue-500" />
                    <span class="hidden md:inline">Add Videos</span>
                    <span class="md:hidden">Videos</span>
                    <span
                      v-if="newVideoFiles.length > 0"
                      class="ml-1 bg-blue-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center"
                    >
                      {{ newVideoFiles.length }}
                    </span>
                  </label>
                  <input
                    id="add-videos-edit"
                    type="file"
                    @change="handleNewFilesEdit($event, 'video')"
                    multiple
                    :accept="SUPPORTED_VIDEO_MIME_TYPES.join(',')"
                    class="hidden"
                    :disabled="
                      newVideoFiles.length >= MAX_VIDEOS || editRemainingPoints < VIDEO_POINTS
                    "
                  />
                  <!-- Updated Tooltip -->
                  <div
                    class="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xs rounded-lg py-1 px-2 opacity-0 group-hover:opacity-100 transition-all duration-200 pointer-events-none whitespace-nowrap shadow-lg z-50 upload-tooltip"
                  >
                    {{
                      newVideoFiles.length >= MAX_VIDEOS
                        ? `Maximum ${MAX_VIDEOS} videos allowed`
                        : editRemainingPoints < VIDEO_POINTS
                          ? 'Limit exceeded'
                          : `Add Videos (up to ${MAX_VIDEOS - newVideoFiles.length})`
                    }}
                  </div>
                </div>
              </div>

              <div class="flex gap-2 w-full md:w-auto">
                <button
                  type="button"
                  @click="cancelEdit"
                  class="px-4 md:px-6 py-2.5 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-all duration-200 text-sm shadow-sm w-full md:w-auto"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  :disabled="post.isUpdating || isCompressing"
                  class="px-4 md:px-6 py-2.5 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-lg transition-all duration-200 disabled:bg-blue-300 disabled:cursor-not-allowed text-sm shadow-md flex items-center justify-center gap-2 w-full md:w-auto"
                >
                  <FontAwesomeIcon
                    :icon="
                      post.isUpdating || isCompressing
                        ? ['fas', 'spinner']
                        : ['fas', 'pen-to-square']
                    "
                    class="w-4 h-4"
                    :class="{ 'animate-spin': post.isUpdating || isCompressing }"
                  />
                  {{
                    post.isUpdating ? 'Saving...' : isCompressing ? 'Processing...' : 'Save Changes'
                  }}
                </button>
              </div>
            </div>
          </form>
        </div>

        <!-- FORM FOR EDITING A POLL POST -->
        <div v-else class="p-4 pb-28 md:p-6 md:pb-6">
          <form @submit.prevent="handleUpdatePoll" novalidate class="space-y-4">
            <div
              v-if="localEditError"
              class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm flex items-center"
            >
              <FontAwesomeIcon :icon="faXmark" class="text-red-500 mr-2" />
              {{ localEditError }}
            </div>

            <div class="bg-white rounded-lg border border-gray-200 p-5 space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Poll Question</label>
                <input
                  type="text"
                  v-model="editPollQuestion"
                  placeholder="Ask a question..."
                  class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm transition-all duration-200 word-break-fix"
                  maxlength="255"
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-3">Poll Options</label>
                <div class="space-y-2">
                  <div
                    v-for="(option, index) in editPollOptions"
                    :key="option.id || `new-${index}`"
                    class="flex items-center gap-3 group"
                  >
                    <div class="flex-grow relative">
                      <input
                        type="text"
                        v-model="option.text"
                        :placeholder="`Option ${index + 1}`"
                        class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm transition-all duration-200 pr-10 word-break-fix"
                        maxlength="100"
                      />
                      <div
                        class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400"
                      >
                        {{ option.text.length }}/100
                      </div>
                    </div>
                    <button
                      @click.prevent="removePollOptionFromEdit(index)"
                      :disabled="editPollOptions.length <= 2"
                      class="text-gray-400 hover:text-red-500 disabled:opacity-30 disabled:cursor-not-allowed transition-colors duration-200 p-2 rounded-full hover:bg-red-50"
                      type="button"
                      title="Remove option"
                    >
                      <FontAwesomeIcon :icon="faXmark" class="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <button
                  @click.prevent="addPollOptionToEdit"
                  :disabled="editPollOptions.length >= 5"
                  class="mt-3 flex items-center gap-2 text-blue-500 hover:text-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 text-sm font-medium"
                  type="button"
                >
                  <FontAwesomeIcon :icon="faPlus" class="w-4 h-4" />
                  Add Option ({{ editPollOptions.length }}/5)
                </button>
              </div>
            </div>

            <div class="flex justify-end gap-3 pt-2">
              <button
                type="button"
                @click="cancelEdit"
                class="px-6 py-2.5 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-all duration-200 text-sm shadow-sm"
              >
                Cancel
              </button>
              <button
                type="submit"
                :disabled="post.isUpdating"
                class="px-6 py-2.5 bg-purple-500 hover:bg-purple-600 text-white font-medium rounded-lg transition-all duration-200 disabled:bg-purple-300 disabled:cursor-not-allowed text-sm shadow-md flex items-center gap-2"
              >
                <FontAwesomeIcon
                  :icon="post.isUpdating ? faRepeat : faPenToSquare"
                  class="w-4 h-4"
                  :class="{ 'animate-spin': post.isUpdating }"
                />
                {{ post.isUpdating ? 'Updating...' : 'Update Poll' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- FIXED Enhanced Image/Video Preview Modal -->
    <div
      v-if="showMediaModal"
      class="fixed inset-0 bg-black/95 flex items-center justify-center z-[10000] p-4 backdrop-blur-sm"
      @click="closeMediaModal"
    >
      <div
        class="flex flex-col lg:flex-row w-full max-w-8xl max-h-[90vh] bg-white rounded-2xl overflow-hidden shadow-2xl relative mobile-modal-container"
        @click.stop
      >
        <!-- Close Button -->
        <button
          @click="closeMediaModal"
          class="absolute top-4 right-4 z-50 bg-white/90 hover:bg-white text-gray-800 hover:text-black rounded-full w-10 h-10 flex items-center justify-center transition-all duration-200 shadow-lg border border-gray-200"
        >
          <FontAwesomeIcon :icon="faXmark" class="w-5 h-5" />
        </button>

        <!-- Left Side - Media Display -->
        <div
          class="flex-1 flex items-center justify-center bg-white lg:bg-white relative min-h-[50vh] lg:min-h-0 portrait-media-container"
        >
          <!-- Mobile Header (Username + Timestamp) -->
          <div
            class="absolute top-0 left-0 right-0 z-30 px-4 pt-4 pb-6 flex items-center gap-3 bg-gradient-to-b from-white to-white text-black lg:hidden"
          >
            <img
              :src="
                getAvatarUrl(post.author.picture, post.author.first_name, post.author.last_name)
              "
              alt="author avatar"
              class="w-8 h-8 rounded-full object-cover bg-gray-200 border border-white/30"
            />
            <div class="min-w-0 flex-1">
              <div class="text-sm font-semibold truncate">{{ post.author.username }}</div>
              <div class="text-xs text-black/70 truncate">{{ formattedTimestamp }}</div>
            </div>
          </div>
          <!-- Navigation Arrows -->
          <button
            v-if="post.media.length > 1"
            @click="prevMediaModal"
            class="absolute left-2 lg:left-0 top-1/2 transform -translate-y-1/2 text-white lg:text-black text-xl z-20 w-12 h-12 flex items-center justify-center transition-all duration-200 rounded-full bg-black/30 hover:bg-black/45 lg:bg-transparent lg:hover:bg-transparent"
          >
            <FontAwesomeIcon :icon="faChevronLeft" class="w-5 h-5" />
          </button>

          <button
            v-if="post.media.length > 1"
            @click="nextMediaModal"
            class="absolute right-2 lg:right-0 top-1/2 transform -translate-y-1/2 text-white lg:text-black text-xl z-20 w-12 h-12 flex items-center justify-center transition-all duration-200 rounded-full bg-black/30 hover:bg-black/45 lg:bg-transparent lg:hover:bg-transparent"
          >
            <FontAwesomeIcon :icon="faChevronRight" class="w-5 h-5" />
          </button>

          <!-- Media Display -->
          <div
            class="flex items-center justify-center h-full w-full p-4 lg:p-8 portrait-media-content"
          >
            <video
              v-if="post.media[modalMediaIndex].media_type === 'video'"
              controls
              class="max-w-full max-h-[70vh] object-contain rounded-lg portrait-media"
              :src="buildMediaUrl(post.media[modalMediaIndex].file_url)"
              autoplay
              @play="pauseOtherVideos"
            ></video>
            <img
              v-else
              :src="buildMediaUrl(post.media[modalMediaIndex].file_url)"
              class="max-w-full max-h-[70vh] object-contain rounded-lg portrait-media"
            />
          </div>

          <!-- Image Counter -->
          <div
            v-if="post.media.length > 1"
            class="absolute bottom-4 left-1/2 transform -translate-x-1/2 text-white bg-black/50 rounded-full px-4 py-2 text-sm backdrop-blur-sm media-counter"
          >
            {{ modalMediaIndex + 1 }} / {{ post.media.length }}
          </div>
        </div>

        <!-- Right Side - Actions and Info (Hidden on Mobile) -->
        <div
          v-if="!isMobile"
          class="w-full lg:w-96 bg-white flex flex-col border-t lg:border-t-0 lg:border-l border-gray-200 max-h-[50vh] lg:max-h-full"
        >
          <!-- Post Header -->
          <div class="p-8 border-b border-gray-100 flex-shrink-0">
            <div class="flex items-center gap-3">
              <img
                :src="
                  getAvatarUrl(post.author.picture, post.author.first_name, post.author.last_name)
                "
                alt="author avatar"
                class="w-10 h-10 rounded-full object-cover bg-gray-200"
              />
              <div>
                <h3 class="font-semibold text-gray-900 text-sm word-break-fix">
                  {{ post.author.username }}
                </h3>
                <p class="text-xs text-gray-500">{{ formattedTimestamp }}</p>
              </div>
            </div>
            <div v-if="post.content" class="mt-3">
              <p class="text-sm text-gray-700 leading-relaxed word-break-fix">
                {{ post.content }}
              </p>
            </div>
          </div>

          <!-- Action Buttons with REACTIONS -->
          <div class="p-0 border-b border-gray-100 flex-shrink-0">
            <div class="flex items-center justify-between gap-2">
              <!-- Like Button with Reactions -->
              <div class="relative flex-1 min-w-0">
                <div
                  class="flex flex-col items-center gap-1"
                  @mouseenter="showModalReactionPicker"
                  @mouseleave="hideModalReactionPicker"
                >
                  <button
                    @click="handleModalReaction('like')"
                    :disabled="isLiking"
                    class="flex flex-col items-center gap-1 px-3 py-2 rounded-lg transition-all duration-200 hover:bg-gray-50 disabled:opacity-50 group w-full"
                    :class="{ 'text-blue-500 font-semibold': post.is_liked_by_user }"
                  >
                    <FontAwesomeIcon
                      :icon="faThumbsUp"
                      class="w-5 h-5 group-hover:scale-110 transition-transform duration-200"
                      :class="
                        post.is_liked_by_user ? 'text-blue-500 fill-current' : 'text-gray-400'
                      "
                    />
                    <span class="text-xs font-medium truncate w-full text-center">{{
                      post.like_count ?? 0
                    }}</span>
                  </button>
                </div>

                <!-- Reaction Picker for Modal -->
                <div
                  v-if="showModalReactions"
                  @mouseenter="cancelHideModalReactionPicker"
                  @mouseleave="hideModalReactionPicker"
                  class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 bg-white rounded-full shadow-xl border border-gray-200 px-2 py-1.5 flex items-center gap-1 z-30"
                >
                  <div
                    v-for="reaction in reactions"
                    :key="reaction.name"
                    class="relative"
                    @mouseenter="setHoveredModalReaction(reaction.name)"
                    @mouseleave="setHoveredModalReaction(null)"
                  >
                    <button
                      @click="handleModalReaction(reaction.name)"
                      class="p-1 rounded-full hover:scale-125 transform transition-all duration-200 hover:bg-gray-100 relative"
                      :class="reaction.color"
                    >
                      <FontAwesomeIcon :icon="reaction.icon" class="w-4 h-4" />

                      <!-- Tooltip -->
                      <div
                        v-if="hoveredModalReaction === reaction.name"
                        class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-1 bg-gray-900 text-white text-xs font-medium py-1 px-2 rounded-md whitespace-nowrap z-50"
                      >
                        {{ reaction.label }}
                        <div
                          class="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"
                        ></div>
                      </div>
                    </button>
                  </div>
                </div>
              </div>

              <!-- Comment Button -->
              <button
                @click="toggleCommentDisplay"
                class="flex flex-col items-center gap-1 px-3 py-2 rounded-lg transition-all duration-200 hover:bg-gray-50 group flex-1 min-w-0"
              >
                <FontAwesomeIcon
                  :icon="faCommentDots"
                  class="w-5 h-5 group-hover:scale-110 transition-transform duration-200 text-gray-400 group-hover:text-[#d97706]"
                />
                <span
                  class="text-xs font-medium truncate w-full text-center group-hover:text-[#d97706]"
                  >{{ post.comment_count ?? 0 }}</span
                >
              </button>

              <!-- Repost Button -->
              <button
                class="flex flex-col items-center gap-1 px-3 py-2 rounded-lg transition-all duration-200 hover:bg-gray-50 group flex-1 min-w-0"
              >
                <FontAwesomeIcon
                  :icon="faRepeat"
                  class="w-5 h-5 group-hover:scale-110 transition-transform duration-200 text-gray-400 group-hover:text-rose-500"
                />
                <span
                  class="text-xs font-medium truncate w-full text-center group-hover:text-rose-500"
                  >Repost</span
                >
              </button>

              <!-- Send Button -->
              <button
                class="flex flex-col items-center gap-1 px-3 py-2 rounded-lg transition-all duration-200 hover:bg-gray-50 group flex-1 min-w-0"
              >
                <FontAwesomeIcon
                  :icon="faPaperPlane"
                  class="w-5 h-5 group-hover:scale-110 transition-transform duration-200 text-gray-400 group-hover:text-purple-600"
                />
                <span
                  class="text-xs font-medium truncate w-full text-center group-hover:text-purple-600"
                  >Send</span
                >
              </button>
            </div>
          </div>

          <!-- Comments Preview -->
          <div class="flex-1 overflow-y-auto p-4">
            <h4 class="font-semibold text-gray-900 text-sm mb-3">Comments</h4>
            <div v-if="isLoadingComments" class="text-sm text-gray-500 text-center py-4">
              Loading comments...
            </div>
            <div v-else-if="commentError" class="text-red-600 text-sm text-center py-4">
              Error loading comments: {{ commentError }}
            </div>
            <div v-else-if="commentsForThisPost.length === 0" class="text-center py-4">
              <div
                class="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center mx-auto mb-2 shadow-sm"
              >
                <FontAwesomeIcon :icon="faComment" class="w-4 h-4 text-white" />
              </div>
              <p class="text-sm font-medium text-blue-700">No comments</p>
            </div>
            <div v-else class="space-y-3">
              <!-- Use CommentItem component with hide-date prop -->
              <div v-for="comment in visibleComments" :key="comment.id" class="comment-item">
                <CommentItem
                  :comment="comment"
                  :parentPostType="props.post.post_type"
                  :parentObjectId="props.post.object_id"
                  :parentPostActualId="props.post.id"
                  :hide-date="true"
                  @report-content="handleModalCommentReport"
                  data-cy="comment-container"
                />
              </div>

              <!-- Show More / Show Less Buttons for Modal -->
              <div v-if="commentsForThisPost.length > 4" class="flex justify-center mt-3">
                <button
                  v-if="visibleCommentCount < commentsForThisPost.length"
                  @click="loadMoreComments"
                  class="flex items-center gap-2 px-3 py-2 text-xs font-medium text-blue-600 hover:text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg transition-all duration-200 border border-blue-200 shadow-sm"
                >
                  <FontAwesomeIcon :icon="faChevronDown" class="w-3 h-3" />
                  Show More ({{ commentsForThisPost.length - visibleCommentCount }}
                  remaining)
                </button>

                <button
                  v-else-if="visibleCommentCount > 4"
                  @click="showLessComments"
                  class="flex items-center gap-2 px-3 py-2 text-xs font-medium text-gray-600 hover:text-gray-700 bg-gray-50 hover:bg-gray-100 rounded-lg transition-all duration-200 border border-gray-200 shadow-sm"
                >
                  <FontAwesomeIcon :icon="faChevronUp" class="w-3 h-3" />
                  Show Less Comments
                </button>
              </div>
            </div>
          </div>

          <!-- Comment Input in Modal (Simple) -->
          <form
            v-if="isAuthenticated"
            @submit.prevent="handleCommentSubmit"
            class="p-4 border-t border-gray-100 bg-gray-50 flex-shrink-0"
          >
            <div class="flex items-center gap-2">
              <img
                :src="
                  getAvatarUrl(
                    authStore.currentUser?.picture,
                    authStore.currentUser?.first_name,
                    authStore.currentUser?.last_name,
                  )
                "
                alt="your avatar"
                class="w-8 h-8 rounded-full object-cover flex-shrink-0 bg-gray-200"
              />

              <div class="relative flex-1">
                <input
                  v-model="newCommentContent"
                  type="text"
                  placeholder="Add a comment..."
                  class="w-full text-sm px-4 py-2 pr-20 rounded-full bg-white border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />

                <div class="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
                  <button
                    type="button"
                    @click="handleGifClick"
                    class="text-purple-600 hover:text-purple-700 flex items-center justify-center"
                    title="Add GIF"
                  >
                    <span class="text-[10px] font-bold leading-none">GIF</span>
                  </button>

                  <button
                    type="button"
                    @click="handleEmojiClick"
                    class="text-yellow-500 hover:text-yellow-600 flex items-center justify-center"
                    title="Add emoji"
                  >
                    <FontAwesomeIcon :icon="faFaceLaughBeam" class="w-4 h-4" />
                  </button>
                </div>
              </div>

              <button
                type="submit"
                data-cy="comment-submit-button"
                :disabled="isCreatingComment || !newCommentContent.trim()"
                class="text-blue-600 hover:text-blue-700 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center"
                title="Post"
              >
                <FontAwesomeIcon :icon="faPaperPlane" class="w-5 h-5" />
              </button>
            </div>
          </form>
        </div>

        <!-- REPORT MODAL FOR PREVIEW COMMENTS -->
        <ReportFormModal
          :is-open="isModalReportModalOpen"
          :target="modalReportTarget"
          @close="isModalReportModalOpen = false"
        />
      </div>
    </div>

    <!-- The Report Modal for Main Post -->
    <ReportFormModal
      :is-open="isReportModalOpen"
      :target="reportTarget"
      @close="isReportModalOpen = false"
    />
  </div>
</template>

<style scoped>
.post-wrapper {
  margin-bottom: 11px !important;
  margin-top: 0px !important;
  position: relative;
  transition: all 0.3s ease;
}

/* Line clamp utility for limiting text to 4 lines */
.line-clamp-4 {
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Comment section animation */
.comment-slide-enter-active,
.comment-slide-leave-active {
  transition: all 0.3s ease;
  max-height: 1000px;
  overflow: hidden;
  border-bottom-left-radius: 1rem; /* rounded-2xl */
  border-bottom-right-radius: 1rem; /* rounded-2xl */
}

.comment-slide-enter-from,
.comment-slide-leave-to {
  max-height: 0;
  opacity: 0;
  transform: translateY(-10px);
  border-bottom-left-radius: 1rem; /* rounded-2xl */
  border-bottom-right-radius: 1rem; /* rounded-2xl */
}

.comment-slide-enter-to,
.comment-slide-leave-from {
  max-height: 1000px;
  opacity: 1;
  transform: translateY(0);
  border-bottom-left-radius: 1rem; /* rounded-2xl */
  border-bottom-right-radius: 1rem; /* rounded-2xl */
}

.comment-section {
  animation: slideIn 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border-top: 1px solid #e5e7eb;
  margin-top: -1px;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Clean Comment Input Form Styles */
.comment-input-form {
  padding-top: 0.5rem !important;
  padding-bottom: 0.5rem !important;
  margin-top: -0.25rem !important; /* Shift the form up */
}

.comment-input-form .min-h-\[34px\] {
  min-height: 34px !important;
  border: none !important;
  box-shadow: none !important;
}

.comment-input-form .min-h-\[38px\] {
  min-height: 38px !important;
  border: none !important;
  box-shadow: none !important;
}

.comment-input-form .min-h-\[34px\]:focus,
.comment-input-form .min-h-\[38px\]:focus {
  background-color: white !important;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1) !important;
}

/* Consistent button sizes for GIF and emoji */
.comment-input-form button[title='Add GIF'],
.comment-input-form button[title='Add emoji'] {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 0.5rem !important;
}

/* Submit button styling */
.comment-input-form button[type='submit'] {
  padding: 0.375rem 0.75rem !important;
  font-size: 0.75rem !important;
}

/* Smooth transitions for tooltips */
.tooltip-enter-active,
.tooltip-leave-active {
  transition: opacity 0.2s ease;
}

.tooltip-enter-from,
.tooltip-leave-to {
  opacity: 0;
}

/* Smooth transitions for modal */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

/* Drag and drop styles */
.drag-item {
  transition: all 0.2s ease;
}

.drag-item.dragging {
  opacity: 0.5;
  transform: scale(0.95);
}

.drag-item.drag-over {
  border: 2px solid #3b82f6;
  transform: scale(1.05);
}

/* Custom scrollbar for comments */
.max-h-64::-webkit-scrollbar,
.max-h-96::-webkit-scrollbar {
  width: 6px;
}

.max-h-64::-webkit-scrollbar-track,
.max-h-96::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 10px;
}

.max-h-64::-webkit-scrollbar-thumb,
.max-h-96::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 10px;
}

.max-h-64::-webkit-scrollbar-thumb:hover,
.max-h-96::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* Enhanced modal backdrop */
.backdrop-blur-sm {
  backdrop-filter: blur(4px);
}

/* Fix word breaking issues */
.word-break-fix {
  word-break: break-word;
  overflow-wrap: break-word;
  hyphens: auto;
}

/* Ensure buttons don't get cut off in modal */
.min-w-0 {
  min-width: 0;
}

/* Active state transitions for comment buttons */
.comment-button-active {
  transform: scale(0.95);
  transition: all 0.2s ease;
}

/* Highlight active comment button */
.comment-button-active .fa-comment-dots {
  color: #d97706 !important;
}

/* Smooth scroll behavior for the page */
html {
  scroll-behavior: smooth;
}

/* Smooth transition for expanding/collapsing text */
.text-expand-transition {
  transition: all 0.3s ease;
}

/* Prevent body scroll when modal is open */
body.modal-open {
  overflow: hidden !important;
  position: fixed;
  width: 100%;
  height: 100%;
}

/* Custom scrollbar for modal */
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.no-scrollbar::-webkit-scrollbar {
  display: none;
}

/* MOBILE-SPECIFIC FIXES FOR EQUAL BUTTON SPACING */
@media (max-width: 768px) {
  /* Ensure all action buttons take equal space */
  .mobile-actions-grid {
    display: flex !important;
    width: 100% !important;
    justify-content: space-between !important;
    align-items: center !important;
  }

  .mobile-action-item {
    flex: 1 !important;
    min-width: 0 !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 4px 0 !important;
  }

  /* Mobile action button styling */
  .mobile-action-button {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    width: 100% !important;
    padding: 6px 2px !important;
    gap: 0 !important;
  }

  /* Mobile icon container */
  .mobile-action-button > div:first-child {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin-bottom: 2px !important;
    min-height: 20px !important;
  }

  /* Mobile text + count container */
  .mobile-text-count-container {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 4px !important;
    line-height: 1 !important;
  }

  /* Mobile action icon sizing */
  .mobile-action-icon {
    width: 18px !important;
    height: 18px !important;
  }

  /* Mobile action count styling - next to text */
  .mobile-action-count {
    font-size: 11px !important;
    font-weight: 500 !important;
    color: #6b7280 !important;
    line-height: 1 !important;
  }

  /* Mobile text label next to count */
  .mobile-action-text {
    font-size: 11px !important;
    font-weight: 500 !important;
    color: #6b7280 !important;
    line-height: 1 !important;
    display: block !important;
  }

  /* Hide desktop labels on mobile */
  .mobile-action-label {
    display: none !important;
  }

  /* Adjust reaction picker for mobile */
  .mobile-reaction-picker {
    transform: translateX(-25%) !important;
    margin-bottom: 8px !important;
    padding: 6px 10px !important;
  }

  .mobile-reaction-picker button {
    padding: 6px !important;
  }

  .mobile-reaction-picker svg {
    width: 16px !important;
    height: 16px !important;
  }

  /* Mobile modal adjustments */
  .mobile-modal-container {
    flex-direction: column;
    max-height: 100vh;
    width: 100%;
    height: 100%;
    border-radius: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
  }

  .portrait-media-container {
    flex: 1;
    min-height: 0;
    max-height: none;
    width: 100%;
  }

  .portrait-media-content {
    height: 100%;
    padding: 4.75rem 1rem 3.5rem;
    width: 100%;
  }

  .portrait-media {
    max-height: calc(100vh - 10rem) !important;
    width: auto !important;
    max-width: 100% !important;
    object-fit: contain !important;
  }

  /* Keep the counter above iOS safe-area */
  .media-counter {
    bottom: calc(env(safe-area-inset-bottom) + 1rem) !important;
  }

  /* Hide right sidebar in mobile media modal */
  .mobile-modal-container > div:last-child:not(.portrait-media-container) {
    display: none;
  }

  /* Adjust close button position for mobile */
  .mobile-modal-container .absolute.top-4.right-4 {
    top: 0.5rem;
    right: 0.5rem;
    width: 2rem;
    height: 2rem;
  }

  /* Tooltip adjustments for mobile */
  .upload-tooltip {
    top: -2.5rem !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    font-size: 0.7rem !important;
    padding: 0.25rem 0.5rem !important;
    white-space: nowrap !important;
  }

  /* Edit modal mobile adjustments */
  .edit-modal-container {
    max-height: 85vh !important;
    margin: 0 !important;
    border-radius: 0 !important;
    width: 100%;
    height: 100%;
  }

  .edit-modal-content {
    padding: 1rem !important;
  }

  .media-preview-grid {
    grid-template-columns: repeat(2, 1fr) !important;
    gap: 0.5rem !important;
  }

  .media-preview-item {
    width: 100px !important;
    height: 100px !important;
  }

  .action-buttons-mobile {
    flex-direction: column !important;
    gap: 0.75rem !important;
    width: 100% !important;
  }

  .upload-buttons-mobile {
    display: flex !important;
    width: 100% !important;
    gap: 0.5rem !important;
  }

  .upload-buttons-mobile > div {
    flex: 1 !important;
  }

  /* Edit modal buttons full width on mobile */
  .edit-modal-buttons {
    width: 100% !important;
  }

  .edit-modal-buttons button {
    width: 100% !important;
    justify-content: center !important;
  }
}

/* Desktop styles for actions */
@media (min-width: 769px) {
  .mobile-actions-grid {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .mobile-action-item {
    flex: 1;
  }

  .mobile-action-button {
    flex-direction: row !important;
    gap: 6px !important;
  }

  .mobile-action-button > div:first-child {
    margin-bottom: 0 !important;
    min-height: auto !important;
  }

  .mobile-action-icon {
    width: 16px !important;
    height: 16px !important;
  }

  .mobile-action-count {
    font-size: 14px !important;
  }

  .mobile-action-label {
    display: inline !important;
    font-size: 14px !important;
  }

  .mobile-action-text {
    display: none !important;
  }

  .mobile-text-count-container {
    display: none !important;
  }

  /* Ensure modal stays centered on desktop */
  .fixed.inset-0 {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }
}

/* Responsive design improvements */
@media (max-width: 640px) {
  .post-wrapper {
    margin-bottom: 8px !important;
  }

  .comment-input-form {
    padding: 0.375rem !important;
    margin-top: -0.375rem !important;
  }

  .comment-input-form img {
    width: 1.75rem !important;
    height: 1.75rem !important;
  }

  .comment-input-form button[type='submit'] {
    padding: 0.25rem 0.5rem !important;
  }

  .comment-input-form button[title='Add GIF'],
  .comment-input-form button[title='Add emoji'] {
    width: 28px !important;
    height: 28px !important;
    padding: 0.375rem !important;
  }

  /* Smaller adjustments for small screens */
  .mobile-action-icon {
    width: 16px !important;
    height: 16px !important;
  }

  .mobile-action-count {
    font-size: 10px !important;
  }

  .mobile-action-text {
    font-size: 10px !important;
  }

  .mobile-text-count-container {
    gap: 3px !important;
  }

  /* Edit modal adjustments for very small screens */
  .edit-modal-content {
    padding: 0.75rem !important;
  }

  .media-preview-grid {
    grid-template-columns: repeat(2, 1fr) !important;
    gap: 0.375rem !important;
  }

  .media-preview-item {
    width: 90px !important;
    height: 90px !important;
  }
}

/* For extra small devices */
@media (max-width: 375px) {
  /* Even smaller adjustments for very small screens */
  .mobile-action-icon {
    width: 14px !important;
    height: 14px !important;
  }

  .mobile-action-count {
    font-size: 9px !important;
  }

  .mobile-action-text {
    font-size: 9px !important;
  }

  .mobile-text-count-container {
    gap: 2px !important;
  }

  /* Edit modal adjustments for extra small screens */
  .edit-modal-content {
    padding: 0.5rem !important;
  }

  .media-preview-grid {
    grid-template-columns: repeat(2, 1fr) !important;
    gap: 0.25rem !important;
  }

  .media-preview-item {
    width: 80px !important;
    height: 80px !important;
  }

  .upload-buttons-mobile {
    flex-direction: column !important;
    gap: 0.375rem !important;
  }

  .upload-buttons-mobile > div {
    width: 100% !important;
  }
}

/* Ensure no wrapping occurs */
.whitespace-nowrap {
  white-space: nowrap !important;
}

/* Prevent any text wrapping inside the notification */
.no-wrap-container {
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  flex-wrap: nowrap !important;
  white-space: nowrap !important;
  overflow: hidden !important;
}

/* Ensure all child elements don't wrap */
.no-wrap-container > * {
  white-space: nowrap !important;
  flex-shrink: 0 !important;
}

/* Desktop new posts notification styling - FOR ALL SCREENS */
@media (min-width: 769px) {
  .new-posts-notification {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    text-align: center !important;
    white-space: nowrap !important;
    width: 100% !important;
    max-width: 600px !important;
    padding: 16px 24px !important;
    margin: 12px auto !important;
    background-color: #f8fafc !important;
    border-radius: 14px !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    color: #334155 !important;
    border: 2px solid #e2e8f0 !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1) !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    letter-spacing: 0.3px !important;
  }
}

/* Post centering after edit animation */
.post-center-animation {
  animation: centerPost 0.5s ease-out;
}

@keyframes centerPost {
  0% {
    transform: translateY(-20px);
    opacity: 0.9;
  }
  100% {
    transform: translateY(0);
    opacity: 1;
  }
}

/* Ensure smooth scroll for post centering */
.smooth-scroll {
  scroll-behavior: smooth;
}

/* Full screen modal on mobile */
@media (max-width: 768px) {
  .fixed.inset-0 {
    padding: 0 !important;
  }

  .bg-white.rounded-none {
    border-radius: 0 !important;
    height: 100vh;
    max-height: 100vh !important;
    overflow-y: auto;
  }
}

/* Prevent body scroll when any modal is open */
body:has(.fixed.inset-0.bg-black) {
  overflow: hidden !important;
}

/* Ensure modal backdrop covers entire screen */
.fixed.inset-0 {
  position: fixed !important;
  top: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  left: 0 !important;
  z-index: 50 !important;
}

/* Mobile modal full screen */
@media (max-width: 768px) {
  .fixed.inset-0 {
    align-items: flex-start !important;
    padding-top: env(safe-area-inset-top);
  }

  .bg-white.rounded-none {
    border-top-left-radius: 0 !important;
    border-top-right-radius: 0 !important;
  }
}

/* Safe area handling for notched phones */
@supports (padding: max(0px)) {
  .fixed.inset-0 {
    padding-top: max(0px, env(safe-area-inset-top));
    padding-bottom: max(0px, env(safe-area-inset-bottom));
  }
}

/* Force 2XL rounding for comment section */
.comment-section {
  border-bottom-left-radius: 1rem !important;
  border-bottom-right-radius: 1rem !important;
  overflow: hidden !important;
}

@media (width: 768px) {
  .md\:flex,
  .md\:block,
  .md\:grid,
  .md\:inline-flex,
  .md\:inline,
  .md\:table,
  .md\:table-row,
  .md\:table-cell,
  .md\:hidden {
    display: unset !important;
  }

  .md\:flex-row {
    flex-direction: column !important;
  }

  .md\:items-center {
    align-items: stretch !important;
  }
}
</style>
