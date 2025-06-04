<script setup lang="ts">
// Import onMounted and watch lifecycle hooks from Vue
import { onMounted, watch } from 'vue'; 
import { RouterView, useRouter, RouterLink } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useNotificationStore } from '@/stores/notification'; // Already imported, good

// Get instances of the stores and router
const authStore = useAuthStore();
const notificationStore = useNotificationStore(); // Already initialized, good
const router = useRouter();

// --- onMounted HOOK ---
onMounted(async () => { // Make onMounted async if initializeAuth is async
  console.log('App.vue: Component mounted, calling initializeAuth...');
  await authStore.initializeAuth(); // Assuming initializeAuth might be async (e.g., involves an API call)
  
  // After auth is initialized, fetch unread notification count if user is authenticated
  if (authStore.isAuthenticated) {
    console.log("App.vue: User is authenticated (onMount), fetching unread notification count.");
    notificationStore.fetchUnreadCount();
  }
});
// --- END onMounted HOOK ---

// --- WATCH for authentication changes ---
watch(
  () => authStore.isAuthenticated, // Source to watch
  (newIsAuthenticated, oldIsAuthenticated) => {
    console.log(`App.vue: authStore.isAuthenticated changed from ${oldIsAuthenticated} to ${newIsAuthenticated}`);
    if (newIsAuthenticated) {
      // User has just logged in (or auth state confirmed after initial uncertainty)
      console.log("App.vue: User is now authenticated (watcher), fetching unread notification count.");
      notificationStore.fetchUnreadCount();
    } else {
      // User has just logged out
      console.log("App.vue: User is now unauthenticated (watcher), resetting unread count and notifications.");
      notificationStore.unreadCount = 0;    // Reset count locally
      notificationStore.notifications = []; // Clear any loaded notifications
      // Optionally, you could also clear pagination.error if it's set
      // notificationStore.error = null; 
      // notificationStore.pagination = { count: 0, next: null, previous: null, currentPage: 1, totalPages: 0 };
    }
  }
  // Optional: { immediate: true } if you want the watcher to run on initial component setup,
  // but onMounted already handles the initial check.
);
// --- END WATCH ---

// Method to handle the logout process
const handleLogout = async () => { // Made async as authStore.logout might be async
  console.log('App.vue: Logout button clicked');
  await authStore.logout(); // Call the store action to clear token/user state
  // No need to manually reset notificationStore here if the watcher on isAuthenticated handles it.
  router.push({ name: 'login' }); // Redirect to the login page
};
</script>

<template>
  <header>
    <nav>
      <div>
        <RouterLink to="/">Loopline</RouterLink>
      </div>
      <div>
        <span v-if="authStore.isAuthenticated">
          <span class="welcome-message">Welcome, {{ authStore.userDisplay }}!</span>
          
          <!-- ADD v-if here for links that depend on currentUser details -->
          <template v-if="authStore.currentUser && authStore.currentUser.username">
            <RouterLink :to="{ name: 'profile', params: { username: authStore.currentUser.username } }" class="nav-link">
              My Profile
            </RouterLink>
            
            <RouterLink :to="{ name: 'notifications' }" class="nav-link notification-bell">
              🔔 <span style="font-size: 0.9rem; vertical-align: middle;">Notifications</span>
              <span v-if="notificationStore.unreadCount > 0" class="notification-badge">
                {{ notificationStore.unreadCount > 9 ? '9+' : notificationStore.unreadCount }}
              </span>
            </RouterLink>
          </template>
          <!-- The Notification link could also be outside this inner v-if if it doesn't depend on username,
               but keeping it grouped with other authenticated-user specific links is fine. -->
          
          <button @click="handleLogout" class="logout-button">Logout</button>
        </span>
        <span v-else>
          <RouterLink to="/login" class="nav-link">Login</RouterLink>
        </span>
      </div>
    </nav>
  </header>
  <main>
    <RouterView />
  </main>
</template>

<style scoped>
header {
  background-color: #f8f8f8;
  padding: 0.5rem 1rem;
  border-bottom: 1px solid #eee;
  line-height: 1.5;
}
nav {
  display: flex; /* Use flexbox for layout */
  justify-content: space-between; /* Space out left/right sides */
  align-items: center; /* Vertically align items */
  max-width: 1200px; /* Max width for content */
  margin: 0 auto; /* Center the nav content */
}
nav button { /* Style logout button */
   margin-left: 1rem;
   padding: 0.3rem 0.6rem;
   cursor: pointer;
   /* Add basic button styles if needed */
   background-color: #eee;
   border: 1px solid #ccc;
   border-radius: 4px;
}
nav button:hover {
    background-color: #ddd;
}
main {
  /* Keep padding, adjust as needed */
  padding: 1rem; /* Consistent padding */
  max-width: 1200px; /* Optional: Max width for main content */
  margin: 1rem auto; /* Optional: Center main content */
}
/* Add basic link styling */
a {
    text-decoration: none;
    color: #007bff; /* Example link color */
    font-weight: 500;
}
a:hover {
    text-decoration: underline;
}
/* Style for the brand link */
nav > div:first-child a {
    font-weight: bold;
    color: #333; /* Example brand color */
}

.nav-link { /* General styling for navbar links */
  margin: 0 0.75rem; /* Space around links */
  text-decoration: none;
  color: #007bff; /* Link color */
}
.nav-link:hover {
  text-decoration: underline;
}

.welcome-message {
    margin-right: 0.75rem; /* Space after welcome message */
}

/* Styles for the notification bell and badge */
.notification-bell {
  position: relative; /* Needed for absolute positioning of the badge */
  display: inline-flex; /* Align icon and text nicely if you have text */
  align-items: center;
  /* margin: 0 0.5rem; /* Already handled by .nav-link if you use that class */
  /* color: #333; /* Bell icon color, adjust as needed */ /* Inherits from .nav-link */
  font-size: 1.2rem; /* Adjust bell icon size if using emoji/icon font */
  text-decoration: none;
  vertical-align: middle; /* Helps align emoji/icon with text */
}
.notification-bell:hover {
    /* color: #0056b3; /* Example hover color */ /* Inherits from .nav-link */
    text-decoration: none; /* Override default link underline on bell itself if desired */
}

.notification-badge {
  position: absolute;
  top: -8px;        /* Adjust to position badge correctly on top of bell icon */
  right: -10px;     /* Adjust to position badge correctly to the right of bell icon */
                    /* For text label, you might want 'right' to be further out or adjust parent padding */
  background-color: red;
  color: white;
  border-radius: 50%; /* Makes it circular */
  padding: 1px 4px;   /* Small padding for small text */
  font-size: 0.65rem; /* Very small font for the count */
  font-weight: bold;
  line-height: 1;     /* Helps with vertical centering */
  min-width: 14px;    /* To make single digit numbers look like a circle */
  min-height: 14px;   /* To make single digit numbers look like a circle */
  box-sizing: border-box;
  text-align: center;
  display: flex;      /* For centering text in badge */
  align-items: center;
  justify-content: center;
  z-index: 1;         /* Ensure badge is on top */
}

/* You might need to adjust your existing nav button styles if they conflict,
   or the .logout-button class I suggested earlier. */
.logout-button { /* Example style if you used this class */
    margin-left: 0.75rem;
}
</style>