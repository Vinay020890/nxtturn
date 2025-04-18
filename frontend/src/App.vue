<script setup lang="ts">
// This line imports the component used by the router to render pages
import { RouterView } from 'vue-router'
</script>

<template>
  <!-- You can add a common header or navigation bar here later -->
  <!-- <header>My App Header</header> -->

  <!-- This is the main placeholder where router pages will be displayed -->
  <main>
    <RouterView />
  </main>

  <!-- You can add a common footer here later -->
  <!-- <footer>My App Footer</footer> -->
</template>

<style scoped>
/* You can keep, modify, or remove existing styles. */
/* Let's remove default header/nav styles if they existed */
main {
  padding-top: 1rem; /* Add some space at the top */
}
</style>
