<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { storeToRefs } from 'pinia';
import { getAvatarUrl } from '@/utils/avatars';

const authStore = useAuthStore();
const { currentUser } = storeToRefs(authStore);
</script>

<template>
  <!-- The main grid container now correctly handles the top padding -->
  <div class="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 grid grid-cols-12 gap-8 pt-6">
    
    <!-- Column 1: Left Sidebar. The 'sticky' class has been removed. -->
    <aside class="col-span-3 hidden md:block">
      <div class="space-y-4">
        <div v-if="currentUser" class="bg-white rounded-lg p-4 border border-gray-200 shadow-sm text-center">
          <img 
            :src="getAvatarUrl(currentUser.picture, currentUser.first_name, currentUser.last_name)" 
            alt="Your avatar" 
            class="w-20 h-20 rounded-full object-cover mx-auto mb-2 border-2 border-white shadow-md"
          >
          <h2 class="font-bold text-gray-800">Welcome, {{ currentUser.first_name || currentUser.username }}!</h2>
        </div>
        <div class="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
           <h3 class="px-3 text-xs font-semibold uppercase text-gray-500 tracking-wider">My Feed</h3>
            <ul class="space-y-1 mt-2">
              <li>
                <RouterLink 
                  :to="{ name: 'group-list' }" 
                  class="group flex items-center px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-gray-100" 
                  active-class="bg-blue-50 text-blue-700 font-semibold"
                >
                  My Groups
                </RouterLink>
              </li>
              <li>
                <RouterLink 
                  :to="{ name: 'saved-posts' }" 
                  class="group flex items-center px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-gray-100" 
                  active-class="bg-blue-50 text-blue-700 font-semibold"
                >
                  Saved Posts
                </RouterLink>
              </li>
              <li>
                <a href="#" class="group flex items-center px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-gray-100">
                  My Connections
                </a>
              </li>
              <li>
                <a href="#" class="group flex items-center px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:bg-gray-100">
                  Events
                </a>
              </li>
            </ul>
        </div>
      </div>
    </aside>

    <!-- Column 2: Main Content. -->
    <main class="col-span-6 min-w-0">
      <RouterView />
    </main>

    <!-- Column 3: Right Sidebar. The 'sticky' class has been removed. -->
    <aside class="col-span-3 hidden lg:block">
      <div class="space-y-6">
        <div class="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
          <h3 class="text-sm font-semibold text-gray-800">People You May Know</h3>
          <ul class="mt-3 space-y-4">
            <li v-for="i in 3" :key="i" class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-gray-200 flex-shrink-0"></div>
              <div class="flex-grow">
                <p class="font-semibold text-sm text-gray-800">User Name {{ i }}</p>
                <p class="text-xs text-gray-500">Suggested for you</p>
              </div>
              <button class="text-sm font-medium text-blue-600 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 px-3 py-1 rounded-full">
                Follow
              </button>
            </li>
          </ul>
        </div>
      </div>
    </aside>
  </div>
</template>