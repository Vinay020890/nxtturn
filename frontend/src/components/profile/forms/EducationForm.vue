<script setup lang="ts">
import { ref, watch } from 'vue';
import type { Education } from '@/types';

// Omit 'id' and 'user' for the form data, as the backend handles those.
type EducationFormData = Omit<Education, 'id'>;

const props = defineProps<{
    initialData?: Education | null;
}>();

const emit = defineEmits(['save', 'cancel']);

const form = ref<EducationFormData>({
    school: '',
    degree: '',
    field_of_study: '',
    start_date: '',
    end_date: null,
    description: ''
});

// Watch for changes in initialData to populate the form for editing.
watch(() => props.initialData, (newData) => {
    if (newData) {
        form.value = { ...newData };
    } else {
        // Reset form for adding a new entry
        form.value = {
            school: '',
            degree: '',
            field_of_study: '',
            start_date: '',
            end_date: null,
            description: ''
        };
    }
}, { immediate: true });

function handleSubmit() {
    // TODO: Add form validation here before emitting.
    emit('save', form.value);
}
</script>

<template>
    <form @submit.prevent="handleSubmit">
        <div class="space-y-4">
            <!-- School -->
            <div>
                <label for="school" class="block text-sm font-medium text-gray-700">School</label>
                <input v-model="form.school" type="text" id="school" required
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500" />
            </div>

            <!-- Degree -->
            <div>
                <label for="degree" class="block text-sm font-medium text-gray-700">Degree</label>
                <input v-model="form.degree" type="text" id="degree"
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500" />
            </div>

            <!-- Field of Study -->
            <div>
                <label for="field_of_study" class="block text-sm font-medium text-gray-700">Field of Study</label>
                <input v-model="form.field_of_study" type="text" id="field_of_study"
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500" />
            </div>

            <!-- Date Inputs -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label for="start_date" class="block text-sm font-medium text-gray-700">Start Date</label>
                    <input v-model="form.start_date" type="date" id="start_date" required
                        class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500" />
                </div>
                <div>
                    <label for="end_date" class="block text-sm font-medium text-gray-700">End Date (or expected)</label>
                    <input v-model="form.end_date" type="date" id="end_date"
                        class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500" />
                </div>
            </div>

            <!-- Description -->
            <div>
                <label for="description" class="block text-sm font-medium text-gray-700">Description</label>
                <textarea v-model="form.description" id="description" rows="4"
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"></textarea>
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
                Save
            </button>
        </div>
    </form>
</template>