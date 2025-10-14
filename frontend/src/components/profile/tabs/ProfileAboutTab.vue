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
            <h3 class="text-xl font-bold text-gray-800">About</h3>
            <button v-if="isOwnProfile" class="text-gray-500 hover:text-gray-800" aria-label="Edit about section">
                <PencilIcon class="h-5 w-5" />
            </button>
        </div>

        <div class="space-y-4 text-gray-700">
            <div>
                <dt class="text-sm font-medium text-gray-500">Display Name</dt>
                <dd class="mt-1">{{ profile.user.first_name }} {{ profile.user.last_name }}</dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-gray-500">Location</dt>
                <dd class="mt-1">{{ profile.location_city || 'Not specified' }}</dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-gray-500">Links</dt>
                <dd class="mt-1">
                    <a v-if="profile.linkedin_url" :href="profile.linkedin_url" target="_blank"
                        rel="noopener noreferrer" class="text-blue-500 hover:underline block">
                        LinkedIn Profile
                    </a>
                    <a v-if="profile.portfolio_url" :href="profile.portfolio_url" target="_blank"
                        rel="noopener noreferrer" class="text-blue-500 hover:underline block">
                        Portfolio / Website
                    </a>
                </dd>
            </div>
        </div>
    </div>
</template>