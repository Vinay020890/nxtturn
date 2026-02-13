<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { Education } from '@/types'
import {
  AcademicCapIcon,
  BookOpenIcon,
  CalendarIcon,
  DocumentTextIcon,
  XMarkIcon,
  CheckIcon,
} from '@heroicons/vue/24/outline'

// Omit 'id' and 'user' for the form data, as the backend handles those.
type EducationFormData = Omit<Education, 'id'>

const props = defineProps<{
  initialData?: Education | null
}>()

const emit = defineEmits(['save', 'cancel'])

const form = ref<EducationFormData>({
  school: '',
  degree: '',
  field_of_study: '',
  start_date: '',
  end_date: null,
  description: '',
})

// Watch for changes in initialData to populate the form for editing.
watch(
  () => props.initialData,
  (newData) => {
    if (newData) {
      form.value = { ...newData }
    } else {
      // Reset form for adding a new entry
      form.value = {
        school: '',
        degree: '',
        field_of_study: '',
        start_date: '',
        end_date: null,
        description: '',
      }
    }
  },
  { immediate: true },
)

function handleSubmit() {
  // TODO: Add form validation here before emitting.
  emit('save', form.value)
}

// Safe description getter/setter
const descriptionText = computed({
  get: () => form.value.description || '',
  set: (value: string) => {
    form.value.description = value
  },
})

// Safe description length calculation
const descriptionLength = computed(() => {
  return descriptionText.value.length
})
</script>

<template>
  <form @submit.prevent="handleSubmit" class="space-y-4">
    <!-- School -->
    <div class="space-y-2">
      <label for="school" class="flex items-center space-x-2 text-sm font-semibold text-gray-700">
        <AcademicCapIcon class="h-4 w-4 text-blue-500" />
        <span>School / University</span>
        <span class="text-red-500">*</span>
      </label>
      <div class="relative">
        <input
          v-model="form.school"
          type="text"
          id="school"
          required
          placeholder="Enter school or university name"
          class="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-white hover:border-gray-400"
        />
        <AcademicCapIcon
          class="h-4 w-4 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2"
        />
      </div>
    </div>

    <!-- Degree and Field of Study -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <!-- Degree -->
      <div class="space-y-2">
        <label for="degree" class="flex items-center space-x-2 text-sm font-semibold text-gray-700">
          <BookOpenIcon class="h-4 w-4 text-green-500" />
          <span>Degree</span>
        </label>
        <div class="relative">
          <input
            v-model="form.degree"
            type="text"
            id="degree"
            placeholder="e.g., Bachelor's"
            class="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200 bg-white hover:border-gray-400"
          />
          <BookOpenIcon
            class="h-4 w-4 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2"
          />
        </div>
      </div>

      <!-- Field of Study -->
      <div class="space-y-2">
        <label
          for="field_of_study"
          class="flex items-center space-x-2 text-sm font-semibold text-gray-700"
        >
          <DocumentTextIcon class="h-4 w-4 text-purple-500" />
          <span>Field of Study</span>
        </label>
        <div class="relative">
          <input
            v-model="form.field_of_study"
            type="text"
            id="field_of_study"
            placeholder="e.g., Computer Science"
            class="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 bg-white hover:border-gray-400"
          />
          <DocumentTextIcon
            class="h-4 w-4 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2"
          />
        </div>
      </div>
    </div>

    <!-- Date Inputs -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div class="space-y-2">
        <label
          for="start_date"
          class="flex items-center space-x-2 text-sm font-semibold text-gray-700"
        >
          <CalendarIcon class="h-4 w-4 text-orange-500" />
          <span>Start Date</span>
          <span class="text-red-500">*</span>
        </label>
        <div class="relative">
          <input
            v-model="form.start_date"
            type="date"
            id="start_date"
            required
            class="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all duration-200 bg-white hover:border-gray-400"
          />
          <CalendarIcon
            class="h-4 w-4 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2"
          />
        </div>
      </div>
      <div class="space-y-2">
        <label
          for="end_date"
          class="flex items-center space-x-2 text-sm font-semibold text-gray-700"
        >
          <CalendarIcon class="h-4 w-4 text-teal-500" />
          <span>End Date (or expected)</span>
        </label>
        <div class="relative">
          <input
            v-model="form.end_date"
            type="date"
            id="end_date"
            class="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all duration-200 bg-white hover:border-gray-400"
          />
          <CalendarIcon
            class="h-4 w-4 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2"
          />
        </div>
      </div>
    </div>

    <!-- Description -->
    <div class="space-y-2">
      <label
        for="description"
        class="flex items-center space-x-2 text-sm font-semibold text-gray-700"
      >
        <DocumentTextIcon class="h-4 w-4 text-indigo-500" />
        <span>Description</span>
      </label>
      <div class="relative">
        <textarea
          v-model="descriptionText"
          id="description"
          rows="3"
          placeholder="Describe your studies, achievements, or relevant coursework..."
          class="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200 bg-white hover:border-gray-400 resize-none"
        ></textarea>
        <DocumentTextIcon class="h-4 w-4 text-gray-400 absolute left-3 top-2" />
      </div>
      <p class="text-xs text-gray-500 text-right">{{ descriptionLength }}/500 characters</p>
    </div>

    <!-- Form Actions -->
    <div class="flex justify-end space-x-3 pt-3 border-t border-gray-200">
      <button
        type="button"
        @click="$emit('cancel')"
        class="flex items-center space-x-2 px-4 py-2 text-sm bg-white border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-1"
      >
        <XMarkIcon class="h-4 w-4" />
        <span>Cancel</span>
      </button>
      <button
        type="submit"
        class="flex items-center space-x-2 px-4 py-2 text-sm bg-gradient-to-r from-blue-600 to-purple-600 border border-transparent rounded-lg font-medium text-white hover:from-blue-700 hover:to-purple-700 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
      >
        <CheckIcon class="h-4 w-4" />
        <span>{{ initialData ? 'Update Education' : 'Add Education' }}</span>
      </button>
    </div>
  </form>
</template>

<style scoped>
/* Custom scrollbar for textarea */
textarea::-webkit-scrollbar {
  width: 4px;
}

textarea::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 2px;
}

textarea::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 2px;
}

textarea::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* Smooth transitions for all interactive elements */
input,
textarea,
button {
  transition: all 0.2s ease-in-out;
}
</style>
