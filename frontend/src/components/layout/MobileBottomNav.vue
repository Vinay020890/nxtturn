<template>
  <div
    class="fixed bottom-0 left-0 right-0 bg-white/95 border-t border-gray-200 z-50 lg:hidden shadow-md"
    style="backdrop-filter: blur(10px)"
  >
    <div class="max-w-4xl mx-auto px-3 py-1.5">
      <nav class="flex justify-between items-center">
        <RouterLink
          to="/"
          @click="handleHomeFeedClick"
          data-cy="mobile-home-link"
          class="flex flex-col items-center justify-center p-1.5 rounded-lg transition-colors duration-200 flex-1"
          :class="
            isHomeRouteActive
              ? 'text-orange-600 bg-orange-50'
              : 'text-gray-600 hover:text-orange-500 hover:bg-gray-50'
          "
        >
          <HomeIcon class="h-5 w-5" />
          <span class="text-xs font-medium mt-0.5">Home</span>
        </RouterLink>

        <RouterLink
          to="/groups"
          @click="handleMyGroupsClick"
          data-cy="mobile-groups-link"
          class="flex flex-col items-center justify-center p-1.5 rounded-lg transition-colors duration-200 flex-1"
          :class="
            isGroupsRouteActive
              ? 'text-blue-600 bg-blue-50'
              : 'text-gray-600 hover:text-blue-500 hover:bg-gray-50'
          "
        >
          <UserGroupIcon class="h-5 w-5" />
          <span class="text-xs font-medium mt-0.5">Groups</span>
        </RouterLink>

        <RouterLink
          to="/saved-posts"
          @click="handleSavedPostsClick"
          data-cy="mobile-saved-link"
          class="flex flex-col items-center justify-center p-1.5 rounded-lg transition-colors duration-200 flex-1"
          :class="
            isSavedPostsRouteActive
              ? 'text-green-600 bg-green-50'
              : 'text-gray-600 hover:text-green-500 hover:bg-gray-50'
          "
        >
          <BookmarkIcon class="h-5 w-5" />
          <span class="text-xs font-medium mt-0.5">Saved</span>
        </RouterLink>
      </nav>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink, useRoute } from 'vue-router'
import { HomeIcon, UserGroupIcon, BookmarkIcon } from '@heroicons/vue/24/solid'
import { computed } from 'vue'
import eventBus from '@/services/eventBus'

const route = useRoute()

const isHomeRouteActive = computed(() => {
  return route.path === '/'
})

const isGroupsRouteActive = computed(() => {
  return route.path.startsWith('/groups')
})

const isSavedPostsRouteActive = computed(() => {
  return route.name === 'saved-posts'
})

function handleHomeFeedClick(event: MouseEvent) {
  if (route.path === '/') {
    event.preventDefault()
    eventBus.emit('scroll-to-top')
  }
}

function handleMyGroupsClick(event: MouseEvent) {
  if (route.name === 'group-list') {
    event.preventDefault()
    eventBus.emit('scroll-groups-to-top')
  }
}

function handleSavedPostsClick(event: MouseEvent) {
  if (route.name === 'saved-posts') {
    event.preventDefault()
    eventBus.emit('scroll-saved-posts-to-top')
  }
}
</script>
