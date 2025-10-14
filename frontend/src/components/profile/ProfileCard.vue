<script setup lang="ts">
import { ref, watch } from 'vue';
import { getAvatarUrl } from '@/utils/avatars';
import type { UserProfile } from '@/stores/profile';
import { useProfileStore } from '@/stores/profile';
import ProfileActions from '@/components/ProfileActions.vue';
import { PencilIcon } from '@heroicons/vue/24/solid';

const props = defineProps<{
    profile: UserProfile;
    isOwnProfile: boolean;
}>();

const profileStore = useProfileStore();

// --- State for Bio Editing ---
const isEditingBio = ref(false);
const editableBio = ref(props.profile.bio || '');
const isSaving = ref(false);
const editError = ref<string | null>(null);

// --- State for Picture Management (Restored) ---
const selectedFile = ref<File | null>(null);
const picturePreviewUrl = ref<string | null>(null);
const isUploadingPicture = ref(false);
const isRemovingPicture = ref(false);
const showPictureOptions = ref(false);
const pictureOptionsRef = ref<HTMLDivElement | null>(null);

function toggleEditBio() {
    isEditingBio.value = !isEditingBio.value;
    editableBio.value = props.profile.bio || '';
    editError.value = null;
}

async function handleBioUpdate() {
    if (!props.isOwnProfile) return;
    isSaving.value = true;
    editError.value = null;
    try {
        await profileStore.updateProfile(props.profile.user.username, { bio: editableBio.value });
        isEditingBio.value = false;
    } catch (error: any) {
        editError.value = error.message;
    } finally {
        isSaving.value = false;
    }
}

// --- Picture Management Functions (Restored) ---
function handleFileChange(event: Event) {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (file) {
        selectedFile.value = file;
        picturePreviewUrl.value = URL.createObjectURL(file);
        showPictureOptions.value = false;
        uploadProfilePicture();
    }
}

async function uploadProfilePicture() {
    if (!selectedFile.value) return;
    isUploadingPicture.value = true;
    try {
        await profileStore.updateProfilePicture(props.profile.user.username, selectedFile.value);
        selectedFile.value = null;
        picturePreviewUrl.value = null; // Let the store's reactive state take over
    } catch (error: any) {
        alert(error.message || "Failed to upload picture.");
        selectedFile.value = null;
        picturePreviewUrl.value = null;
    } finally {
        isUploadingPicture.value = false;
    }
}

async function handleRemovePicture() {
    if (window.confirm("Are you sure you want to remove your profile picture?")) {
        isRemovingPicture.value = true;
        try {
            await profileStore.removeProfilePicture(props.profile.user.username);
        } catch (error) {
            alert("Failed to remove profile picture.");
        } finally {
            isRemovingPicture.value = false;
        }
    }
}

const closeOnClickOutside = (event: MouseEvent) => {
    if (pictureOptionsRef.value && !pictureOptionsRef.value.contains(event.target as Node)) {
        showPictureOptions.value = false;
    }
};

watch(showPictureOptions, (isOpen) => {
    if (isOpen) document.addEventListener('click', closeOnClickOutside);
    else document.removeEventListener('click', closeOnClickOutside);
});
</script>

<template>
    <div class="bg-white rounded-lg shadow-md p-6">
        <div class="flex flex-col items-center text-center">
            <!-- Picture Section -->
            <div data-cy="profile-picture-container" class="relative w-32 h-32 mb-4 group" ref="pictureOptionsRef">
                <img data-cy="profile-picture-img"
                    :src="picturePreviewUrl || getAvatarUrl(profile.picture, profile.user.first_name, profile.user.last_name)"
                    alt="Profile Picture"
                    class="w-full h-full rounded-full object-cover border-4 border-white shadow-lg bg-gray-200">

                <div v-if="isOwnProfile" @click.stop="showPictureOptions = !showPictureOptions"
                    class="absolute inset-0 rounded-full bg-black bg-opacity-0 group-hover:bg-opacity-40 flex items-center justify-center cursor-pointer transition-opacity duration-300">
                    <svg xmlns="http://www.w3.org/2000/svg"
                        class="h-8 w-8 text-white opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                        fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round"
                            d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                </div>

                <div v-if="showPictureOptions"
                    class="origin-top-left absolute left-1/2 -translate-x-1/2 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-10">
                    <ul class="py-1">
                        <li>
                            <label for="picture-upload"
                                class="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 cursor-pointer">
                                Upload a photo
                            </label>
                            <input id="picture-upload" type="file" @change="handleFileChange" accept="image/*"
                                class="hidden">
                        </li>
                        <li v-if="profile.picture">
                            <button data-cy="remove-picture-button" @click.stop="handleRemovePicture"
                                :disabled="isRemovingPicture"
                                class="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 disabled:opacity-50">
                                Remove photo
                            </button>
                        </li>
                    </ul>
                </div>
            </div>

            <!-- Name, Username, Headline -->
            <h1 class="text-2xl font-bold text-gray-800">{{ profile.user.first_name }} {{ profile.user.last_name }}</h1>
            <p class="text-md text-gray-500">@{{ profile.user.username }}</p>
            <p v-if="profile.headline" class="mt-2 text-md text-gray-700 font-semibold">{{ profile.headline }}</p>

            <!-- Bio Section -->
            <div class="mt-4 text-sm text-gray-600 w-full group relative">
                <div v-if="!isEditingBio">
                    <p data-cy="profile-bio-display" v-if="profile.bio">{{ profile.bio }}</p>
                    <p data-cy="profile-bio-display" v-else class="text-gray-400 italic">No bio available.</p>
                    <!-- FIX: The comment was moved outside the button tag -->
                    <button v-if="isOwnProfile" @click="toggleEditBio" data-cy="edit-bio-button"
                        class="absolute -top-2 -right-2 p-1 rounded-full bg-gray-100 text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity focus:opacity-100 hover:bg-gray-200"
                        aria-label="Edit bio">
                        <PencilIcon class="h-4 w-4" />
                    </button>
                </div>
                <div v-else>
                    <!-- In-place Bio Editing Form -->
                    <form @submit.prevent="handleBioUpdate">
                        <textarea v-model="editableBio" data-cy="bio-textarea" rows="4"
                            class="block w-full rounded-md border-gray-300 shadow-sm sm:text-sm"></textarea>
                        <div class="mt-2 flex justify-end gap-2">
                            <button @click="toggleEditBio" type="button"
                                class="text-sm font-medium text-gray-700">Cancel</button>
                            <!-- FIX: The comment was moved outside the button tag -->
                            <button type="submit" data-cy="save-bio-button" :disabled="isSaving"
                                class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-1 px-3 rounded-full text-sm disabled:bg-blue-300">
                                {{ isSaving ? 'Saving...' : 'Save' }}
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            <!-- Action Buttons -->
            <div class="w-full mt-6">
                <ProfileActions v-if="!isOwnProfile" />
            </div>
        </div>
    </div>
</template>