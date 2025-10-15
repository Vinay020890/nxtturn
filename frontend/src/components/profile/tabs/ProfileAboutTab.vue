<script setup lang="ts">
import { ref } from 'vue';
import type { UserProfile } from '@/types';
import { PencilIcon } from '@heroicons/vue/24/solid';

// Import our new components and the store
import BaseModal from '@/components/common/BaseModal.vue';
import AboutForm from '@/components/profile/forms/AboutForm.vue';
import { useProfileStore } from '@/stores/profile';

const props = defineProps<{
    profile: UserProfile;
    isOwnProfile: boolean;
}>();

const profileStore = useProfileStore();

// State management for the modal
const isModalOpen = ref(false);

type AboutFormData = {
    bio: string | null;
    location: string | null;
    linkedin_url: string | null;
    portfolio_url: string | null;
};

async function handleSaveChanges(formData: AboutFormData) {
    try {
        // Our existing updateProfile action can be used here.
        // The backend serializer will only update the fields we send.
        await profileStore.updateProfile(props.profile.user.username, formData);
        isModalOpen.value = false; // Close modal on success
    } catch (error) {
        console.error("Failed to update profile:", error);
        alert("Could not update profile. Please try again.");
    }
}
</script>

<template>
    <div class="bg-white rounded-lg shadow-md p-6 relative">
        <!-- Header Section -->
        <div class="flex justify-between items-center mb-4">
            <h3 class="text-xl font-bold text-gray-800">About</h3>
            <!-- This button now opens the modal -->
            <button v-if="isOwnProfile" @click="isModalOpen = true"
                class="text-gray-400 hover:text-blue-500 transition-colors" aria-label="Edit about section">
                <PencilIcon class="h-5 w-5" />
            </button>
        </div>

        <!-- Display Section (Unchanged from your original, but using the correct 'location' field) -->
        <div class="space-y-4 text-gray-700">
            <div>
                <dt class="text-sm font-medium text-gray-500">Bio</dt>
                <dd class="mt-1 whitespace-pre-wrap">{{ profile.bio || 'No bio available.' }}</dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-gray-500">Location</dt>
                <dd class="mt-1">{{ profile.location || 'Not specified' }}</dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-gray-500">Links</dt>
                <dd v-if="profile.linkedin_url || profile.portfolio_url" class="mt-1 space-y-1">
                    <a v-if="profile.linkedin_url" :href="profile.linkedin_url" target="_blank"
                        rel="noopener noreferrer" class="text-blue-500 hover:underline block">
                        LinkedIn Profile
                    </a>
                    <a v-if="profile.portfolio_url" :href="profile.portfolio_url" target="_blank"
                        rel="noopener noreferrer" class="text-blue-500 hover:underline block">
                        Portfolio / Website
                    </a>
                </dd>
                <dd v-else class="mt-1 text-gray-500 italic">No links provided.</dd>
            </div>
        </div>

        <!-- Modal for Editing About Info -->
        <BaseModal :show="isModalOpen" title="Edit About Information" @close="isModalOpen = false">
            <AboutForm :initial-data="profile" @save="handleSaveChanges" @cancel="isModalOpen = false" />
        </BaseModal>
    </div>
</template>