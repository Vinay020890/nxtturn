<script setup lang="ts">
import { HashtagIcon } from '@heroicons/vue/24/outline'

// Curated dummy data relevant to nxtturn
const trends = [
  { id: 1, tag: 'HigherEducation', posts: '1.2k' },
  { id: 2, tag: 'StudyAbroad', posts: '850' },
  { id: 3, tag: 'TechInternships2026', posts: '540' },
  { id: 4, tag: 'CareerGrowth', posts: '320' },
]
</script>

<template>
  <div
    class="bg-gradient-to-br from-white to-gray-50 p-5 rounded-2xl border border-gray-200 shadow-sm hover:shadow-md transition-all"
  >
    <!-- Header -->
    <div class="flex items-center gap-2 mb-4">
      <div class="w-1 h-5 bg-gradient-to-b from-orange-400 to-red-500 rounded-full"></div>
      <h3 class="font-bold text-gray-800 text-sm">Trending Topics</h3>
    </div>

    <!-- Trend List -->
    <div class="space-y-4">
      <div v-for="trend in trends" :key="trend.id" class="group cursor-pointer">
        <div class="flex items-center justify-between">
          <div class="flex flex-col">
            <span
              class="text-sm font-bold text-gray-900 group-hover:text-blue-600 transition-colors"
            >
              #{{ trend.tag }}
            </span>
            <span class="text-[10px] text-gray-400 font-medium uppercase tracking-tight">
              {{ trend.posts }} posts
            </span>
          </div>
          <HashtagIcon class="w-4 h-4 text-gray-300 group-hover:text-blue-400 transition-colors" />
        </div>
      </div>
    </div>

    <!-- See More -->
    <div class="mt-4 pt-3 border-t border-gray-100">
      <button
        class="w-full text-center text-xs font-bold text-blue-600 hover:text-blue-700 transition-colors"
      >
        Explore Trends
      </button>
    </div>
  </div>
</template>
