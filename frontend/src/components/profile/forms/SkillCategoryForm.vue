<script setup lang="ts">
import { ref } from 'vue'
import type { SkillCategory, Skill } from '@/types'
import { TrashIcon, PlusIcon } from '@heroicons/vue/24/solid'

const props = defineProps<{
  category: SkillCategory
  isSubmitting: boolean
}>()

const emit = defineEmits<{
  (e: 'add-skill', payload: Omit<Skill, 'id'>): void
  (e: 'delete-skill', skillId: number): void
  (e: 'close'): void
}>()

// --- New Skill Form State ---
const newSkillName = ref('')
const newSkillProficiency = ref<Skill['proficiency']>('intermediate')

function handleAddSkill() {
  if (!newSkillName.value.trim()) return

  emit('add-skill', {
    name: newSkillName.value.trim(),
    proficiency: newSkillProficiency.value,
    icon_name: null,
  })

  // Reset form to allow adding another one immediately
  newSkillName.value = ''
  newSkillProficiency.value = 'intermediate'
}

function handleDone() {
  // UX Improvement: If the user typed something but forgot to click "+", save it now.
  if (newSkillName.value.trim()) {
    handleAddSkill()
  }
  // Then close the modal
  emit('close')
}
</script>

<template>
  <div class="space-y-6">
    <!-- List of Existing Skills -->
    <div>
      <h4 class="text-sm font-medium text-gray-700 mb-2">Existing Skills</h4>

      <div v-if="category.skills.length === 0" class="text-gray-500 text-sm italic mb-4">
        No skills in this category yet.
      </div>

      <ul class="space-y-2 max-h-60 overflow-y-auto pr-2">
        <li
          v-for="skill in category.skills"
          :key="skill.id"
          class="flex justify-between items-center bg-gray-50 p-3 rounded-md border border-gray-200"
        >
          <div>
            <span class="font-medium text-gray-900 block">{{ skill.name }}</span>
            <span class="text-xs text-gray-500 capitalize">{{ skill.proficiency }}</span>
          </div>
          <button
            @click="emit('delete-skill', skill.id)"
            class="text-gray-400 hover:text-red-500 transition-colors p-1"
            title="Delete Skill"
          >
            <TrashIcon class="w-5 h-5" />
          </button>
        </li>
      </ul>
    </div>

    <!-- Add New Skill Section -->
    <div class="border-t pt-4">
      <h4 class="text-sm font-medium text-gray-700 mb-3">Add New Skill</h4>
      <div class="flex gap-2 items-start">
        <!-- Name Input -->
        <div class="flex-grow">
          <input
            v-model="newSkillName"
            type="text"
            placeholder="Skill Name (e.g. React)"
            class="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
            @keyup.enter="handleAddSkill"
          />
        </div>

        <!-- Proficiency Select -->
        <div class="w-1/3">
          <select
            v-model="newSkillProficiency"
            class="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
          >
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
            <option value="expert">Expert</option>
          </select>
        </div>

        <!-- Add Button (For adding multiple items) -->
        <button
          @click="handleAddSkill"
          :disabled="!newSkillName.trim() || isSubmitting"
          class="bg-blue-600 text-white p-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
          title="Add this skill and clear form"
        >
          <PlusIcon class="w-5 h-5" />
        </button>
      </div>
    </div>

    <div class="flex justify-end pt-2">
      <!-- Done Button (Saves any pending text, then closes) -->
      <button
        @click="handleDone"
        class="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
      >
        Done
      </button>
    </div>
  </div>
</template>
