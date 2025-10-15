<script setup lang="ts">
import { useProfileStore } from '@/stores/profile';
import { storeToRefs } from 'pinia';

const profileStore = useProfileStore();
// We still get the main connection status from here
const { relationshipStatus, currentProfile, isLoadingFollow } = storeToRefs(profileStore);

const handleConnect = () => {
    if (currentProfile.value) {
        profileStore.sendConnectRequest(currentProfile.value.user.username);
    }
}

const handleFollow = () => {
    if (currentProfile.value) {
        profileStore.followUser(currentProfile.value.user.username);
    }
}

const handleUnfollow = () => {
    if (currentProfile.value) {
        profileStore.unfollowUser(currentProfile.value.user.username);
    }
}

const handleAccept = () => {
    if (currentProfile.value) {
        profileStore.acceptConnectRequest(currentProfile.value.user.username);
    }
}
</script>

<template>
    <!-- We need both relationshipStatus AND currentProfile to be loaded -->
    <div v-if="relationshipStatus && currentProfile" class="mt-4 flex items-center justify-center space-x-3">

        <!-- Primary "Connect" Button Logic (Unchanged) -->
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

        <!-- === RESTORED & FIXED: Secondary "Follow" Button Logic === -->
        <!-- This logic is only shown if the users are NOT already connected -->
        <div class="flex-1" v-if="relationshipStatus.connection_status !== 'connected'">
            <!--
                FIX: Instead of 'follow_status', we check the boolean 'is_followed_by_request_user'
                which is part of the main 'currentProfile' object.
             -->
            <button v-if="!currentProfile.is_followed_by_request_user" @click="handleFollow" :disabled="isLoadingFollow"
                data-cy="follow-button"
                class="w-full bg-white hover:bg-gray-100 text-gray-800 font-semibold py-2 px-4 border border-gray-400 rounded-full shadow disabled:opacity-50">
                {{ isLoadingFollow ? '...' : 'Follow' }}
            </button>
            <button v-else @click="handleUnfollow" :disabled="isLoadingFollow" data-cy="following-button"
                class="w-full bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-4 rounded-full disabled:opacity-50">
                {{ isLoadingFollow ? '...' : 'Following' }}
            </button>
        </div>

    </div>
</template>