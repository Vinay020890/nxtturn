<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useGroupStore } from '@/stores/group'
import { storeToRefs } from 'pinia'
import { useRouter, useRoute } from 'vue-router'
import CreateGroupFormModal from '@/components/CreateGroupFormModal.vue'
import type { Group } from '@/stores/group'
import eventBus from '@/services/eventBus'

// Import Lucide icons
import { Sparkles, Users, FolderKanban } from 'lucide-vue-next'

const groupStore = useGroupStore()
const router = useRouter()
const route = useRoute()
const { allGroups, isLoadingAllGroups, allGroupsError, allGroupsHasNextPage } =
  storeToRefs(groupStore)
const isCreateGroupModalOpen = ref(false)

// Tab state
const activeTab = ref<'recommendation' | 'joined' | 'self-created'>('recommendation')

onMounted(() => {
  // CACHING LOGIC: Only fetch the list if it's empty.
  if (allGroups.value.length === 0) {
    groupStore.fetchGroups()
  }

  // Always scroll to top on initial mount/refresh
  scrollToTop()

  // Listen for eventBus scroll event
  eventBus.on('scroll-groups-to-top', scrollToTop)
})

onUnmounted(() => {
  eventBus.off('scroll-groups-to-top', scrollToTop)
})

// Watch for route changes - scroll to top when navigating to groups page
watch(
  () => route.path,
  (newPath, oldPath) => {
    // Check if we're navigating to the groups page
    // Adjust this condition based on your actual route path
    if (newPath.includes('/groups') || newPath === '/groups') {
      // Small delay to ensure DOM is ready
      setTimeout(scrollToTop, 100)
    }
  },
  { immediate: true },
)

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function openCreateGroupModal() {
  isCreateGroupModalOpen.value = true
}

async function handleGroupCreated(newGroup: Group) {
  // Wait for the navigation to complete before doing anything else.
  await router.push({ name: 'group-detail', params: { slug: newGroup.slug } })

  // Now that the redirect is done, it is safe to close the modal.
  isCreateGroupModalOpen.value = false
}

function loadMoreGroups() {
  groupStore.fetchNextPageOfGroups()
}

// --- UI Helper Functions from New Code ---
function pastelBgForText(text = '') {
  const palettes = [
    'bg-gradient-to-r from-rose-50 to-pink-50',
    'bg-gradient-to-r from-amber-50 to-orange-50',
    'bg-gradient-to-r from-lime-50 to-emerald-50',
    'bg-gradient-to-r from-sky-50 to-blue-50',
    'bg-gradient-to-r from-violet-50 to-purple-50',
    'bg-gradient-to-r from-emerald-50 to-teal-50',
    'bg-gradient-to-r from-pink-50 to-rose-50',
    'bg-gradient-to-r from-orange-50 to-amber-50',
  ]
  let code = 0
  for (let i = 0; i < text.length; i++) code = (code << 5) - code + text.charCodeAt(i)
  const idx = Math.abs(code) % palettes.length
  return palettes[idx]
}

function pastelBorderForText(text = '') {
  const palettes = [
    'border-rose-200',
    'border-amber-200',
    'border-lime-200',
    'border-sky-200',
    'border-violet-200',
    'border-emerald-200',
    'border-pink-200',
    'border-orange-200',
  ]
  let code = 0
  for (let i = 0; i < text.length; i++) code = (code << 5) - code + text.charCodeAt(i)
  const idx = Math.abs(code) % palettes.length
  return palettes[idx]
}

function initialsFromName(name = '') {
  const parts = name.trim().split(/\s+/)
  if (parts.length === 0) return ''
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[1][0]).toUpperCase()
}

// Format member count as "X+" or just the number
function formatMemberCount(count: number) {
  return count > 4 ? '4+' : count.toString()
}

// Helper to get avatar URL from member (using picture property)
function getMemberAvatar(member: any) {
  return member.picture || null
}

// Helper to get creator avatar URL
function getCreatorAvatar(creator: any) {
  return creator?.picture || null
}

// Helper to safely get title text (handle null/undefined values)
function getTitleText(text: string | null | undefined): string | undefined {
  return text || undefined
}

/**
 * ✅ Emoji fix: emojis turn black when inside `text-transparent bg-clip-text`.
 * We keep emojis in normal text color and apply gradient only to the remaining text.
 */
function leadingEmoji(name = ''): string {
  const m = name.match(/^([\p{Extended_Pictographic}\p{Emoji_Presentation}\p{Emoji}]+)\s*/u)
  return m ? m[1] : ''
}

function nameWithoutLeadingEmoji(name = ''): string {
  const m = name.match(/^([\p{Extended_Pictographic}\p{Emoji_Presentation}\p{Emoji}]+)\s*/u)
  return m ? name.slice(m[0].length) : name
}
</script>

<template>
  <!-- Added pb-20 for mobile bottom padding and sm:pb-0 to remove it on desktop -->
  <div class="max-w-4xl mx-auto px-0 sm:px-0 min-h-[calc(100vh-12rem)] pb-3 sm:pb-0">
    <!-- Header - Stack on mobile -->
    <header
      class="bg-white p-4 sm:p-4 rounded-2xl shadow-sm border border-gray-200 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-3"
    >
      <h1 class="text-2xl font-bold text-gray-800 w-full sm:w-auto text-center sm:text-left">
        Discover Groups
      </h1>
      <button
        data-cy="create-group-button"
        @click="openCreateGroupModal"
        class="w-full sm:w-auto px-5 py-3 sm:py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-2xl font-semibold hover:from-blue-700 hover:to-blue-800 transition-all shadow-md hover:shadow-lg text-base sm:text-sm"
      >
        + Create New Group
      </button>
    </header>

    <!-- Tab Section with Icons on Top for Mobile -->
    <div class="mb-3">
      <div class="flex border-b border-gray-200">
        <!-- Recommendation Tab - Blue -->
        <button
          @click="activeTab = 'recommendation'"
          :class="[
            'flex-1 flex flex-col items-center justify-center px-2 py-3 sm:px-4 sm:flex-row sm:gap-2 transition-colors rounded-t-2xl',
            activeTab === 'recommendation'
              ? 'text-blue-600 border-b-2 border-blue-500'
              : 'text-gray-600 hover:text-gray-800',
          ]"
        >
          <Sparkles
            class="w-5 h-5 sm:w-5 sm:h-5 mb-1 sm:mb-0"
            :class="
              activeTab === 'recommendation' ? 'text-blue-500 fill-blue-500' : 'text-gray-500'
            "
          />
          <span class="text-xs sm:text-sm font-medium">Recommendation</span>
        </button>

        <!-- Joined Groups Tab - Green -->
        <button
          @click="activeTab = 'joined'"
          :class="[
            'flex-1 flex flex-col items-center justify-center px-2 py-3 sm:px-4 sm:flex-row sm:gap-2 transition-colors rounded-t-2xl',
            activeTab === 'joined'
              ? 'text-emerald-600 border-b-2 border-emerald-500'
              : 'text-gray-600 hover:text-gray-800',
          ]"
        >
          <Users
            class="w-5 h-5 sm:w-5 sm:h-5 mb-1 sm:mb-0"
            :class="activeTab === 'joined' ? 'text-emerald-500 fill-emerald-500' : 'text-gray-500'"
          />
          <span class="text-xs sm:text-sm font-medium">Joined</span>
        </button>

        <!-- Self Created Tab - Purple -->
        <button
          @click="activeTab = 'self-created'"
          :class="[
            'flex-1 flex flex-col items-center justify-center px-2 py-3 sm:px-4 sm:flex-row sm:gap-2 transition-colors rounded-t-2xl',
            activeTab === 'self-created'
              ? 'text-purple-600 border-b-2 border-purple-500'
              : 'text-gray-600 hover:text-gray-800',
          ]"
        >
          <FolderKanban
            class="w-5 h-5 sm:w-5 sm:h-5 mb-1 sm:mb-0"
            :class="
              activeTab === 'self-created' ? 'text-purple-500 fill-purple-500' : 'text-gray-500'
            "
          />
          <span class="text-xs sm:text-sm font-medium">Self Created</span>
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div
      v-if="isLoadingAllGroups && allGroups.length === 0"
      class="text-center py-10 text-gray-500"
    >
      <p>Loading groups...</p>
    </div>

    <!-- Error State -->
    <div
      v-else-if="allGroupsError"
      class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 rounded-2xl"
    >
      <p class="font-bold">Error</p>
      <p>{{ allGroupsError }}</p>
    </div>

    <!-- Group List - Responsive grid with very small gaps -->
    <!-- Changed gap-3 sm:gap-4 to gap-2 sm:gap-3 -->
    <div
      v-else-if="allGroups && allGroups.length > 0"
      class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 gap-2 sm:gap-3"
    >
      <div
        v-for="group in allGroups"
        :key="group.id"
        class="bg-white rounded-2xl shadow-md hover:shadow-xl transition-all duration-300 flex flex-col border border-gray-100 overflow-hidden group-card"
      >
        <!-- Highlighted Group Name and Slug Section with Gradient Background -->
        <div class="relative overflow-hidden">
          <div
            :class="[
              'p-4 sm:p-5 transition-all duration-300 border-b rounded-t-2xl',
              pastelBgForText(group.name),
              pastelBorderForText(group.name),
            ]"
          >
            <router-link
              :to="{ name: 'group-detail', params: { slug: group.slug } }"
              class="block relative z-10"
            >
              <!-- Group Name with single line truncation -->
              <h2
                class="text-lg sm:text-xl font-bold text-gray-900 hover:text-gray-800 transition-colors mb-2 truncate group-hover:translate-x-1 duration-300"
                :title="getTitleText(group.name)"
              >
                <!-- ✅ Emoji is kept OUTSIDE of gradient text -->
                <span v-if="leadingEmoji(group.name)" class="mr-1 text-gray-900">
                  {{ leadingEmoji(group.name) }}
                </span>

                <!-- Gradient only for remaining text -->
                <span
                  class="bg-clip-text text-transparent bg-gradient-to-r from-gray-800 to-gray-700"
                >
                  {{ nameWithoutLeadingEmoji(group.name) }}
                </span>
              </h2>

              <!-- Group Slug with single line truncation and @ inside the box -->
              <div class="flex items-center gap-2 min-w-0">
                <div class="flex items-center gap-1 min-w-0 flex-1">
                  <span
                    class="text-xs sm:text-sm font-semibold px-2 sm:px-3 py-1 rounded-2xl inline-flex items-center gap-1.5 transition-all duration-300 truncate flex-1 min-w-0"
                    :class="[
                      'bg-white/80 backdrop-blur-sm shadow-sm',
                      pastelBorderForText(group.name),
                    ]"
                    :title="getTitleText(group.slug)"
                  >
                    <span class="text-xs font-medium text-gray-500">@</span>
                    <span class="truncate">{{ group.slug }}</span>
                    <svg
                      class="w-3 h-3 opacity-70 group-hover:translate-x-0.5 transition-transform flex-shrink-0"
                      viewBox="0 0 24 24"
                      fill="none"
                    >
                      <path
                        d="M13 7l5 5-5 5"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                      />
                      <path
                        d="M6 12h12"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                      />
                    </svg>
                  </span>
                </div>
              </div>
            </router-link>
          </div>
        </div>

        <!-- Card content -->
        <div class="p-3 flex flex-col flex-grow">
          <!-- Description in single line border box -->
          <div class="mb-3 sm:mb-4">
            <div class="border border-gray-200 rounded-2xl p-2 sm:p-3 bg-gray-50/50">
              <p
                class="text-gray-600 text-xs sm:text-sm truncate"
                :title="getTitleText(group.description)"
              >
                {{ group.description }}
              </p>
            </div>
          </div>

          <!-- Created by and username inline -->
          <div class="mb-3 sm:mb-4">
            <div class="flex items-center gap-1 sm:gap-2 flex-wrap">
              <span class="text-xs font-medium text-gray-500 uppercase tracking-wide"
                >Created by</span
              >
              <span class="text-gray-400 text-xs">•</span>
              <router-link
                v-if="group.creator && group.creator.username"
                :to="{ name: 'profile', params: { username: group.creator.username } }"
                class="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm text-gray-700 hover:underline min-w-0 group/creator"
                @click.stop
              >
                <!-- creator avatar -->
                <div
                  class="w-5 h-5 sm:w-6 sm:h-6 rounded-full overflow-hidden flex items-center justify-center border-2 border-white shadow-sm transition-transform group-hover/creator:scale-105"
                >
                  <img
                    v-if="getCreatorAvatar(group.creator)"
                    :src="getCreatorAvatar(group.creator)"
                    :alt="group.creator.username + ' avatar'"
                    class="w-full h-full object-cover"
                  />
                  <template v-else>
                    <div
                      :class="[
                        'flex items-center justify-center w-full h-full text-xs font-semibold',
                        pastelBgForText(group.creator?.username || ''),
                      ]"
                    >
                      {{ initialsFromName(group.creator?.username || 'U') }}
                    </div>
                  </template>
                </div>

                <span class="font-semibold text-gray-800 truncate max-w-[80px] sm:max-w-[120px]">
                  {{ group.creator.username }}
                </span>
              </router-link>
            </div>
          </div>

          <!-- Privacy and membership status badges -->
          <div class="flex items-center gap-1 sm:gap-2 mb-3 flex-wrap">
            <div
              :class="[
                'text-xs font-semibold py-1 px-2 sm:py-1.5 sm:px-3 rounded-2xl border shadow-sm whitespace-nowrap',
                group.privacy_level === 'private'
                  ? 'bg-gradient-to-r from-red-50 to-rose-50 text-red-600 border-red-200'
                  : 'bg-gradient-to-r from-emerald-50 to-green-50 text-emerald-700 border-emerald-200',
              ]"
              v-if="group.privacy_level"
            >
              {{ group.privacy_level === 'private' ? '🔒 Private' : '🌍 Public' }}
            </div>
            <div v-else class="text-xs text-gray-400 px-2 whitespace-nowrap">Unknown Privacy</div>

            <!-- This block now handles both 'member' and 'pending' statuses like old code -->
            <div
              v-if="group.membership_status === 'member' || group.membership_status === 'creator'"
              class="text-xs font-semibold py-1 px-2 sm:py-1.5 sm:px-3 rounded-2xl bg-gradient-to-r from-blue-50 to-cyan-50 text-blue-700 border border-blue-200 shadow-sm whitespace-nowrap"
            >
              👤 Member
            </div>
            <div
              v-else-if="group.membership_status === 'pending'"
              class="text-xs font-semibold py-1 px-2 sm:py-1.5 sm:px-3 rounded-2xl bg-gradient-to-r from-yellow-50 to-amber-50 text-yellow-700 border border-yellow-200 shadow-sm whitespace-nowrap"
            >
              ⏳ Pending
            </div>
          </div>

          <!-- bottom row: members avatars, count, and view button -->
          <div
            class="pt-3 border-t border-gray-100 flex items-center justify-between gap-2 sm:gap-3 mt-auto"
          >
            <div class="flex items-center gap-2 min-w-0">
              <div class="flex items-center -space-x-3 sm:-space-x-5">
                <template v-if="group.members && group.members.length > 0">
                  <div
                    v-for="(member, idx) in group.members.slice(0, 4)"
                    :key="member.id || idx"
                    class="relative group/member"
                    :title="getTitleText(member.username || 'Member')"
                  >
                    <div
                      class="w-6 h-6 sm:w-8 sm:h-8 rounded-full ring-2 ring-white border border-gray-100 overflow-hidden shadow-sm flex-shrink-0 transition-transform group-hover/member:scale-110"
                    >
                      <img
                        v-if="getMemberAvatar(member)"
                        :src="getMemberAvatar(member)"
                        :alt="member.username"
                        class="w-full h-full object-cover"
                      />
                      <template v-else>
                        <div
                          :class="[
                            'w-full h-full flex items-center justify-center text-xs font-semibold',
                            pastelBgForText(member.username || ''),
                          ]"
                        >
                          {{ initialsFromName(member.username || 'M') }}
                        </div>
                      </template>
                    </div>
                  </div>
                </template>

                <!-- Show placeholder avatars when no members data but member_count > 0 -->
                <template v-else-if="group.member_count > 0">
                  <!-- Generate placeholder avatars based on member_count (max 4) -->
                  <div
                    v-for="i in Math.min(group.member_count, 4)"
                    :key="i"
                    class="relative group/member"
                  >
                    <div
                      class="w-6 h-6 sm:w-8 sm:h-8 rounded-full ring-2 ring-white border border-gray-100 overflow-hidden shadow-sm flex-shrink-0 transition-transform group-hover/member:scale-110"
                    >
                      <div
                        :class="[
                          'w-full h-full flex items-center justify-center text-xs font-semibold text-gray-600',
                          pastelBgForText('member' + i),
                        ]"
                      >
                        M{{ i }}
                      </div>
                    </div>
                  </div>
                </template>
              </div>

              <!-- Member count with + for more than 4 members -->
              <div
                v-if="group.member_count > 0"
                class="text-xs sm:text-sm font-medium whitespace-nowrap"
                :class="['text-gray-700', group.member_count > 4 ? 'font-bold' : 'font-semibold']"
              >
                {{ formatMemberCount(group.member_count) }} member{{
                  group.member_count !== 1 ? 's' : ''
                }}
              </div>
              <div v-else class="text-xs sm:text-sm text-gray-400 whitespace-nowrap">
                No members yet
              </div>
            </div>

            <!-- View button -->
            <router-link
              :to="{ name: 'group-detail', params: { slug: group.slug } }"
              class="inline-flex items-center gap-1 sm:gap-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-2xl border border-gray-200 bg-white shadow-sm hover:shadow-md text-xs sm:text-sm font-medium whitespace-nowrap flex-shrink-0 transition-all duration-300 hover:-translate-y-0.5 group/view"
            >
              View
              <svg
                class="w-3 h-3 sm:w-4 sm:h-4 text-gray-500 group-hover/view:translate-x-1 transition-transform"
                viewBox="0 0 24 24"
                fill="none"
                aria-hidden
              >
                <path
                  d="M5 12h14"
                  stroke="currentColor"
                  stroke-width="1.6"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                <path
                  d="M12 5l7 7-7 7"
                  stroke="currentColor"
                  stroke-width="1.6"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-else
      class="bg-gradient-to-r from-gray-50 to-white p-6 sm:p-8 rounded-2xl shadow-sm text-center text-gray-500 border border-gray-100"
    >
      <div
        class="w-12 h-12 sm:w-16 sm:h-16 mx-auto mb-3 sm:mb-4 rounded-2xl bg-gradient-to-r from-blue-50 to-indigo-50 flex items-center justify-center"
      >
        <Users class="w-6 h-6 sm:w-8 sm:h-8 text-blue-400" />
      </div>
      <p class="text-base sm:text-lg font-medium text-gray-600 mb-1 sm:mb-2">No groups found</p>
      <p class="text-sm sm:text-gray-500">Be the first to create one!</p>
    </div>

    <!-- "Load More" button for pagination -->
    <!-- Added mb-4 for extra bottom margin on mobile -->
    <div v-if="allGroupsHasNextPage" class="flex justify-center mt-6 sm:mt-8 mb-4 sm:mb-0">
      <button
        @click="loadMoreGroups"
        :disabled="isLoadingAllGroups"
        class="w-full sm:w-auto bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold py-3 px-6 sm:px-8 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 ease-in-out transform hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base"
      >
        {{ isLoadingAllGroups ? 'Loading...' : 'Load More Groups' }}
      </button>
    </div>

    <CreateGroupFormModal
      :is-open="isCreateGroupModalOpen"
      @close="isCreateGroupModalOpen = false"
      @group-created="handleGroupCreated"
    />
  </div>
</template>

<style scoped>
/* Ensure consistent card heights */
.grid > div {
  display: flex;
  flex-direction: column;
  min-height: 300px;
  height: auto;
}

/* Fix for the odd card issue - make all cards equal width */
.grid > div {
  width: 100%;
}

/* On desktop, ensure proper 2-column layout with very small gaps */
@media (min-width: 640px) {
  .grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.5rem; /* Reduced from 0.75rem to 0.5rem (8px) */
  }

  .grid > div {
    grid-column: span 1;
    width: 100%;
    max-width: 100%;
  }

  /* Fix for odd number of cards - don't center the last card */
  .grid > div:last-child:nth-child(odd) {
    justify-self: start;
    margin-right: auto;
  }
}

@media (min-width: 768px) {
  .grid {
    gap: 0.75rem; /* Reduced from 1rem to 0.75rem (12px) */
  }
}

/* On mobile, single column with smaller gap */
@media (max-width: 639px) {
  .grid {
    display: flex;
    flex-direction: column;
    gap: 0.5rem; /* Reduced from 0.75rem to 0.5rem */
  }

  .grid > div {
    width: 100%;
  }
}

/* Ensure cards grow properly */
.grid > div > div:nth-child(2) {
  flex-grow: 1;
}

/* Make sure the view button stays at bottom */
.grid > div > div:last-child {
  margin-top: auto;
}

/* Enhanced hover effects for cards */
.group-card {
  transition: all 0.3s ease;
}

.group-card:hover {
  transform: translateY(-4px);
}

/* Truncation styles */
.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.min-w-0 {
  min-width: 0;
}

/* Hide scrollbar for tabs on mobile but allow scrolling */
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
</style>
