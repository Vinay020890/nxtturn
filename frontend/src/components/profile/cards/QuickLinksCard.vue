<script setup lang="ts">
import { ref } from 'vue'
import type { UserProfile, SocialLink, ProfileUpdatePayload } from '@/types'
import { useProfileStore } from '@/stores/profile'
import { Save, Edit3, Link2, MoreVertical, Trash2 } from 'lucide-vue-next'
import BaseModal from '@/components/common/BaseModal.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BrandIcon from '@/components/icons/BrandIcon.vue'

interface EditableLink {
  id?: number
  link_type: SocialLink['link_type']
  url: string
}

const props = defineProps<{
  profile: UserProfile
  isOwnProfile: boolean
}>()

const profileStore = useProfileStore()
const isModalOpen = ref(false)
const isLoading = ref(false)

const editableLinks = ref<EditableLink[]>([])

const linkOptions = [
  { value: 'linkedin', text: 'LinkedIn' },
  { value: 'github', text: 'GitHub' },
  { value: 'twitter', text: 'Twitter' },
  { value: 'portfolio', text: 'Personal Portfolio' },
]

function openModal() {
  editableLinks.value = props.profile.social_links?.map((link) => ({ ...link })) || []
  isModalOpen.value = true
}

function addLink() {
  editableLinks.value.push({ link_type: 'linkedin', url: '' })
}

function removeLink(index: number) {
  editableLinks.value.splice(index, 1)
}

async function handleSaveChanges() {
  if (isLoading.value) return
  isLoading.value = true
  try {
    const linksToSave: Omit<SocialLink, 'id'>[] = editableLinks.value
      .filter((link) => link.url && link.url.trim() !== '')
      .map((link) => ({
        link_type: link.link_type,
        url: link.url,
      }))

    const payload: ProfileUpdatePayload = { social_links: linksToSave }
    await profileStore.updateProfile(props.profile.user.username, payload)
    isModalOpen.value = false
  } catch (error) {
    console.error('Failed to update social links:', error)
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div
    data-cy="quick-links-card"
    class="bg-white rounded-xl shadow-lg border border-gray-100 p-6 relative hover:shadow-xl transition-all duration-300"
  >
    <!-- Header -->
    <div class="flex items-center mb-6 pb-4 border-b border-gray-100">
      <div
        class="flex items-center justify-center w-8 h-8 bg-gradient-to-r from-orange-500 to-pink-500 rounded-lg mr-3"
      >
        <Link2 class="h-6 w-6 text-white" />
      </div>
      <h3 class="text-xl font-bold text-gray-800">Quick Links</h3>

      <!-- Three Dots Button - Opens Modal Directly -->
      <button
        data-cy="edit-quick-links-button"
        v-if="isOwnProfile"
        @click="openModal"
        class="ml-auto flex items-center justify-center w-8 h-8 rounded-full hover:bg-gray-100 text-gray-600 hover:text-gray-900 transition-all duration-200"
        aria-label="Edit quick links"
      >
        <MoreVertical class="h-4 w-4" />
      </button>
    </div>

    <!-- Links Display - Show full URL with https:// -->
    <div v-if="profile.social_links && profile.social_links.length > 0" class="grid gap-3">
      <a
        v-for="link in profile.social_links"
        :key="link.id"
        :href="link.url"
        target="_blank"
        rel="noopener noreferrer"
        class="group flex items-center p-4 rounded-xl border border-gray-100 hover:border-gray-200 hover:shadow-md transition-all duration-200 bg-white"
      >
        <!-- Smaller Colorful Icon Background -->
        <div
          class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg text-white transition-all duration-200 group-hover:scale-105"
          :class="{
            'bg-blue-500': link.link_type === 'linkedin',
            'bg-gray-800': link.link_type === 'github',
            'bg-sky-500': link.link_type === 'twitter',
            'bg-purple-500': link.link_type === 'portfolio',
          }"
        >
          <BrandIcon :type="link.link_type" class="h-4 w-4" />
        </div>

        <!-- Link Details with full URL -->
        <div class="ml-3 flex-1 min-w-0 overflow-hidden">
          <p class="text-sm font-semibold text-gray-900 truncate">
            {{ linkOptions.find((o) => o.value === link.link_type)?.text || 'Link' }}
          </p>
          <p class="text-xs text-gray-500 break-all overflow-hidden line-clamp-2 mt-0.5">
            {{ link.url }}
          </p>
        </div>

        <!-- External Link Indicator -->
        <div
          class="opacity-0 group-hover:opacity-100 transition-opacity duration-200 ml-2 flex-shrink-0"
        >
          <svg class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
            />
          </svg>
        </div>
      </a>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-8">
      <div
        class="flex items-center justify-center w-16 h-16 bg-orange-100 rounded-full mx-auto mb-4"
      >
        <Link2 class="h-8 w-8 text-orange-500" />
      </div>
      <p class="text-gray-400 italic text-sm mb-2">No links provided.</p>
      <button
        v-if="isOwnProfile"
        @click="openModal"
        class="text-orange-500 hover:text-orange-600 font-medium text-sm flex items-center gap-1 mx-auto"
      >
        + Add your first link
      </button>
    </div>

    <!-- Compact & Responsive Modal for Editing -->
    <BaseModal
      :show="isModalOpen"
      title="Edit Quick Links"
      @close="isModalOpen = false"
      class="max-w-md"
    >
      <div class="space-y-3 max-h-64 overflow-y-auto pr-1">
        <!-- Compact Header -->
        <div
          class="flex items-center gap-3 p-3 bg-gradient-to-r from-orange-50 to-pink-50 rounded-lg border border-orange-100"
        >
          <div
            class="flex items-center justify-center w-10 h-10 bg-gradient-to-r from-orange-500 to-pink-500 rounded-lg flex-shrink-0"
          >
            <Link2 class="h-5 w-5 text-white" />
          </div>
          <div class="min-w-0 flex-1">
            <h3 class="text-sm font-semibold text-gray-900 truncate">Manage Your Links</h3>
            <p class="text-xs text-gray-600 truncate">Add and organize your social profiles</p>
          </div>
        </div>

        <!-- Compact Links List -->
        <div
          v-for="(link, index) in editableLinks"
          :key="index"
          class="group p-3 border border-gray-200 rounded-lg bg-white hover:border-orange-300 transition-all duration-200 relative"
        >
          <button
            data-cy="remove-link-button"
            @click="removeLink(index)"
            aria-label="Remove link"
            class="absolute top-2 right-2 p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-all duration-200 opacity-70 group-hover:opacity-100"
          >
            <Trash2 class="h-3 w-3" />
          </button>

          <div class="space-y-2 pr-6">
            <div class="flex items-center gap-2">
              <div
                class="w-6 h-6 flex items-center justify-center bg-orange-100 rounded flex-shrink-0"
              >
                <BrandIcon :type="link.link_type" class="h-3 w-3 text-orange-600" />
              </div>
              <div class="flex-1 min-w-0">
                <label
                  :for="`link-type-${index}`"
                  class="block text-xs font-medium text-gray-700 mb-1"
                  >Platform</label
                >
                <select
                  :id="`link-type-${index}`"
                  v-model="link.link_type"
                  class="w-full p-1.5 text-xs border border-gray-200 rounded focus:ring-1 focus:ring-orange-500 focus:border-orange-500 transition-all duration-200 bg-white outline-none"
                >
                  <option v-for="option in linkOptions" :key="option.value" :value="option.value">
                    {{ option.text }}
                  </option>
                </select>
              </div>
            </div>
            <div class="space-y-1">
              <label
                :for="`link-url-${index}`"
                class="flex items-center gap-1 text-xs font-medium text-gray-700"
              >
                <svg
                  class="h-3 w-3 text-orange-500 flex-shrink-0"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                  />
                </svg>
                URL
              </label>
              <input
                :id="`link-url-${index}`"
                v-model="link.url"
                type="url"
                placeholder="https://example.com/your-profile"
                class="w-full p-1.5 text-xs border border-gray-200 rounded focus:ring-1 focus:ring-orange-500 focus:border-orange-500 transition-all duration-200 outline-none"
              />
            </div>
          </div>
        </div>

        <!-- Compact Add Link Button -->
        <BaseButton
          @click="addLink"
          variant="secondary"
          class="w-full py-2.5 border border-dashed border-gray-200 hover:border-orange-300 hover:bg-orange-50 text-gray-600 hover:text-orange-600 transition-all duration-200 flex items-center justify-center group text-xs focus:ring-1 focus:ring-orange-500 focus:border-orange-500 outline-none"
        >
          + Add another link
        </BaseButton>
      </div>

      <template #footer>
        <div class="flex flex-col xs:flex-row justify-end gap-2 pt-3 border-t border-gray-100">
          <BaseButton
            @click="isModalOpen = false"
            variant="secondary"
            class="px-3 py-1.5 text-xs order-2 xs:order-1 focus:ring-1 focus:ring-orange-500 focus:border-orange-500 outline-none"
          >
            Cancel
          </BaseButton>
          <BaseButton
            @click="handleSaveChanges"
            :is-loading="isLoading"
            class="px-3 py-1.5 text-xs bg-gradient-to-r from-orange-500 to-pink-500 hover:from-orange-600 hover:to-pink-600 text-white shadow hover:shadow-md transition-all duration-200 flex items-center gap-1 order-1 xs:order-2 focus:ring-1 focus:ring-orange-500 focus:border-orange-500 outline-none"
          >
            <Save class="h-3 w-3" v-if="!isLoading" />
            {{ isLoading ? 'Saving...' : 'Save Changes' }}
          </BaseButton>
        </div>
      </template>
    </BaseModal>
  </div>
</template>

<style scoped>
/* Custom breakpoint for extra small devices */
@media (max-width: 475px) {
  .xs\:flex-row {
    flex-direction: row !important;
  }

  .xs\:order-1 {
    order: 1 !important;
  }

  .xs\:order-2 {
    order: 2 !important;
  }
}
</style>
