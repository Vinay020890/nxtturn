<!-- C:\Users\Vinay\Project\frontend\src\components\CreateGroupFormModal.vue -->

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useGroupStore } from '@/stores/group'
import { useAuthStore } from '@/stores/auth'
import type { Group } from '@/stores/group'

// Heroicons imports
import {
  UserGroupIcon,
  ChatBubbleLeftRightIcon,
  LockClosedIcon,
  GlobeAltIcon,
  LockOpenIcon,
  XMarkIcon,
  PlusIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
} from '@heroicons/vue/24/solid'

// --- Component Props ---
const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true,
  },
})

// --- Component Emits ---
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'group-created', newGroup: Group): void
}>()

// --- Pinia Stores ---
const groupStore = useGroupStore()
const authStore = useAuthStore()

// --- Local State ---
const groupData = ref({
  name: '',
  description: '',
  privacy_level: 'public' as 'public' | 'private',
})

const localError = ref('')
const isCreatingGroup = computed(() => groupStore.isCreatingGroup)
const createGroupError = computed(() => groupStore.createGroupError)

const errorMessages = computed(() => {
  const errors: { name: string; description: string; privacy_level: string } = {
    name: '',
    description: '',
    privacy_level: '',
  }
  const backendError = groupStore.createGroupError

  if (typeof backendError === 'string') {
    try {
      const parsedError = JSON.parse(backendError)
      if (parsedError.name?.[0]) errors.name = parsedError.name[0]
      if (parsedError.description?.[0]) errors.description = parsedError.description[0]
      if (parsedError.privacy_level?.[0]) errors.privacy_level = parsedError.privacy_level[0]
    } catch (e) {
      // Not a JSON string, will be handled by the general error display.
    }
  } else if (backendError && typeof backendError === 'object') {
    const errObj = backendError as any
    if (errObj.name?.[0]) errors.name = errObj.name[0]
    if (errObj.description?.[0]) errors.description = errObj.description[0]
    if (errObj.privacy_level?.[0]) errors.privacy_level = errObj.privacy_level[0]
  }
  return errors
})

// --- Methods ---
watch(
  () => props.isOpen,
  (newVal) => {
    if (newVal) {
      resetForm()
    }
  },
)

function handleClose() {
  emit('close')
  resetForm()
}

function resetForm() {
  groupData.value = {
    name: '',
    description: '',
    privacy_level: 'public',
  }
  localError.value = ''
  groupStore.createGroupError = null
}

async function handleSubmit() {
  if (!groupData.value.name.trim()) {
    localError.value = 'Group name is required.'
    return
  }
  if (!groupData.value.description.trim()) {
    localError.value = 'Group description is required.'
    return
  }
  groupStore.createGroupError = null
  localError.value = ''

  const newGroup = await groupStore.createGroup(groupData.value)

  if (newGroup) {
    emit('group-created', newGroup)
  }
}
</script>

<template>
  <transition
    enter-active-class="transition duration-200 ease-out"
    leave-active-class="transition duration-150 ease-in"
    enter-from-class="opacity-0"
    enter-to-class="opacity-100"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="isOpen"
      class="fixed inset-0 z-50 overflow-y-auto modal-scroll"
      aria-labelledby="modal-title"
      role="dialog"
      aria-modal="true"
    >
      <!-- Backdrop - Fixed in place -->
      <div class="fixed inset-0 bg-black/50 backdrop-blur-sm" @click="handleClose"></div>

      <!-- Modal Container - Fixed in center -->
      <div class="fixed inset-0 flex items-center justify-center p-4 sm:p-6">
        <div class="relative w-full max-w-md mx-auto">
          <!-- Modal Card -->
          <div
            class="relative bg-white rounded-xl shadow-2xl overflow-hidden transform transition-all max-h-[90vh] flex flex-col"
          >
            <!-- Header -->
            <div class="bg-gradient-to-r from-blue-600 to-indigo-600 px-5 py-4 sm:px-6 sm:py-5">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <div class="bg-white/20 p-1.5 rounded-lg backdrop-blur-sm">
                    <UserGroupIcon class="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <h2 id="modal-title" class="text-lg sm:text-xl font-bold text-white">
                      Create New Group
                    </h2>
                    <p class="text-blue-100 text-xs sm:text-sm mt-0.5">
                      Start connecting people with shared interests
                    </p>
                  </div>
                </div>
                <button
                  @click="handleClose"
                  class="text-white/80 hover:text-white p-1 rounded-lg transition-colors duration-150 hover:bg-white/10"
                  aria-label="Close modal"
                >
                  <XMarkIcon class="h-5 w-5" />
                </button>
              </div>
            </div>

            <!-- Form Content - Scrollable inside modal -->
            <div class="px-5 py-4 sm:px-6 sm:py-5 flex-1 overflow-y-auto custom-scrollbar">
              <form @submit.prevent="handleSubmit" class="space-y-5">
                <!-- Group Name -->
                <div class="space-y-2">
                  <div class="flex items-center gap-2 mb-1">
                    <div class="bg-blue-100 p-1.5 rounded-md">
                      <UserGroupIcon class="h-4 w-4 text-blue-600" />
                    </div>
                    <label for="group-name" class="text-sm font-semibold text-gray-700">
                      Group Name
                    </label>
                  </div>
                  <input
                    data-cy="group-name-input"
                    type="text"
                    id="group-name"
                    v-model="groupData.name"
                    required
                    class="w-full px-3 py-2.5 text-sm rounded-lg border border-gray-300 text-gray-900 placeholder-gray-500 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 focus:outline-none transition-all duration-150"
                    placeholder="e.g., Python Developers Community"
                    :disabled="isCreatingGroup"
                  />
                  <p
                    v-if="errorMessages.name"
                    class="text-xs text-red-600 bg-red-50 px-2 py-1.5 rounded flex items-center gap-1.5"
                  >
                    <ExclamationTriangleIcon class="h-3.5 w-3.5 flex-shrink-0" />
                    {{ errorMessages.name }}
                  </p>
                </div>

                <!-- Group Description -->
                <div class="space-y-2">
                  <div class="flex items-center gap-2 mb-1">
                    <div class="bg-purple-100 p-1.5 rounded-md">
                      <ChatBubbleLeftRightIcon class="h-4 w-4 text-purple-600" />
                    </div>
                    <label for="group-description" class="text-sm font-semibold text-gray-700">
                      Description
                    </label>
                  </div>
                  <textarea
                    data-cy="group-description-input"
                    id="group-description"
                    v-model="groupData.description"
                    rows="3"
                    class="w-full px-3 py-2.5 text-sm rounded-lg border border-gray-300 text-gray-900 placeholder-gray-500 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 focus:outline-none transition-all duration-150 resize-none"
                    placeholder="Briefly describe your group's purpose, goals, and who should join..."
                    :disabled="isCreatingGroup"
                  ></textarea>
                  <div class="flex justify-between items-center">
                    <p
                      v-if="errorMessages.description"
                      class="text-xs text-red-600 bg-red-50 px-2 py-1.5 rounded flex items-center gap-1.5"
                    >
                      <ExclamationTriangleIcon class="h-3.5 w-3.5 flex-shrink-0" />
                      {{ errorMessages.description }}
                    </p>
                    <span class="text-xs text-gray-400 ml-auto">
                      {{ groupData.description.length }}/500
                    </span>
                  </div>
                </div>

                <!-- Privacy Level -->
                <div class="space-y-3">
                  <div class="flex items-center gap-2 mb-1">
                    <div class="bg-emerald-100 p-1.5 rounded-md">
                      <LockClosedIcon class="h-4 w-4 text-emerald-600" />
                    </div>
                    <label class="text-sm font-semibold text-gray-700"> Privacy Settings </label>
                  </div>
                  <p class="text-xs text-gray-500 -mt-1 mb-3">
                    Control who can see and join your group
                  </p>

                  <!-- Privacy Options -->
                  <div class="space-y-3">
                    <!-- Public Option -->
                    <div class="relative">
                      <div
                        @click="groupData.privacy_level = 'public'"
                        class="cursor-pointer border-2 rounded-lg p-4 transition-all duration-150 hover:border-blue-300"
                        :class="{
                          'border-blue-500 bg-blue-50': groupData.privacy_level === 'public',
                          'border-gray-200': groupData.privacy_level !== 'public',
                        }"
                      >
                        <div class="flex items-start gap-3">
                          <div class="flex-shrink-0 mt-0.5">
                            <div class="relative">
                              <div
                                class="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-100 to-blue-50 flex items-center justify-center"
                              >
                                <GlobeAltIcon class="w-4 h-4 text-blue-600" />
                              </div>
                              <div
                                v-if="groupData.privacy_level === 'public'"
                                class="absolute -top-1 -right-1"
                              ></div>
                            </div>
                          </div>
                          <div class="flex-1 min-w-0">
                            <div class="flex flex-wrap items-center gap-2 mb-1">
                              <span class="font-semibold text-gray-900">Public</span>
                              <span
                                class="bg-emerald-100 text-emerald-800 text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap"
                              >
                                Recommended
                              </span>
                            </div>
                            <p class="text-xs text-gray-600 mb-2">
                              Anyone can view and join your group. Great for open communities.
                            </p>
                            <div class="space-y-1">
                              <div class="flex items-center gap-1.5 text-xs text-gray-500">
                                <CheckCircleIcon class="w-3 h-3 text-emerald-500 flex-shrink-0" />
                                <span class="truncate">Visible to everyone</span>
                              </div>
                              <div class="flex items-center gap-1.5 text-xs text-gray-500">
                                <CheckCircleIcon class="w-3 h-3 text-emerald-500 flex-shrink-0" />
                                <span class="truncate">Instant joining</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                      <!-- FIX: Radio input that Cypress can interact with -->
                      <input
                        type="radio"
                        name="privacy"
                        value="public"
                        v-model="groupData.privacy_level"
                        class="absolute top-0 left-0 w-full h-full opacity-0 cursor-pointer z-10"
                        :disabled="isCreatingGroup"
                      />
                    </div>

                    <!-- Private Option -->
                    <div class="relative">
                      <div
                        @click="groupData.privacy_level = 'private'"
                        class="cursor-pointer border-2 rounded-lg p-4 transition-all duration-150 hover:border-purple-300"
                        :class="{
                          'border-purple-500 bg-purple-50': groupData.privacy_level === 'private',
                          'border-gray-200': groupData.privacy_level !== 'private',
                        }"
                      >
                        <div class="flex items-start gap-3">
                          <div class="flex-shrink-0 mt-0.5">
                            <div class="relative">
                              <div
                                class="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-100 to-purple-50 flex items-center justify-center"
                              >
                                <LockOpenIcon class="w-4 h-4 text-purple-600" />
                              </div>
                              <div
                                v-if="groupData.privacy_level === 'private'"
                                class="absolute -top-1 -right-1"
                              ></div>
                            </div>
                          </div>
                          <div class="flex-1 min-w-0">
                            <div class="flex items-center gap-2 mb-1">
                              <span class="font-semibold text-gray-900">Private</span>
                            </div>
                            <p class="text-xs text-gray-600 mb-2">
                              Only approved members can view and join. You control who gets in.
                            </p>
                            <div class="space-y-1">
                              <div class="flex items-center gap-1.5 text-xs text-gray-500">
                                <CheckCircleIcon class="w-3 h-3 text-purple-500 flex-shrink-0" />
                                <span class="truncate">Hidden from public view</span>
                              </div>
                              <div class="flex items-center gap-1.5 text-xs text-gray-500">
                                <CheckCircleIcon class="w-3 h-3 text-purple-500 flex-shrink-0" />
                                <span class="truncate">Requires approval to join</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                      <!-- FIX: Radio input that Cypress can interact with -->
                      <input
                        data-cy="privacy-private-radio"
                        type="radio"
                        name="privacy"
                        value="private"
                        v-model="groupData.privacy_level"
                        class="absolute top-0 left-0 w-full h-full opacity-0 cursor-pointer z-10"
                        :disabled="isCreatingGroup"
                      />
                    </div>
                  </div>

                  <p
                    v-if="errorMessages.privacy_level"
                    class="text-xs text-red-600 bg-red-50 px-2 py-1.5 rounded flex items-center gap-1.5"
                  >
                    <ExclamationTriangleIcon class="h-3.5 w-3.5" />
                    {{ errorMessages.privacy_level }}
                  </p>
                </div>

                <!-- General Error -->
                <div v-if="localError" class="bg-red-50 border border-red-200 rounded-lg p-3">
                  <div class="flex items-center gap-2">
                    <div class="flex-shrink-0">
                      <div class="w-6 h-6 rounded-full bg-red-100 flex items-center justify-center">
                        <ExclamationTriangleIcon class="w-3.5 h-3.5 text-red-600" />
                      </div>
                    </div>
                    <div class="min-w-0">
                      <p class="text-sm font-medium text-red-800 truncate">Validation Error</p>
                      <p class="text-xs text-red-600 mt-0.5">{{ localError }}</p>
                    </div>
                  </div>
                </div>
              </form>
            </div>

            <!-- Footer Actions - Fixed at bottom of modal -->
            <div class="bg-gray-50 px-5 py-4 sm:px-6 sm:py-4 border-t border-gray-200">
              <div class="flex flex-col sm:flex-row gap-3">
                <button
                  type="button"
                  @click="handleClose"
                  :disabled="isCreatingGroup"
                  class="px-4 py-2.5 text-sm rounded-lg border border-gray-300 bg-white text-gray-700 font-medium hover:bg-gray-50 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-200 transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
                <button
                  data-cy="create-group-submit-button"
                  type="submit"
                  @click="handleSubmit"
                  :disabled="isCreatingGroup"
                  class="flex-1 px-4 py-2.5 text-sm rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-medium hover:from-blue-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-blue-500/30 transition-all duration-150 shadow hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span class="flex items-center justify-center gap-2">
                    <PlusIcon v-if="!isCreatingGroup" class="w-4 h-4" />
                    <span v-if="!isCreatingGroup">Create Group</span>
                    <span v-if="isCreatingGroup">Creating...</span>
                  </span>
                </button>
              </div>
              <p class="text-xs text-gray-500 text-center mt-3">
                <InformationCircleIcon class="w-3 h-3 inline mr-1" />
                You'll be the admin and can manage settings & members
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<style scoped>
/* Fixed positioning for backdrop and modal */
.fixed {
  position: fixed;
}

/* Modal stays perfectly centered */
.fixed.inset-0.flex.items-center.justify-center {
  align-items: center;
  justify-content: center;
}

/* Custom light scrollbar for form content */
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 #f1f5f9;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 10px;
  margin: 4px 0;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 10px;
  border: 2px solid #f1f5f9;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.custom-scrollbar::-webkit-scrollbar-thumb:active {
  background: #64748b;
}

.custom-scrollbar::-webkit-scrollbar-corner {
  background: #f1f5f9;
}

/* Modal max height - prevents it from being too tall */
.max-h-\[90vh\] {
  max-height: 90vh;
}

/* Prevent text overflow */
.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Better focus styles for accessibility */
input:focus,
textarea:focus,
button:focus {
  outline: 2px solid transparent;
  outline-offset: 2px;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.5);
}

/* Responsive adjustments */
@media (max-width: 640px) {
  .p-4 {
    padding: 1rem;
  }

  .max-h-\[90vh\] {
    max-height: 85vh;
  }

  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
  }
}

/* Modal will never exceed viewport height */
.flex.flex-col {
  display: flex;
  flex-direction: column;
}

.flex-1 {
  flex: 1 1 0%;
}

/* Smooth transitions */
.transition-all {
  transition-property: all;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 150ms;
}

/* Modal backdrop blur effect */
.backdrop-blur-sm {
  backdrop-filter: blur(4px);
}

/* Enhanced scrollbar for the entire modal when needed */
.modal-scroll::-webkit-scrollbar {
  width: 8px;
}

.modal-scroll::-webkit-scrollbar-track {
  background: rgba(241, 245, 249, 0.3);
}

.modal-scroll::-webkit-scrollbar-thumb {
  background: rgba(203, 213, 225, 0.5);
  border-radius: 4px;
}

.modal-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.6);
}

/* FIX: Make radio inputs invisible to users but interactable by Cypress */
.absolute.top-0.left-0.w-full.h-full.opacity-0 {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
  z-index: 10;
}

/* Ensure the radio input covers the entire clickable area */
.relative {
  position: relative;
}

/* Make sure the visual card is above the radio input for users */
.relative > div:first-child {
  position: relative;
  z-index: 1;
}
</style>
