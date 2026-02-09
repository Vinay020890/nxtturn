<script setup lang="ts">
import { computed } from 'vue'
import { PencilIcon, TrashIcon } from '@heroicons/vue/24/solid'
import type { SkillCategory, Skill } from '@/types'

const props = defineProps<{
  category: SkillCategory
  isOwner: boolean
}>()

const emit = defineEmits<{
  (e: 'edit', category: SkillCategory): void
  (e: 'delete', categoryId: number): void
}>()

// --- Theme Mapping ---
// Maps the backend color_theme string to Tailwind CSS classes
const themeClasses = computed(() => {
  switch (props.category.color_theme) {
    case 'blue':
      return 'bg-blue-50 border-blue-200 text-blue-800'
    case 'green':
      return 'bg-green-50 border-green-200 text-green-800'
    case 'purple':
      return 'bg-purple-50 border-purple-200 text-purple-800'
    case 'orange':
      return 'bg-orange-50 border-orange-200 text-orange-800'
    case 'red':
      return 'bg-red-50 border-red-200 text-red-800'
    case 'teal':
      return 'bg-teal-50 border-teal-200 text-teal-800'
    default:
      return 'bg-gray-50 border-gray-200 text-gray-800'
  }
})

const headerClasses = computed(() => {
  switch (props.category.color_theme) {
    case 'blue':
      return 'bg-blue-600 text-white'
    case 'green':
      return 'bg-green-600 text-white'
    case 'purple':
      return 'bg-purple-600 text-white'
    case 'orange':
      return 'bg-orange-600 text-white'
    case 'red':
      return 'bg-red-600 text-white'
    case 'teal':
      return 'bg-teal-600 text-white'
    default:
      return 'bg-gray-700 text-white'
  }
})

// Helper for Proficiency Badge Colors
function getProficiencyColor(level: Skill['proficiency']) {
  switch (level) {
    case 'beginner':
      return 'bg-gray-100 text-gray-600'
    case 'intermediate':
      return 'bg-yellow-100 text-yellow-800'
    case 'advanced':
      return 'bg-blue-100 text-blue-800'
    case 'expert':
      return 'bg-green-100 text-green-800'
    default:
      return 'bg-gray-100 text-gray-600'
  }
}
</script>

<template>
  <div
    class="rounded-lg border overflow-hidden shadow-sm hover:shadow-md transition-shadow bg-white"
  >
    <!-- Colored Header -->
    <div :class="['px-4 py-3 flex justify-between items-center', headerClasses]">
      <h3 class="font-bold text-lg truncate">{{ category.name }}</h3>

      <div v-if="isOwner" class="flex gap-2">
        <button
          @click="emit('edit', category)"
          class="p-1.5 rounded-full hover:bg-white/20 transition-colors text-white"
          title="Edit Category"
        >
          <PencilIcon class="w-4 h-4" />
        </button>
        <button
          @click="emit('delete', category.id)"
          class="p-1.5 rounded-full hover:bg-white/20 transition-colors text-white hover:text-red-200"
          title="Delete Category"
        >
          <TrashIcon class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- Skills List (Body) -->
    <div class="p-4 min-h-[100px]">
      <div
        v-if="category.skills.length === 0"
        class="text-gray-400 italic text-sm text-center py-4"
      >
        No skills added yet.
      </div>

      <div v-else class="space-y-3">
        <!-- Skill Item -->
        <div
          v-for="skill in category.skills"
          :key="skill.id"
          class="flex items-center justify-between p-2 rounded-md hover:bg-gray-50 border border-transparent hover:border-gray-100 transition-colors"
        >
          <div class="flex items-center gap-3">
            <!-- Icon Placeholder (We can add BrandIcon later if needed) -->
            <!-- <div class="w-8 h-8 rounded bg-gray-100 flex items-center justify-center text-xs font-bold text-gray-500">
              {{ skill.name.substring(0, 2).toUpperCase() }}
            </div> -->

            <span class="font-medium text-gray-800">{{ skill.name }}</span>
          </div>

          <!-- Proficiency Badge -->
          <span
            :class="[
              'text-xs px-2 py-1 rounded-full font-medium',
              getProficiencyColor(skill.proficiency),
            ]"
          >
            {{ skill.proficiency.charAt(0).toUpperCase() + skill.proficiency.slice(1) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
