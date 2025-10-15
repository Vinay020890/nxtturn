<script setup lang="ts">
import { useProfileStore } from '@/stores/profile';
import { storeToRefs } from 'pinia';
import { ref, computed } from 'vue';

// --- 1. Import all necessary Heroicons ---
// Use the `/24/outline` for a consistent, modern look
import {
    UserPlusIcon,
    ClockIcon,
    CheckCircleIcon,
    UserGroupIcon,
    HeartIcon as HeartIconOutline,
    ChatBubbleOvalLeftEllipsisIcon,
    ArrowPathIcon
} from '@heroicons/vue/24/outline';
// Import the solid HeartIcon for the "Following" state
import { HeartIcon as HeartIconSolid } from '@heroicons/vue/24/solid';

const profileStore = useProfileStore();
// Use storeToRefs to get reactive access to the state
const { relationshipStatus, currentProfile, isLoadingFollow } = storeToRefs(profileStore);

// --- 2. Local state for managing the disconnect confirmation ---
const showDisconnectConfirm = ref(false);

// --- 3. Computed property for the "Follow" icon for cleaner template logic ---
const followIcon = computed(() => {
    // If the relationshipStatus object exists and the user is following, show the solid icon.
    return relationshipStatus.value?.is_followed_by_request_user ? HeartIconSolid : HeartIconOutline;
});

// --- 4. Handlers for all icon actions ---
const handleConnect = () => {
    if (currentProfile.value) {
        profileStore.sendConnectRequest(currentProfile.value.user.username);
    }
};

const handleAccept = () => {
    if (currentProfile.value) {
        // NOTE: Your old code had 'acceptConnectRequest' taking a username.
        // The ViewSet uses a request ID. We'll assume the store handles this lookup.
        // If it needs the ID, you'll need to pass that from the request object.
        profileStore.acceptConnectRequest(currentProfile.value.user.username);
    }
};

const handleFollowToggle = () => {
    if (currentProfile.value) {
        if (relationshipStatus.value?.is_followed_by_request_user) {
            // Unfollow action (which might also disconnect)
            profileStore.unfollowUser(currentProfile.value.user.username);
        } else {
            // Follow action (which might also connect)
            profileStore.followUser(currentProfile.value.user.username);
        }
    }
};

const handleDisconnect = () => {
    if (currentProfile.value) {
        // The "Disconnect" action is simply an unfollow from a connected state.
        // The backend will handle the full disconnection logic.
        profileStore.unfollowUser(currentProfile.value.user.username);
        showDisconnectConfirm.value = false; // Close the confirmation dropdown
    }
};

// Placeholder for messaging functionality
const handleMessage = () => {
    console.log("Messaging functionality to be implemented.");
    // Example: router.push(`/messages/${currentProfile.value?.user.username}`);
};

</script>

<template>
    <!-- Main container, ensuring it only renders when the relationship status is loaded -->
    <div v-if="relationshipStatus" class="mt-4 flex items-center justify-start space-x-4 px-4">

        <!-- SLOT 1: CONNECT ICON -->
        <div class="relative text-center">
            <!-- State: Default (No Relationship) -->
            <button v-if="relationshipStatus.connection_status === 'not_connected'" @click="handleConnect"
                data-cy="connect-button"
                class="flex flex-col items-center p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                <component :is="UserPlusIcon" class="w-7 h-7" />
                <span class="text-xs font-semibold mt-1">Connect</span>
            </button>

            <!-- State: Request Sent -->
            <button v-else-if="relationshipStatus.connection_status === 'request_sent'" disabled
                data-cy="pending-button" class="flex flex-col items-center p-2 text-gray-400 cursor-not-allowed">
                <component :is="ClockIcon" class="w-7 h-7" />
                <span class="text-xs font-semibold mt-1">Pending</span>
            </button>

            <!-- State: Request Received -->
            <button v-else-if="relationshipStatus.connection_status === 'request_received'" @click="handleAccept"
                data-cy="accept-request-button"
                class="flex flex-col items-center p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors">
                <component :is="CheckCircleIcon" class="w-7 h-7" />
                <span class="text-xs font-semibold mt-1">Accept</span>
            </button>

            <!-- State: Mutually Connected (with Disconnect dropdown) -->
            <div v-else-if="relationshipStatus.connection_status === 'connected'" class="relative">
                <button @click="showDisconnectConfirm = !showDisconnectConfirm" data-cy="connected-button"
                    class="flex flex-col items-center p-2 text-green-600 bg-green-50 rounded-lg">
                    <component :is="UserGroupIcon" class="w-7 h-7" />
                    <span class="text-xs font-semibold mt-1">Connected</span>
                </button>
                <!-- Disconnect confirmation dropdown -->
                <div v-if="showDisconnectConfirm" @mouseleave="showDisconnectConfirm = false"
                    class="absolute top-full mt-2 w-40 bg-white border border-gray-200 rounded-lg shadow-xl z-10">
                    <button @click="handleDisconnect" data-cy="disconnect-button"
                        class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50">
                        Disconnect
                    </button>
                </div>
            </div>
        </div>

        <!-- SLOT 2: FOLLOW ICON (Hidden when connected) -->
        <div v-if="relationshipStatus.connection_status !== 'connected'" class="text-center">
            <button @click="handleFollowToggle" :disabled="isLoadingFollow" :class="[
                relationshipStatus.is_followed_by_request_user
                    ? 'text-green-600 hover:bg-green-50'
                    : 'text-gray-600 hover:bg-gray-100'
            ]" class="flex flex-col items-center p-2 rounded-lg transition-colors disabled:opacity-50"
                data-cy="follow-toggle-button">
                <component :is="followIcon" class="w-7 h-7" />
                <span class="text-xs font-semibold mt-1">
                    {{ relationshipStatus.is_followed_by_request_user ? 'Following' : 'Follow' }}
                </span>
            </button>
        </div>

        <!-- SLOT 3: MESSAGE ICON (Always visible, unless blocked in the future) -->
        <div class="text-center">
            <button @click="handleMessage"
                class="flex flex-col items-center p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                data-cy="message-button">
                <component :is="ChatBubbleOvalLeftEllipsisIcon" class="w-7 h-7" />
                <span class="text-xs font-semibold mt-1">Message</span>
            </button>
        </div>
    </div>
</template>