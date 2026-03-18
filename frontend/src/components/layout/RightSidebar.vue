<script setup lang="ts">
import { useRoute } from 'vue-router'
import { computed } from 'vue'

// --- WIDGET IMPORTS ---
import SuggestedUsersWidget from '@/components/widgets/SuggestedUsersWidget.vue'
import ProfileCompletionWidget from '@/components/widgets/ProfileCompletionWidget.vue'

const route = useRoute()
const isNetworkPage = computed(() => route.name === 'network')

// Dummy data for other cards can remain for now
interface Institute {
  id: number
  name: string
  logo: string
}

const institutes: Institute[] = [
  { id: 1, name: 'IIT Bombay', logo: 'https://placehold.co/40x40/E2E8F0/475569?text=IITB' },
  { id: 2, name: 'IIM Ahmedabad', logo: 'https://placehold.co/40x40/E2E8F0/475569?text=IIMA' },
  { id: 3, name: 'NIT Trichy', logo: 'https://placehold.co/40x40/E2E8F0/475569?text=NITT' },
]
</script>

<template>
  <div class="relative left-[-12px] w-full">
    <div class="flex justify-start">
      <div class="space-y-6 w-full">
        <div
          class="max-h-[calc(100vh-theme(spacing.24))] overflow-y-auto custom-scrollbar space-y-4 pr-2"
        >
          <!-- ========================================== -->
          <!-- OPTION A: CONTENT FOR NETWORK PAGE ONLY  -->
          <!-- ========================================== -->
          <template v-if="isNetworkPage">
            <!-- 1. Network Insights Card -->
            <div
              class="bg-gradient-to-br from-white to-gray-50 p-5 rounded-2xl border border-gray-200 shadow-md"
            >
              <div class="flex items-center gap-2 mb-4">
                <div
                  class="w-1 h-5 bg-gradient-to-b from-blue-500 to-purple-500 rounded-full"
                ></div>
                <h3 class="font-bold text-gray-800 text-lg">Network Insights</h3>
              </div>
              <div class="p-3 bg-blue-50/50 rounded-xl border border-blue-100">
                <p class="text-xs text-blue-800 font-medium">
                  <strong>Tip:</strong> Users with a completed profile get 3x more connection
                  requests.
                </p>
              </div>
            </div>

            <!-- 2. Also show suggestions on the network page -->
            <SuggestedUsersWidget />
          </template>

          <!-- ========================================== -->
          <!-- OPTION B: CONTENT FOR FEED AND OTHER PAGES -->
          <!-- ========================================== -->
          <template v-else>
            <!-- 1. Profile Strength (Shows if < 100%) -->
            <ProfileCompletionWidget />

            <!-- 2. Our dynamic suggestions widget -->
            <SuggestedUsersWidget />

            <!-- 3. Featured Institutes Card -->
            <div
              class="bg-gradient-to-br from-white to-gray-50 p-5 rounded-2xl border border-gray-200 shadow-md hover:shadow-lg transition-all duration-300"
            >
              <div class="flex items-center gap-2 mb-4">
                <div
                  class="w-1 h-5 bg-gradient-to-b from-amber-500 to-orange-500 rounded-full"
                ></div>
                <h3 class="font-bold text-gray-800 text-lg">Featured Institutes</h3>
              </div>
              <ul class="space-y-3">
                <li
                  v-for="inst in institutes"
                  :key="inst.id"
                  class="flex items-center p-3 hover:bg-gray-50 rounded-xl transition-colors duration-200"
                >
                  <div class="flex-shrink-0 mr-3">
                    <img
                      :src="inst.logo"
                      alt=""
                      class="h-11 w-11 rounded-xl ring-2 ring-white shadow-sm"
                    />
                  </div>
                  <div class="flex-1 min-w-0 mr-4">
                    <p class="font-semibold text-gray-800 text-sm">{{ inst.name }}</p>
                    <p class="text-xs text-gray-600">Premier Institute</p>
                  </div>
                  <button
                    class="flex-shrink-0 text-sm font-medium bg-gray-800 text-white px-2 py-1.5 rounded-xl hover:bg-gray-900 transition-all"
                  >
                    Follow
                  </button>
                </li>
              </ul>
            </div>

            <!-- 4. Sponsored Card -->
            <div
              class="bg-gradient-to-br from-white to-gray-50 p-5 rounded-2xl border border-gray-200 shadow-md hover:shadow-lg group"
            >
              <div class="flex justify-between items-center mb-3">
                <h3 class="font-bold text-gray-800 text-lg">Sponsored</h3>
                <span
                  class="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-1 rounded-lg"
                  >Ad</span
                >
              </div>
              <p class="text-sm text-gray-600">Placeholder for sponsored ad content.</p>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: linear-gradient(to bottom, #3b82f6, #8b5cf6);
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(to bottom, #2563eb, #7c3aed);
}
</style>
