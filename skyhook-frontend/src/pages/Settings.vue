<script setup>
import { useAlerts } from "@/lib/alerts"
import { onMounted } from "vue";
const { show } = useAlerts()

onMounted(() => {
  show({ title: "Disconnected from server", description: "You have been disconnected from the server. Please check your network connection, and validate that the server is running.", variant: "destructive" })

});
</script>

<template>
  <div class="space-y-2">
    <div class="text-lg font-semibold">Settings</div>
    <p class="text-sm text-muted-foreground">
      Configure your Skyhook preferences here.
    </p>
  </div>
</template>
