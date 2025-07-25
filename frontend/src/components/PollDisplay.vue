<script setup lang="ts">
import { computed, ref } from 'vue';
import type { Poll, PollOption } from '@/stores/feed';
import { useFeedStore } from '@/stores/feed';
import { useAuthStore } from '@/stores/auth';

const props = defineProps<{ poll: Poll }>();

const feedStore = useFeedStore();
const authStore = useAuthStore();
const isVoting = ref(false);

const hasVoted = computed(() => props.poll.user_vote !== null);
const optionLetters = ['A', 'B', 'C', 'D', 'E'];

function getPercentage(option: PollOption): number {
  if (props.poll.total_votes === 0) return 0;
  return Math.round((option.vote_count / props.poll.total_votes) * 100);
}

async function handleVote(optionId: number) {
  if (!authStore.isAuthenticated) {
    alert("Please log in to vote.");
    return;
  }
  // The only guard is if an action is already in progress.
  if (isVoting.value) return;

  isVoting.value = true;
  try {
    // The store now handles all the complex logic of changing vs. retracting.
    await feedStore.castVote(props.poll.id, optionId);
  } finally {
    isVoting.value = false;
  }
}
</script>

<template>
  <div class="p-4">
    <p class="font-bold text-gray-800 mb-4">{{ poll.question }}</p>

    <!-- 
      This is a much cleaner structure. We have ONE loop, and each option is a button.
      The button's appearance changes based on whether the user has voted or not.
    -->
    <div class="space-y-3">
      <div v-for="(option, index) in poll.options" :key="option.id">
        <button 
          @click="handleVote(option.id)" 
          :disabled="isVoting" 
          class="w-full text-left border rounded-lg p-3 text-sm transition-all duration-150 relative overflow-hidden flex items-center gap-3 disabled:opacity-70 disabled:cursor-wait"
          :class="{
            'border-gray-300 bg-white hover:border-blue-500 hover:bg-blue-50 hover:shadow-sm': !hasVoted,
            'border-gray-300': hasVoted,
            'border-blue-500 ring-2 ring-blue-200': hasVoted && poll.user_vote === option.id
          }"
        >
          <!-- Progress Bar (only visible if user has voted) -->
          <div 
            v-if="hasVoted"
            class="absolute top-0 left-0 h-full bg-blue-100 transition-all duration-500" 
            :style="{ width: getPercentage(option) + '%' }"
          ></div>
          
          <!-- Content Layer (always visible) -->
          <div class="relative flex-shrink-0 w-6 h-6 flex items-center justify-center bg-gray-200 text-gray-600 text-xs font-bold rounded-full">
            {{ optionLetters[index] }}
          </div>
          <span class="relative flex-grow font-medium text-gray-800">{{ option.text }}</span>
          
          <!-- Results (Percentage and Checkmark) (only visible if user has voted) -->
          <div v-if="hasVoted" class="relative flex items-center gap-3">
            <span class="font-semibold text-gray-600">{{ getPercentage(option) }}%</span>
            <div class="w-5 h-5">
              <svg v-if="poll.user_vote === option.id" class="text-blue-600" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>
            </div>
          </div>
        </button>
      </div>
    </div>

    <div class="text-xs text-gray-500 mt-3 text-right">{{ poll.total_votes }} vote<span v-if="poll.total_votes !== 1">s</span></div>
  </div>
</template>