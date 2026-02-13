<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { PropType } from 'vue'

// Heroicons imports
import {
  UserIcon,
  ArrowRightIcon,
  ShieldExclamationIcon,
  XMarkIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  UsersIcon,
  ChevronDownIcon,
} from '@heroicons/vue/24/solid'

// --- Props ---
const props = defineProps({
  isOpen: { type: Boolean, required: true },
  members: { type: Array as PropType<any[]>, required: true, default: () => [] },
  creatorId: { type: Number, required: true },
  isSubmitting: { type: Boolean, default: false },
})

// --- Emits ---
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'submit', newOwnerId: number): void
}>()

// --- State ---
const selectedOwnerId = ref<number | null>(null)

// --- Helpers ---
function getMemberUserId(member: any): number | null {
  if (!member) return null
  const raw =
    member.user_id ?? member.userId ?? member.user?.id ?? member.user?.user_id ?? member.id
  const num = Number(raw)
  return Number.isFinite(num) ? num : null
}

function getMemberDisplay(member: any) {
  const username = member?.username ?? member?.user?.username ?? ''
  const firstName = member?.first_name ?? member?.user?.first_name ?? member?.firstName ?? ''
  const lastName = member?.last_name ?? member?.user?.last_name ?? member?.lastName ?? ''
  return { username, firstName, lastName }
}

function getMemberAvatar(member: any): string | null {
  return (
    member?.profile_pic ??
    member?.profilePic ??
    member?.avatar ??
    member?.picture ??
    member?.picture_url ??
    member?.pictureUrl ??
    member?.user?.profile_pic ??
    member?.user?.profilePic ??
    member?.user?.avatar ??
    member?.user?.picture ??
    member?.user?.picture_url ??
    member?.user?.pictureUrl ??
    null
  )
}

function initials(first?: string, last?: string) {
  const a = (first || '').trim().charAt(0)
  const b = (last || '').trim().charAt(0)
  const out = `${a}${b}`.trim()
  return out || '?'
}

// --- Computed ---
const transferableMembers = computed(() => {
  if (!Array.isArray(props.members)) return []
  const creatorIdNum = Number(props.creatorId)

  return props.members
    .filter((m) => {
      const uid = getMemberUserId(m)
      if (uid == null) return false
      return uid !== creatorIdNum
    })
    .map((m) => {
      const uid = getMemberUserId(m)
      const { username, firstName, lastName } = getMemberDisplay(m)
      return {
        ...m,
        id: uid ?? m?.id,
        username,
        first_name: firstName,
        last_name: lastName,
        _avatar: getMemberAvatar(m),
      }
    })
})

const selectedMember = computed(() => {
  if (selectedOwnerId.value == null) return null
  return (
    transferableMembers.value.find((m: any) => Number(m.id) === Number(selectedOwnerId.value)) ??
    null
  )
})

const currentOwnerMember = computed(() => {
  if (!Array.isArray(props.members)) return null
  const creatorIdNum = Number(props.creatorId)
  const found = props.members.find((m: any) => Number(getMemberUserId(m)) === creatorIdNum) ?? null
  if (!found) return null
  const { username, firstName, lastName } = getMemberDisplay(found)
  return {
    ...found,
    id: creatorIdNum,
    username,
    first_name: firstName,
    last_name: lastName,
    _avatar: getMemberAvatar(found),
  }
})

// --- Methods ---
function handleSubmit() {
  if (selectedOwnerId.value == null) return
  emit('submit', Number(selectedOwnerId.value))
}

function handleClose() {
  selectedOwnerId.value = null
  emit('close')
}

watch(
  () => props.isOpen,
  (isOpen) => {
    if (isOpen) {
      selectedOwnerId.value = null
      if (transferableMembers.value.length === 1) {
        selectedOwnerId.value = Number(transferableMembers.value[0].id)
      }
    }
  },
)
</script>

<template>
  <!-- Modal -->
  <div v-if="isOpen" class="fixed inset-0 z-50" @click.self="handleClose">
    <!-- Backdrop -->
    <div class="absolute inset-0 bg-black/60"></div>

    <!-- Container
         NOTE: pb-safe-modal ensures the modal never hides behind bottom nav in mobile.
    -->
    <div
      class="relative flex min-h-full items-start sm:items-center justify-center p-3 pb-safe-modal overflow-y-auto"
    >
      <!-- Panel -->
      <div
        class="relative w-full max-w-[92vw] sm:max-w-md bg-white rounded-2xl shadow-xl overflow-hidden"
      >
        <!-- Header -->
        <div class="bg-gradient-to-r from-orange-500 to-red-600 px-5 py-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3 min-w-0">
              <div class="bg-white/20 p-2 rounded-xl backdrop-blur-sm shrink-0">
                <ShieldExclamationIcon class="h-5 w-5 text-white" />
              </div>
              <div class="min-w-0">
                <h2 class="text-lg sm:text-xl font-bold text-white truncate">
                  Transfer Group Ownership
                </h2>
                <p class="text-orange-100 text-xs mt-1 truncate">
                  This action is permanent and irreversible
                </p>
              </div>
            </div>
            <button
              @click="handleClose"
              class="text-white/80 hover:text-white p-1.5 rounded-lg hover:bg-white/10"
              aria-label="Close modal"
            >
              <XMarkIcon class="h-5 w-5" />
            </button>
          </div>
        </div>

        <!-- Scrollable body (prevents footer from getting hidden) -->
        <div class="max-h-[calc(100vh-10rem)] overflow-y-auto">
          <div class="px-5 py-4">
            <!-- Warning -->
            <div
              class="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-xl p-3 mb-4"
            >
              <div class="flex items-start gap-3">
                <div
                  class="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center shrink-0"
                >
                  <ExclamationTriangleIcon class="w-4 h-4 text-amber-600" />
                </div>
                <div class="min-w-0">
                  <h3 class="font-semibold text-amber-800 text-sm">Important Notice</h3>
                  <p class="text-xs text-amber-700 mt-1">
                    After transferring ownership, you will become a regular member and lose all
                    administrative privileges. This action cannot be undone.
                  </p>
                </div>
              </div>
            </div>

            <!-- Selection -->
            <div class="space-y-4">
              <div class="space-y-2">
                <div class="flex items-center gap-2">
                  <div class="bg-blue-100 p-1.5 rounded-md">
                    <UsersIcon class="h-4 w-4 text-blue-600" />
                  </div>
                  <label for="new-owner" class="text-sm font-semibold text-gray-700">
                    Select New Owner
                  </label>
                </div>

                <div class="relative min-w-0">
                  <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <UserIcon class="h-5 w-5 text-gray-400" />
                  </div>

                  <select
                    id="new-owner"
                    v-model="selectedOwnerId"
                    class="w-full max-w-full pl-10 pr-10 py-2.5 text-sm rounded-lg border border-gray-300 bg-white text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 focus:outline-none appearance-none"
                    :class="{ 'cursor-not-allowed opacity-50': transferableMembers.length === 0 }"
                    :disabled="transferableMembers.length === 0 || isSubmitting"
                  >
                    <option disabled :value="null" class="text-gray-500">
                      -- Select member --
                    </option>
                    <option
                      v-for="member in transferableMembers"
                      :key="member.id"
                      :value="Number(member.id)"
                      class="text-gray-900"
                    >
                      {{ member.first_name }} {{ member.last_name }} (@{{ member.username }})
                    </option>
                  </select>

                  <div
                    class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none"
                  >
                    <ChevronDownIcon class="h-5 w-5 text-gray-400" />
                  </div>
                </div>

                <div v-if="transferableMembers.length === 0" class="text-center py-3">
                  <div
                    class="inline-flex items-center justify-center w-11 h-11 rounded-full bg-gray-100 mb-2"
                  >
                    <UserIcon class="h-6 w-6 text-gray-400" />
                  </div>
                  <p class="text-sm text-gray-600 font-medium">No members available</p>
                  <p class="text-xs text-gray-500 mt-1">
                    You need at least one other member in the group to transfer ownership.
                  </p>
                </div>

                <!-- Selected new owner preview -->
                <div
                  v-if="selectedMember"
                  class="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-3 mt-3"
                >
                  <div class="flex items-center justify-between gap-3">
                    <div class="flex items-center gap-3 min-w-0">
                      <div
                        class="w-10 h-10 rounded-full overflow-hidden bg-gray-200 flex items-center justify-center shrink-0"
                      >
                        <img
                          v-if="selectedMember._avatar"
                          :src="selectedMember._avatar"
                          class="w-full h-full object-cover"
                          alt=""
                        />
                        <span v-else class="text-sm font-bold text-blue-600">
                          {{ initials(selectedMember.first_name, selectedMember.last_name) }}
                        </span>
                      </div>

                      <div class="min-w-0">
                        <p class="font-semibold text-gray-900 text-sm truncate">
                          {{ selectedMember.first_name }} {{ selectedMember.last_name }}
                        </p>
                        <p class="text-xs text-gray-600 truncate">@{{ selectedMember.username }}</p>
                      </div>
                    </div>

                    <CheckCircleIcon class="h-5 w-5 text-blue-500 shrink-0" />
                  </div>

                  <div class="mt-2 pt-2 border-t border-blue-100">
                    <p class="text-[11px] text-gray-600">
                      <span class="font-medium text-gray-700">Will become:</span> Group Owner with
                      full administrative privileges
                    </p>
                  </div>
                </div>
              </div>

              <!-- Transfer visualization -->
              <div v-if="selectedMember" class="pt-3 border-t border-gray-100">
                <div class="flex items-center justify-center gap-4">
                  <div class="text-center">
                    <div
                      class="w-11 h-11 rounded-full overflow-hidden bg-gray-200 flex items-center justify-center mx-auto mb-2"
                    >
                      <img
                        v-if="currentOwnerMember?._avatar"
                        :src="currentOwnerMember._avatar"
                        class="w-full h-full object-cover"
                        alt=""
                      />
                      <div v-else class="w-full h-full flex items-center justify-center bg-red-100">
                        <ShieldExclamationIcon class="h-5 w-5 text-red-600" />
                      </div>
                    </div>
                    <p class="text-[11px] font-medium text-gray-700">Current Owner</p>
                    <p class="text-[11px] text-gray-500 truncate max-w-[110px]">
                      {{ currentOwnerMember?.first_name || 'You' }}
                      <span v-if="currentOwnerMember?.username"
                        >(@{{ currentOwnerMember.username }})</span
                      >
                    </p>
                  </div>

                  <div class="flex-1 flex items-center justify-center">
                    <div
                      class="w-8 h-8 rounded-full bg-gradient-to-r from-orange-500 to-red-500 flex items-center justify-center"
                    >
                      <ArrowRightIcon class="h-4 w-4 text-white" />
                    </div>
                  </div>

                  <div class="text-center">
                    <div
                      class="w-11 h-11 rounded-full overflow-hidden bg-gray-200 flex items-center justify-center mx-auto mb-2"
                    >
                      <img
                        v-if="selectedMember._avatar"
                        :src="selectedMember._avatar"
                        class="w-full h-full object-cover"
                        alt=""
                      />
                      <div
                        v-else
                        class="w-full h-full flex items-center justify-center bg-green-100"
                      >
                        <UserIcon class="h-5 w-5 text-green-600" />
                      </div>
                    </div>
                    <p class="text-[11px] font-medium text-gray-700 truncate max-w-[110px]">
                      {{ selectedMember.first_name }}
                    </p>
                    <p class="text-[11px] text-gray-500">New Owner</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="bg-gray-50 px-5 py-4 border-t border-gray-200">
            <div class="flex flex-col sm:flex-row gap-3">
              <button
                type="button"
                @click="handleClose"
                :disabled="isSubmitting"
                class="px-5 py-2.5 text-sm rounded-lg border border-gray-300 bg-white text-gray-700 font-medium hover:bg-gray-50 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancel
              </button>

              <button
                type="button"
                @click="handleSubmit"
                :disabled="
                  selectedOwnerId == null || isSubmitting || transferableMembers.length === 0
                "
                class="relative flex-1 px-5 py-2.5 text-sm rounded-lg bg-gradient-to-r from-orange-500 to-red-500 text-white font-medium hover:from-orange-600 hover:to-red-600 focus:outline-none focus:ring-2 focus:ring-red-500/30 transition-all shadow hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed group"
              >
                <span class="flex items-center justify-center gap-2">
                  <ArrowRightIcon class="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                  <span v-if="isSubmitting">Transferring...</span>
                  <span v-else>Transfer Ownership</span>
                </span>
              </button>
            </div>

            <div class="mt-3 flex items-start gap-2 text-[11px] text-gray-500">
              <ExclamationTriangleIcon class="h-3 w-3 text-amber-500 flex-shrink-0 mt-0.5" />
              <p>
                You will no longer be able to manage group settings, approve members, or delete the
                group after this transfer.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Ensure dropdown options are visible */
select option {
  background: white;
  color: #1f2937;
  padding: 8px;
}

/* Remove default arrow */
select {
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  background-image: none;
}

/* Safe bottom padding so modal isn't hidden behind mobile bottom nav */
.pb-safe-modal {
  /* 72px typical bottom nav + safe area + a little buffer */
  padding-bottom: calc(env(safe-area-inset-bottom, 0px) + 88px);
}
</style>
