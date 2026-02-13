<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { EducationEntry } from '@/types'
import {
  AcademicCapIcon,
  BookOpenIcon,
  CalendarIcon,
  DocumentTextIcon,
  MapPinIcon,
  TrophyIcon,
  BuildingLibraryIcon,
  IdentificationIcon,
  XMarkIcon,
  CheckIcon,
} from '@heroicons/vue/24/outline'

// Omit 'id' as the backend handles that.
type EducationFormData = Omit<EducationEntry, 'id'>

const props = defineProps<{
  initialData?: EducationEntry | null
}>()

const emit = defineEmits(['save', 'cancel'])

// --- UI state for year/month (Vinay's Logic) ---
const startYear = ref<number | null>(null)
const startMonth = ref<number | null>(null)
const endYear = ref<number | null>(null)
const endMonth = ref<number | null>(null)

// --- State for all form data (Vinay's Backend Fields) ---
const form = ref({
  institution: '',
  degree: '',
  field_of_study: '',
  university: '',
  board: '',
  description: '',
  location: '',
  achievements: '',
})

// Helper to combine year/month into YYYY-MM-DD (Vinay's Logic)
function combineDate(year: number | null, month: number | null): string | null {
  if (!year) return null
  const monthStr = month ? String(month).padStart(2, '0') : '01'
  return `${year}-${monthStr}-01`
}

// Watcher to populate the form (Vinay's Logic)
watch(
  () => props.initialData,
  (newData) => {
    if (newData) {
      if (newData.start_date) {
        const startDate = new Date(newData.start_date)
        startYear.value = startDate.getUTCFullYear()
        startMonth.value = startDate.getUTCMonth() + 1
      }
      if (newData.end_date) {
        const endDate = new Date(newData.end_date)
        endYear.value = endDate.getUTCFullYear()
        endMonth.value = endDate.getUTCMonth() + 1
      }
      form.value = {
        institution: newData.institution || '',
        degree: newData.degree || '',
        field_of_study: newData.field_of_study || '',
        university: newData.university || '',
        board: newData.board || '',
        description: newData.description || '',
        location: newData.location || '',
        achievements: newData.achievements || '',
      }
    } else {
      startYear.value = startMonth.value = endYear.value = endMonth.value = null
      form.value = {
        institution: '',
        degree: '',
        field_of_study: '',
        university: '',
        board: '',
        description: '',
        location: '',
        achievements: '',
      }
    }
  },
  { immediate: true },
)

function handleSubmit() {
  const payload: EducationFormData = {
    ...form.value,
    start_date: combineDate(startYear.value, startMonth.value),
    end_date: combineDate(endYear.value, endMonth.value),
  }
  emit('save', payload)
}

const monthOptions = [
  { value: 1, name: 'January' },
  { value: 2, name: 'February' },
  { value: 3, name: 'March' },
  { value: 4, name: 'April' },
  { value: 5, name: 'May' },
  { value: 6, name: 'June' },
  { value: 7, name: 'July' },
  { value: 8, name: 'August' },
  { value: 9, name: 'September' },
  { value: 10, name: 'October' },
  { value: 11, name: 'November' },
  { value: 12, name: 'December' },
]
</script>

<template>
  <form @submit.prevent="handleSubmit" class="space-y-5">
    <!-- Institution (Using Aditya's Styles) -->
    <div class="space-y-1.5">
      <label
        for="institution"
        class="flex items-center space-x-2 text-sm font-semibold text-gray-700"
      >
        <AcademicCapIcon class="h-4 w-4 text-blue-500" />
        <span>Institution / School</span>
        <span class="text-red-500">*</span>
      </label>
      <div class="relative">
        <input
          v-model="form.institution"
          type="text"
          id="institution"
          required
          placeholder="e.g. IIT Bombay"
          class="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition-all"
        />
        <AcademicCapIcon class="h-4 w-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
      </div>
    </div>

    <!-- Degree & Field of Study Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div class="space-y-1.5">
        <label for="degree" class="flex items-center space-x-2 text-sm font-semibold text-gray-700">
          <BookOpenIcon class="h-4 w-4 text-green-500" />
          <span>Degree</span>
        </label>
        <div class="relative">
          <input
            v-model="form.degree"
            type="text"
            id="degree"
            placeholder="e.g. Bachelor of Tech"
            class="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 outline-none"
          />
          <BookOpenIcon class="h-4 w-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
        </div>
      </div>
      <div class="space-y-1.5">
        <label for="field" class="flex items-center space-x-2 text-sm font-semibold text-gray-700">
          <DocumentTextIcon class="h-4 w-4 text-purple-500" />
          <span>Field of Study</span>
        </label>
        <div class="relative">
          <input
            v-model="form.field_of_study"
            type="text"
            id="field"
            placeholder="e.g. Computer Science"
            class="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
          />
          <DocumentTextIcon
            class="h-4 w-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2"
          />
        </div>
      </div>
    </div>

    <!-- University & Board Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div class="space-y-1.5">
        <label for="univ" class="flex items-center space-x-2 text-sm font-semibold text-gray-700">
          <BuildingLibraryIcon class="h-4 w-4 text-indigo-500" />
          <span>University</span>
        </label>
        <input
          v-model="form.university"
          type="text"
          id="univ"
          placeholder="Affiliated University"
          class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
        />
      </div>
      <div class="space-y-1.5">
        <label for="board" class="flex items-center space-x-2 text-sm font-semibold text-gray-700">
          <IdentificationIcon class="h-4 w-4 text-pink-500" />
          <span>Board</span>
        </label>
        <input
          v-model="form.board"
          type="text"
          id="board"
          placeholder="e.g. CBSE / HSC"
          class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 outline-none"
        />
      </div>
    </div>

    <!-- Dates (Vinay's Logic + Aditya's Style) -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div class="space-y-1.5">
        <label class="flex items-center space-x-2 text-sm font-semibold text-gray-700">
          <CalendarIcon class="h-4 w-4 text-orange-500" />
          <span>Start Date</span>
        </label>
        <div class="flex gap-2">
          <select
            v-model.number="startMonth"
            class="w-1/2 p-2 text-sm border border-gray-300 rounded-lg outline-none"
          >
            <option :value="null">Month</option>
            <option v-for="m in monthOptions" :key="m.value" :value="m.value">{{ m.name }}</option>
          </select>
          <input
            v-model.number="startYear"
            type="number"
            placeholder="Year"
            class="w-1/2 p-2 text-sm border border-gray-300 rounded-lg outline-none"
          />
        </div>
      </div>
      <div class="space-y-1.5">
        <label class="flex items-center space-x-2 text-sm font-semibold text-gray-700">
          <CalendarIcon class="h-4 w-4 text-teal-500" />
          <span>End Date</span>
        </label>
        <div class="flex gap-2">
          <select
            v-model.number="endMonth"
            class="w-1/2 p-2 text-sm border border-gray-300 rounded-lg outline-none"
          >
            <option :value="null">Month</option>
            <option v-for="m in monthOptions" :key="m.value" :value="m.value">{{ m.name }}</option>
          </select>
          <input
            v-model.number="endYear"
            type="number"
            placeholder="Year"
            class="w-1/2 p-2 text-sm border border-gray-300 rounded-lg outline-none"
          />
        </div>
      </div>
    </div>

    <!-- Location & Achievements -->
    <div class="space-y-1.5">
      <label for="loc" class="flex items-center space-x-2 text-sm font-semibold text-gray-700">
        <MapPinIcon class="h-4 w-4 text-red-500" />
        <span>Location</span>
      </label>
      <input
        v-model="form.location"
        type="text"
        id="loc"
        placeholder="City, Country"
        class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 outline-none"
      />
    </div>

    <div class="space-y-1.5">
      <label for="ach" class="flex items-center space-x-2 text-sm font-semibold text-gray-700">
        <TrophyIcon class="h-4 w-4 text-yellow-500" />
        <span>Achievements</span>
      </label>
      <textarea
        v-model="form.achievements"
        id="ach"
        rows="2"
        placeholder="Scholarships, Honors, etc."
        class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500 outline-none resize-none"
      />
    </div>

    <!-- Actions (Aditya's Buttons) -->
    <div class="flex justify-end space-x-3 pt-4 border-t">
      <button
        type="button"
        @click="$emit('cancel')"
        class="flex items-center space-x-2 px-4 py-2 text-sm bg-white border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50 transition-all"
      >
        <XMarkIcon class="h-4 w-4" />
        <span>Cancel</span>
      </button>
      <button
        type="submit"
        class="flex items-center space-x-2 px-6 py-2 text-sm bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg font-medium text-white hover:from-blue-700 hover:to-purple-700 transition-all shadow-md"
      >
        <CheckIcon class="h-4 w-4" />
        <span>Save Education</span>
      </button>
    </div>
  </form>
</template>
