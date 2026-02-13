<script setup lang="ts">
import { XMarkIcon } from '@heroicons/vue/24/solid'
import { computed, useAttrs } from 'vue'
import type { StyleValue } from 'vue'

// Define props
const props = defineProps<{
  show: boolean
  title: string
  maxWidth?: string
}>()

// Define emits
const emit = defineEmits(['close'])

// Disable automatic attribute inheritance
defineOptions({
  inheritAttrs: false,
})

// Get all attributes
const attrs = useAttrs()

// Create a computed property for attributes that are safe to bind
const filteredAttributes = computed(() => {
  const { class: className, style, ...otherAttrs } = attrs

  const result: Record<string, unknown> = { ...otherAttrs }

  // Handle class - ensure it's a string or array
  if (className) {
    result.class = className
  }

  // Handle style - ensure it's a valid StyleValue
  if (style) {
    result.style = style as StyleValue
  }

  return result
})

// Compute container classes
const containerClass = computed(() => {
  const base = 'relative w-full bg-white rounded-lg shadow-xl'
  const maxWidthClass = props.maxWidth || 'max-w-lg'

  if (attrs.class) {
    return `${base} ${maxWidthClass} ${attrs.class}`
  }

  return `${base} ${maxWidthClass}`
})

// Close modal function
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
      <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <!-- Modal container -->
        <div :class="containerClass" v-bind="filteredAttributes" @click.stop>
          <!-- Header -->
          <div class="flex items-center justify-between p-4 border-b">
            <h3 class="text-lg font-semibold text-gray-800">{{ title }}</h3>
            <button
              @click="closeModal"
              class="p-1 rounded-full text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              aria-label="Close modal"
            >
              <XMarkIcon class="w-6 h-6" />
            </button>
          </div>

          <!-- Content -->
          <div class="p-6 max-h-[70vh] overflow-y-auto">
            <slot></slot>
          </div>

          <!-- Footer (optional) -->
          <div v-if="$slots.footer" class="p-4 bg-gray-50 border-t rounded-b-lg">
            <slot name="footer"></slot>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>
