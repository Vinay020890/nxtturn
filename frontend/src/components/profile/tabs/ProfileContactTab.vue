<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useProfileStore } from '@/stores/profile'
import { useToast } from 'vue-toastification'
import type { UserProfile } from '@/types'
import { Mail, Phone, ShieldCheck, Edit2, X, Loader2, Info } from 'lucide-vue-next'

const props = defineProps<{
  isOwnProfile: boolean
  profile: UserProfile | null
}>()

const profileStore = useProfileStore()
const toast = useToast()

const isEditing = ref(false)
const isSaving = ref(false)

// 1. Define allowed types to fix the TypeScript "Argument of type..." error
type VisibilityTier = 'public' | 'followers' | 'connections' | 'self'

// 2. Initialize local form state with explicit casting
const formData = reactive({
  phone_number: '' as string,
  phone_visibility: 'connections' as VisibilityTier,
  email_visibility: 'connections' as VisibilityTier,
})

// 3. CRITICAL: Watch for the profile to load/change and sync the form data
watch(
  () => props.profile,
  (newVal) => {
    if (newVal) {
      formData.phone_number = newVal.phone_number || ''
      formData.phone_visibility = (newVal.phone_visibility as VisibilityTier) || 'connections'
      formData.email_visibility = (newVal.email_visibility as VisibilityTier) || 'connections'
    }
  },
  { immediate: true },
)

/**
 * Toggles edit mode and resets form data if canceling.
 */
function toggleEdit() {
  if (isEditing.value) {
    formData.phone_number = props.profile?.phone_number || ''
    formData.phone_visibility = (props.profile?.phone_visibility as VisibilityTier) || 'connections'
    formData.email_visibility = (props.profile?.email_visibility as VisibilityTier) || 'connections'
  }
  isEditing.value = !isEditing.value
}

/**
 * Saves contact details using the new store action.
 */
async function handleSave() {
  isSaving.value = true
  try {
    // TypeScript now allows this because formData matches Partial<UserProfile>
    await profileStore.updateContactDetails(formData)
    toast.success('Contact information updated!')
    isEditing.value = false
  } catch (error: any) {
    toast.error(error.message || 'Update failed')
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <div class="space-y-6 animate-fade-in">
    <!-- Header -->
    <div class="flex items-center justify-between border-b pb-4 dark:border-gray-700">
      <div>
        <h3 class="text-lg font-bold text-gray-900 dark:text-white">Contact & Privacy</h3>
        <p class="text-sm text-gray-500">Manage your contact details and visibility settings.</p>
      </div>

      <!-- Only owner can see the Edit button -->
      <button
        v-if="isOwnProfile"
        @click="toggleEdit"
        type="button"
        class="flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        :class="
          isEditing
            ? 'bg-red-50 text-red-600 hover:bg-red-100'
            : 'bg-blue-50 text-blue-600 hover:bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400'
        "
      >
        <component :is="isEditing ? X : Edit2" class="w-4 h-4" />
        <span>{{ isEditing ? 'Cancel' : 'Edit Details' }}</span>
      </button>
    </div>

    <div v-if="profile" class="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
      <!-- Email (Always Read Only) -->
      <div class="space-y-2">
        <label class="block text-sm font-semibold text-gray-700 dark:text-gray-300"
          >Email Address</label
        >
        <div class="relative">
          <Mail class="absolute left-3 top-3.5 w-4 h-4 text-gray-400" />
          <input
            type="email"
            :value="profile.email || 'Private'"
            disabled
            class="block w-full pl-10 bg-gray-50 border border-gray-200 text-gray-500 rounded-xl p-3 cursor-not-allowed dark:bg-gray-800/50 dark:border-gray-700"
          />
        </div>
        <p v-if="isEditing" class="text-[10px] text-amber-600 flex items-center mt-1">
          <Info class="w-3 h-3 mr-1" />
          Email can only be changed in account settings.
        </p>
      </div>

      <!-- Phone Number -->
      <div class="space-y-2">
        <label class="block text-sm font-semibold text-gray-700 dark:text-gray-300"
          >Phone Number</label
        >
        <div class="relative">
          <Phone class="absolute left-3 top-3.5 w-4 h-4 text-gray-400" />
          <input
            v-model="formData.phone_number"
            :disabled="!isEditing"
            :placeholder="isOwnProfile ? 'No phone number added' : 'Private'"
            class="block w-full pl-10 rounded-xl border p-3 transition-all outline-none"
            :class="
              isEditing
                ? 'bg-white border-blue-400 focus:ring-2 focus:ring-blue-100 dark:bg-gray-900 dark:border-blue-900'
                : 'bg-gray-50 border-gray-200 text-gray-500 dark:bg-gray-800/50 dark:border-gray-700'
            "
          />
        </div>
      </div>

      <!-- Visibility Controls - ONLY VISIBLE TO THE OWNER -->
      <div v-if="isOwnProfile" class="md:col-span-2 space-y-4 mt-4">
        <div class="flex items-center space-x-2 border-t pt-4 dark:border-gray-800">
          <ShieldCheck class="w-4 h-4 text-blue-500" />
          <h4 class="text-xs font-bold text-gray-400 uppercase tracking-widest">
            Privacy Settings
          </h4>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Email Visibility -->
          <div class="p-4 bg-gray-50 rounded-2xl dark:bg-gray-800/50 border dark:border-gray-700">
            <label class="block text-xs font-medium text-gray-500 mb-2"
              >Who can see your email?</label
            >
            <select
              v-model="formData.email_visibility"
              :disabled="!isEditing"
              class="w-full bg-white border border-gray-200 rounded-lg p-2.5 dark:bg-gray-900 dark:border-gray-700 dark:text-white outline-none focus:border-blue-500 cursor-pointer disabled:cursor-not-allowed"
            >
              <option value="public">Everyone</option>
              <option value="followers">My Followers</option>
              <option value="connections">Mutual Connections</option>
              <option value="self">Only Me</option>
            </select>
          </div>

          <!-- Phone Visibility -->
          <div class="p-4 bg-gray-50 rounded-2xl dark:bg-gray-800/50 border dark:border-gray-700">
            <label class="block text-xs font-medium text-gray-500 mb-2"
              >Who can see your phone?</label
            >
            <select
              v-model="formData.phone_visibility"
              :disabled="!isEditing"
              class="w-full bg-white border border-gray-200 rounded-lg p-2.5 dark:bg-gray-900 dark:border-gray-700 dark:text-white outline-none focus:border-blue-500 cursor-pointer disabled:cursor-not-allowed"
            >
              <option value="public">Everyone</option>
              <option value="followers">My Followers</option>
              <option value="connections">Mutual Connections</option>
              <option value="self">Only Me</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- Save Button (Owner Only) -->
    <div v-if="isEditing" class="flex justify-end pt-6">
      <button
        @click="handleSave"
        :disabled="isSaving"
        type="button"
        class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-10 rounded-xl shadow-lg transition-all disabled:opacity-50 flex items-center"
      >
        <Loader2 v-if="isSaving" class="w-4 h-4 mr-2 animate-spin" />
        Save Details
      </button>
    </div>
  </div>
</template>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.3s ease-out;
}
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
