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
            <h3 class="text-xl font-bold text-gray-800">Education</h3>
            <button v-if="isOwnProfile" class="text-gray-500 hover:text-gray-800" aria-label="Edit education section">
                <PencilIcon class="h-5 w-5" />
            </button>
        </div>
        <div class="text-center text-gray-500 py-8">
            <p>Education information has not been added yet.</p>
        </div>
    </div>
</template>