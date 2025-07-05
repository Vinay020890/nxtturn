<script setup lang="ts">
import { ref, watch } from 'vue';

const props = defineProps<{
  isOpen: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'submit', payload: { reason: string; details: string }): void;
}>();

const selectedReason = ref('');
const reportDetails = ref('');
const error = ref('');

const reasonOptions = [
  { value: 'SPAM', label: 'Spam or Misleading' },
  { value: 'HARASSMENT', label: 'Harassment or Bullying' },
  { value: 'HATE_SPEECH', label: 'Hate Speech' },
  { value: 'VIOLENCE', label: 'Violence or Graphic Content' },
  { value: 'OTHER', label: 'Other' },
];

const handleSubmit = () => {
  error.value = '';
  if (!selectedReason.value) {
    error.value = 'Please select a reason for the report.';
    return;
  }
  if (selectedReason.value === 'OTHER' && !reportDetails.value.trim()) {
    error.value = "Details are required when selecting 'Other'.";
    return;
  }
  emit('submit', { reason: selectedReason.value, details: reportDetails.value });
};

const handleClose = () => {
  emit('close');
};

// Reset form when the modal is closed
watch(() => props.isOpen, (newVal) => {
  if (!newVal) {
    selectedReason.value = '';
    reportDetails.value = '';
    error.value = '';
  }
});
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 bg-black bg-opacity-50 z-40 flex items-center justify-center p-4" @click.self="handleClose">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-md" @click.stop>
      <div class="p-6">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-xl font-bold text-gray-800">Report Content</h2>
          <button @click="handleClose" class="text-gray-400 hover:text-gray-600">×</button>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Reason for reporting:</label>
            <select v-model="selectedReason" class="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500">
              <option disabled value="">Please select a reason</option>
              <option v-for="option in reasonOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>

          <div v-if="selectedReason === 'OTHER'">
            <label for="report-details" class="block text-sm font-medium text-gray-700">Details:</label>
            <textarea
              id="report-details"
              v-model="reportDetails"
              rows="3"
              class="mt-1 w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              placeholder="Please provide specific details about your report."
            ></textarea>
          </div>

          <div v-if="error" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-3 text-sm">
            <p>{{ error }}</p>
          </div>

          <div class="pt-4 flex justify-end gap-3">
            <button type="button" @click="handleClose" class="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300">
              Cancel
            </button>
            <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
              Submit Report
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>