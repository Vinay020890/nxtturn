<script setup lang="ts">
import { ref } from 'vue'
import { useProfileStore } from '@/stores/profile'
import { useToast } from 'vue-toastification'
import {
  DocumentIcon,
  ArrowUpTrayIcon,
  TrashIcon,
  ArrowDownTrayIcon,
  DocumentTextIcon,
} from '@heroicons/vue/24/outline'

const props = defineProps<{
  resumeUrl: string | null
  username: string
  isOwner: boolean
}>()

const profileStore = useProfileStore()
const toast = useToast()
const fileInput = ref<HTMLInputElement | null>(null)
const isUploading = ref(false)

const handleFileUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  if (!target.files?.length) return

  const file = target.files[0]

  // 1. Frontend Validation
  if (file.type !== 'application/pdf') {
    toast.error('Please upload a PDF file.')
    return
  }
  if (file.size > 5 * 1024 * 1024) {
    // 5MB Limit
    toast.error('File is too large (Max 5MB).')
    return
  }

  isUploading.value = true
  try {
    await profileStore.updateResume(props.username, file)
    toast.success('Resume uploaded successfully!')
  } catch (error: any) {
    toast.error(error.message || 'Upload failed')
  } finally {
    isUploading.value = false
    // Clear input so the same file can be re-selected if needed
    if (fileInput.value) fileInput.value.value = ''
  }
}

const handleDelete = async () => {
  if (!confirm('Are you sure you want to remove your resume?')) return
  try {
    await profileStore.removeResume(props.username)
    toast.success('Resume removed.')
  } catch (error: any) {
    toast.error(error.message || 'Failed to remove resume')
  }
}
</script>

<template>
  <div
    class="bg-white rounded-xl border border-gray-200 p-8 shadow-sm transition-all hover:shadow-md"
  >
    <div class="flex flex-col items-center text-center">
      <!-- Icon Header -->
      <div
        class="w-20 h-20 bg-indigo-50 rounded-full flex items-center justify-center text-indigo-600 mb-6"
      >
        <DocumentTextIcon class="w-12 h-12" />
      </div>

      <h3 class="text-2xl font-bold text-gray-900 mb-2">Resume / CV</h3>

      <!-- CASE A: No Resume Uploaded -->
      <div v-if="!resumeUrl" class="space-y-6">
        <p class="text-gray-500 max-w-sm leading-relaxed">
          Sharing your resume helps recruiters and connections understand your professional
          background better.
        </p>

        <div v-if="isOwner">
          <input
            type="file"
            ref="fileInput"
            class="hidden"
            accept=".pdf"
            @change="handleFileUpload"
          />
          <button
            @click="fileInput?.click()"
            :disabled="isUploading"
            class="inline-flex items-center gap-2 px-8 py-3 bg-indigo-600 text-white font-bold rounded-full hover:bg-indigo-700 shadow-lg hover:shadow-indigo-200 transition-all disabled:bg-indigo-300 disabled:cursor-wait"
            data-cy="upload-resume-button"
          >
            <ArrowUpTrayIcon class="w-5 h-5" />
            {{ isUploading ? 'Uploading...' : 'Upload PDF' }}
          </button>
        </div>
        <p v-else class="text-gray-400 italic bg-gray-50 px-4 py-2 rounded-lg">
          This user hasn't shared a resume yet.
        </p>
      </div>

      <!-- CASE B: Resume exists -->
      <div v-else class="w-full max-w-md mt-4">
        <div
          class="bg-gray-50 rounded-2xl p-5 border border-gray-100 flex items-center justify-between"
        >
          <div class="flex items-center gap-4 overflow-hidden">
            <div class="p-3 bg-white rounded-xl shadow-sm border border-gray-100 flex-shrink-0">
              <span class="text-sm font-black text-red-500">PDF</span>
            </div>
            <div class="text-left overflow-hidden">
              <p class="text-sm font-bold text-gray-900 truncate">Curriculum Vitae</p>
              <p class="text-xs text-gray-500">Shared publicly</p>
            </div>
          </div>

          <div class="flex items-center gap-2">
            <!-- View/Download Link -->
            <a
              :href="resumeUrl"
              target="_blank"
              class="p-2.5 text-gray-500 hover:text-indigo-600 hover:bg-white rounded-full transition-all shadow-sm hover:shadow"
              title="View Resume"
              data-cy="view-resume-link"
            >
              <ArrowDownTrayIcon class="w-5 h-5" />
            </a>

            <!-- Delete Button (Owner Only) -->
            <button
              v-if="isOwner"
              @click="handleDelete"
              class="p-2.5 text-gray-500 hover:text-red-600 hover:bg-white rounded-full transition-all shadow-sm hover:shadow"
              title="Delete Resume"
              data-cy="delete-resume-button"
            >
              <TrashIcon class="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
