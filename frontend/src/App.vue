<script setup lang="ts">
import { watch, onMounted, onUnmounted } from 'vue'; // <-- 1. Import onUnmounted
import { RouterView, useRouter } from 'vue-router'; // <-- 2. Import useRouter
import { notificationService } from '@/services/notificationService';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();
const router = useRouter(); // <-- 3. Get the router instance

// This watcher correctly handles WebSocket connections based on auth state.
// No changes needed here.
watch(() => authStore.isAuthenticated, (isNowAuthenticated) => {
  if (isNowAuthenticated) {
    console.log("Watcher Triggered: Auth state is TRUE. Connecting to WebSocket.");
    notificationService.connect();
  } else {
    console.log("Watcher Triggered: Auth state is FALSE. Disconnecting from WebSocket.");
    notificationService.disconnect();
  }
}, {
  immediate: true
});

// --- THIS IS THE NEW LOGIC FOR MULTI-TAB SYNC ---
// The event handler that will run when localStorage changes in another tab.
const handleStorageChange = (event: StorageEvent) => {
  // We only care about the 'authToken'. IMPORTANT: Verify this key is correct!
  // And we only act if the token was removed (newValue is null).
  if (event.key === 'authToken' && !event.newValue) {
    console.log('Auth token removed in another tab. Forcing logout and redirect.');
    
    // Reset the pinia state WITHOUT calling the full logout API endpoint again.
    authStore.resetAuthState(); 

    // Force a redirect to the login page.
    router.push({ name: 'login' });
  }
};
// --- END OF NEW LOGIC ---

onMounted(() => {
  authStore.initializeAuth();

  // Add the event listener when the component mounts.
  window.addEventListener('storage', handleStorageChange);
});

onUnmounted(() => {
  // IMPORTANT: Clean up the event listener when the component unmounts
  // to prevent memory leaks.
  window.removeEventListener('storage', handleStorageChange);
});
</script>

<template>
  <RouterView />
</template>