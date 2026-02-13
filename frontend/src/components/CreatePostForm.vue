<script setup lang="ts">
import { ref, watch, computed, onUnmounted } from 'vue'
import { useFeedStore } from '@/stores/feed'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'
import { getAvatarUrl } from '@/utils/avatars'
import MentionAutocomplete from './MentionAutocomplete.vue'

// FontAwesome imports
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { library } from '@fortawesome/fontawesome-svg-core'
import {
  faImage,
  faVideo,
  faChartBar,
  faFileAlt,
  faTimes,
  faPlus,
  faSquarePlus,
  faGripVertical,
  faInfoCircle,
  faExclamationTriangle,
  faListOl,
  faPaperPlane,
  faSpinner,
  faArrowsUpDownLeftRight,
  faCompress,
  faPlayCircle,
  faClock,
  faExclamationCircle,
  faCheckCircle,
  faCut,
  faDownload,
  faTrash,
  faRedo,
} from '@fortawesome/free-solid-svg-icons'

// Add icons to library
library.add(
  faImage,
  faVideo,
  faChartBar,
  faFileAlt,
  faTimes,
  faPlus,
  faSquarePlus,
  faGripVertical,
  faInfoCircle,
  faExclamationTriangle,
  faListOl,
  faPaperPlane,
  faSpinner,
  faArrowsUpDownLeftRight,
  faCompress,
  faPlayCircle,
  faClock,
  faExclamationCircle,
  faCheckCircle,
  faCut,
  faDownload,
  faTrash,
  faRedo,
)

// Define interface for media files with custom properties
interface ProcessedFile extends File {
  trimmed?: boolean
  compressed?: boolean
  originalDuration?: number
  originalSize?: number
  finalSize?: number
}

interface MediaFile {
  type: 'image' | 'video'
  file: ProcessedFile
  previewUrl: string | null
  duration?: number
  durationSeconds?: number
  processingMessages?: string[]
}

const props = defineProps<{
  groupSlug?: string
}>()

// --- Stores and State ---
const feedStore = useFeedStore()
const authStore = useAuthStore()
const { isCreatingPost, createPostError } = storeToRefs(feedStore)
const { currentUser } = storeToRefs(authStore)

// --- Form State ---
const postContent = ref('')
const selectedImageFiles = ref<ProcessedFile[]>([])
const selectedVideoFiles = ref<ProcessedFile[]>([])
const imagePreviewUrls = ref<string[]>([])
const videoPreviewUrls = ref<string[]>([])
const showPollCreator = ref(false)
const pollQuestion = ref('')
const pollOptions = ref<string[]>(['', ''])
const processingMessages = ref<string[]>([])

// Drag and drop state
const dragOverIndex = ref(-1)
const isDragging = ref(false)

// Processing state
const isCompressing = ref(false)
const compressionProgress = ref(0)

// --- Limits ---
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

// --- Helper function to get error message ---
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

// --- Computed Properties ---
const selectedMediaFiles = computed((): MediaFile[] => {
  const media: MediaFile[] = []

  // Add images with their preview URLs
  selectedImageFiles.value.forEach((file, index) => {
    media.push({
      type: 'image',
      file: file,
      previewUrl: imagePreviewUrls.value[index],
    })
  })

  // Add videos with their preview URLs
  selectedVideoFiles.value.forEach((file, index) => {
    media.push({
      type: 'video',
      file: file,
      previewUrl: videoPreviewUrls.value[index],
    })
  })

  return media
})

// Calculate current points
const currentPoints = computed(() => {
  return (
    selectedImageFiles.value.length * IMAGE_POINTS + selectedVideoFiles.value.length * VIDEO_POINTS
  )
})

const remainingPoints = computed(() => {
  return MAX_TOTAL_POINTS - currentPoints.value
})

const isSubmittable = computed(() => {
  if (showPollCreator.value) {
    return (
      pollQuestion.value.trim() !== '' &&
      pollOptions.value.length >= 2 &&
      pollOptions.value.every((opt) => opt.trim() !== '')
    )
  }
  const hasContent = postContent.value.trim() !== ''
  const hasMedia = selectedImageFiles.value.length > 0 || selectedVideoFiles.value.length > 0
  return hasContent || hasMedia
})

// --- Enhanced Image Compression Function ---
const compressImageFast = (file: File): Promise<ProcessedFile> => {
  return new Promise((resolve, reject) => {
    // If image is already small enough, return as-is
    if (file.size <= MAX_IMAGE_SIZE_BYTES) {
      const processedFile = file as ProcessedFile
      processedFile.finalSize = file.size
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

      // Calculate dimensions with aggressive reduction for large images
      let width = img.width
      let height = img.height

      // More aggressive reduction for images way over limit
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

      // Draw image
      ctx.imageSmoothingEnabled = true
      ctx.imageSmoothingQuality = 'high'
      ctx.drawImage(img, 0, 0, width, height)

      // Start with lower quality for faster compression
      let quality = 0.7

      const compressAttempt = (attemptQuality: number): void => {
        canvas.toBlob(
          (blob) => {
            if (!blob) {
              reject(new Error('Compression failed'))
              return
            }

            if (blob.size > MAX_IMAGE_SIZE_BYTES && attemptQuality > 0.1) {
              // Try again with even lower quality
              compressAttempt(attemptQuality - 0.1)
            } else {
              // If still too large, reduce dimensions further
              if (blob.size > MAX_IMAGE_SIZE_BYTES && width > 400 && height > 400) {
                width = Math.floor(width * 0.8)
                height = Math.floor(height * 0.8)
                canvas.width = width
                canvas.height = height
                ctx.drawImage(img, 0, 0, width, height)
                compressAttempt(0.5)
              } else {
                const compressedFile = new File([blob], file.name, {
                  type: 'image/jpeg',
                  lastModified: Date.now(),
                }) as ProcessedFile

                compressedFile.compressed = true
                compressedFile.originalSize = file.size
                compressedFile.finalSize = blob.size
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

// --- Enhanced Video Processing Functions ---

// Get video duration
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

// ACTUAL Video trimming using MediaRecorder
const trimVideoToDuration = (file: File, maxDurationSeconds: number): Promise<ProcessedFile> => {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video')
    video.src = URL.createObjectURL(file)
    video.muted = true
    video.playsInline = true

    video.onloadedmetadata = async () => {
      const originalDuration = video.duration
      const targetDuration = Math.min(originalDuration, maxDurationSeconds)

      // If video is already within duration limit, return as-is
      if (originalDuration <= maxDurationSeconds) {
        URL.revokeObjectURL(video.src)
        const unchangedFile = new File([file], file.name, {
          type: file.type,
          lastModified: Date.now(),
        }) as ProcessedFile
        unchangedFile.originalDuration = originalDuration
        unchangedFile.finalSize = file.size
        resolve(unchangedFile)
        return
      }

      try {
        // Create a MediaStream from the video element
        const stream = await (video as any).captureStream()
        const mediaRecorder = new MediaRecorder(stream, {
          mimeType: 'video/webm; codecs=vp9',
          videoBitsPerSecond: 2500000, // 2.5 Mbps for compression
        })

        const chunks: Blob[] = []

        mediaRecorder.ondataavailable = (e) => {
          if (e.data.size > 0) {
            chunks.push(e.data)
          }
        }

        mediaRecorder.onstop = () => {
          const trimmedBlob = new Blob(chunks, { type: 'video/webm' })

          // Check if the trimmed video is within size limits
          if (trimmedBlob.size > MAX_VIDEO_SIZE_BYTES) {
            // If still too large, compress it further
            compressVideoFile(new File([trimmedBlob], file.name, { type: 'video/webm' }))
              .then((compressedFile) => {
                const finalFile = new File([compressedFile], file.name, {
                  type: compressedFile.type,
                  lastModified: Date.now(),
                }) as ProcessedFile

                finalFile.trimmed = true
                finalFile.originalDuration = originalDuration
                finalFile.originalSize = file.size
                finalFile.finalSize = compressedFile.size

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
            const trimmedFile = new File([trimmedBlob], file.name, {
              type: 'video/webm',
              lastModified: Date.now(),
            }) as ProcessedFile

            trimmedFile.trimmed = true
            trimmedFile.originalDuration = originalDuration
            trimmedFile.originalSize = file.size
            trimmedFile.finalSize = trimmedBlob.size

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

        // Start recording
        mediaRecorder.start()

        // Play video to capture frames
        video.currentTime = 0
        await video.play()

        // Stop recording after target duration
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

// ACTUAL Video compression by reducing quality and resolution
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

      // Reduce resolution for compression (max 720p)
      let targetWidth = video.videoWidth
      let targetHeight = video.videoHeight

      if (targetWidth > 1280 || targetHeight > 720) {
        const ratio = Math.min(1280 / targetWidth, 720 / targetHeight)
        targetWidth = Math.floor(targetWidth * ratio)
        targetHeight = Math.floor(targetHeight * ratio)
      }

      canvas.width = targetWidth
      canvas.height = targetHeight

      // Use MediaRecorder with canvas for re-encoding
      const stream = canvas.captureStream(30) // 30 FPS
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'video/webm; codecs=vp9',
        videoBitsPerSecond: 1500000, // 1.5 Mbps for better compression
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

      // Start capturing frames
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

      // Start recording
      mediaRecorder.start()

      // Play and capture video
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

// Generate Video Preview
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

// --- Automatic File Processing ---

const processImage = async (file: File): Promise<ProcessedFile> => {
  try {
    processingMessages.value.push('Optimizing image...')
    compressionProgress.value = 30

    const processedFile = await compressImageFast(file)

    compressionProgress.value = 70
    processingMessages.value.push('✓ Image optimized')

    return processedFile
  } catch (error) {
    throw new Error(`Image processing error: ${getErrorMessage(error)}`)
  }
}

// ACTUAL Video processing with both trimming and compression
const processVideo = async (file: File): Promise<ProcessedFile> => {
  try {
    // Check duration and size
    const duration = await getVideoDuration(file)
    const sizeMB = file.size / (1024 * 1024)

    let processedFile: ProcessedFile = file as ProcessedFile
    let needsProcessing = false

    processingMessages.value.push(`Video: ${Math.round(duration)}s, ${sizeMB.toFixed(2)}MB`)

    // Check if video needs processing
    if (duration > MAX_VIDEO_DURATION_SECONDS) {
      processingMessages.value.push('Trimming video to 30 seconds...')
      compressionProgress.value = 30
      needsProcessing = true
    }

    if (sizeMB > MAX_VIDEO_SIZE_MB) {
      processingMessages.value.push('Compressing video to under 50MB...')
      compressionProgress.value = needsProcessing ? 50 : 30
      needsProcessing = true
    }

    if (!needsProcessing) {
      // Video already meets requirements
      const withinLimitFile = new File([file], file.name, {
        type: file.type,
        lastModified: Date.now(),
      }) as ProcessedFile
      withinLimitFile.originalDuration = duration
      withinLimitFile.finalSize = file.size
      compressionProgress.value = 100
      return withinLimitFile
    }

    // First trim if needed
    if (duration > MAX_VIDEO_DURATION_SECONDS) {
      compressionProgress.value = 40
      processedFile = await trimVideoToDuration(file, MAX_VIDEO_DURATION_SECONDS)
      processingMessages.value.push('✓ Video trimmed to 30 seconds')
    }

    // Then compress if still needed (or if original was too large)
    const currentSizeMB = (processedFile as File).size / (1024 * 1024)
    if (currentSizeMB > MAX_VIDEO_SIZE_MB || sizeMB > MAX_VIDEO_SIZE_MB) {
      compressionProgress.value = 70
      const compressedBlob = await compressVideoFile(processedFile as File)

      const finalFile = new File([compressedBlob], file.name, {
        type: compressedBlob.type,
        lastModified: Date.now(),
      }) as ProcessedFile

      finalFile.trimmed = processedFile.trimmed || duration > MAX_VIDEO_DURATION_SECONDS
      finalFile.compressed = true
      finalFile.originalDuration = duration
      finalFile.originalSize = file.size
      finalFile.finalSize = compressedBlob.size

      processedFile = finalFile
      processingMessages.value.push('✓ Video compressed')
    }

    compressionProgress.value = 100
    processingMessages.value.push(
      `Final: ${Math.round(processedFile.originalDuration || duration)}s → ${MAX_VIDEO_DURATION_SECONDS}s, ${sizeMB.toFixed(2)}MB → ${((processedFile.finalSize || file.size) / (1024 * 1024)).toFixed(2)}MB`,
    )

    return processedFile
  } catch (error) {
    throw new Error(`Video processing error: ${getErrorMessage(error)}`)
  }
}

const handleFileChange = async (event: Event, type: 'image' | 'video') => {
  if (showPollCreator.value) return

  const target = event.target as HTMLInputElement
  const files = target.files
  if (!files) return

  if (createPostError.value) {
    feedStore.createPostError = null
  }

  // Calculate potential new counts
  const currentImages = selectedImageFiles.value.length
  const currentVideos = selectedVideoFiles.value.length
  const filesToAdd = files.length
  const filePoints = type === 'image' ? IMAGE_POINTS : VIDEO_POINTS
  const potentialPoints = currentPoints.value + filesToAdd * filePoints

  // Check individual limits before processing
  if (type === 'image') {
    const remainingSlots = MAX_IMAGES - currentImages
    if (filesToAdd > remainingSlots) {
      feedStore.createPostError = `You can only upload ${MAX_IMAGES} images maximum.`
      target.value = ''
      return
    }
  } else {
    const remainingSlots = MAX_VIDEOS - currentVideos
    if (filesToAdd > remainingSlots) {
      feedStore.createPostError = `You can only upload ${MAX_VIDEOS} videos maximum.`
      target.value = ''
      return
    }
  }

  // Check point limit
  if (potentialPoints > MAX_TOTAL_POINTS) {
    const maxFiles = Math.floor(remainingPoints.value / filePoints)
    if (maxFiles <= 0) {
      feedStore.createPostError = `You have reached the maximum upload limit.`
    } else {
      feedStore.createPostError = `You can only upload ${maxFiles} more ${type}${maxFiles > 1 ? 's' : ''}.`
    }
    target.value = ''
    return
  }

  const filesToProcess = Array.from(files)

  // Start compression process
  isCompressing.value = true
  compressionProgress.value = 10
  processingMessages.value = [] // Clear previous messages

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

          selectedImageFiles.value.push(processedFile)
          const reader = new FileReader()
          reader.onload = (e) => {
            if (e.target?.result) {
              imagePreviewUrls.value.push(e.target.result as string)
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

          selectedVideoFiles.value.push(processedFile)

          // Generate and add video preview
          try {
            const previewUrl = await generateVideoPreview(processedFile)
            videoPreviewUrls.value.push(previewUrl)
          } catch (previewError) {
            console.warn('Failed to generate video preview:', getErrorMessage(previewError))
            videoPreviewUrls.value.push('')
          }
        }
      } catch (error) {
        const errorMessage = getErrorMessage(error)
        feedStore.createPostError = `Failed to process ${type}: ${errorMessage}`
        target.value = ''
        isCompressing.value = false
        compressionProgress.value = 0
        return
      }
    }

    // Success message
    processingMessages.value.push(
      `✓ All ${filesToProcess.length} ${type}(s) processed successfully`,
    )

    // Clear messages after 3 seconds
    setTimeout(() => {
      processingMessages.value = []
      isCompressing.value = false
      compressionProgress.value = 0
    }, 3000)
  } catch (error) {
    feedStore.createPostError = getErrorMessage(error)
    isCompressing.value = false
    compressionProgress.value = 0
    processingMessages.value = []
  }

  target.value = ''
}

// --- Drag and Drop Functions ---
const onDragStart = (index: number, event: DragEvent) => {
  isDragging.value = true
  event.dataTransfer?.setData('text/plain', index.toString())
  event.dataTransfer && (event.dataTransfer.effectAllowed = 'move')
}

const onDragOver = (index: number, event: DragEvent) => {
  event.preventDefault()
  dragOverIndex.value = index
}

const onDragEnd = () => {
  isDragging.value = false
  dragOverIndex.value = -1
}

const onDrop = (targetIndex: number, event: DragEvent) => {
  event.preventDefault()
  const sourceIndex = parseInt(event.dataTransfer?.getData('text/plain') || '-1')

  if (sourceIndex !== -1 && sourceIndex !== targetIndex) {
    const mediaToMove = selectedMediaFiles.value[sourceIndex]

    if (mediaToMove.type === 'image') {
      const imageFile = selectedImageFiles.value.splice(sourceIndex, 1)[0]
      const imagePreview = imagePreviewUrls.value.splice(sourceIndex, 1)[0]

      let adjustedTargetIndex = 0
      for (let i = 0; i < targetIndex; i++) {
        if (selectedMediaFiles.value[i].type === 'image') {
          adjustedTargetIndex++
        }
      }

      selectedImageFiles.value.splice(adjustedTargetIndex, 0, imageFile)
      imagePreviewUrls.value.splice(adjustedTargetIndex, 0, imagePreview)
    } else {
      const videoIndex = sourceIndex - selectedImageFiles.value.length
      const videoFile = selectedVideoFiles.value.splice(videoIndex, 1)[0]
      const videoPreview = videoPreviewUrls.value.splice(videoIndex, 1)[0]

      let adjustedTargetIndex = 0
      for (let i = 0; i < targetIndex; i++) {
        if (selectedMediaFiles.value[i].type === 'video') {
          adjustedTargetIndex++
        }
      }

      selectedVideoFiles.value.splice(adjustedTargetIndex, 0, videoFile)
      videoPreviewUrls.value.splice(adjustedTargetIndex, 0, videoPreview)
    }
  }

  onDragEnd()
}

const togglePollCreator = () => {
  showPollCreator.value = !showPollCreator.value
  feedStore.createPostError = null

  if (showPollCreator.value) {
    selectedImageFiles.value = []
    selectedVideoFiles.value = []
    imagePreviewUrls.value = []
    videoPreviewUrls.value = []
    postContent.value = ''
  } else {
    pollQuestion.value = ''
    pollOptions.value = ['', '']
  }
}

const removeSelectedFile = (index: number, type: 'image' | 'video') => {
  if (type === 'image') {
    selectedImageFiles.value.splice(index, 1)
    imagePreviewUrls.value.splice(index, 1)
  } else {
    const videoIndex = index - selectedImageFiles.value.length
    selectedVideoFiles.value.splice(videoIndex, 1)
    videoPreviewUrls.value.splice(videoIndex, 1)
  }
}

const clearForm = () => {
  postContent.value = ''
  selectedImageFiles.value = []
  selectedVideoFiles.value = []
  imagePreviewUrls.value = []
  videoPreviewUrls.value = []
  showPollCreator.value = false
  pollQuestion.value = ''
  pollOptions.value = ['', '']
  feedStore.createPostError = null
  processingMessages.value = []
}

const handleSubmit = async () => {
  if (!isSubmittable.value) return
  if (createPostError.value) feedStore.createPostError = null

  const formData = new FormData()

  if (props.groupSlug) {
    formData.append('group', props.groupSlug)
  }

  if (showPollCreator.value) {
    const validOptions = pollOptions.value.map((o) => o.trim()).filter(Boolean)
    const pollPayload = {
      question: pollQuestion.value.trim(),
      options: validOptions,
    }
    formData.append('content', pollPayload.question)
    formData.append('poll_data', JSON.stringify(pollPayload))
  } else {
    if (postContent.value.trim()) {
      formData.append('content', postContent.value.trim())
    }
    selectedImageFiles.value.forEach((file) => formData.append('images', file))
    selectedVideoFiles.value.forEach((file) => formData.append('videos', file))
  }

  const newPost = await feedStore.createPost(formData)
  if (newPost) {
    clearForm()
  }
}

const addPollOption = () => {
  if (pollOptions.value.length < 5) {
    pollOptions.value.push('')
  }
}

const removePollOption = (index: number) => {
  if (pollOptions.value.length > 2) {
    pollOptions.value.splice(index, 1)
  }
}

// Cleanup
onUnmounted(() => {
  // Revoke object URLs to prevent memory leaks
  imagePreviewUrls.value.forEach((url) => {
    if (url.startsWith('blob:')) {
      URL.revokeObjectURL(url)
    }
  })

  // Clear video previews
  videoPreviewUrls.value = []
})
</script>

<template>
  <div class="bg-white p-4 sm:p-6 rounded-2xl shadow-md">
    <!-- Compression Progress Overlay -->
    <div
      v-if="isCompressing"
      class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
    >
      <div class="bg-white rounded-xl p-4 sm:p-6 max-w-sm w-full">
        <div class="flex items-center gap-3 mb-4">
          <font-awesome-icon
            :icon="['fas', 'compress']"
            class="text-blue-500 text-xl animate-pulse"
          />
          <div>
            <h3 class="font-bold text-gray-800 text-sm sm:text-base">Optimizing Media</h3>
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
            <font-awesome-icon
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

    <form @submit.prevent="handleSubmit" novalidate>
      <div class="flex items-start gap-3 sm:gap-4">
        <img
          :src="getAvatarUrl(currentUser?.picture, currentUser?.first_name, currentUser?.last_name)"
          alt="Your avatar"
          class="w-9 h-9 sm:w-11 sm:h-11 rounded-full object-cover bg-gray-200 flex-shrink-0 -ml-2"
        />
        <div class="w-full">
          <div v-if="!showPollCreator">
            <MentionAutocomplete
              v-model="postContent"
              placeholder="What's on your mind? Mention users with @"
              :rows="3"
              :disabled="isCreatingPost"
              data-cy="create-post-input"
            />
          </div>

          <div v-else class="w-full">
            <div class="mb-3">
              <label class="block-text-sm font-semibold text-gray-700 mb-1 flex items-center gap-2">
                <font-awesome-icon :icon="['fas', 'chart-bar']" class="text-purple-500" />
                <span class="text-xs sm:text-sm">Poll Question</span>
              </label>
              <input
                type="text"
                v-model="pollQuestion"
                placeholder="Ask a question..."
                class="w-full p-2 sm:p-3 border-2 border-gray-200 rounded-lg text-sm font-medium focus:border-purple-400 focus:ring-2 focus:ring-purple-50 transition-all duration-200 outline-none bg-white"
                maxlength="255"
              />
            </div>

            <div class="space-y-1.5 mb-3">
              <label class="blocktext-sm font-semibold text-gray-700 mb-1 flex items-center gap-2">
                <font-awesome-icon :icon="['fas', 'list-ol']" class="text-purple-500" />
                <span class="text-xs sm:text-sm">Poll Options</span>
              </label>
              <div
                v-for="(option, index) in pollOptions"
                :key="index"
                class="flex items-center gap-1.5 group hover:bg-gray-50 rounded transition-all duration-200 p-1"
              >
                <div class="flex items-center gap-1.5 flex-grow">
                  <div
                    class="w-5 h-5 sm:w-6 sm:h-6 flex items-center justify-center bg-gradient-to-br from-purple-100 to-pink-100 text-purple-600 rounded text-xs font-semibold shadow-sm"
                  >
                    {{ index + 1 }}
                  </div>
                  <input
                    type="text"
                    v-model="pollOptions[index]"
                    :placeholder="`Option ${index + 1}`"
                    class="flex-grow p-2 sm:p-2.5 border-2 border-gray-200 rounded focus:border-purple-400 focus:ring-2 focus:ring-purple-50 transition-all duration-200 outline-none bg-white text-sm"
                    maxlength="100"
                  />
                </div>
                <button
                  @click="removePollOption(index)"
                  type="button"
                  class="w-5 h-5 sm:w-6 sm:h-6 flex items-center justify-center text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-all duration-200 disabled:opacity-30 disabled:hover:bg-transparent group-hover:scale-110"
                  :disabled="pollOptions.length <= 2"
                >
                  <font-awesome-icon :icon="['fas', 'times']" class="text-xs" />
                </button>
              </div>
            </div>

            <div class="flex items-center gap-2 mb-3 flex-wrap">
              <button
                @click="addPollOption"
                type="button"
                class="flex items-center gap-1.5 px-2 py-1 sm:px-3 sm:py-1.5 text-purple-600 hover:text-purple-700 hover:bg-purple-50 rounded transition-all duration-200 disabled:opacity-50 font-semibold group text-xs"
                :disabled="pollOptions.length >= 5"
              >
                <div
                  class="w-4 h-4 sm:w-5 sm:h-5 bg-purple-100 rounded flex items-center justify-center group-hover:scale-110 transition-transform"
                >
                  <font-awesome-icon :icon="['fas', 'plus']" class="text-purple-600 text-xs" />
                </div>
                <span>Add Option</span>
              </button>
              <div class="flex-1"></div>
              <button
                @click="clearForm"
                type="button"
                class="px-2 py-1 sm:px-3 sm:py-1.5 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded transition-all duration-200 font-semibold text-xs"
              >
                Cancel
              </button>
            </div>

            <div class="bg-blue-50 border border-blue-200 rounded p-2">
              <div class="flex items-center gap-1.5 text-blue-700">
                <font-awesome-icon :icon="['fas', 'info-circle']" class="text-blue-500 text-xs" />
                <div>
                  <p class="font-semibold text-xs">Poll Information</p>
                  <p class="text-xs text-blue-600">Your poll will be active for 7 days</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Error Display -->
      <div
        v-if="createPostError"
        class="bg-red-50 border border-red-200 text-red-700 px-3 py-2 sm:px-4 sm:py-3 rounded-xl relative my-3 sm:my-4 flex items-center gap-2 sm:gap-3 text-sm sm:text-base"
      >
        <font-awesome-icon
          :icon="['fas', 'exclamation-circle']"
          class="text-red-500 flex-shrink-0"
        />
        <span class="block sm:inline">{{ createPostError }}</span>
      </div>

      <!-- Media Previews -->
      <div
        v-if="selectedMediaFiles.length > 0 && !showPollCreator"
        class="mt-3 sm:mt-4 pl-12 sm:pl-14"
      >
        <div class="space-y-3 sm:space-y-4">
          <div
            class="flex items-center gap-2 sm:gap-3 text-xs sm:text-sm text-gray-600 mb-3 sm:mb-4 bg-gradient-to-r from-purple-50 to-blue-50 px-3 py-2 sm:px-4 sm:py-3 rounded-xl border border-purple-100"
          >
            <div
              class="w-6 h-6 sm:w-8 sm:h-8 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0"
            >
              <font-awesome-icon
                :icon="['fas', 'arrows-up-down-left-right']"
                class="text-purple-600 text-xs sm:text-sm"
              />
            </div>
            <span class="font-medium">Drag to rearrange photos and videos</span>
          </div>

          <div class="flex flex-wrap gap-2 sm:gap-4">
            <div
              v-for="(media, index) in selectedMediaFiles"
              :key="index"
              class="relative group transform hover:scale-105 transition-transform duration-200"
              draggable="true"
              @dragstart="onDragStart(index, $event as DragEvent)"
              @dragover.prevent="onDragOver(index, $event as DragEvent)"
              @dragenter.prevent
              @dragend="onDragEnd"
              @drop="onDrop(index, $event as DragEvent)"
            >
              <div
                class="relative rounded-xl overflow-hidden border-2 border-gray-200 bg-gradient-to-br from-gray-50 to-white w-20 h-20 sm:w-24 sm:h-24 shadow-sm hover:shadow-md transition-all duration-300"
              >
                <!-- Image Preview -->
                <img
                  v-if="media.type === 'image'"
                  :src="media.previewUrl || ''"
                  alt="Selected image preview"
                  class="w-full h-full object-cover"
                />

                <!-- Video Preview -->
                <div v-else class="w-full h-full">
                  <div v-if="media.previewUrl" class="relative w-full h-full">
                    <img
                      :src="media.previewUrl"
                      alt="Video thumbnail"
                      class="w-full h-full object-cover"
                    />
                    <!-- Play button overlay for video -->
                    <div class="absolute inset-0 bg-black/30 flex items-center justify-center">
                      <font-awesome-icon
                        :icon="['fas', 'play-circle']"
                        class="text-white text-lg sm:text-xl opacity-80"
                      />
                    </div>
                  </div>
                  <!-- Fallback if no preview available -->
                  <div
                    v-else
                    class="w-full h-full flex flex-col items-center justify-center p-1 sm:p-2 text-center bg-gradient-to-br from-blue-50 to-purple-50"
                  >
                    <font-awesome-icon
                      :icon="['fas', 'video']"
                      class="text-purple-500 text-sm sm:text-base mb-1"
                    />
                    <span class="text-xs text-gray-700 font-medium truncate w-full px-1">{{
                      media.file.name
                    }}</span>
                  </div>
                </div>

                <!-- Position Indicator -->
                <div
                  class="absolute top-1 left-1 bg-gradient-to-br from-gray-800 to-gray-900 text-white rounded-full w-4 h-4 sm:w-5 sm:h-5 flex items-center justify-center text-xs font-bold shadow-lg z-10"
                >
                  {{ index + 1 }}
                </div>

                <button
                  @click="removeSelectedFile(index, media.type)"
                  type="button"
                  class="absolute top-1 right-1 bg-gradient-to-br from-red-500 to-red-600 text-white rounded-full w-4 h-4 sm:w-5 sm:h-5 flex items-center justify-center text-xs hover:from-red-600 hover:to-red-700 transition-all duration-200 opacity-0 group-hover:opacity-100 shadow-lg hover:scale-110 z-20"
                >
                  <font-awesome-icon :icon="['fas', 'times']" class="text-[10px]" />
                </button>

                <div
                  class="absolute bottom-1 left-1 w-3 h-3 sm:w-4 sm:h-4 bg-gradient-to-br from-gray-800 to-gray-900 text-white rounded flex items-center justify-center text-xs opacity-0 group-hover:opacity-100 transition-all duration-200 cursor-grab active:cursor-grabbing shadow-lg z-10"
                  @mousedown.stop
                  @touchstart.stop
                >
                  <font-awesome-icon
                    :icon="['fas', 'grip-vertical']"
                    class="text-[8px] sm:text-[10px]"
                  />
                </div>
              </div>

              <!-- Drag Overlay -->
              <div
                class="absolute inset-0 bg-gradient-to-br from-purple-500/20 to-blue-500/20 border-2 border-purple-400 rounded-xl opacity-0 transition-all duration-200"
                :class="{ 'opacity-100': dragOverIndex === index }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Action Bar -->
      <div
        class="mt-3 sm:mt-4 flex justify-between items-center pl-2 xl:pl-14 border-t border-gray-100 pt-3 sm:pt-4"
      >
        <div class="flex gap-1 sm:gap-2 -ml-1 xl:ml-0">
          <!-- Image Upload Button -->
          <div class="relative group">
            <label
              for="postImageInput"
              class="text-blue-500 transition-all duration-200 p-1.5 sm:p-2 rounded-xl bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center w-8 h-8 sm:w-10 sm:h-10 shadow-sm border border-blue-200"
              :class="{
                'hover:text-blue-600 hover:from-blue-100 hover:to-blue-200 hover:shadow-md cursor-pointer':
                  !showPollCreator &&
                  selectedImageFiles.length < MAX_IMAGES &&
                  remainingPoints >= IMAGE_POINTS,
                'cursor-not-allowed opacity-50':
                  showPollCreator ||
                  selectedImageFiles.length >= MAX_IMAGES ||
                  remainingPoints < IMAGE_POINTS,
              }"
            >
              <font-awesome-icon :icon="['fas', 'image']" class="text-sm sm:text-base" />
              <span
                v-if="selectedImageFiles.length > 0"
                class="absolute -top-1 -right-1 bg-blue-500 text-white text-[10px] w-4 h-4 rounded-full flex items-center justify-center"
              >
                {{ selectedImageFiles.length }}
              </span>
              <input
                type="file"
                id="postImageInput"
                @change="handleFileChange($event, 'image')"
                multiple
                accept="image/jpeg,image/png,image/gif,image/webp,image/avif"
                class="hidden"
                :disabled="
                  showPollCreator ||
                  selectedImageFiles.length >= MAX_IMAGES ||
                  remainingPoints < IMAGE_POINTS
                "
              />
            </label>
            <div
              v-if="!showPollCreator"
              class="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xs rounded-lg py-1 px-2 opacity-0 group-hover:opacity-100 transition-all duration-200 pointer-events-none whitespace-nowrap shadow-lg"
            >
              {{
                selectedImageFiles.length >= MAX_IMAGES
                  ? `Maximum ${MAX_IMAGES} images allowed`
                  : remainingPoints < IMAGE_POINTS
                    ? 'Not enough upload slots remaining'
                    : `Add Images (${selectedImageFiles.length}/${MAX_IMAGES})`
              }}
            </div>
          </div>

          <!-- Video Upload Button -->
          <div class="relative group">
            <label
              for="postVideoInput"
              class="text-green-500 transition-all duration-200 p-1.5 sm:p-2 rounded-xl bg-gradient-to-br from-green-50 to-green-100 flex items-center justify-center w-8 h-8 sm:w-10 sm:h-10 shadow-sm border border-green-200"
              :class="{
                'hover:text-green-600 hover:from-green-100 hover:to-green-200 hover:shadow-md cursor-pointer':
                  !showPollCreator &&
                  selectedVideoFiles.length < MAX_VIDEOS &&
                  remainingPoints >= VIDEO_POINTS,
                'cursor-not-allowed opacity-50':
                  showPollCreator ||
                  selectedVideoFiles.length >= MAX_VIDEOS ||
                  remainingPoints < VIDEO_POINTS,
              }"
            >
              <font-awesome-icon :icon="['fas', 'video']" class="text-sm sm:text-base" />
              <span
                v-if="selectedVideoFiles.length > 0"
                class="absolute -top-1 -right-1 bg-green-500 text-white text-[10px] w-4 h-4 rounded-full flex items-center justify-center"
              >
                {{ selectedVideoFiles.length }}
              </span>
              <input
                type="file"
                id="postVideoInput"
                @change="handleFileChange($event, 'video')"
                multiple
                accept="video/mp4,video/webm,video/quicktime"
                class="hidden"
                :disabled="
                  showPollCreator ||
                  selectedVideoFiles.length >= MAX_VIDEOS ||
                  remainingPoints < VIDEO_POINTS
                "
              />
            </label>
            <div
              v-if="!showPollCreator"
              class="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xs rounded-lg py-1 px-2 opacity-0 group-hover:opacity-100 transition-all duration-200 pointer-events-none whitespace-nowrap shadow-lg"
            >
              {{
                selectedVideoFiles.length >= MAX_VIDEOS
                  ? `Maximum ${MAX_VIDEOS} videos allowed`
                  : remainingPoints < VIDEO_POINTS
                    ? 'Not enough upload slots remaining'
                    : `Add Videos (${selectedVideoFiles.length}/${MAX_VIDEOS})`
              }}
            </div>
          </div>

          <!-- Poll Button -->
          <div class="relative group">
            <button
              @click="togglePollCreator"
              type="button"
              class="text-purple-500 hover:text-purple-600 cursor-pointer transition-all duration-200 p-1.5 sm:p-2 rounded-xl bg-gradient-to-br from-purple-50 to-pink-100 hover:from-purple-100 hover:to-pink-200 flex items-center justify-center w-8 h-8 sm:w-10 sm:h-10 shadow-sm hover:shadow-md border border-purple-200"
              :class="{ 'ring-2 ring-purple-300 shadow-md': showPollCreator }"
            >
              <font-awesome-icon :icon="['fas', 'chart-bar']" class="text-sm sm:text-base" />
            </button>
            <div
              class="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xs rounded-lg py-1 px-2 opacity-0 group-hover:opacity-100 transition-all duration-200 pointer-events-none whitespace-nowrap shadow-lg"
            >
              Create Poll
            </div>
          </div>

          <!-- Document Button -->
          <div class="relative group">
            <button
              type="button"
              class="text-orange-500 transition-all duration-200 p-1.5 sm:p-2 rounded-xl bg-gradient-to-br from-orange-50 to-orange-100 flex items-center justify-center w-8 h-8 sm:w-10 sm:h-10 shadow-sm border border-orange-200"
              :class="{
                'hover:text-orange-600 hover:from-orange-100 hover:to-orange-200 hover:shadow-md cursor-pointer':
                  !showPollCreator,
                'cursor-not-allowed': showPollCreator,
              }"
              :disabled="showPollCreator"
            >
              <font-awesome-icon :icon="['fas', 'file-alt']" class="text-sm sm:text-base" />
            </button>
            <div
              v-if="!showPollCreator"
              class="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xs rounded-lg py-1 px-2 opacity-0 group-hover:opacity-100 transition-all duration-200 pointer-events-none whitespace-nowrap shadow-lg"
            >
              Add Documents
            </div>
          </div>

          <!-- Content Box Button -->
          <div class="relative group">
            <button
              type="button"
              class="text-red-500 transition-all duration-200 p-1.5 sm:p-2 rounded-xl bg-gradient-to-br from-red-50 to-red-100 flex items-center justify-center w-8 h-8 sm:w-10 sm:h-10 shadow-sm border border-red-200"
              :class="{
                'hover:text-red-600 hover:from-red-100 hover:to-red-200 hover:shadow-md cursor-pointer':
                  !showPollCreator,
                'cursor-not-allowed': showPollCreator,
              }"
              :disabled="showPollCreator"
            >
              <font-awesome-icon :icon="['fas', 'square-plus']" class="text-sm sm:text-base" />
            </button>
            <div
              v-if="!showPollCreator"
              class="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xs rounded-lg py-1 px-2 opacity-0 group-hover:opacity-100 transition-all duration-200 pointer-events-none whitespace-nowrap shadow-lg"
            >
              Content Box
            </div>
          </div>
        </div>

        <div class="flex items-center gap-2 sm:gap-4">
          <div
            class="text-xs sm:text-sm text-gray-500 bg-gray-100 px-2 py-1 sm:px-3 sm:py-2 rounded-lg"
          >
            <span :class="{ 'text-orange-500 font-semibold': postContent.length > 250 }">
              {{ postContent.length }}/280
            </span>
          </div>
          <!-- Post Button -->
          <button
            type="submit"
            :disabled="isCreatingPost || !isSubmittable || isCompressing"
            class="bg-gradient-to-br from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-bold py-1.5 px-3 sm:py-2 sm:px-5 rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl disabled:from-blue-300 disabled:to-purple-400 disabled:cursor-not-allowed disabled:shadow-none transform hover:scale-105 disabled:hover:scale-100 min-w-16 sm:min-w-20 text-xs sm:text-sm"
            data-cy="create-post-submit-button"
          >
            <span v-if="isCreatingPost" class="flex items-center gap-1 sm:gap-2">
              <font-awesome-icon :icon="['fas', 'spinner']" class="animate-spin" />
              <span class="hidden sm:inline">Posting...</span>
            </span>
            <span v-else-if="isCompressing" class="flex items-center gap-1 sm:gap-2">
              <font-awesome-icon :icon="['fas', 'compress']" class="animate-pulse" />
              <span class="hidden sm:inline">Processing...</span>
            </span>
            <span v-else class="flex items-center gap-1 sm:gap-2">
              <font-awesome-icon :icon="['fas', 'paper-plane']" />
              Post
            </span>
          </button>
        </div>
      </div>
    </form>
  </div>
</template>
