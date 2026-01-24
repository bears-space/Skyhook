<script setup>
import { RouterView } from "vue-router"
import DashboardLayout from "@/layouts/DashboardLayout.vue"
import AlertStack from "@/components/ui/alert/AlertStack.vue"
</script>

<template>
  <DashboardLayout>
    <AlertStack />
    <RouterView />
  </DashboardLayout>
</template>
