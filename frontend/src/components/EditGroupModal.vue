<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { Group } from '@/stores/group'

interface Props {
  isOpen: boolean
  isSubmitting: boolean
  group: Group | null
}
const props = withDefaults(defineProps<Props>(), {
  isOpen: false,
  isSubmitting: false,
  group: null,
})

const emit = defineEmits(['close', 'submit'])

const editableGroup = ref({ name: '', description: '' })

// When the modal opens, populate the form with the group's current data
watch(
  () => props.group,
  (newGroup) => {
    if (newGroup) {
      editableGroup.value.name = newGroup.name
      editableGroup.value.description = newGroup.description || ''
    }
  },
  { immediate: true },
)

const isFormValid = computed(() => {
  return editableGroup.value.name.trim().length > 0
})

function handleSubmit() {
  if (isFormValid.value && !props.isSubmitting) {
    emit('submit', { ...editableGroup.value })
  }
}
</script>

<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 bg-gradient-to-br from-gray-900/50 to-blue-900/20 z-40 flex justify-center items-center p-4 backdrop-blur-sm overflow-y-auto py-8"
    @click.self="emit('close')"
  >
    <div
      class="bg-white rounded-xl shadow-xl w-full max-w-xs sm:max-w-sm md:max-w-sm mx-auto my-auto transform transition-all duration-300 scale-100 border border-gray-100"
    >
      <!-- Header with Icon -->
      <div class="p-4 sm:p-5">
        <div class="flex items-center mb-5 sm:mb-6">
          <div
            class="bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 p-2.5 rounded-lg mr-3 shadow"
          >
            <i class="fas fa-users text-white text-base"></i>
          </div>
          <div>
            <h2 class="text-lg sm:text-xl font-bold text-gray-800">Edit Group Details</h2>
            <p class="text-gray-500 text-xs sm:text-sm mt-0.5">Update your group information</p>
          </div>
        </div>

        <form @submit.prevent="handleSubmit">
          <!-- Name Field -->
          <div class="mb-4 sm:mb-5">
            <label for="group-name" class="block text-sm font-semibold text-gray-700 mb-2">
              <i class="fas fa-hashtag text-blue-500 mr-1.5"></i>
              Group Name
            </label>
            <div class="relative">
              <input
                id="group-name"
                v-model="editableGroup.name"
                type="text"
                required
                placeholder="Enter group name"
                class="w-full px-3 py-2.5 border-2 border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-500 transition-all duration-200 bg-white hover:border-blue-300 shadow-sm text-sm"
                :class="{
                  'border-blue-500 bg-blue-50': editableGroup.name,
                  'border-red-300': !isFormValid && editableGroup.name,
                }"
              />
            </div>
            <p
              v-if="!isFormValid && editableGroup.name"
              class="text-red-500 text-xs mt-1.5 flex items-center"
            >
              <i class="fas fa-exclamation-triangle mr-1.5 text-xs"></i> Group name cannot be empty
            </p>
          </div>

          <!-- Description Field -->
          <div class="mb-5 sm:mb-6">
            <label for="group-description" class="block text-sm font-semibold text-gray-700 mb-2">
              <i class="fas fa-align-left text-green-500 mr-1.5"></i>
              Description
            </label>
            <div class="relative">
              <textarea
                id="group-description"
                v-model="editableGroup.description"
                rows="3"
                class="w-full px-3 py-2.5 border-2 border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-100 focus:border-green-500 transition-all duration-200 bg-white hover:border-green-300 shadow-sm resize-none text-sm"
                placeholder="Add a description for your group (optional)"
              ></textarea>
            </div>
            <div class="flex justify-between mt-1.5">
              <span class="text-xs text-gray-500">Optional description</span>
              <span
                class="text-xs"
                :class="
                  editableGroup.description.length > 400 ? 'text-orange-500' : 'text-gray-400'
                "
              >
                {{ editableGroup.description.length }}/500
              </span>
            </div>
          </div>

          <!-- Action Buttons -->
          <div
            class="flex flex-col xs:flex-row justify-end gap-2 sm:gap-3 pt-5 border-t border-gray-100"
          >
            <button
              type="button"
              @click="emit('close')"
              class="px-4 py-2 bg-gradient-to-r from-gray-100 to-gray-50 text-gray-700 rounded-lg hover:from-gray-200 hover:to-gray-100 font-medium flex items-center justify-center transition-all duration-200 shadow-sm hover:shadow border border-gray-200 hover:border-gray-300 text-sm order-2 xs:order-1"
            >
              <i class="fas fa-times mr-1.5 text-xs"></i>
              Cancel
            </button>
            <button
              type="submit"
              :disabled="!isFormValid || isSubmitting"
              :class="[
                'px-4 py-2 rounded-lg font-medium flex items-center justify-center transition-all duration-200 shadow hover:shadow-md order-1 xs:order-2 text-sm',
                isFormValid && !isSubmitting
                  ? 'bg-gradient-to-r from-blue-600 via-blue-500 to-blue-600 hover:from-blue-700 hover:via-blue-600 hover:to-blue-700 text-white transform hover:-translate-y-0.5 active:scale-95'
                  : 'bg-gradient-to-r from-blue-300 to-blue-200 text-white cursor-not-allowed',
              ]"
            >
              <i v-if="isSubmitting" class="fas fa-spinner fa-spin mr-1.5 text-xs"></i>
              <i v-else class="fas fa-save mr-1.5 text-xs"></i>
              {{ isSubmitting ? 'Saving...' : 'Save Changes' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style>
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');

.fa-spinner.fa-spin {
  animation: fa-spin 1s linear infinite;
}

@keyframes fa-spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.transform {
  transform: translate3d(0, 0, 0);
  backface-visibility: hidden;
}

.hover\:-translate-y-0\.5:hover {
  transform: translateY(-0.125rem);
}

.active\:scale-95:active {
  transform: scale(0.95);
}

.transition-all {
  transition-property: all;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 200ms;
}

.backdrop-blur-sm {
  backdrop-filter: blur(4px);
}

.shadow-sm {
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.shadow {
  box-shadow:
    0 4px 6px -1px rgba(0, 0, 0, 0.1),
    0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.shadow-md {
  box-shadow:
    0 6px 10px -1px rgba(0, 0, 0, 0.1),
    0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.shadow-xl {
  box-shadow:
    0 10px 15px -3px rgba(0, 0, 0, 0.1),
    0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

.hover\:shadow:hover {
  box-shadow:
    0 4px 6px -1px rgba(0, 0, 0, 0.1),
    0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.hover\:shadow-md:hover {
  box-shadow:
    0 6px 10px -1px rgba(0, 0, 0, 0.1),
    0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.bg-gradient-to-br {
  background-image: linear-gradient(to bottom right, var(--tw-gradient-stops));
}

.bg-gradient-to-r {
  background-image: linear-gradient(to right, var(--tw-gradient-stops));
}

.from-gray-900\/50 {
  --tw-gradient-from: rgba(17, 24, 39, 0.5);
  --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to, rgba(17, 24, 39, 0));
}

.to-blue-900\/20 {
  --tw-gradient-to: rgba(30, 58, 138, 0.2);
}

.from-blue-500 {
  --tw-gradient-from: #3b82f6;
  --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to, rgba(59, 130, 246, 0));
}

.via-purple-500 {
  --tw-gradient-stops:
    var(--tw-gradient-from), #8b5cf6, var(--tw-gradient-to, rgba(139, 92, 246, 0));
}

.to-pink-500 {
  --tw-gradient-to: #ec4899;
}

.from-gray-100 {
  --tw-gradient-from: #f3f4f6;
  --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to, rgba(243, 244, 246, 0));
}

.to-gray-50 {
  --tw-gradient-to: #f9fafb;
}

.hover\:from-gray-200:hover {
  --tw-gradient-from: #e5e7eb;
  --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to, rgba(229, 231, 235, 0));
}

.hover\:to-gray-100:hover {
  --tw-gradient-to: #f3f4f6;
}

.from-blue-600 {
  --tw-gradient-from: #2563eb;
  --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to, rgba(37, 99, 235, 0));
}

.via-blue-500 {
  --tw-gradient-stops:
    var(--tw-gradient-from), #3b82f6, var(--tw-gradient-to, rgba(59, 130, 246, 0));
}

.to-blue-600 {
  --tw-gradient-to: #2563eb;
}

.hover\:from-blue-700:hover {
  --tw-gradient-from: #1d4ed8;
  --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to, rgba(29, 78, 216, 0));
}

.hover\:via-blue-600:hover {
  --tw-gradient-stops:
    var(--tw-gradient-from), #2563eb, var(--tw-gradient-to, rgba(37, 99, 235, 0));
}

.hover\:to-blue-700:hover {
  --tw-gradient-to: #1d4ed8;
}

.from-blue-300 {
  --tw-gradient-from: #93c5fd;
  --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to, rgba(147, 197, 253, 0));
}

.to-blue-200 {
  --tw-gradient-to: #bfdbfe;
}

.focus\:ring-2:focus {
  --tw-ring-offset-shadow: var(--tw-ring-inset) 0 0 0 var(--tw-ring-offset-width)
    var(--tw-ring-offset-color);
  --tw-ring-shadow: var(--tw-ring-inset) 0 0 0 calc(2px + var(--tw-ring-offset-width))
    var(--tw-ring-color);
  box-shadow: var(--tw-ring-offset-shadow), var(--tw-ring-shadow), var(--tw-shadow, 0 0 #0000);
}

.focus\:ring-blue-100:focus {
  --tw-ring-color: rgba(219, 234, 254, 1);
}

.focus\:ring-green-100:focus {
  --tw-ring-color: rgba(220, 252, 231, 1);
}

.focus\:border-blue-500:focus {
  border-color: #3b82f6;
}

.focus\:border-green-500:focus {
  border-color: #10b981;
}

.focus\:outline-none:focus {
  outline: 2px solid transparent;
  outline-offset: 2px;
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.resize-none {
  resize: none;
}

.rounded-lg {
  border-radius: 0.5rem;
}

.rounded-xl {
  border-radius: 0.75rem;
}

/* Responsive breakpoints */
@media (max-width: 639px) {
  .max-w-xs {
    max-width: 18rem;
  }
}

@media (min-width: 475px) {
  .xs\:flex-row {
    flex-direction: row;
  }

  .xs\:order-1 {
    order: 1;
  }

  .xs\:order-2 {
    order: 2;
  }
}

@media (min-width: 640px) {
  .sm\:max-w-sm {
    max-width: 22rem;
  }

  .sm\:p-5 {
    padding: 1.25rem;
  }

  .sm\:mb-6 {
    margin-bottom: 1.5rem;
  }

  .sm\:mb-5 {
    margin-bottom: 1.25rem;
  }

  .sm\:text-xl {
    font-size: 1.25rem;
    line-height: 1.75rem;
  }

  .sm\:text-sm {
    font-size: 0.875rem;
    line-height: 1.25rem;
  }
}

@media (min-width: 768px) {
  .md\:max-w-sm {
    max-width: 24rem;
  }
}

.overflow-y-auto {
  overflow-y: auto;
}
</style>
