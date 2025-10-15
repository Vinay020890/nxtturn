<script setup lang="ts">
import { ref, computed } from 'vue';
import type { UserProfile, Education } from '@/types';
import { PencilIcon, TrashIcon, PlusIcon } from '@heroicons/vue/24/solid';
import { format } from 'date-fns';

import BaseModal from '@/components/common/BaseModal.vue';
import EducationForm from '@/components/profile/forms/EducationForm.vue';

// 1. IMPORT the profile store
import { useProfileStore } from '@/stores/profile';

const props = defineProps<{
    profile: UserProfile;
    isOwnProfile: boolean;
}>();

// 2. INITIALIZE the store
const profileStore = useProfileStore();

// --- State management for the modal (unchanged) ---
const isModalOpen = ref(false);
const editingEducation = ref<Education | null>(null);

const modalTitle = computed(() => {
    return editingEducation.value ? 'Edit Education' : 'Add Education';
});

// --- Modal control functions (unchanged) ---
function openAddModal() {
    editingEducation.value = null;
    isModalOpen.value = true;
}

function openEditModal(educationItem: Education) {
    editingEducation.value = educationItem;
    isModalOpen.value = true;
}

function closeModal() {
    isModalOpen.value = false;
    editingEducation.value = null;
}

// 3. REPLACE the old data handling functions with these new versions
async function handleSaveEducation(formData: Omit<Education, 'id'>) {
    try {
        const username = props.profile.user.username;
        if (editingEducation.value) {
            // --- UPDATE LOGIC ---
            await profileStore.updateEducation(username, editingEducation.value.id, formData);
        } else {
            // --- CREATE LOGIC ---
            await profileStore.addEducation(username, formData);
        }
        closeModal();
    } catch (error) {
        // TODO: Add a user-friendly error notification (e.g., a toast)
        console.error("Failed to save education:", error);
        alert("Could not save education details. Please try again.");
    }
}

async function handleDeleteEducation(educationId: number) {
    if (confirm("Are you sure you want to delete this education entry?")) {
        try {
            const username = props.profile.user.username;
            await profileStore.deleteEducation(username, educationId);
        } catch (error) {
            // TODO: Add a user-friendly error notification
            console.error("Failed to delete education:", error);
            alert("Could not delete education entry. Please try again.");
        }
    }
}

// --- Helper functions for display (unchanged) ---
function formatDate(dateString: string): string {
    if (!dateString) return '';
    return format(new Date(dateString), 'MMM yyyy');
}

function formatDateRange(startDate: string, endDate: string | null): string {
    const start = formatDate(startDate);
    const end = endDate ? formatDate(endDate) : 'Present';
    return `${start} - ${end}`;
}
</script>

<template>
    <div class="bg-white rounded-lg shadow-md p-6">
        <!-- Header Section -->
        <div class="flex justify-between items-center mb-4 pb-4 border-b">
            <h3 class="text-xl font-bold text-gray-800">Education</h3>
            <!-- This button now correctly calls openAddModal -->
            <button v-if="isOwnProfile" @click="openAddModal"
                class="p-1 rounded-full text-gray-400 hover:bg-gray-100 hover:text-blue-500 transition-colors duration-200"
                aria-label="Add new education">
                <PlusIcon class="h-6 w-6" />
            </button>
        </div>

        <!-- Education List -->
        <div v-if="profile.education && profile.education.length > 0">
            <ul class="space-y-6">
                <li v-for="item in profile.education" :key="item.id" class="flex justify-between items-start">
                    <div>
                        <h4 class="font-bold text-gray-800">{{ item.school }}</h4>
                        <p v-if="item.degree || item.field_of_study" class="text-sm text-gray-600">
                            {{ item.degree }}<span v-if="item.degree && item.field_of_study">, </span>{{
                                item.field_of_study }}
                        </p>
                        <p class="text-xs text-gray-500 mt-1">
                            {{ formatDateRange(item.start_date, item.end_date) }}
                        </p>
                        <p v-if="item.description" class="mt-2 text-sm text-gray-700 whitespace-pre-wrap">
                            {{ item.description }}
                        </p>
                    </div>
                    <div v-if="isOwnProfile" class="flex items-center space-x-2 ml-4 flex-shrink-0">
                        <!-- This button now correctly calls openEditModal -->
                        <button @click="openEditModal(item)"
                            class="text-gray-400 hover:text-blue-500 transition-colors duration-200"
                            aria-label="Edit education">
                            <PencilIcon class="h-5 w-5" />
                        </button>
                        <button @click="handleDeleteEducation(item.id)"
                            class="text-gray-400 hover:text-red-500 transition-colors duration-200"
                            aria-label="Delete education">
                            <TrashIcon class="h-5 w-5" />
                        </button>
                    </div>
                </li>
            </ul>
        </div>

        <!-- Placeholder -->
        <div v-else class="text-center text-gray-500 py-8">
            <p>No education information has been added yet.</p>
        </div>

        <!-- ADD THIS NEW SECTION: Modal for Adding/Editing Education -->
        <BaseModal :show="isModalOpen" :title="modalTitle" @close="closeModal">
            <EducationForm :initial-data="editingEducation" @save="handleSaveEducation" @cancel="closeModal" />
        </BaseModal>
    </div>
</template>