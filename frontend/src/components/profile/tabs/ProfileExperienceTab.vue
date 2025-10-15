<script setup lang="ts">
import type { UserProfile, Experience } from '@/types';
import { PencilIcon, TrashIcon, PlusIcon } from '@heroicons/vue/24/solid';
import { format } from 'date-fns';

defineProps<{
    profile: UserProfile;
    isOwnProfile: boolean;
}>();

/**
 * Formats a date string (YYYY-MM-DD) into a more readable format (e.g., 'Sep 2023').
 */
function formatDate(dateString: string): string {
    return format(new Date(dateString), 'MMM yyyy');
}

/**
 * Creates a formatted date range string. Handles cases where the end date is null or is_current is true.
 */
function formatDateRange(startDate: string, endDate: string | null, isCurrent: boolean): string {
    const start = formatDate(startDate);
    const end = isCurrent ? 'Present' : (endDate ? formatDate(endDate) : 'Present');
    return `${start} - ${end}`;
}

// --- Placeholder functions for future CRUD operations ---
function handleAddExperience() {
    // TODO: This will open a modal to add a new experience entry.
    console.log('Open modal to add experience');
}

function handleEditExperience(experienceItem: Experience) {
    // TODO: This will open a modal pre-filled with the experienceItem data to edit.
    console.log('Open modal to edit experience item:', experienceItem);
}

function handleDeleteExperience(experienceId: number) {
    // TODO: This will show a confirmation and then make an API call to delete.
    console.log('Trigger delete for experience item ID:', experienceId);
}
</script>

<template>
    <div class="bg-white rounded-lg shadow-md p-6">
        <!-- Header Section with "Add" button for owner -->
        <div class="flex justify-between items-center mb-4 pb-4 border-b">
            <h3 class="text-xl font-bold text-gray-800">Experience</h3>
            <button v-if="isOwnProfile" @click="handleAddExperience"
                class="p-1 rounded-full text-gray-400 hover:bg-gray-100 hover:text-blue-500 transition-colors duration-200"
                aria-label="Add new experience">
                <PlusIcon class="h-6 w-6" />
            </button>
        </div>

        <!-- Conditional Content: Show list or placeholder -->
        <div v-if="profile.experience && profile.experience.length > 0">
            <ul class="space-y-6">
                <li v-for="item in profile.experience" :key="item.id" class="flex justify-between items-start">
                    <!-- Experience Details -->
                    <div class="flex-grow">
                        <h4 class="font-bold text-gray-800">{{ item.title }}</h4>
                        <p class="text-sm text-gray-600">
                            {{ item.company }}<span v-if="item.company && item.location"> &middot; </span>{{
                                item.location }}
                        </p>
                        <p class="text-xs text-gray-500 mt-1">
                            {{ formatDateRange(item.start_date, item.end_date, item.is_current) }}
                        </p>
                        <p v-if="item.description" class="mt-2 text-sm text-gray-700 whitespace-pre-wrap">
                            {{ item.description }}
                        </p>
                    </div>

                    <!-- Action Buttons for owner -->
                    <div v-if="isOwnProfile" class="flex items-center space-x-2 ml-4 flex-shrink-0">
                        <button @click="handleEditExperience(item)"
                            class="text-gray-400 hover:text-blue-500 transition-colors duration-200"
                            aria-label="Edit experience">
                            <PencilIcon class="h-5 w-5" />
                        </button>
                        <button @click="handleDeleteExperience(item.id)"
                            class="text-gray-400 hover:text-red-500 transition-colors duration-200"
                            aria-label="Delete experience">
                            <TrashIcon class="h-5 w-5" />
                        </button>
                    </div>
                </li>
            </ul>
        </div>

        <!-- Placeholder when no experience entries exist -->
        <div v-else class="text-center text-gray-500 py-8">
            <p>No experience information has been added yet.</p>
        </div>
    </div>
</template>