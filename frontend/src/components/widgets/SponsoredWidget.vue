<script setup lang="ts">
import { MegaphoneIcon } from '@heroicons/vue/24/outline'

// In the future, this will accept props from a "Campaigns" API
const sponsoredContent = {
  title: 'Full-Stack AI Bootcamp',
  provider: 'Stanford Professional Education',
  description:
    'Master Generative AI and LLMs with hands-on projects. 12-week intensive program starting April 2026.',
  image:
    'https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&q=80&w=400',
  cta: 'Apply Now',
}
</script>

<template>
  <div
    class="bg-gradient-to-br from-white to-slate-50 p-5 rounded-2xl border border-emerald-100 shadow-sm hover:shadow-md transition-all group overflow-hidden relative"
  >
    <!-- Header -->
    <div class="flex justify-between items-center mb-4">
      <div class="flex items-center gap-2">
        <div class="w-1 h-5 bg-gradient-to-b from-emerald-400 to-teal-600 rounded-full"></div>
        <h3 class="font-bold text-slate-800 text-sm">Featured Opportunity</h3>
      </div>
      <span
        class="flex items-center gap-1 text-[10px] font-black text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded uppercase tracking-widest border border-emerald-100"
      >
        <MegaphoneIcon class="w-3 h-3" />
        Sponsored
      </span>
    </div>

    <!-- Banner Image -->
    <div class="relative overflow-hidden rounded-xl mb-3 h-32">
      <img
        :src="sponsoredContent.image"
        class="w-full h-full object-cover transform group-hover:scale-110 transition-transform duration-700"
        alt="Sponsored Content"
      />
      <div class="absolute inset-0 bg-gradient-to-t from-slate-900/40 to-transparent"></div>
    </div>

    <!-- Text Content -->
    <div class="space-y-1 mb-4">
      <p class="text-[10px] font-bold text-emerald-600 uppercase tracking-tight">
        {{ sponsoredContent.provider }}
      </p>
      <h4
        class="font-bold text-slate-900 text-sm leading-snug group-hover:text-emerald-700 transition-colors"
      >
        {{ sponsoredContent.title }}
      </h4>
      <p class="text-xs text-slate-500 line-clamp-2 leading-relaxed">
        {{ sponsoredContent.description }}
      </p>
    </div>

    <!-- Action Button -->
    <button
      class="w-full py-2.5 bg-slate-900 hover:bg-black text-white text-xs font-bold rounded-xl shadow-sm transition-all active:scale-95"
    >
      {{ sponsoredContent.cta }}
    </button>
  </div>
</template>
