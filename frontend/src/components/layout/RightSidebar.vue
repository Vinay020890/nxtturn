<script setup lang="ts">
// Define interfaces for our data
interface Person {
  id: number
  name: string
  role: string
  avatar: string
}

interface Institute {
  id: number
  name: string
  logo: string
}

// Dummy data for visual representation with proper typing
const people: Person[] = [
  {
    id: 1,
    name: 'Sahil Gupta',
    role: 'Software Engineer',
    avatar: 'https://i.pravatar.cc/150?u=p1',
  },

  { id: 2, name: 'Anish Mehta', role: 'UX Designer', avatar: 'https://i.pravatar.cc/150?u=p3' },

  { id: 3, name: 'Rehan Khan', role: 'QA Engineer', avatar: 'https://i.pravatar.cc/150?u=p5' },
]

const institutes: Institute[] = [
  { id: 1, name: 'IIT Bombay', logo: 'https://placehold.co/40x40/E2E8F0/475569?text=IITB' },
  { id: 2, name: 'IIM Ahmedabad', logo: 'https://placehold.co/40x40/E2E8F0/475569?text=IIMA' },
  { id: 3, name: 'NIT Trichy', logo: 'https://placehold.co/40x40/E2E8F0/475569?text=NITT' },
]
</script>

<template>
  <div class="relative left-[-12px] w-full">
    <div class="flex justify-start">
      <div class="space-y-6">
        <div
          class="max-h-[calc(100vh-theme(spacing.24))] overflow-y-auto custom-scrollbar space-y-3 pr-2"
        >
          <!-- People You May Know Card -->
          <div
            class="bg-gradient-to-br from-white to-gray-50 p-5 rounded-2xl border border-gray-200 shadow-md hover:shadow-lg transition-all duration-300"
          >
            <div class="flex items-center gap-2 mb-4">
              <div class="w-1 h-5 bg-gradient-to-b from-blue-500 to-purple-500 rounded-full"></div>
              <h3 class="font-bold text-gray-800 text-lg">People You May Know</h3>
            </div>
            <ul class="space-y-4">
              <li
                v-for="person in people"
                :key="person.id"
                class="flex items-center p-2 hover:bg-gray-50 rounded-xl transition-colors duration-200"
              >
                <!-- Logo/avatar container - stays left-aligned -->
                <div class="flex-shrink-0 mr-3">
                  <div class="relative">
                    <img
                      :src="person.avatar"
                      alt=""
                      class="h-11 w-11 rounded-full ring-2 ring-white shadow-sm"
                    />
                    <div
                      class="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-400 rounded-full border border-white"
                    ></div>
                  </div>
                </div>

                <!-- Name and role - takes available space -->
                <div class="flex-1 min-w-0 mr-4">
                  <p class="font-semibold text-gray-800 text-sm truncate">{{ person.name }}</p>
                  <p class="text-xs text-gray-600 truncate">{{ person.role }}</p>
                </div>

                <!-- Connect button - now has more gap -->
                <button
                  class="flex-shrink-0 text-sm font-medium bg-gradient-to-r from-blue-500 to-blue-600 text-white px-2 py-1.5 rounded-xl hover:from-blue-600 hover:to-blue-700 transition-all duration-300 shadow-sm hover:shadow"
                >
                  Connect
                </button>
              </li>
            </ul>
            <div class="mt-3 pt-2 border-t border-gray-100">
              <button
                class="w-full text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 py-2 rounded-xl transition-colors duration-200"
              >
                Show more suggestions
              </button>
            </div>
          </div>

          <!-- Featured Institutes Card -->
          <div
            class="bg-gradient-to-br from-white to-gray-50 p-5 rounded-2xl border border-gray-200 shadow-md hover:shadow-lg transition-all duration-300"
          >
            <div class="flex items-center gap-2 mb-4">
              <div class="w-1 h-5 bg-gradient-to-b from-amber-500 to-orange-500 rounded-full"></div>
              <h3 class="font-bold text-gray-800 text-lg">Featured Institutes</h3>
            </div>
            <ul class="space-y-3">
              <li
                v-for="inst in institutes"
                :key="inst.id"
                class="flex items-center p-3 hover:bg-gray-50 rounded-xl transition-colors duration-200"
              >
                <!-- Logo container - stays left-aligned -->
                <div class="flex-shrink-0 mr-3">
                  <div class="relative">
                    <img
                      :src="inst.logo"
                      alt=""
                      class="h-11 w-11 rounded-xl ring-2 ring-white shadow-sm"
                    />
                    <div
                      class="absolute -top-1 -right-1 w-5 h-5 bg-gradient-to-br from-amber-400 to-orange-500 rounded-full flex items-center justify-center"
                    >
                      <svg class="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                        <path
                          fill-rule="evenodd"
                          d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
                          clip-rule="evenodd"
                        />
                      </svg>
                    </div>
                  </div>
                </div>

                <!-- Institute name and description - takes available space -->
                <div class="flex-1 min-w-0 mr-4">
                  <p class="font-semibold text-gray-800 text-sm">{{ inst.name }}</p>
                  <p class="text-xs text-gray-600 flex items-center gap-1">
                    <svg class="w-3 h-3 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fill-rule="evenodd"
                        d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z"
                        clip-rule="evenodd"
                      />
                    </svg>
                    Premier Institute
                  </p>
                </div>

                <!-- Follow button - now has more gap -->
                <button
                  class="flex-shrink-0 text-sm font-medium bg-gradient-to-r from-gray-800 to-gray-900 text-white px-2 py-1.5 rounded-xl hover:from-gray-900 hover:to-black transition-all duration-300 shadow-sm hover:shadow"
                >
                  Follow
                </button>
              </li>
            </ul>
          </div>

          <!-- Sponsored Card -->
          <div
            class="bg-gradient-to-br from-white to-gray-50 p-5 rounded-2xl border border-gray-200 shadow-md hover:shadow-lg transition-all duration-300 group"
          >
            <div class="flex justify-between items-center mb-3">
              <div class="flex items-center gap-2">
                <div
                  class="w-1 h-5 bg-gradient-to-b from-emerald-500 to-teal-500 rounded-full"
                ></div>
                <h3 class="font-bold text-gray-800 text-lg">Sponsored</h3>
              </div>
              <span class="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-1 rounded-lg"
                >Ad</span
              >
            </div>
            <div
              class="relative overflow-hidden rounded-xl mb-4 group-hover:shadow transition-all duration-300"
            >
              <img
                src="https://picsum.photos/seed/ad1/400/300"
                alt="Sponsored Ad"
                class="rounded-xl w-full transform group-hover:scale-[1.02] transition-transform duration-500"
              />
              <div class="absolute top-3 left-3">
                <span
                  class="text-xs font-bold bg-gradient-to-r from-purple-600 to-pink-600 text-white px-3 py-1 rounded-full shadow"
                >
                  Featured
                </span>
              </div>
            </div>
            <div class="mt-2">
              <div class="flex items-center justify-between mb-2">
                <p class="font-bold text-gray-900 text-lg">Master the Vue 3 Composition API</p>
                <svg
                  class="w-5 h-5 text-gray-400 group-hover:text-blue-500 transition-colors duration-200"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fill-rule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                    clip-rule="evenodd"
                  />
                </svg>
              </div>
              <p class="text-sm text-gray-600 mb-4">
                The ultimate course for building scalable and maintainable Vue applications. Enroll
                now!
              </p>
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <div class="flex items-center">
                    <svg class="w-4 h-4 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"
                      />
                    </svg>
                    <span class="text-sm font-semibold text-gray-700 ml-1">4.9</span>
                  </div>
                  <span class="text-xs text-gray-500">• 2.5k+ students</span>
                </div>
                <button
                  class="text-sm font-bold bg-gradient-to-r from-purple-600 to-blue-600 text-white px-5 py-2.5 rounded-xl hover:from-purple-700 hover:to-blue-700 transition-all duration-300 shadow hover:shadow-lg"
                >
                  Enroll Now
                </button>
              </div>
            </div>
          </div>
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
