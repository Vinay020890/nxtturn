<script setup lang="ts">
import { XMarkIcon } from '@heroicons/vue/24/solid'
import { computed, useAttrs } from 'vue'
import type { StyleValue } from 'vue'

// Define props - Combining both versions
const props = defineProps<{
  show: boolean
  title: string
  maxWidth?: string // Aditya's improvement
}>()

const emit = defineEmits(['close'])

// Disable automatic attribute inheritance (Aditya's improvement)
defineOptions({
  inheritAttrs: false,
})

// Get all attributes
const attrs = useAttrs()

// Create a computed property for attributes (Aditya's improvement)
const filteredAttributes = computed(() => {
  const { class: className, style, ...otherAttrs } = attrs
  const result: Record<string, unknown> = { ...otherAttrs }
  if (className) result.class = className
  if (style) result.style = style as StyleValue
  return result
})

// Compute container classes - Merging your critical Flex/Height logic with his width logic
const containerClass = computed(() => {
  // We use YOUR max-h-[90vh] because 70vh is too short for our forms
  const base = 'relative flex flex-col w-full bg-white rounded-lg shadow-xl max-h-[90vh]'
  const maxWidthClass = props.maxWidth || 'max-w-lg'

  return `${base} ${maxWidthClass}`
})

function closeModal() {
  emit('close')
}
</script>

<template>
  <teleport to="body">
    <!-- Backdrop -->
    <transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="show"
        class="fixed inset-0 z-40 bg-black bg-opacity-60 backdrop-blur-sm"
        @click="closeModal"
      ></div>
    </transition>

    <!-- Modal -->
    <transition
      enter-active-class="transition ease-out duration-300"
      enter-from-class="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
      enter-to-class="opacity-100 translate-y-0 sm:scale-100"
      leave-active-class="transition ease-in duration-200"
      leave-from-class="opacity-100 translate-y-0 sm:scale-100"
      leave-to-class="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
    >
      <!-- Click container for "click outside" -->
      <div
        v-if="show"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
        @click="closeModal"
      >
        <!-- Modal panel - Using the merged containerClass and filteredAttributes -->
        <div :class="containerClass" v-bind="filteredAttributes" @click.stop>
          <!-- Modal Header (flex-shrink-0 prevents it from disappearing - Your Fix) -->
          <div class="flex items-center justify-between p-4 border-b flex-shrink-0">
            <h3 class="text-lg font-semibold text-gray-800">{{ title }}</h3>
            <button
              @click="closeModal"
              class="p-1 rounded-full text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              aria-label="Close modal"
            >
              <XMarkIcon class="w-6 h-6" />
            </button>
          </div>

          <!-- Modal Body (overflow-y-auto enables scrolling - Your Fix) -->
          <div class="p-6 overflow-y-auto flex-grow">
            <slot></slot>
          </div>

          <!-- Modal Footer (flex-shrink-0 prevents it from disappearing - Your Fix) -->
          <div v-if="$slots.footer" class="p-4 bg-gray-50 border-t rounded-b-lg flex-shrink-0">
            <slot name="footer"></slot>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>
