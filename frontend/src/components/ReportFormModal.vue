<script setup lang="ts">
import { ref, watch } from 'vue'
import { useModerationStore } from '@/stores/moderation'
import {
  ExclamationTriangleIcon,
  FlagIcon,
  XMarkIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  PaperAirplaneIcon,
  ArrowPathIcon,
  ChatBubbleLeftRightIcon,
  NoSymbolIcon,
  UserMinusIcon,
  EllipsisHorizontalIcon,
  PencilSquareIcon,
  ShieldExclamationIcon,
} from '@heroicons/vue/24/outline'

const props = defineProps<{
  isOpen: boolean
  target: { ct_id: number; obj_id: number } | null
}>()

const emit = defineEmits(['close'])

const moderationStore = useModerationStore()

const selectedReason = ref('')
const reportDetails = ref('')
const localValidationError = ref('')

const reasonOptions = [
  {
    value: 'SPAM',
    label: 'Spam',
    icon: FlagIcon,
    color: 'text-amber-500',
    bgColor: 'bg-amber-50',
    borderColor: 'border-amber-200',
    gradient: 'from-amber-400 to-amber-500',
  },
  {
    value: 'HARASSMENT',
    label: 'Harassment',
    icon: UserMinusIcon,
    color: 'text-rose-500',
    bgColor: 'bg-rose-50',
    borderColor: 'border-rose-200',
    gradient: 'from-rose-400 to-rose-500',
  },
  {
    value: 'HATE_SPEECH',
    label: 'Hate Speech',
    icon: ChatBubbleLeftRightIcon,
    color: 'text-red-500',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    gradient: 'from-red-400 to-red-500',
  },
  {
    value: 'VIOLENCE',
    label: 'Violence',
    icon: NoSymbolIcon,
    color: 'text-purple-500',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
    gradient: 'from-purple-400 to-purple-500',
  },
  {
    value: 'OTHER',
    label: 'Other',
    icon: EllipsisHorizontalIcon,
    color: 'text-slate-500',
    bgColor: 'bg-slate-50',
    borderColor: 'border-slate-200',
    gradient: 'from-slate-400 to-slate-500',
  },
]

const handleSubmit = async () => {
  localValidationError.value = ''
  if (!selectedReason.value) {
    localValidationError.value = 'Please select a reason for the report.'
    return
  }
  if (selectedReason.value === 'OTHER' && !reportDetails.value.trim()) {
    localValidationError.value = "Details are required when selecting 'Other'."
    return
  }
  if (!props.target) {
    localValidationError.value = 'Cannot submit report: target is missing.'
    return
  }

  const success = await moderationStore.submitReport({
    ct_id: props.target.ct_id,
    obj_id: props.target.obj_id,
    reason: selectedReason.value,
    details: reportDetails.value,
  })

  if (success) {
    setTimeout(() => {
      handleClose()
    }, 2500)
  }
}

const handleClose = () => {
  emit('close')
  setTimeout(() => {
    moderationStore.resetReportState()
  }, 300)
}

watch(
  () => props.isOpen,
  (newVal) => {
    if (!newVal) {
      selectedReason.value = ''
      reportDetails.value = ''
      localValidationError.value = ''
    }
  },
)
</script>

<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 bg-black bg-opacity-60 z-40 flex items-center justify-center p-3"
    @click.self="handleClose"
  >
    <!-- Removed border class from the main container -->
    <div
      class="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden transform transition-all duration-300 scale-100"
      @click.stop
    >
      <!-- Compact Header -->
      <div
        class="bg-gradient-to-br from-blue-500 via-purple-500 to-indigo-600 p-4 text-white relative"
      >
        <div class="flex justify-between items-center">
          <div class="flex items-center space-x-2">
            <div class="bg-white/20 p-1.5 rounded-lg">
              <ShieldExclamationIcon class="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 class="text-lg font-bold">Report Content</h2>
              <p class="text-blue-100 text-xs opacity-90">Help keep our community safe</p>
            </div>
          </div>
          <button
            @click="handleClose"
            class="text-white hover:bg-white/20 rounded-lg w-7 h-7 flex items-center justify-center transition-all duration-200"
          >
            <XMarkIcon class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- Compact Content -->
      <div class="p-4 max-h-[65vh] overflow-y-auto">
        <!-- Success Message -->
        <div
          v-if="moderationStore.submissionSuccess"
          class="text-center p-3 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg mb-4"
        >
          <div class="flex items-center justify-center mb-2">
            <div class="bg-green-100 p-2 rounded-full">
              <CheckCircleIcon class="w-6 h-6 text-green-500" />
            </div>
          </div>
          <p class="font-bold text-green-800 text-sm">Report Submitted!</p>
          <p class="text-green-700 text-xs mt-0.5">Thank you for your feedback</p>
        </div>

        <!-- Report Form -->
        <form v-else @submit.prevent="handleSubmit" class="space-y-4">
          <!-- Compact Reason Selection -->
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-2 flex items-center">
              <ExclamationTriangleIcon class="w-4 h-4 text-orange-500 mr-1.5" />
              Select Reason
            </label>
            <div class="grid grid-cols-2 gap-2">
              <div
                v-for="option in reasonOptions"
                :key="option.value"
                @click="selectedReason = option.value"
                class="border rounded-lg p-2.5 cursor-pointer flex items-center space-x-2 transition-all duration-200 hover:shadow-sm group"
                :class="
                  selectedReason === option.value
                    ? `${option.borderColor} ${option.bgColor} border-2 shadow-sm`
                    : 'border-gray-200 hover:border-gray-300'
                "
              >
                <div
                  class="p-1.5 rounded-md group-hover:scale-110 transition-transform"
                  :class="
                    selectedReason === option.value
                      ? `bg-gradient-to-r ${option.gradient} text-white`
                      : option.bgColor
                  "
                >
                  <component
                    :is="option.icon"
                    :class="`w-3.5 h-3.5 ${selectedReason === option.value ? 'text-white' : option.color}`"
                  />
                </div>
                <span class="font-medium text-gray-800 text-sm">{{ option.label }}</span>
              </div>
            </div>
          </div>

          <!-- Compact Details for "Other" -->
          <div
            v-if="selectedReason === 'OTHER'"
            class="transition-all duration-300 bg-blue-50 rounded-lg p-3"
          >
            <label
              for="report-details"
              class="block text-sm font-semibold text-gray-700 mb-1.5 flex items-center"
            >
              <PencilSquareIcon class="w-4 h-4 text-blue-500 mr-1.5" />
              Additional Details
            </label>
            <div class="relative">
              <textarea
                id="report-details"
                v-model="reportDetails"
                rows="3"
                class="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-300 focus:border-blue-400 transition-all text-sm"
                placeholder="Please provide specific details..."
              ></textarea>
              <div class="absolute bottom-2 right-2 text-gray-400">
                <PencilSquareIcon class="w-4 h-4" />
              </div>
            </div>
          </div>

          <!-- Compact Error/Feedback Messages -->
          <div
            v-if="localValidationError || moderationStore.submissionError"
            class="p-2.5 rounded-lg border-l-3 flex items-start"
            :class="{
              'bg-amber-50 border-amber-400':
                moderationStore.submissionError?.includes('already reported'),
              'bg-red-50 border-red-400':
                localValidationError ||
                !moderationStore.submissionError?.includes('already reported'),
            }"
          >
            <div class="flex-shrink-0 mr-2 mt-0.5">
              <ExclamationCircleIcon
                v-if="moderationStore.submissionError?.includes('already reported')"
                class="w-4 h-4 text-amber-500"
              />
              <ExclamationCircleIcon v-else class="w-4 h-4 text-red-500" />
            </div>
            <div class="flex-1">
              <p
                class="font-bold text-sm"
                v-if="moderationStore.submissionError?.includes('already reported')"
              >
                Already Reported
              </p>
              <p class="text-sm">{{ localValidationError || moderationStore.submissionError }}</p>
              <p
                v-if="moderationStore.submissionError?.includes('already reported')"
                class="mt-1 text-xs text-amber-700"
              >
                Our moderation team has been notified. Thank you for your vigilance.
              </p>
            </div>
          </div>

          <!-- Compact Action Buttons -->
          <div class="pt-3 flex flex-col sm:flex-row justify-end gap-2">
            <button
              type="button"
              @click="handleClose"
              class="px-4 py-2.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium flex items-center justify-center text-sm order-2 sm:order-1 flex-1 sm:flex-none"
            >
              <XMarkIcon class="w-4 h-4 mr-1.5" />
              Cancel
            </button>
            <button
              type="submit"
              :disabled="moderationStore.isSubmittingReport"
              class="px-4 py-2.5 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-lg hover:from-blue-600 hover:to-indigo-700 disabled:from-gray-400 disabled:to-gray-500 font-medium flex items-center justify-center transition-all duration-300 shadow-sm hover:shadow disabled:shadow-none text-sm order-1 sm:order-2 flex-1 sm:flex-none"
            >
              <ArrowPathIcon
                v-if="moderationStore.isSubmittingReport"
                class="w-4 h-4 mr-1.5 animate-spin"
              />
              <PaperAirplaneIcon v-else class="w-4 h-4 mr-1.5" />
              {{ moderationStore.isSubmittingReport ? 'Submitting...' : 'Submit' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Smooth animations */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition:
    transform 0.25s ease,
    opacity 0.25s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateY(-8px);
  opacity: 0;
}

/* Custom hover effects */
.reason-option {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.reason-option:hover {
  transform: translateY(-1px);
}
</style>
