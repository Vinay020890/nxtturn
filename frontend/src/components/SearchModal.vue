<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue';
import { useSearchStore } from '@/stores/search';
import { storeToRefs } from 'pinia';
import { RouterLink, useRouter } from 'vue-router';
import { debounce } from 'lodash-es';

const props = defineProps<{
  show: boolean
}>();

const emit = defineEmits(['close']);

const searchStore = useSearchStore();
const { searchResults, isLoading, error } = storeToRefs(searchStore);
const router = useRouter();
const searchInput = ref<HTMLInputElement | null>(null);

const handleSearch = debounce((event: Event) => {
  const query = (event.target as HTMLInputElement).value;
  searchStore.searchUsers(query);
}, 300);

const goToResult = (username: string) => {
  router.push({ name: 'profile', params: { username } });
  closeModal();
};

const closeModal = () => {
  emit('close');
};

// Handle Escape key to close modal
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape') {
    closeModal();
  }
};

watch(() => props.show, (newValue) => {
  if (newValue) {
    // When modal opens, focus the input
    // nextTick is needed to wait for the element to be in the DOM
    import('vue').then(({ nextTick }) => {
      nextTick(() => searchInput.value?.focus());
    });
    document.addEventListener('keydown', handleKeydown);
  } else {
    // When modal closes, clean up
    searchStore.clearSearch();
    document.removeEventListener('keydown', handleKeydown);
  }
});

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown);
});
</script>

<template>
  <div v-if="show" @click="closeModal" class="fixed inset-0 bg-gray-800 bg-opacity-50 z-40 flex justify-center pt-20">
    <div @click.stop class="w-full max-w-2xl bg-white rounded-lg shadow-xl overflow-hidden flex flex-col">
      <!-- Search Input -->
      <div class="p-4 border-b border-gray-200 flex items-center gap-3">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
        <input 
          ref="searchInput"
          type="text"
          @input="handleSearch"
          placeholder="Search for users..."
          class="w-full text-lg placeholder-gray-400 focus:outline-none bg-transparent"
        />
      </div>

      <!-- Search Results Area -->
      <div class="flex-grow overflow-y-auto">
        <div v-if="isLoading" class="p-6 text-center text-gray-500">Searching...</div>
        <div v-else-if="error" class="p-6 text-center text-red-500">{{ error }}</div>
        <ul v-else-if="searchResults.length > 0" class="divide-y divide-gray-200">
          <li v-for="user in searchResults" :key="user.id">
            <a @click="goToResult(user.username)" class="flex items-center gap-4 p-4 hover:bg-blue-50 cursor-pointer">
              <div class="w-10 h-10 bg-gray-300 rounded-full flex-shrink-0"></div>
              <div>
                <p class="font-semibold text-gray-800">{{ user.first_name }} {{ user.last_name }}</p>
                <p class="text-sm text-gray-500">@{{ user.username }}</p>
              </div>
            </a>
          </li>
        </ul>
        <div v-else-if="searchStore.searchQuery" class="p-6 text-center text-gray-500">
          No results for "{{ searchStore.searchQuery }}"
        </div>
        <div v-else class="p-6 text-center text-gray-400">
          Find users by their name or username.
        </div>
      </div>
    </div>
  </div>
</template>