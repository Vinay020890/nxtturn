<script setup lang="ts">
import { XMarkIcon } from '@heroicons/vue/24/solid';

const props = defineProps<{
    show: boolean;
    title: string;
}>();

const emit = defineEmits(['close']);

function closeModal() {
    emit('close');
}
</script>

<template>
    <teleport to="body">
        <transition enter-active-class="transition ease-out duration-200" enter-from-class="opacity-0"
            enter-to-class="opacity-100" leave-active-class="transition ease-in duration-150"
            leave-from-class="opacity-100" leave-to-class="opacity-0">
            <div v-if="show" class="fixed inset-0 z-40 bg-black bg-opacity-60 backdrop-blur-sm" @click="closeModal">
            </div>
        </transition>

        <transition enter-active-class="transition ease-out duration-300"
            enter-from-class="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            enter-to-class="opacity-100 translate-y-0 sm:scale-100" leave-active-class="transition ease-in duration-200"
            leave-from-class="opacity-100 translate-y-0 sm:scale-100"
            leave-to-class="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95">
            <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center p-4">
                <div class="relative w-full max-w-lg bg-white rounded-lg shadow-xl" @click.stop>
                    <!-- Modal Header -->
                    <div class="flex items-center justify-between p-4 border-b">
                        <h3 class="text-lg font-semibold text-gray-800">{{ title }}</h3>
                        <button @click="closeModal"
                            class="p-1 rounded-full text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
                            aria-label="Close modal">
                            <XMarkIcon class="w-6 h-6" />
                        </button>
                    </div>

                    <!-- Modal Body (where our form will go) -->
                    <div class="p-6">
                        <slot></slot>
                    </div>
                </div>
            </div>
        </transition>
    </teleport>
</template>