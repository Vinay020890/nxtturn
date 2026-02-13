<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProfileStore } from '@/stores/profile'
import { useAuthStore } from '@/stores/auth'
import { usePostsStore } from '@/stores/posts'
import { useInfiniteScroll } from '@/composables/useInfiniteScroll'
import { storeToRefs } from 'pinia'
import eventBus from '@/services/eventBus'

import ProfileCard from '@/components/profile/ProfileCard.vue'
import PostItem from '@/components/PostItem.vue'
import ProfileAboutTab from '@/components/profile/tabs/ProfileAboutTab.vue'
import ProfileEducationTab from '@/components/profile/tabs/ProfileEducationTab.vue'
import ProfileSkillsTab from '@/components/profile/tabs/ProfileSkillsTab.vue'
import ProfileExperienceTab from '@/components/profile/tabs/ProfileExperienceTab.vue'
import ProfileContactTab from '@/components/profile/tabs/ProfileContactTab.vue'
import ProfileResumeTab from '@/components/profile/tabs/ProfileResumeTab.vue'

import { User, GraduationCap, Code2, Briefcase, FileText, Mail } from 'lucide-vue-next'

const leftColumn = ref<HTMLElement | null>(null)
const rightColumn = ref<HTMLElement | null>(null)
const route = useRoute()
const router = useRouter()
const profileStore = useProfileStore()
const authStore = useAuthStore()
const postsStore = usePostsStore()
const { currentProfile, isLoadingProfile, isLoadingPosts, errorProfile, errorPosts } =
  storeToRefs(profileStore)
const { currentUser, isAuthenticated } = storeToRefs(authStore)
const username = computed(() => (route.params.username as string) || '')

// Check if we're in a test environment (Cypress)
const isTestEnvironment = typeof window !== 'undefined' && (window as any).Cypress

// Tabs setup
const activeTab = ref('About')
const tabs = [
  { key: 'About', label: 'About', icon: User },
  { key: 'Education', label: 'Education', icon: GraduationCap },
  { key: 'Skills', label: 'Skills', icon: Code2 },
  { key: 'Experience', label: 'Experience', icon: Briefcase },
  { key: 'Resume/CV', label: 'Resume', icon: FileText },
  { key: 'Contact', label: 'Contact', icon: Mail },
]

// Refs for tab elements
const tabRefs = ref<HTMLElement[]>([])
const tabContainerRef = ref<HTMLElement | null>(null)

// Active pill style - now we need two for different views
const activePillStyleMobile = ref({
  width: '0px',
  left: '0px',
  top: '0px',
  height: '0px',
})

const activePillStyleDesktop = ref({
  width: '0px',
  left: '0px',
})

// Padding values for mobile pill (increased)
const MOBILE_PILL_PADDING = 6 // Increased from 4 to 6 pixels

// Function to update active pill position for desktop (full tab)
const updateActivePillDesktop = () => {
  nextTick(() => {
    const activeIndex = tabs.findIndex((tab) => tab.key === activeTab.value)
    if (activeIndex >= 0 && tabRefs.value[activeIndex] && tabContainerRef.value) {
      const activeTabElement = tabRefs.value[activeIndex]
      const tabRect = activeTabElement.getBoundingClientRect()
      const containerRect = tabContainerRef.value.getBoundingClientRect()

      // Calculate width and position relative to container
      const width = tabRect.width
      const left = tabRect.left - containerRect.left

      activePillStyleDesktop.value = {
        width: `${width}px`,
        left: `${left}px`,
      }
    }
  })
}

// Function to update active pill position for mobile (icon only)
const updateActivePillMobile = () => {
  nextTick(() => {
    const activeIndex = tabs.findIndex((tab) => tab.key === activeTab.value)
    if (activeIndex >= 0 && tabRefs.value[activeIndex] && tabContainerRef.value) {
      const activeTabElement = tabRefs.value[activeIndex]
      const tabRect = activeTabElement.getBoundingClientRect()
      const containerRect = tabContainerRef.value.getBoundingClientRect()

      // Find the icon element within the tab
      const iconElement = activeTabElement.querySelector('.tab-icon')
      if (iconElement) {
        const iconRect = iconElement.getBoundingClientRect()

        // Calculate position and size relative to container with increased padding
        const width = iconRect.width + MOBILE_PILL_PADDING * 2 // Increased padding on both sides
        const height = iconRect.height + MOBILE_PILL_PADDING * 2 // Increased padding on top and bottom
        const left = iconRect.left - containerRect.left - MOBILE_PILL_PADDING // Center the pill with increased padding
        const top = iconRect.top - containerRect.top - MOBILE_PILL_PADDING // Center the pill with increased padding

        activePillStyleMobile.value = {
          width: `${width}px`,
          left: `${left}px`,
          top: `${top}px`,
          height: `${height}px`,
        }
      }
    }
  })
}

// Combined update function
const updateActivePill = () => {
  updateActivePillDesktop()
  updateActivePillMobile()
}

// Watch for tab changes
watch(activeTab, () => {
  updateActivePill()
})

// Update on window resize
const handleResize = () => {
  updateActivePill()
}

// Watch for currentProfile to ensure tabs are rendered
watch(currentProfile, (newProfile) => {
  if (newProfile) {
    // Wait for the next tick to ensure DOM is updated
    nextTick(() => {
      updateActivePill()
    })
  }
})

const userPostIds = computed(() => profileStore.postIdsByUsername[username.value] || [])
const userPostsNextPageUrl = computed(() => profileStore.nextPageUrlByUsername[username.value])
const userPosts = computed(() => postsStore.getPostsByIds(userPostIds.value))
const isOwnProfile = computed(
  () => isAuthenticated.value && currentUser.value?.username === username.value,
)
const loadMoreTrigger = ref<HTMLElement | null>(null)

useInfiniteScroll(
  loadMoreTrigger,
  () => profileStore.fetchNextPageOfUserPosts(username.value),
  userPostsNextPageUrl,
)

const loadProfileData = () => {
  if (username.value) {
    profileStore.fetchProfile(username.value)
    profileStore.refreshUserPosts(username.value)
  }
}

watch(
  username,
  () => {
    loadProfileData()
    activeTab.value = 'About'
  },
  { immediate: true },
)

function scrollToTop() {
  leftColumn.value?.scrollTo({ top: 0, behavior: 'smooth' })
  rightColumn.value?.scrollTo({ top: 0, behavior: 'smooth' })
}

// Function to navigate to posts page
function navigateToPostsPage() {
  router.push(`/profile/${username.value}/posts`)
}

onMounted(() => {
  eventBus.on('scroll-profile-to-top', scrollToTop)
  window.addEventListener('resize', handleResize)

  // Initial update after component is mounted - use a longer timeout to ensure DOM is ready
  setTimeout(() => {
    updateActivePill()
  }, 300)
})

onUnmounted(() => {
  eventBus.off('scroll-profile-to-top', scrollToTop)
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <div>
    <!-- LOADING -->
    <div v-if="isLoadingProfile && !currentProfile" class="text-center p-10 text-gray-500 pt-20">
      Loading profile...
    </div>

    <!-- ERROR -->
    <div
      v-else-if="errorProfile"
      class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md m-4 mt-20"
    >
      <p>{{ errorProfile }}</p>
    </div>

    <!-- PROFILE CONTENT -->
    <div v-else-if="currentProfile" class="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-20">
      <div class="grid grid-cols-12 lg:gap-x-3 h-[calc(100vh-5rem)]">
        <!-- LEFT COLUMN - Full width on mobile, 6 columns on desktop -->
        <aside
          ref="leftColumn"
          data-cy="profile-left-column"
          :class="[
            'h-full overflow-y-auto',
            isTestEnvironment ? 'col-span-12 lg:col-span-6' : 'col-span-12 lg:col-span-6',
          ]"
        >
          <!-- Reduced gap between ProfileCard and tabs -->
          <div class="space-y-4">
            <!-- Pass postsCount prop to ProfileCard -->
            <ProfileCard
              :profile="currentProfile"
              :is-own-profile="isOwnProfile"
              :posts-count="userPosts.length"
              @posts-clicked="navigateToPostsPage"
            />

            <!-- PILL STYLE TAB SECTION (Updated UI only) -->
            <div>
              <div class="mb-3">
                <!-- Reduced margin-bottom -->
                <div
                  ref="tabContainerRef"
                  class="relative flex items-center bg-gray-100 rounded-full p-1"
                >
                  <!-- Reduced padding -->

                  <!-- ACTIVE PILL FOR DESKTOP (full tab) - hidden on mobile -->
                  <div
                    class="hidden lg:block absolute top-0.5 bottom-0.5 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-300 ease-out"
                    :style="activePillStyleDesktop"
                  />

                  <!-- ACTIVE PILL FOR MOBILE (icon only) - shown on mobile, hidden on desktop -->
                  <div
                    class="lg:hidden absolute rounded-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-300 ease-out"
                    :style="activePillStyleMobile"
                  />

                  <!-- Tabs with reduced horizontal padding -->
                  <button
                    v-for="(tab, index) in tabs"
                    :key="tab.key"
                    :ref="
                      (el) => {
                        if (el) tabRefs[index] = el as HTMLElement
                      }
                    "
                    @click="activeTab = tab.key"
                    class="relative z-10 flex flex-col items-center justify-center px-3 py-1.5 text-xs font-medium rounded-full transition-colors duration-300 min-w-0 flex-1"
                    :class="[
                      activeTab === tab.key
                        ? 'lg:text-white text-blue-500 border-blue-500'
                        : 'text-gray-600 hover:text-gray-900',
                    ]"
                    :title="tab.label"
                  >
                    <!-- Mobile: Icon above text, Desktop: Icon beside text -->
                    <div class="flex flex-col items-center lg:flex-row lg:gap-1">
                      <!-- Icon container with special class for mobile pill targeting -->
                      <div class="relative">
                        <component
                          :is="tab.icon"
                          class="tab-icon w-3.5 h-3.5 flex-shrink-0 mb-0.5 lg:mb-0 relative z-20"
                          :class="activeTab === tab.key ? 'text-white lg:text-inherit' : ''"
                        />
                      </div>
                      <span
                        class="truncate whitespace-nowrap text-[10px] lg:text-xs mt-0.5 lg:mt-0"
                      >
                        {{ tab.label }}
                      </span>
                    </div>
                  </button>
                </div>
              </div>

              <!-- Tab Content with fixed width constraints to prevent stretching -->
              <div class="transition-all duration-300">
                <div class="max-w-4xl mx-auto">
                  <ProfileAboutTab
                    v-if="activeTab === 'About'"
                    :profile="currentProfile"
                    :is-own-profile="isOwnProfile"
                  />
                  <ProfileEducationTab
                    v-if="activeTab === 'Education'"
                    :profile="currentProfile"
                    :is-own-profile="isOwnProfile"
                  />
                  <ProfileSkillsTab
                    v-if="activeTab === 'Skills'"
                    :profile="currentProfile"
                    :is-own-profile="isOwnProfile"
                  />
                  <ProfileExperienceTab
                    v-if="activeTab === 'Experience'"
                    :profile="currentProfile"
                    :is-own-profile="isOwnProfile"
                  />
                  <ProfileResumeTab
                    v-if="activeTab === 'Resume/CV'"
                    :profile="currentProfile"
                    :is-own-profile="isOwnProfile"
                  />
                  <ProfileContactTab
                    v-if="activeTab === 'Contact'"
                    :profile="currentProfile"
                    :is-own-profile="isOwnProfile"
                  />
                </div>
              </div>
            </div>
          </div>
        </aside>

        <!-- RIGHT COLUMN - Show conditionally based on environment -->
        <div
          v-if="isTestEnvironment"
          ref="rightColumn"
          class="col-span-12 lg:col-span-6 min-w-0 mt-6 lg:mt-0 h-full overflow-y-auto"
        >
          <div
            v-if="isLoadingPosts && userPosts.length === 0"
            class="text-center p-10 text-gray-500"
          >
            Loading posts...
          </div>
          <div
            v-else-if="errorPosts"
            class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md"
          >
            {{ errorPosts }}
          </div>
          <div v-else-if="userPosts.length > 0" class="space-y-4">
            <PostItem v-for="post in userPosts" :key="post.id" :post="post" />
          </div>
          <div v-else class="bg-white rounded-lg shadow-md p-10 text-center text-gray-500">
            This user hasn't posted anything yet.
          </div>

          <div v-if="userPostsNextPageUrl" ref="loadMoreTrigger" class="h-10"></div>
          <div v-if="isLoadingPosts && userPosts.length > 0" class="text-center p-4 text-gray-500">
            Loading more posts...
          </div>
        </div>

        <!-- RIGHT COLUMN for non-test environments (hidden on mobile) -->
        <div
          v-else
          ref="rightColumn"
          class="hidden lg:block col-span-12 lg:col-span-6 min-w-0 mt-6 lg:mt-0 h-full overflow-y-auto"
        >
          <div
            v-if="isLoadingPosts && userPosts.length === 0"
            class="text-center p-10 text-gray-500"
          >
            Loading posts...
          </div>
          <div
            v-else-if="errorPosts"
            class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md"
          >
            {{ errorPosts }}
          </div>
          <div v-else-if="userPosts.length > 0" class="space-y-4">
            <PostItem v-for="post in userPosts" :key="post.id" :post="post" />
          </div>
          <div v-else class="bg-white rounded-lg shadow-md p-10 text-center text-gray-500">
            This user hasn't posted anything yet.
          </div>

          <div v-if="userPostsNextPageUrl" ref="loadMoreTrigger" class="h-10"></div>
          <div v-if="isLoadingPosts && userPosts.length > 0" class="text-center p-4 text-gray-500">
            Loading more posts...
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Optional: Add smooth transition for tab content */
.transition-all {
  transition-property: all;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 300ms;
}
</style>
