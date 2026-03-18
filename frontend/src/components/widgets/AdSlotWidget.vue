<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { InformationCircleIcon } from '@heroicons/vue/24/outline'

// 1. Detect Environment
const isProd = import.meta.env.PROD
const isLoading = ref(true)
const currentAd = ref<any>(null)

// --- MOCK DATA (For Development) ---
const mockAds = [
  {
    provider: 'Skillshare',
    title: 'Start Your Free Trial',
    image: 'https://picsum.photos/seed/skill/300/150',
    url: 'https://skillshare.com',
  },
  {
    provider: 'Coursera',
    title: 'Get a Degree',
    image: 'https://picsum.photos/seed/edu/300/150',
    url: 'https://coursera.org',
  },
]

// --- NEW: Helper function to handle clicks (Fixes the 'window' error) ---
const handleAdClick = () => {
  if (currentAd.value && currentAd.value.url) {
    window.open(currentAd.value.url, '_blank')
  }
}

onMounted(() => {
  if (isProd) {
    // 2. PRODUCTION LOGIC: Initialize Google AdSense
    try {
      // @ts-ignore
      const adsbygoogle = (window as any).adsbygoogle || []
      adsbygoogle.push({})
      isLoading.value = false
    } catch (e) {
      console.error('AdSense failed to load', e)
    }
  } else {
    // 3. DEVELOPMENT LOGIC: Show Mock Ad
    setTimeout(() => {
      currentAd.value = mockAds[Math.floor(Math.random() * mockAds.length)]
      isLoading.value = false
    }, 1000)
  }
})
</script>

<template>
  <div class="bg-gray-50 p-4 rounded-2xl border border-gray-100 flex flex-col min-h-[180px]">
    <div class="flex items-center justify-between mb-3">
      <span class="text-[9px] font-black text-gray-400 uppercase tracking-widest">
        {{ isProd ? 'Advertisement' : 'Dev-Ad Simulator' }}
      </span>
      <InformationCircleIcon class="w-3 h-3 text-gray-300 cursor-help" />
    </div>

    <!-- LOADING STATE -->
    <div v-if="isLoading" class="flex-1 flex items-center justify-center">
      <div class="w-full h-24 bg-gray-200 rounded-xl animate-pulse"></div>
    </div>

    <!-- PRODUCTION: REAL GOOGLE ADSENSE CODE -->
    <template v-if="isProd">
      <ins
        class="adsbygoogle"
        style="display: block"
        data-ad-client="ca-pub-XXXXXXXXXXXXXXXX"
        data-ad-slot="XXXXXXXXXX"
        data-ad-format="auto"
        data-full-width-responsive="true"
      ></ins>
    </template>

    <!-- DEVELOPMENT: MOCK AD CONTENT (Now using handleAdClick) -->
    <div
      v-else-if="currentAd"
      class="flex-1 flex flex-col group cursor-pointer"
      @click="handleAdClick"
    >
      <div class="relative overflow-hidden rounded-xl mb-3 h-24">
        <img
          :src="currentAd.image"
          class="w-full h-full object-cover group-hover:scale-105 transition-transform"
        />
      </div>
      <h4 class="text-xs font-bold text-gray-800 mb-1">{{ currentAd.title }}</h4>
      <div class="flex items-center justify-between mt-auto pt-2 border-t border-gray-200/50">
        <span class="text-[10px] font-bold text-blue-600">{{ currentAd.provider }}</span>
        <span class="text-[10px] text-gray-400">Visit Site</span>
      </div>
    </div>
  </div>
</template>
