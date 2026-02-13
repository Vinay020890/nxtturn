<script setup lang="ts">
import { RouterView } from 'vue-router'
import TopNavBar from '@/components/layout/TopNavBar.vue'
import CommunitySidebar from '@/components/layout/CommunitySidebar.vue'
import RightSidebar from '@/components/layout/RightSidebar.vue'
import MobileBottomNav from '@/components/layout/MobileBottomNav.vue'
</script>

<template>
  <div class="bg-gray-50 min-h-screen">
    <TopNavBar />
    <main class="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-20 pb-safe-mobile lg:pb-0">
      <div class="grid grid-cols-12 gap-6 items-start">
        <aside class="col-span-3 hidden lg:block sticky top-20">
          <CommunitySidebar />
        </aside>
        <div class="col-span-12 lg:col-span-6 min-w-0">
          <RouterView :key="$route.fullPath" />
        </div>
        <aside class="col-span-3 hidden lg:block sticky top-20">
          <RightSidebar />
        </aside>
      </div>
    </main>

    <!-- Mobile Bottom Navigation (only on mobile) -->
    <MobileBottomNav />
  </div>
</template>

<style scoped>
/* Reduced padding - thinner bottom nav */
.pb-safe-mobile {
  padding-bottom: 3rem; /* Reduced from 5rem */
}

@media (max-width: 768px) {
  .pb-safe-mobile {
    padding-bottom: calc(3rem + env(safe-area-inset-bottom, 0));
  }
}
</style>
