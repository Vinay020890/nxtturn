<script setup lang="ts">
import { ref, watch } from 'vue';
import type { UserProfile } from '@/types';

// Define the shape of the data our form will manage and emit.
type AboutFormData = {
    bio: string | null;
    location: string | null;
    linkedin_url: string | null;
    portfolio_url: string | null;
};

const props = defineProps<{
    // The form is pre-filled with the current profile data.
    initialData: UserProfile;
}>();

const emit = defineEmits(['save', 'cancel']);

const form = ref<AboutFormData>({
    bio: '',
    location: '',
    linkedin_url: '',
    portfolio_url: ''
});

// When the component loads or the initialData prop changes, populate the form.
watch(() => props.initialData, (newData) => {
    if (newData) {
        form.value = {
            bio: newData.bio || '',
            location: newData.location || '',
            linkedin_url: newData.linkedin_url || '',
            portfolio_url: newData.portfolio_url || ''
        };
    }
}, { immediate: true });

function handleSubmit() {
    emit('save', form.value);
}
</script>

<template>
    <form @submit.prevent="handleSubmit">
        <div class="space-y-4">
            <!-- Bio -->
            <div>
                <label for="bio" class="block text-sm font-medium text-gray-700">Bio</label>
                <textarea v-model="form.bio" id="bio" rows="4" placeholder="Tell us a little about yourself"
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"></textarea>
            </div>

            <!-- Location -->
            <div>
                <label for="location" class="block text-sm font-medium text-gray-700">Location</label>
                <input v-model="form.location" type="text" id="location" placeholder="e.g., Mumbai, India"
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500" />
            </div>

            <!-- LinkedIn URL -->
            <div>
                <label for="linkedin_url" class="block text-sm font-medium text-gray-700">LinkedIn Profile URL</label>
                <input v-model="form.linkedin_url" type="url" id="linkedin_url"
                    placeholder="https://www.linkedin.com/in/your-profile"
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500" />
            </div>

            <!-- Portfolio URL -->
            <div>
                <label for="portfolio_url" class="block text-sm font-medium text-gray-700">Portfolio or Website
                    URL</label>
                <input v-model="form.portfolio_url" type="url" id="portfolio_url"
                    placeholder="https://your-portfolio.com"
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500" />
            </div>
        </div>

        <!-- Form Actions -->
        <div class="mt-6 flex justify-end space-x-3">
            <button type="button" @click="$emit('cancel')"
                class="px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50">
                Cancel
            </button>
            <button type="submit"
                class="px-4 py-2 bg-blue-600 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-blue-700">
                Save Changes
            </button>
        </div>
    </form>
</template>