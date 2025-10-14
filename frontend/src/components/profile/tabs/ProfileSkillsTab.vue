<script setup lang="ts">
import type { UserProfile } from '@/stores/profile';
import { PencilIcon } from '@heroicons/vue/24/solid';

defineProps<{
    profile: UserProfile;
    isOwnProfile: boolean;
}>();
</script>

<template>
    <div class="bg-white rounded-lg shadow-md p-6 relative">
        <div class="flex justify-between items-center mb-4">
            <h3 class="text-xl font-bold text-gray-800">Skills</h3>
            <button v-if="isOwnProfile" class="text-gray-500 hover:text-gray-800" aria-label="Edit skills section">
                <PencilIcon class="h-5 w-5" />
            </button>
        </div>
        <div v-if="profile.skills && profile.skills.length">
            <ul class="flex flex-wrap gap-2">
                <li v-for="skill in profile.skills" :key="skill"
                    class="bg-gray-200 text-gray-800 text-sm font-medium px-3 py-1 rounded-full">
                    {{ skill }}
                </li>
            </ul>
        </div>
        <div v-else class="text-center text-gray-500 py-8">
            <p>No skills have been added yet.</p>
        </div>
    </div>
</template>