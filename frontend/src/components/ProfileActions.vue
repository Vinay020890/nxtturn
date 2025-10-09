<script setup lang="ts">
import { useProfileStore } from '@/stores/profile';
import { storeToRefs } from 'pinia';

const profileStore = useProfileStore();
const { relationshipStatus, currentProfile, isLoadingFollow } = storeToRefs(profileStore);

const handleConnect = () => {
    if (currentProfile.value) {
        profileStore.sendConnectRequest(currentProfile.value.user.username);
    }
}

const handleFollow = () => {
    if (currentProfile.value) {
        profileStore.followUser(currentProfile.value.user.username);
        // Optimistic updates are now removed from here
    }
}

const handleUnfollow = () => {
    if (currentProfile.value) {
        profileStore.unfollowUser(currentProfile.value.user.username);
        // Optimistic updates are now removed from here
    }
}

const handleAccept = () => {
    if (currentProfile.value) {
        profileStore.acceptConnectRequest(currentProfile.value.user.username);
    }
}
</script>

<template>
    <div v-if="relationshipStatus" class="mt-4 flex items-center justify-center space-x-3">

        <!-- Primary "Connect" Button Logic -->
        <div class="flex-1">
            <button v-if="relationshipStatus.connection_status === 'not_connected'" @click="handleConnect"
                data-cy="connect-button"
                class="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-full transition">
                Connect
            </button>
            <button v-else-if="relationshipStatus.connection_status === 'request_sent'" disabled
                data-cy="pending-button"
                class="w-full bg-gray-300 text-gray-600 font-bold py-2 px-4 rounded-full cursor-not-allowed">
                Pending
            </button>
            <button v-else-if="relationshipStatus.connection_status === 'request_received'" @click="handleAccept"
                data-cy="accept-request-button"
                class="w-full bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded-full transition">
                Accept Request
            </button>
            <button v-else-if="relationshipStatus.connection_status === 'connected'" disabled data-cy="connected-button"
                class="w-full bg-gray-200 text-gray-700 font-bold py-2 px-4 rounded-full flex items-center justify-center">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
                Connected
            </button>
        </div>

        <!-- Secondary "Follow" Button Logic -->
        <div class="flex-1">
            <button v-if="relationshipStatus.follow_status === 'not_following'" @click="handleFollow"
                :disabled="isLoadingFollow" data-cy="follow-button"
                class="w-full bg-white hover:bg-gray-100 text-gray-800 font-semibold py-2 px-4 border border-gray-400 rounded-full shadow disabled:opacity-50">
                {{ isLoadingFollow ? '...' : 'Follow' }}
            </button>
            <button v-else-if="relationshipStatus.follow_status === 'followed_by'" @click="handleFollow"
                :disabled="isLoadingFollow" data-cy="follow-back-button"
                class="w-full bg-white hover:bg-gray-100 text-gray-800 font-semibold py-2 px-4 border border-gray-400 rounded-full shadow disabled:opacity-50">
                {{ isLoadingFollow ? '...' : 'Follow Back' }}
            </button>
            <button v-else-if="relationshipStatus.follow_status === 'following'" @click="handleUnfollow"
                :disabled="isLoadingFollow" data-cy="following-button"
                class="w-full bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-4 rounded-full disabled:opacity-50">
                {{ isLoadingFollow ? '...' : 'Following' }}
            </button>
        </div>

    </div>
</template>