<script setup lang="ts">
import { onMounted, onUnmounted, watch, ref, computed } from 'vue'
import { useRouter, RouterLink, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import { storeToRefs } from 'pinia'
import { debounce } from 'lodash-es'
import { getAvatarUrl } from '@/utils/avatars'
import type { User } from '@/stores/auth'
import { useSearchStore } from '@/stores/search'
import { useFeedStore } from '@/stores/feed'
import { useGroupStore } from '@/stores/group'
import { usePostsStore } from '@/stores/posts'
import type { Post } from '@/types'
import eventBus from '@/services/eventBus'

// Import animate.css ONLY for bell animation
import 'animate.css'

// --- Icon Imports for new dropdown ---
import {
  Cog6ToothIcon,
  QuestionMarkCircleIcon,
  EyeIcon,
  ChatBubbleLeftRightIcon,
  MoonIcon,
  ArrowLeftOnRectangleIcon,
  ChevronDownIcon,
  Bars3Icon,
  XMarkIcon,
} from '@heroicons/vue/24/outline'

// --- Solid Heroicons for profile dropdown ---
import {
  Cog6ToothIcon as Cog6ToothIconSolid,
  QuestionMarkCircleIcon as QuestionMarkCircleIconSolid,
  EyeIcon as EyeIconSolid,
  ChatBubbleLeftRightIcon as ChatBubbleLeftRightIconSolid,
  MoonIcon as MoonIconSolid,
  ArrowLeftOnRectangleIcon as ArrowLeftOnRectangleIconSolid,
} from '@heroicons/vue/24/solid'

// --- Font Awesome Icons for new navbar items ---
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { library } from '@fortawesome/fontawesome-svg-core'
import {
  faCompass,
  faUserGraduate,
  faBriefcase,
  faUsers,
  faComment,
  faBell,
  faSchool,
  faBuildingColumns,
  faLandmark,
  faPenToSquare,
  faFlask,
  faHelmetSafety,
  faBuildingFlag,
  faEarthAsia,
  faLaptopCode,
  faClipboardCheck,
  faCalendarDays,
  faMessage,
  faUser,
  faHashtag,
  faClock,
  faFileAlt,
  faSearch,
  faChevronRight,
  faTimes,
} from '@fortawesome/free-solid-svg-icons'

// Add icons to library
library.add(
  faCompass,
  faUserGraduate,
  faBriefcase,
  faUsers,
  faComment,
  faBell,
  faSchool,
  faBuildingColumns,
  faLandmark,
  faPenToSquare,
  faFlask,
  faHelmetSafety,
  faBuildingFlag,
  faEarthAsia,
  faLaptopCode,
  faClipboardCheck,
  faCalendarDays,
  faMessage,
  faUser,
  faHashtag,
  faClock,
  faFileAlt,
  faSearch,
  faChevronRight,
  faTimes,
)

const authStore = useAuthStore()
const notificationStore = useNotificationStore()
const searchStore = useSearchStore()
const feedStore = useFeedStore()
const groupStore = useGroupStore()
const postsStore = usePostsStore()
const router = useRouter()
const route = useRoute()

const { unreadCount } = storeToRefs(notificationStore)
const { currentUser } = storeToRefs(authStore)
const { userResults, isLoadingUsers } = storeToRefs(searchStore)

const { isLoadingSearchResults: isLoadingPosts } = storeToRefs(feedStore)
const postResultIds = computed(() => feedStore.searchResultPostIds)
const postResults = computed(() => postsStore.getPostsByIds(postResultIds.value))

const { groupSearchResults: groupResults, isLoadingGroupSearch } = storeToRefs(groupStore)

const searchQuery = ref('')
const showSearchDropdown = ref(false)
const searchContainerRef = ref<HTMLDivElement | null>(null)

// --- State for the new Profile Dropdown ---
const isProfileMenuOpen = ref(false)
const isExploreMenuOpen = ref(false)
const isSeekersMenuOpen = ref(false)
const isMobileMenuOpen = ref(false)
const profileMenuRef = ref<HTMLDivElement | null>(null)
const exploreMenuRef = ref<HTMLDivElement | null>(null)
const seekersMenuRef = ref<HTMLDivElement | null>(null)
const mobileMenuRef = ref<HTMLDivElement | null>(null)

// --- NEW: Mobile search state ---
const showMobileSearch = ref(false)
const mobileSearchInputRef = ref<HTMLInputElement | null>(null)

// --- Notification bell animation state ---
const isBellRinging = ref(false)
let bellInterval: number | null = null

// Check if we're on the current user's profile page
const isOnOwnProfilePage = computed(() => {
  return route.name === 'profile' && route.params.username === currentUser.value?.username
})

const hasAnyResults = computed(
  () =>
    userResults.value.length > 0 || postResults.value.length > 0 || groupResults.value.length > 0,
)
const isSearching = computed(
  () => isLoadingUsers.value || isLoadingPosts.value || isLoadingGroupSearch.value,
)

// --- Notification bell animation functions ---
const startBellAnimation = () => {
  if (bellInterval) return

  bellInterval = window.setInterval(() => {
    if (unreadCount.value > 0) {
      isBellRinging.value = true
      setTimeout(() => {
        isBellRinging.value = false
      }, 1000)
    }
  }, 3000)
}

const stopBellAnimation = () => {
  if (bellInterval) {
    window.clearInterval(bellInterval)
    bellInterval = null
  }
  isBellRinging.value = false
}

// Start/stop bell animation based on unread count
watch(unreadCount, (newCount) => {
  if (newCount > 0) {
    startBellAnimation()
  } else {
    stopBellAnimation()
  }
})

// Stop animation when component unmounts
onUnmounted(() => {
  stopBellAnimation()
  document.removeEventListener('click', closeSearchDropdownOnClickOutside)
  document.removeEventListener('click', closeAllMenusOnClickOutside)
  document.removeEventListener('click', closeMobileMenuOnClickOutside)
  document.body.style.overflow = ''
})

function handleLogoClick(event: MouseEvent) {
  if (route.path === '/') {
    event.preventDefault()
    eventBus.emit('scroll-to-top')
  }
  isMobileMenuOpen.value = false
  closeMobileSearch()
}

function handleProfileClick(event: MouseEvent) {
  if (
    currentUser.value?.username &&
    route.name === 'profile' &&
    route.params.username === currentUser.value.username
  ) {
    event.preventDefault()
    eventBus.emit('scroll-profile-to-top')
  }
  isProfileMenuOpen.value = false
  isMobileMenuOpen.value = false
  closeMobileSearch()
}

function handleNotificationsClick(event: MouseEvent) {
  if (route.name === 'notifications') {
    event.preventDefault()
    eventBus.emit('scroll-notifications-to-top')
  }
  isMobileMenuOpen.value = false
  closeMobileSearch()

  stopBellAnimation()
  if (unreadCount.value > 0) {
    setTimeout(() => {
      startBellAnimation()
    }, 10000)
  }
}

const handleNonNavigableClick = (event: MouseEvent) => {
  event.preventDefault()
  event.stopPropagation()
  closeMobileSearch()
}

const handleFullSearchSubmit = () => {
  if (searchQuery.value.trim()) {
    showSearchDropdown.value = false
    router.push({ name: 'search', query: { q: searchQuery.value.trim() } })
  }
  isMobileMenuOpen.value = false
  closeMobileSearch()
}

const debouncedSearch = debounce(async (query: string) => {
  if (query.length < 1) {
    searchStore.clearSearch()
    feedStore.searchResultPostIds = []
    groupStore.groupSearchResults = []
    return
  }
  await Promise.all([
    searchStore.searchUsers(query),
    feedStore.searchPosts(query),
    groupStore.searchGroups(query),
  ])
}, 300)

const handleSearchInput = () => {
  if (searchQuery.value.trim()) {
    showSearchDropdown.value = true
    debouncedSearch(searchQuery.value)
  } else {
    showSearchDropdown.value = false
    searchStore.clearSearch()
    feedStore.searchResultPostIds = []
    groupStore.groupSearchResults = []
  }
}

const selectUserAndNavigate = (user: User) => {
  showSearchDropdown.value = false
  searchQuery.value = ''
  router.push({ name: 'profile', params: { username: user.username } })
  isMobileMenuOpen.value = false
  closeMobileSearch()
}

const selectPostAndNavigate = (post: Post) => {
  showSearchDropdown.value = false
  searchQuery.value = ''
  router.push({ name: 'single-post', params: { postId: post.id } })
  isMobileMenuOpen.value = false
  closeMobileSearch()
}

const closeSearchDropdownOnClickOutside = (event: MouseEvent) => {
  if (searchContainerRef.value && !searchContainerRef.value.contains(event.target as Node)) {
    showSearchDropdown.value = false
  }
}

const closeMobileMenuOnClickOutside = (event: MouseEvent) => {
  if (mobileMenuRef.value && !mobileMenuRef.value.contains(event.target as Node)) {
    isMobileMenuOpen.value = false
  }
}

const closeAllMenusOnClickOutside = (event: MouseEvent) => {
  if (profileMenuRef.value && !profileMenuRef.value.contains(event.target as Node)) {
    isProfileMenuOpen.value = false
  }
  if (exploreMenuRef.value && !exploreMenuRef.value.contains(event.target as Node)) {
    isExploreMenuOpen.value = false
  }
  if (seekersMenuRef.value && !seekersMenuRef.value.contains(event.target as Node)) {
    isSeekersMenuOpen.value = false
  }
  if (mobileMenuRef.value && !mobileMenuRef.value.contains(event.target as Node)) {
    isMobileMenuOpen.value = false
  }
}

// NEW: Toggle mobile search
const toggleMobileSearch = () => {
  showMobileSearch.value = !showMobileSearch.value
  if (showMobileSearch.value) {
    // Focus the input when search opens
    setTimeout(() => {
      mobileSearchInputRef.value?.focus()
    }, 100)
  } else {
    // Clear search when closing
    searchQuery.value = ''
    showSearchDropdown.value = false
    searchStore.clearSearch()
    feedStore.searchResultPostIds = []
    groupStore.groupSearchResults = []
  }
}

// NEW: Close mobile search
const closeMobileSearch = () => {
  showMobileSearch.value = false
  searchQuery.value = ''
  showSearchDropdown.value = false
  searchStore.clearSearch()
  feedStore.searchResultPostIds = []
  groupStore.groupSearchResults = []
}

// NEW: Clear search input
const handleClearSearch = () => {
  searchQuery.value = ''
  showSearchDropdown.value = false
}

watch(showSearchDropdown, (isOpen) => {
  if (isOpen) document.addEventListener('click', closeSearchDropdownOnClickOutside)
  else document.removeEventListener('click', closeSearchDropdownOnClickOutside)
})

watch(isMobileMenuOpen, (isOpen) => {
  if (isOpen) {
    document.addEventListener('click', closeMobileMenuOnClickOutside)
    document.body.style.overflow = 'hidden'
  } else {
    document.removeEventListener('click', closeMobileMenuOnClickOutside)
    document.body.style.overflow = ''
  }
})

watch([isProfileMenuOpen, isExploreMenuOpen, isSeekersMenuOpen, isMobileMenuOpen], (menus) => {
  if (menus.some((menu) => menu)) {
    document.addEventListener('click', closeAllMenusOnClickOutside)
  } else {
    document.removeEventListener('click', closeAllMenusOnClickOutside)
  }
})

onMounted(() => {
  authStore.initializeAuth()
  if (unreadCount.value > 0) {
    startBellAnimation()
  }
})

const handleLogout = async () => {
  await authStore.logout()
  isMobileMenuOpen.value = false
  closeMobileSearch()
}

const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
  closeMobileSearch()
}

const handleMobileMenuClick = () => {
  // Only close the menu if it's a navigation item, not when toggling submenus
}

const toggleExploreSubmenu = (event: Event) => {
  event.stopPropagation()
  isExploreMenuOpen.value = !isExploreMenuOpen.value
}

const toggleSeekersSubmenu = (event: Event) => {
  event.stopPropagation()
  isSeekersMenuOpen.value = !isSeekersMenuOpen.value
}

const handleMobileNavigation = () => {
  isMobileMenuOpen.value = false
  closeMobileSearch()
}

const handleProfileNavigation = () => {
  isMobileMenuOpen.value = false
  closeMobileSearch()
  if (currentUser.value?.username) {
    router.push({ name: 'profile', params: { username: currentUser.value.username } })
  }
}

const handleProfileImageClick = (event: MouseEvent) => {
  if (isProfileMenuOpen.value) {
    isProfileMenuOpen.value = false
    return
  }

  if (
    currentUser.value?.username &&
    route.name === 'profile' &&
    route.params.username === currentUser.value.username
  ) {
    event.preventDefault()
    eventBus.emit('scroll-profile-to-top')
  } else if (currentUsername.value) {
    router.push({ name: 'profile', params: { username: currentUsername.value } })
  }

  isProfileMenuOpen.value = false
  closeMobileSearch()
}

const currentUsername = computed(() => currentUser.value?.username || '')
</script>

<template>
  <header
    class="bg-white shadow-sm flex-shrink-0 z-40 fixed top-0 left-0 w-full"
    style="height: 70px"
  >
    <nav class="mx-auto max-w-7xl h-full px-4 sm:px-5 lg:px-6">
      <div class="flex items-center justify-between h-full">
        <!-- Logo and Search Container -->
        <div class="flex items-center flex-1">
          <div class="flex-shrink-0 ml-2 sm:ml-3 lg:ml-4">
            <RouterLink
              to="/"
              @click="handleLogoClick"
              data-cy="navbar-logo-link"
              class="text-2xl font-bold tracking-tight transition-all duration-200 rounded-lg px-3 py-2"
            >
              <span
                class="bg-gradient-to-r from-blue-600 to-purple-500 bg-clip-text text-transparent"
                >NxtTurn</span
              >
            </RouterLink>
          </div>

          <!-- Desktop Search - Hidden on mobile -->
          <div
            class="hidden md:flex flex-grow justify-start px-3 sm:px-4 ml-2 sm:ml-3 lg:ml-4"
            ref="searchContainerRef"
          >
            <div class="relative w-full max-w-md">
              <form @submit.prevent="handleFullSearchSubmit" v-if="authStore.isAuthenticated">
                <input
                  data-cy="global-search-input"
                  type="text"
                  v-model="searchQuery"
                  @input="handleSearchInput"
                  @focus="handleSearchInput"
                  placeholder="Search for users or content..."
                  class="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-full bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition"
                />
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg
                    class="h-5 w-5 text-gray-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    />
                  </svg>
                </div>
              </form>

              <!-- Search Dropdown - Made more compact -->
              <div
                v-if="showSearchDropdown && searchQuery"
                class="absolute top-full mt-2 w-full rounded-lg shadow-lg bg-white border border-gray-200 z-50 search-dropdown compact-search-dropdown"
              >
                <div class="py-1">
                  <!-- Loading State -->
                  <div
                    v-if="isSearching"
                    class="px-3 py-2 flex items-center gap-2 text-sm text-gray-600"
                  >
                    <div
                      class="w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"
                    ></div>
                    <div class="flex-1 min-w-0">
                      <p class="font-medium text-gray-800 text-sm">Searching...</p>
                      <p class="text-xs text-gray-500 break-words">
                        Looking for "{{ searchQuery }}"
                      </p>
                    </div>
                  </div>

                  <!-- No Results State -->
                  <div v-else-if="!isSearching && !hasAnyResults" class="px-3 py-4 text-center">
                    <div
                      class="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center mb-2 mx-auto"
                    >
                      <font-awesome-icon :icon="['fas', 'search']" class="text-gray-400 text-sm" />
                    </div>
                    <p class="font-medium text-gray-700 text-sm mb-1">No results found</p>
                    <p class="text-xs text-gray-500">Try different keywords</p>
                  </div>

                  <!-- Users Results -->
                  <template v-if="userResults.length > 0">
                    <div class="px-3 py-1.5 border-b border-gray-100">
                      <div
                        class="flex items-center gap-2 text-xs font-semibold text-gray-600 uppercase tracking-wide"
                      >
                        <font-awesome-icon :icon="['fas', 'user']" class="text-blue-500 text-xs" />
                        <span>Users</span>
                      </div>
                    </div>
                    <div v-for="user in userResults.slice(0, 2)" :key="`user-${user.id}`">
                      <a
                        @click.prevent="selectUserAndNavigate(user)"
                        href="#"
                        class="flex items-center gap-2 px-3 py-2 text-sm hover:bg-blue-50 transition-all duration-200 group"
                      >
                        <div class="relative flex-shrink-0">
                          <img
                            :src="getAvatarUrl(user.picture, user.first_name, user.last_name)"
                            alt="avatar"
                            class="w-7 h-7 rounded-full object-cover border border-gray-200 group-hover:border-blue-300 transition-colors"
                          />
                        </div>
                        <div class="flex-1 min-w-0">
                          <p class="font-medium text-gray-900 text-sm truncate break-all">
                            {{ user.first_name }} {{ user.last_name }}
                          </p>
                          <p class="text-xs text-gray-500 truncate break-all">
                            @{{ user.username }}
                          </p>
                        </div>
                        <font-awesome-icon
                          :icon="['fas', 'chevron-right']"
                          class="text-gray-300 text-xs opacity-0 group-hover:opacity-100 group-hover:text-blue-500 transition-all duration-200 flex-shrink-0"
                        />
                      </a>
                    </div>
                  </template>

                  <!-- Groups Results -->
                  <template v-if="groupResults.length > 0">
                    <div class="px-3 py-1.5 border-b border-gray-100 mt-0.5">
                      <div
                        class="flex items-center gap-2 text-xs font-semibold text-gray-600 uppercase tracking-wide"
                      >
                        <font-awesome-icon
                          :icon="['fas', 'users']"
                          class="text-purple-500 text-xs"
                        />
                        <span>Groups</span>
                      </div>
                    </div>
                    <div v-for="group in groupResults.slice(0, 2)" :key="`group-${group.id}`">
                      <router-link
                        :to="{ name: 'group-detail', params: { slug: group.slug } }"
                        @click="showSearchDropdown = false"
                        class="flex items-center gap-2 px-3 py-2 text-sm hover:bg-purple-50 transition-all duration-200 group"
                      >
                        <div
                          class="w-7 h-7 bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0 group-hover:bg-purple-600 transition-colors"
                        >
                          <font-awesome-icon :icon="['fas', 'users']" class="text-white text-xs" />
                        </div>
                        <div class="flex-1 min-w-0">
                          <p class="font-medium text-gray-900 text-sm truncate break-all">
                            {{ group.name }}
                          </p>
                          <p class="text-xs text-gray-500 truncate break-all">{{ group.slug }}</p>
                        </div>
                        <font-awesome-icon
                          :icon="['fas', 'chevron-right']"
                          class="text-gray-300 text-xs opacity-0 group-hover:opacity-100 group-hover:text-purple-500 transition-all duration-200 flex-shrink-0"
                        />
                      </router-link>
                    </div>
                  </template>

                  <!-- Posts Results -->
                  <template v-if="postResults.length > 0">
                    <div class="px-3 py-1.5 border-b border-gray-100 mt-0.5">
                      <div
                        class="flex items-center gap-2 text-xs font-semibold text-gray-600 uppercase tracking-wide"
                      >
                        <font-awesome-icon
                          :icon="['fas', 'file-alt']"
                          class="text-green-500 text-xs"
                        />
                        <span>Posts</span>
                      </div>
                    </div>
                    <div v-for="post in postResults.slice(0, 2)" :key="`post-${post.id}`">
                      <a
                        @click.prevent="selectPostAndNavigate(post)"
                        href="#"
                        class="flex items-center gap-2 px-3 py-2 text-sm hover:bg-green-50 transition-all duration-200 group"
                      >
                        <div
                          class="w-7 h-7 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0 group-hover:bg-green-600 transition-colors"
                        >
                          <font-awesome-icon
                            :icon="['fas', 'file-alt']"
                            class="text-white text-xs"
                          />
                        </div>
                        <div class="flex-1 min-w-0">
                          <p class="text-gray-900 text-sm leading-snug line-clamp-2 break-words">
                            {{ post.content || post.title }}
                          </p>
                          <p class="text-xs text-gray-500 mt-0.5">
                            {{
                              post.created_at
                                ? new Date(post.created_at).toLocaleDateString()
                                : 'Recent'
                            }}
                          </p>
                        </div>
                        <font-awesome-icon
                          :icon="['fas', 'chevron-right']"
                          class="text-gray-300 text-xs opacity-0 group-hover:opacity-100 group-hover:text-green-500 transition-all duration-200 flex-shrink-0"
                        />
                      </a>
                    </div>
                  </template>

                  <!-- See All Results -->
                  <div v-if="!isSearching && hasAnyResults" class="border-t border-gray-100">
                    <button
                      @click="handleFullSearchSubmit"
                      class="w-full text-left px-3 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 transition-all duration-200 flex items-center justify-between group"
                    >
                      <div class="flex items-center gap-2 flex-1 min-w-0">
                        <font-awesome-icon
                          :icon="['fas', 'search']"
                          class="text-blue-500 text-sm flex-shrink-0"
                        />
                        <span class="break-words truncate text-sm"
                          >See all results for "{{ searchQuery }}"</span
                        >
                      </div>
                      <font-awesome-icon
                        :icon="['fas', 'chevron-right']"
                        class="text-blue-400 text-xs group-hover:translate-x-0.5 transition-transform flex-shrink-0 ml-1"
                      />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Desktop Navigation - Hidden on mobile -->
        <div class="hidden md:flex items-center gap-1 lg:gap-2 flex-shrink-0 mr-2 sm:mr-3 lg:mr-4">
          <template v-if="authStore.isAuthenticated && currentUser">
            <!-- EXPLORE with dropdown -->
            <div class="relative group" ref="exploreMenuRef">
              <button
                type="button"
                @click="isExploreMenuOpen = !isExploreMenuOpen"
                class="nav-btn group relative flex flex-col items-center justify-center gap-0 focus-ring min-w-[50px] lg:min-w-[60px]"
                :class="{
                  'active-explore': isExploreMenuOpen,
                  'hover:bg-explore-hover': !isExploreMenuOpen,
                }"
                aria-label="Explore"
                aria-haspopup="true"
                :aria-expanded="isExploreMenuOpen"
              >
                <font-awesome-icon
                  :icon="['fas', 'compass']"
                  class="icon icon-explore icon-fa"
                  aria-hidden="true"
                />
                <span class="nav-label nav-label-explore">Explore</span>
              </button>

              <!-- Explore Dropdown -->
              <div
                v-if="isExploreMenuOpen"
                class="menu-panel absolute left-1/2 z-50 mt-2 w-72 -translate-x-1/2 overflow-hidden rounded-xl bg-white shadow-lg border border-gray-200"
                role="menu"
                aria-label="Explore menu"
              >
                <ul class="divide-y divide-gray-100 text-sm">
                  <li>
                    <a class="menu-item hover:bg-blue-50" href="#"
                      ><font-awesome-icon :icon="['fas', 'school']" class="menu-ico" /><span
                        >Schools</span
                      ></a
                    >
                  </li>
                  <li>
                    <a class="menu-item hover:bg-blue-50" href="#"
                      ><font-awesome-icon
                        :icon="['fas', 'building-columns']"
                        class="menu-ico"
                      /><span>Institutes</span></a
                    >
                  </li>
                  <li>
                    <a class="menu-item hover:bg-blue-50" href="#"
                      ><font-awesome-icon :icon="['fas', 'briefcase']" class="menu-ico" /><span
                        >Enterprises</span
                      ></a
                    >
                  </li>
                  <li>
                    <a class="menu-item hover:bg-blue-50" href="#"
                      ><font-awesome-icon :icon="['fas', 'landmark']" class="menu-ico" /><span
                        >Government Enterprises</span
                      ></a
                    >
                  </li>
                  <li>
                    <a class="menu-item hover:bg-blue-50" href="#"
                      ><font-awesome-icon :icon="['fas', 'pen-to-square']" class="menu-ico" /><span
                        >Exams</span
                      ></a
                    >
                  </li>
                  <li class="pl-10 pr-4 py-2 flex gap-2">
                    <a
                      class="text-[13px] px-2 py-1 rounded hover:bg-green-100 text-green-600"
                      href="#"
                      ><font-awesome-icon :icon="['fas', 'clipboard-check']" class="mr-1" />Mock
                      Test</a
                    >
                    <a
                      class="text-[13px] px-2 py-1 rounded hover:bg-green-100 text-green-600"
                      href="#"
                      ><font-awesome-icon
                        :icon="['fas', 'calendar-days']"
                        class="mr-1"
                      />Calendar</a
                    >
                  </li>
                  <li>
                    <a class="menu-item hover:bg-blue-50" href="#"
                      ><font-awesome-icon :icon="['fas', 'flask']" class="menu-ico" /><span
                        >Research</span
                      ></a
                    >
                  </li>
                </ul>
              </div>
            </div>

            <!-- SEEKERS with dropdown -->
            <div class="relative group" ref="seekersMenuRef">
              <button
                type="button"
                @click="isSeekersMenuOpen = !isSeekersMenuOpen"
                class="nav-btn group relative flex flex-col items-center justify-center gap-0 focus-ring min-w-[50px] lg:min-w-[60px]"
                :class="{
                  'active-seekers': isSeekersMenuOpen,
                  'hover:bg-seekers-hover': !isSeekersMenuOpen,
                }"
                aria-label="Seekers"
                aria-haspopup="true"
                :aria-expanded="isSeekersMenuOpen"
              >
                <font-awesome-icon
                  :icon="['fas', 'user-graduate']"
                  class="icon icon-seekers icon-fa"
                  aria-hidden="true"
                />
                <span class="nav-label nav-label-seekers">Seekers</span>
              </button>

              <!-- Seekers Dropdown -->
              <div
                v-if="isSeekersMenuOpen"
                class="menu-panel absolute left-1/2 z-50 mt-2 w-72 -translate-x-1/2 overflow-hidden rounded-xl bg-white shadow-lg border border-gray-200"
                role="menu"
                aria-label="Seekers menu"
              >
                <ul class="divide-y divide-gray-100 text-sm">
                  <li>
                    <a class="menu-item hover:bg-pink-50" href="#"
                      ><font-awesome-icon :icon="['fas', 'user-graduate']" class="menu-ico" /><span
                        >Internship</span
                      ></a
                    >
                  </li>
                  <li>
                    <a class="menu-item hover:bg-pink-50" href="#"
                      ><font-awesome-icon :icon="['fas', 'helmet-safety']" class="menu-ico" /><span
                        >Apprenticeship</span
                      ></a
                    >
                  </li>
                  <li>
                    <a class="menu-item hover:bg-pink-50" href="#"
                      ><font-awesome-icon :icon="['fas', 'briefcase']" class="menu-ico" /><span
                        >Job</span
                      ></a
                    >
                  </li>
                  <li>
                    <a class="menu-item hover:bg-pink-50" href="#"
                      ><font-awesome-icon :icon="['fas', 'building-flag']" class="menu-ico" /><span
                        >Government Openings</span
                      ></a
                    >
                  </li>
                  <li>
                    <a class="menu-item hover:bg-pink-50" href="#"
                      ><font-awesome-icon :icon="['fas', 'earth-asia']" class="menu-ico" /><span
                        >International Govt. Openings</span
                      ></a
                    >
                  </li>
                  <li>
                    <a class="menu-item hover:bg-pink-50" href="#"
                      ><font-awesome-icon :icon="['fas', 'laptop-code']" class="menu-ico" /><span
                        >Freelances</span
                      ></a
                    >
                  </li>
                </ul>
              </div>
            </div>

            <!-- NETWORK -->
            <button
              type="button"
              @click="handleNonNavigableClick"
              class="nav-btn group relative flex flex-col items-center justify-center gap-0 focus-ring min-w-[50px] lg:min-w-[60px] hover:bg-network-hover"
              aria-label="My Network"
            >
              <font-awesome-icon
                :icon="['fas', 'users']"
                class="icon icon-network icon-fa"
                aria-hidden="true"
              />
              <span class="nav-label nav-label-network">Network</span>
            </button>

            <!-- MESSAGES (Now with color-filled solid icon and slightly bigger) -->
            <button
              type="button"
              @click="handleNonNavigableClick"
              class="nav-btn group relative flex flex-col items-center justify-center gap-0 focus-ring min-w-[50px] lg:min-w-[60px] hover:bg-messages-hover"
              aria-label="Messaging"
            >
              <ChatBubbleLeftRightIconSolid
                class="icon icon-messages icon-messages-solid"
                aria-hidden="true"
              />
              <span class="nav-label nav-label-messages">Messages</span>
              <span class="notification-badge" aria-label="3 unread messages">3</span>
            </button>

            <!-- NOTIFICATIONS -->
            <RouterLink
              :to="{ name: 'notifications' }"
              @click="handleNotificationsClick"
              data-cy="navbar-notifications-link"
              class="nav-btn group relative flex flex-col items-center justify-center gap-0 focus-ring min-w-[50px] lg:min-w-[60px] hover:bg-notifications-hover"
              aria-label="Notifications"
            >
              <!-- Bell animation wrapper -->
              <div
                :class="{ 'animate__animated animate__swing': isBellRinging }"
                class="bell-animation-container"
              >
                <font-awesome-icon
                  :icon="['fas', 'bell']"
                  class="icon icon-notifications icon-fa"
                  aria-hidden="true"
                />
              </div>
              <span class="nav-label nav-label-notifications">Alerts</span>
              <span
                v-if="unreadCount > 0"
                data-cy="notification-indicator"
                class="notification-badge"
                aria-label="12 notifications"
              >
                {{ unreadCount > 9 ? '9+' : unreadCount }}
              </span>
            </RouterLink>

            <!-- Separator -->
            <div class="mx-1 h-6 w-px bg-gray-300"></div>

            <!-- PROFILE - Adjusted positioning -->
            <div class="relative profile-container" ref="profileMenuRef">
              <div class="flex items-center profile-inner-container">
                <!-- Profile Image Button -->
                <button
                  v-if="currentUsername"
                  @click="handleProfileImageClick"
                  data-cy="profile-link"
                  class="rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all duration-200 profile-image-btn"
                  :class="{ 'profile-on-page': isOnOwnProfilePage }"
                >
                  <span class="sr-only">View your profile</span>
                  <img
                    :src="
                      getAvatarUrl(
                        currentUser?.picture,
                        currentUser?.first_name,
                        currentUser?.last_name,
                      )
                    "
                    alt="Your avatar"
                    class="h-9 w-9 rounded-full object-cover transition-all duration-200 profile-avatar"
                    :class="{ 'profile-on-page': isOnOwnProfilePage }"
                    data-cy="navbar-avatar-main"
                  />
                </button>

                <button
                  @click="isProfileMenuOpen = !isProfileMenuOpen"
                  type="button"
                  data-cy="profile-menu-button"
                  class="ml-1 p-1 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-200 profile-menu-toggle"
                  :class="{
                    'rotate-180 bg-blue-50 text-blue-600': isProfileMenuOpen,
                    'hover:bg-gray-100': !isProfileMenuOpen,
                  }"
                >
                  <span class="sr-only">Open user menu</span>
                  <ChevronDownIcon
                    class="h-5 w-5 transition-all duration-200"
                    :class="
                      isProfileMenuOpen ? 'text-blue-600' : 'text-gray-500 hover:text-gray-700'
                    "
                  />
                </button>
              </div>

              <transition
                enter-active-class="transition ease-out duration-100"
                enter-from-class="transform opacity-0 scale-95"
                enter-to-class="transform opacity-100 scale-100"
                leave-active-class="transition ease-in duration-75"
                leave-from-class="transform opacity-100 scale-100"
                leave-to-class="transform opacity-0 scale-95"
              >
                <div
                  v-if="isProfileMenuOpen && currentUser"
                  class="profile-dropdown absolute right-0 z-50 mt-4 w-72 origin-top-right rounded-xl bg-white py-2 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none border border-gray-200"
                >
                  <!-- User Info Header -->
                  <div
                    class="px-4 py-3 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50"
                  >
                    <div class="flex items-center gap-3">
                      <img
                        :src="
                          getAvatarUrl(
                            currentUser.picture,
                            currentUser.first_name,
                            currentUser.last_name,
                          )
                        "
                        alt="Your avatar"
                        class="h-12 w-12 rounded-full object-cover ring-2 ring-white shadow-sm"
                        data-cy="navbar-avatar-dropdown"
                      />
                      <div>
                        <p class="text-sm font-semibold text-gray-800">
                          {{ currentUser.first_name }} {{ currentUser.last_name }}
                        </p>
                        <p class="text-xs text-gray-600">@{{ currentUser.username }}</p>
                        <p class="text-xs text-amber-600 font-medium mt-0.5">Premium Member</p>
                      </div>
                    </div>
                  </div>

                  <!-- Menu Items with color-filled icons -->
                  <div class="py-1">
                    <a
                      href="#"
                      class="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-blue-50 transition-colors group"
                    >
                      <Cog6ToothIconSolid class="h-5 w-5 text-blue-600 group-hover:text-blue-700" />
                      <span class="font-medium">Settings & Privacy</span>
                    </a>
                    <a
                      href="#"
                      class="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-green-50 transition-colors group"
                    >
                      <QuestionMarkCircleIconSolid
                        class="h-5 w-5 text-green-600 group-hover:text-green-700"
                      />
                      <span class="font-medium">Help & Support</span>
                    </a>
                    <a
                      href="#"
                      class="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-purple-50 transition-colors group"
                    >
                      <EyeIconSolid class="h-5 w-5 text-purple-600 group-hover:text-purple-700" />
                      <span class="font-medium">Display & Accessibility</span>
                    </a>
                    <a
                      href="#"
                      class="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-blue-50 transition-colors group"
                    >
                      <!-- Give Feedback icon made smaller -->
                      <font-awesome-icon
                        :icon="['fas', 'message']"
                        class="h-4 w-4 text-amber-600 group-hover:text-amber-700 give-feedback-icon"
                      />
                      <span class="font-medium">Give Feedback</span>
                    </a>
                  </div>

                  <!-- Dark Mode -->
                  <div class="py-1 border-t border-gray-200">
                    <div
                      class="flex items-center justify-between px-4 py-2.5 text-sm text-gray-700 hover:bg-indigo-50 transition-colors group"
                    >
                      <div class="flex items-center gap-3">
                        <MoonIconSolid
                          class="h-5 w-5 text-indigo-600 group-hover:text-indigo-700"
                        />
                        <span class="font-medium">Dark Mode</span>
                      </div>
                      <button
                        type="button"
                        class="bg-gray-200 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 group-hover:bg-gray-300"
                        role="switch"
                        aria-checked="false"
                      >
                        <span
                          class="pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out translate-x-0"
                        ></span>
                      </button>
                    </div>
                  </div>

                  <!-- Logout -->
                  <div class="py-1 border-t border-gray-200">
                    <button
                      @click="handleLogout"
                      data-cy="logout-button"
                      class="w-full text-left flex items-center gap-3 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 transition-colors group"
                    >
                      <ArrowLeftOnRectangleIconSolid class="h-5 w-5 group-hover:text-red-700" />
                      <span class="font-medium">Log Out</span>
                    </button>
                  </div>
                </div>
              </transition>
            </div>
          </template>
          <template v-else>
            <RouterLink
              to="/login"
              class="text-sm font-medium text-gray-600 hover:text-indigo-500 mr-2"
              >Login</RouterLink
            >
          </template>
        </div>

        <!-- Mobile menu button and search icon - Visible only on mobile -->
        <div class="md:hidden flex items-center mr-2" ref="mobileMenuRef">
          <template v-if="authStore.isAuthenticated && currentUser">
            <!-- Mobile Search Icon -->
            <button
              v-show="!showMobileSearch && !isMobileMenuOpen"
              @click="toggleMobileSearch"
              class="mobile-search-toggle p-3 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center outline-none border-none mr-2"
              aria-label="Open search"
            >
              <font-awesome-icon :icon="['fas', 'search']" class="h-5 w-5" />
            </button>

            <button
              v-show="!isMobileMenuOpen"
              @click="toggleMobileMenu"
              class="mobile-toggle-btn p-3 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center outline-none border-none"
              aria-label="Toggle mobile menu"
            >
              <Bars3Icon class="h-6 w-6" />
            </button>

            <!-- Mobile Search Close Icon (when search is open) -->
            <button
              v-if="showMobileSearch"
              @click="toggleMobileSearch"
              class="mobile-search-close p-3 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center outline-none border-none"
              aria-label="Close search"
            >
              <font-awesome-icon :icon="['fas', 'times']" class="h-5 w-5" />
            </button>
          </template>
          <template v-else>
            <RouterLink
              to="/login"
              class="text-sm font-medium text-gray-600 hover:text-indigo-500 px-3 py-2"
              >Login</RouterLink
            >
          </template>
        </div>
      </div>

      <!-- Mobile Search Bar (appears below navbar when search icon is clicked) -->
      <transition
        enter-active-class="transform transition-all duration-300 ease-in-out"
        enter-from-class="opacity-0 -translate-y-4"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transform transition-all duration-300 ease-in-out"
        leave-from-class="opacity-100 translate-y-0"
        leave-to-class="opacity-0 -translate-y-4"
      >
        <div
          v-if="showMobileSearch && authStore.isAuthenticated"
          class="md:hidden absolute top-full left-0 right-0 bg-white border-t border-gray-200 shadow-lg z-40"
        >
          <div class="p-3" ref="searchContainerRef">
            <div class="relative">
              <form @submit.prevent="handleFullSearchSubmit">
                <input
                  ref="mobileSearchInputRef"
                  type="text"
                  v-model="searchQuery"
                  @input="handleSearchInput"
                  @focus="handleSearchInput"
                  placeholder="Search for users or content..."
                  class="w-full pl-10 pr-10 py-3 border border-gray-300 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition"
                />
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <font-awesome-icon :icon="['fas', 'search']" class="h-5 w-5 text-gray-400" />
                </div>
                <button
                  v-if="searchQuery"
                  @click="handleClearSearch"
                  type="button"
                  class="absolute inset-y-0 right-0 pr-3 flex items-center"
                  aria-label="Clear search"
                >
                  <font-awesome-icon
                    :icon="['fas', 'times']"
                    class="h-5 w-5 text-gray-400 hover:text-gray-600"
                  />
                </button>
              </form>

              <!-- Mobile Search Dropdown -->
              <div
                v-if="showSearchDropdown && searchQuery"
                class="absolute top-full mt-1 w-full rounded-lg shadow-lg bg-white border border-gray-200 z-50 max-h-[60vh] overflow-y-auto custom-scrollbar"
              >
                <div class="py-1">
                  <!-- Loading State -->
                  <div
                    v-if="isSearching"
                    class="px-3 py-3 flex items-center gap-2 text-sm text-gray-600"
                  >
                    <div
                      class="w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"
                    ></div>
                    <div class="flex-1 min-w-0">
                      <p class="font-medium text-gray-800 text-sm">Searching...</p>
                      <p class="text-xs text-gray-500 break-words">
                        Looking for "{{ searchQuery }}"
                      </p>
                    </div>
                  </div>

                  <!-- No Results State -->
                  <div v-else-if="!isSearching && !hasAnyResults" class="px-3 py-4 text-center">
                    <div
                      class="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center mb-2 mx-auto"
                    >
                      <font-awesome-icon :icon="['fas', 'search']" class="text-gray-400 text-sm" />
                    </div>
                    <p class="font-medium text-gray-700 text-sm mb-1">No results found</p>
                    <p class="text-xs text-gray-500">Try different keywords</p>
                  </div>

                  <!-- Users Results -->
                  <template v-if="userResults.length > 0">
                    <div class="px-3 py-1.5 border-b border-gray-100">
                      <div
                        class="flex items-center gap-2 text-xs font-semibold text-gray-600 uppercase tracking-wide"
                      >
                        <font-awesome-icon :icon="['fas', 'user']" class="text-blue-500 text-xs" />
                        <span>Users</span>
                      </div>
                    </div>
                    <div v-for="user in userResults.slice(0, 3)" :key="`user-${user.id}`">
                      <a
                        @click.prevent="selectUserAndNavigate(user)"
                        href="#"
                        class="flex items-center gap-2 px-3 py-3 text-sm hover:bg-blue-50 transition-all duration-200 group border-b border-gray-100 last:border-b-0"
                      >
                        <div class="relative flex-shrink-0">
                          <img
                            :src="getAvatarUrl(user.picture, user.first_name, user.last_name)"
                            alt="avatar"
                            class="w-8 h-8 rounded-full object-cover border border-gray-200 group-hover:border-blue-300 transition-colors"
                          />
                        </div>
                        <div class="flex-1 min-w-0">
                          <p class="font-medium text-gray-900 text-sm truncate break-all">
                            {{ user.first_name }} {{ user.last_name }}
                          </p>
                          <p class="text-xs text-gray-500 truncate break-all">
                            @{{ user.username }}
                          </p>
                        </div>
                        <font-awesome-icon
                          :icon="['fas', 'chevron-right']"
                          class="text-gray-300 text-xs opacity-0 group-hover:opacity-100 group-hover:text-blue-500 transition-all duration-200 flex-shrink-0"
                        />
                      </a>
                    </div>
                  </template>

                  <!-- Groups Results -->
                  <template v-if="groupResults.length > 0">
                    <div class="px-3 py-1.5 border-b border-gray-100 mt-0.5">
                      <div
                        class="flex items-center gap-2 text-xs font-semibold text-gray-600 uppercase tracking-wide"
                      >
                        <font-awesome-icon
                          :icon="['fas', 'users']"
                          class="text-purple-500 text-xs"
                        />
                        <span>Groups</span>
                      </div>
                    </div>
                    <div v-for="group in groupResults.slice(0, 3)" :key="`group-${group.id}`">
                      <router-link
                        :to="{ name: 'group-detail', params: { slug: group.slug } }"
                        @click="showSearchDropdown = false"
                        closeMobileSearch()
                        class="flex items-center gap-2 px-3 py-3 text-sm hover:bg-purple-50 transition-all duration-200 group border-b border-gray-100 last:border-b-0"
                      >
                        <div
                          class="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0 group-hover:bg-purple-600 transition-colors"
                        >
                          <font-awesome-icon :icon="['fas', 'users']" class="text-white text-xs" />
                        </div>
                        <div class="flex-1 min-w-0">
                          <p class="font-medium text-gray-900 text-sm truncate break-all">
                            {{ group.name }}
                          </p>
                          <p class="text-xs text-gray-500 truncate break-all">{{ group.slug }}</p>
                        </div>
                        <font-awesome-icon
                          :icon="['fas', 'chevron-right']"
                          class="text-gray-300 text-xs opacity-0 group-hover:opacity-100 group-hover:text-purple-500 transition-all duration-200 flex-shrink-0"
                        />
                      </router-link>
                    </div>
                  </template>

                  <!-- Posts Results -->
                  <template v-if="postResults.length > 0">
                    <div class="px-3 py-1.5 border-b border-gray-100 mt-0.5">
                      <div
                        class="flex items-center gap-2 text-xs font-semibold text-gray-600 uppercase tracking-wide"
                      >
                        <font-awesome-icon
                          :icon="['fas', 'file-alt']"
                          class="text-green-500 text-xs"
                        />
                        <span>Posts</span>
                      </div>
                    </div>
                    <div v-for="post in postResults.slice(0, 3)" :key="`post-${post.id}`">
                      <a
                        @click.prevent="selectPostAndNavigate(post)"
                        href="#"
                        class="flex items-center gap-2 px-3 py-3 text-sm hover:bg-green-50 transition-all duration-200 group border-b border-gray-100 last:border-b-0"
                      >
                        <div
                          class="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0 group-hover:bg-green-600 transition-colors"
                        >
                          <font-awesome-icon
                            :icon="['fas', 'file-alt']"
                            class="text-white text-xs"
                          />
                        </div>
                        <div class="flex-1 min-w-0">
                          <p class="text-gray-900 text-sm leading-snug line-clamp-2 break-words">
                            {{ post.content || post.title }}
                          </p>
                          <p class="text-xs text-gray-500 mt-0.5">
                            {{
                              post.created_at
                                ? new Date(post.created_at).toLocaleDateString()
                                : 'Recent'
                            }}
                          </p>
                        </div>
                        <font-awesome-icon
                          :icon="['fas', 'chevron-right']"
                          class="text-gray-300 text-xs opacity-0 group-hover:opacity-100 group-hover:text-green-500 transition-all duration-200 flex-shrink-0"
                        />
                      </a>
                    </div>
                  </template>

                  <!-- See All Results -->
                  <div v-if="!isSearching && hasAnyResults" class="border-t border-gray-100">
                    <button
                      @click="handleFullSearchSubmit"
                      class="w-full text-left px-3 py-3 text-sm font-medium text-blue-600 hover:bg-blue-50 transition-all duration-200 flex items-center justify-between group"
                    >
                      <div class="flex items-center gap-2 flex-1 min-w-0">
                        <font-awesome-icon
                          :icon="['fas', 'search']"
                          class="text-blue-500 text-sm flex-shrink-0"
                        />
                        <span class="break-words truncate text-sm"
                          >See all results for "{{ searchQuery }}"</span
                        >
                      </div>
                      <font-awesome-icon
                        :icon="['fas', 'chevron-right']"
                        class="text-blue-400 text-xs group-hover:translate-x-0.5 transition-transform flex-shrink-0 ml-1"
                      />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </transition>

      <!-- Mobile Menu - Slides in from right -->
      <transition
        enter-active-class="transform transition ease-in-out duration-300"
        enter-from-class="translate-x-full"
        enter-to-class="translate-x-0"
        leave-active-class="transform transition ease-in-out duration-300"
        leave-from-class="translate-x-0"
        leave-to-class="translate-x-full"
      >
        <div
          v-if="isMobileMenuOpen && authStore.isAuthenticated && currentUser"
          class="md:hidden fixed inset-y-0 right-0 z-50 w-80 bg-white shadow-xl border-l border-gray-200 overflow-y-auto"
        >
          <!-- Close button at the top -->
          <div class="sticky top-0 bg-white z-10 border-b border-gray-200">
            <button
              @click="toggleMobileMenu"
              class="w-full flex justify-end p-3 text-gray-600 hover:bg-gray-100 transition-colors outline-none border-none"
              aria-label="Close menu"
            >
              <XMarkIcon class="h-5 w-5" />
            </button>
          </div>

          <div class="p-6 pt-4">
            <!-- User Info - Now Clickable -->
            <RouterLink
              v-if="currentUsername"
              :to="{ name: 'profile', params: { username: currentUsername } }"
              @click="handleProfileNavigation"
              class="flex items-center gap-4 pb-6 border-b border-gray-200 cursor-pointer hover:bg-gray-50 -m-3 p-3 rounded-lg transition-colors"
            >
              <img
                :src="
                  getAvatarUrl(currentUser.picture, currentUser.first_name, currentUser.last_name)
                "
                alt="Your avatar"
                class="w-12 h-12 rounded-full object-cover"
              />
              <div>
                <p class="font-semibold text-gray-900">
                  {{ currentUser.first_name }} {{ currentUser.last_name }}
                </p>
                <p class="text-sm text-gray-500">@{{ currentUser.username }}</p>
              </div>
            </RouterLink>

            <!-- All Navigation Items with Icons -->
            <nav class="py-4 space-y-2">
              <!-- Explore -->
              <button
                @click="toggleExploreSubmenu"
                class="w-full flex items-center justify-between p-3 rounded-lg hover:bg-explore-hover transition-colors"
              >
                <div class="flex items-center gap-3">
                  <font-awesome-icon :icon="['fas', 'compass']" class="icon-explore text-lg" />
                  <span class="font-medium text-gray-900">Explore</span>
                </div>
                <ChevronDownIcon
                  class="h-4 w-4 text-gray-500 transition-transform duration-200"
                  :class="{ 'rotate-180': isExploreMenuOpen }"
                />
              </button>

              <!-- Explore Submenu -->
              <div v-if="isExploreMenuOpen" class="ml-8 space-y-1">
                <a
                  @click="handleMobileNavigation"
                  class="flex items-center gap-3 py-2 px-3 text-sm text-gray-700 hover:bg-blue-50 rounded-lg"
                >
                  <font-awesome-icon :icon="['fas', 'school']" class="text-blue-500 text-sm" />
                  <span>Schools</span>
                </a>
                <a
                  @click="handleMobileNavigation"
                  class="flex items-center gap-3 py-2 px-3 text-sm text-gray-700 hover:bg-blue-50 rounded-lg"
                >
                  <font-awesome-icon
                    :icon="['fas', 'building-columns']"
                    class="text-blue-500 text-sm"
                  />
                  <span>Institutes</span>
                </a>
                <a
                  @click="handleMobileNavigation"
                  class="flex items-center gap-3 py-2 px-3 text-sm text-gray-700 hover:bg-blue-50 rounded-lg"
                >
                  <font-awesome-icon :icon="['fas', 'briefcase']" class="text-blue-500 text-sm" />
                  <span>Enterprises</span>
                </a>
                <a
                  @click="handleMobileNavigation"
                  class="flex items-center gap-3 py-2 px-3 text-sm text-gray-700 hover:bg-blue-50 rounded-lg"
                >
                  <font-awesome-icon :icon="['fas', 'landmark']" class="text-blue-500 text-sm" />
                  <span>Government Enterprises</span>
                </a>
                <a
                  @click="handleMobileNavigation"
                  class="flex items-center gap-3 py-2 px-3 text-sm text-gray-700 hover:bg-blue-50 rounded-lg"
                >
                  <font-awesome-icon
                    :icon="['fas', 'pen-to-square']"
                    class="text-blue-500 text-sm"
                  />
                  <span>Exams</span>
                </a>
                <a
                  @click="handleMobileNavigation"
                  class="flex items-center gap-3 py-2 px-3 text-sm text-gray-700 hover:bg-blue-50 rounded-lg"
                >
                  <font-awesome-icon :icon="['fas', 'flask']" class="text-blue-500 text-sm" />
                  <span>Research</span>
                </a>
              </div>

              <!-- Seekers -->
              <button
                @click="toggleSeekersSubmenu"
                class="w-full flex items-center justify-between p-3 rounded-lg hover:bg-seekers-hover transition-colors"
              >
                <div class="flex items-center gap-3">
                  <font-awesome-icon
                    :icon="['fas', 'user-graduate']"
                    class="icon-seekers text-lg"
                  />
                  <span class="font-medium text-gray-900">Seekers</span>
                </div>
                <ChevronDownIcon
                  class="h-4 w-4 text-gray-500 transition-transform duration-200"
                  :class="{ 'rotate-180': isSeekersMenuOpen }"
                />
              </button>

              <!-- Seekers Submenu -->
              <div v-if="isSeekersMenuOpen" class="ml-8 space-y-1">
                <a
                  @click="handleMobileNavigation"
                  class="flex items-center gap-3 py-2 px-3 text-sm text-gray-700 hover:bg-pink-50 rounded-lg"
                >
                  <font-awesome-icon
                    :icon="['fas', 'user-graduate']"
                    class="text-pink-500 text-sm"
                  />
                  <span>Internship</span>
                </a>
                <a
                  @click="handleMobileNavigation"
                  class="flex items-center gap-3 py-2 px-3 text-sm text-gray-700 hover:bg-pink-50 rounded-lg"
                >
                  <font-awesome-icon
                    :icon="['fas', 'helmet-safety']"
                    class="text-pink-500 text-sm"
                  />
                  <span>Apprenticeship</span>
                </a>
                <a
                  @click="handleMobileNavigation"
                  class="flex items-center gap-3 py-2 px-3 text-sm text-gray-700 hover:bg-pink-50 rounded-lg"
                >
                  <font-awesome-icon :icon="['fas', 'briefcase']" class="text-pink-500 text-sm" />
                  <span>Job</span>
                </a>
                <a
                  @click="handleMobileNavigation"
                  class="flex items-center gap-3 py-2 px-3 text-sm text-gray-700 hover:bg-pink-50 rounded-lg"
                >
                  <font-awesome-icon
                    :icon="['fas', 'building-flag']"
                    class="text-pink-500 text-sm"
                  />
                  <span>Government Openings</span>
                </a>
                <a
                  @click="handleMobileNavigation"
                  class="flex items-center gap-3 py-2 px-3 text-sm text-gray-700 hover:bg-pink-50 rounded-lg"
                >
                  <font-awesome-icon :icon="['fas', 'earth-asia']" class="text-pink-500 text-sm" />
                  <span>International Govt. Openings</span>
                </a>
                <a
                  @click="handleMobileNavigation"
                  class="flex items-center gap-3 py-2 px-3 text-sm text-gray-700 hover:bg-pink-50 rounded-lg"
                >
                  <font-awesome-icon :icon="['fas', 'laptop-code']" class="text-pink-500 text-sm" />
                  <span>Freelances</span>
                </a>
              </div>

              <!-- NETWORK -->
              <button
                @click="handleNonNavigableClick"
                class="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-network-hover transition-colors text-left"
              >
                <font-awesome-icon :icon="['fas', 'users']" class="icon-network text-lg" />
                <span class="font-medium text-gray-900">Network</span>
              </button>

              <!-- MESSAGES (Swapped in mobile too) -->
              <button
                @click="handleNonNavigableClick"
                class="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-messages-hover transition-colors text-left"
              >
                <ChatBubbleLeftRightIconSolid class="h-6 w-6 text-current" />
                <span class="font-medium text-gray-900">Messages</span>
                <span class="ml-auto bg-red-500 text-white text-xs px-2 py-1 rounded-full">3</span>
              </button>

              <!-- NOTIFICATIONS -->
              <RouterLink
                :to="{ name: 'notifications' }"
                @click="handleMobileNavigation"
                class="flex items-center gap-3 p-3 rounded-lg hover:bg-notifications-hover transition-colors"
              >
                <div :class="{ 'animate__animated animate__swing': isBellRinging }">
                  <font-awesome-icon :icon="['fas', 'bell']" class="icon-notifications text-lg" />
                </div>
                <span class="font-medium text-gray-900">Notifications</span>
                <span
                  v-if="unreadCount > 0"
                  class="ml-auto bg-red-500 text-white text-xs px-2 py-1 rounded-full"
                >
                  {{ unreadCount > 9 ? '9+' : unreadCount }}
                </span>
              </RouterLink>
            </nav>

            <!-- Settings & Logout -->
            <div class="pt-4 border-t border-gray-200 space-y-2">
              <a
                @click="handleMobileNavigation"
                class="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <Cog6ToothIcon class="h-5 w-5 text-gray-500" />
                <span class="font-medium text-gray-900">Settings</span>
              </a>
              <button
                @click="handleLogout"
                class="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-100 transition-colors text-red-600"
              >
                <ArrowLeftOnRectangleIcon class="h-5 w-5" />
                <span class="font-medium">Log Out</span>
              </button>
            </div>
          </div>
        </div>
      </transition>
    </nav>
  </header>
</template>

<style scoped>
/* Navigation Button Styles */
.nav-btn {
  padding: 0.5rem;
  border-radius: 10px;
  transition: all 0.2s ease;
  min-width: 50px;
  position: relative;
}

@media (min-width: 1024px) {
  .nav-btn {
    min-width: 60px;
  }
}

.nav-label {
  font-size: 11px;
  line-height: 1rem;
  color: #64748b;
  white-space: nowrap;
  transition: all 0.2s ease;
  font-weight: 500;
  margin-top: 2px;
}

/* Notification badges positioning */
.notification-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  background: #ef4444;
  color: #fff;
  border-radius: 9px;
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #fff;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

/* Profile container adjustments - Move profile icon up slightly */
.profile-container {
  margin-top: -3px !important; /* Move the entire profile section up */
}

/* Profile button positioning */
.profile-image-btn,
.profile-menu-toggle,
.profile-avatar {
  transform: translateY(-2px) !important; /* Move up slightly */
}

/* Remove blue ring when dropdown is open, add only when on profile page */
.profile-image-btn:not(.profile-on-page):focus,
.profile-image-btn:not(.profile-on-page):active {
  outline: none !important;
  box-shadow: none !important;
  ring-width: 0 !important;
}

/* Very thin blue ring only when on profile page */
.profile-on-page .profile-avatar {
  box-shadow: 0 0 0 1px #3b82f6; /* Very thin blue ring */
}

/* Profile dropdown - Move it up slightly */
.profile-dropdown {
  margin-top: 18px !important; /* Reduced from 24px to 18px */
  box-shadow: 0 20px 40px rgba(2, 6, 23, 0.15);
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
}

/* Bell animation container */
.bell-animation-container {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Icon adjustments */
.icon-explore,
.icon-seekers,
.icon-network,
.icon-notifications {
  font-size: 20px !important;
  margin-bottom: 2px;
}

/* Messages icon (now using solid HeroIcon) - Made slightly bigger */
.icon-messages-solid {
  width: 22px !important; /* Slightly bigger than other icons */
  height: 22px !important;
  margin-bottom: 2px;
  color: #3dcb38 !important; /* Original green color */
}

/* Hover effect for messages icon */
.nav-btn:hover .icon-messages-solid {
  color: #1aac15 !important; /* Darker green on hover */
}

/* Give Feedback icon in profile dropdown - Made smaller */
.give-feedback-icon {
  width: 16px !important;
  height: 16px !important;
}

.flex.items-center.gap-2.flex-shrink-0 {
  column-gap: 0.5rem !important;
}

@media (min-width: 1024px) {
  .flex.items-center.gap-2.flex-shrink-0 {
    column-gap: 0.875rem !important;
  }
}

.menu-panel {
  box-shadow: 0 20px 40px rgba(2, 6, 23, 0.15);
  border: 1px solid #e2e8f0;
  transform-origin: top center;
  margin-top: 8px !important; /* Explore dropdown margin */
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.75rem 1rem;
  transition: all 0.15s ease;
}

.menu-item .menu-ico {
  width: 18px;
  min-width: 18px;
  text-align: center;
  color: #64748b;
}

.menu-item:hover {
  background: #f5f8ff;
}

.menu-item:hover .menu-ico {
  color: #2f78f0;
}

/* Compact search dropdown styles */
.compact-search-dropdown {
  /* No scroll, just compact layout */
}

.compact-search-dropdown .py-1 {
  padding-top: 0.25rem;
  padding-bottom: 0.25rem;
}

.compact-search-dropdown .px-3 {
  padding-left: 0.75rem;
  padding-right: 0.75rem;
}

.compact-search-dropdown .py-2 {
  padding-top: 0.5rem;
  padding-bottom: 0.5rem;
}

.compact-search-dropdown .gap-2 {
  gap: 0.5rem;
}

.compact-search-dropdown .w-7 {
  width: 1.75rem;
}

.compact-search-dropdown .h-7 {
  height: 1.75rem;
}

.compact-search-dropdown .text-sm {
  font-size: 0.875rem;
  line-height: 1.25rem;
}

.compact-search-dropdown .text-xs {
  font-size: 0.75rem;
  line-height: 1rem;
}

/* Original icon colors */
.icon-explore {
  color: #8b5cf6;
}

.icon-seekers {
  color: #ec4899;
}

.icon-network {
  color: #f59e0b;
}

.icon-notifications {
  color: #6366f1;
}

.nav-btn:hover .icon-explore {
  color: #7c3aed;
}

.nav-btn:hover .icon-seekers {
  color: #db2777;
}

.nav-btn:hover .icon-network {
  color: #d97706;
}

.nav-btn:hover .icon-notifications {
  color: #4f46e5;
}

.nav-label-explore,
.nav-label-seekers,
.nav-label-network,
.nav-label-messages,
.nav-label-notifications {
  color: black;
}

.nav-btn:hover .nav-label-explore {
  color: #7c3aed;
}

.nav-btn:hover .nav-label-seekers {
  color: #db2777;
}

.nav-btn:hover .nav-label-network {
  color: #d97706;
}

.nav-btn:hover .nav-label-messages {
  color: #1aac15;
}

.nav-btn:hover .nav-label-notifications {
  color: #4f46e5;
}

.rotate-180 {
  transform: rotate(180deg);
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.active-explore {
  background: rgba(139, 92, 246, 0.1) !important;
}

.active-explore .icon-explore {
  color: #7c3aed !important;
}

.active-explore .nav-label-explore {
  color: #7c3aed !important;
}

.active-seekers {
  background: rgba(236, 72, 153, 0.1) !important;
}

.active-seekers .icon-seekers {
  color: #db2777 !important;
}

.active-seekers .nav-label-seekers {
  color: #db2777 !important;
}

.hover\:bg-explore-hover:hover {
  background: rgba(139, 92, 246, 0.1);
}

.hover\:bg-seekers-hover:hover {
  background: rgba(236, 72, 153, 0.1);
}

.hover\:bg-network-hover:hover {
  background: rgba(245, 158, 11, 0.1);
}

.hover\:bg-messages-hover:hover {
  background: rgba(61, 203, 56, 0.1);
}

.hover\:bg-notifications-hover:hover {
  background: rgba(99, 102, 241, 0.1);
}

/* Line clamp utility for post content */
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Remove logo hover background */
.text-2xl.font-bold.tracking-tight.rounded-lg.px-3.py-2:hover {
  background-color: transparent !important;
}

/* Search dropdown width fixes */
.search-dropdown {
  min-width: 100% !important;
  width: 100% !important;
  max-width: 100% !important;
}

/* Text breaking for long words */
.break-words {
  word-break: break-word;
  overflow-wrap: break-word;
}

.break-all {
  word-break: break-all;
}

/* Mobile specific styles */
@media (max-width: 767px) {
  .flex-grow.flex.justify-start.px-4.ml-4 {
    margin-left: 0.5rem;
    padding-left: 0.5rem;
    padding-right: 0.5rem;
  }

  .relative.w-full.max-w-md {
    max-width: 100%;
  }
}

/* Fix for mobile toggle button */
.mobile-toggle-btn {
  position: relative;
  z-index: 60;
  cursor: pointer;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}

/* Mobile search toggle button */
.mobile-search-toggle,
.mobile-search-close {
  position: relative;
  z-index: 60;
  cursor: pointer;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}

/* Ensure the entire button area is clickable */
.mobile-toggle-btn::before,
.mobile-search-toggle::before,
.mobile-search-close::before {
  content: '';
  position: absolute;
  top: -10px;
  left: -10px;
  right: -10px;
  bottom: -10px;
}

/* Improve touch targets for mobile */
@media (max-width: 767px) {
  .mobile-toggle-btn,
  .mobile-search-toggle,
  .mobile-search-close {
    min-width: 44px;
    min-height: 44px;
  }
}

/* Remove outline from all toggle buttons */
.mobile-toggle-btn:focus,
.mobile-toggle-btn:active,
.mobile-search-toggle:focus,
.mobile-search-toggle:active,
.mobile-search-close:focus,
.mobile-search-close:active {
  outline: none !important;
  box-shadow: none !important;
}

/* Specifically remove outline from cross icon in mobile menu */
button:focus {
  outline: none !important;
  box-shadow: none !important;
}

/* Enhanced profile dropdown styling */
.profile-dropdown a,
.profile-dropdown button {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.profile-dropdown .group:hover span {
  color: #1f2937;
}

.profile-dropdown .border-t {
  border-color: #e5e7eb;
}

/* Premium member badge styling */
.text-amber-600 {
  background: linear-gradient(135deg, #fbbf24, #d97706);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Color-filled icons specific colors */
.profile-dropdown .text-blue-600 {
  color: #2563eb !important;
}

.profile-dropdown .text-green-600 {
  color: #16a34a !important;
}

.profile-dropdown .text-purple-600 {
  color: #7c3aed !important;
}

.profile-dropdown .text-amber-600 {
  color: #d97706 !important;
}

.profile-dropdown .text-indigo-600 {
  color: #4f46e5 !important;
}

/* Add color-filled icons styling for profile dropdown */
.profile-dropdown .group:hover svg {
  transform: scale(1.05);
  transition: transform 0.2s ease;
}

/* Mobile search bar animation */
.mobile-search-bar-enter-active,
.mobile-search-bar-leave-active {
  transition: all 0.3s ease;
}

.mobile-search-bar-enter-from,
.mobile-search-bar-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
