<script setup lang="ts">
import { watch, onMounted } from 'vue';
import { RouterView } from 'vue-router';
import { notificationService } from '@/services/notificationService';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();

// This watcher is now the SINGLE source of truth and will run immediately.
watch(() => authStore.isAuthenticated, (isNowAuthenticated) => {
  if (isNowAuthenticated) {
    console.log("Watcher Triggered: Auth state is TRUE. Connecting to WebSocket.");
    notificationService.connect();
  } else {
    console.log("Watcher Triggered: Auth state is FALSE. Disconnecting from WebSocket.");
    notificationService.disconnect();
  }
}, {
  immediate: true // <-- THIS IS THE CRITICAL FIX
});

// onMounted's only job is to initialize the auth state, which will trigger the watcher.
onMounted(() => {
  authStore.initializeAuth();
});
</script>

<template>
  <!-- Your App.vue template can be simple. The real layouts are in the router. -->
  <RouterView />
</template>