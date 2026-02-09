<script setup lang="ts">
import { computed } from "vue"
import { useRoute, useRouter } from "vue-router"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

const route = useRoute()
const router = useRouter()

const scope = computed(() => (route.query.scope === "system" ? "system" : "user"))

const setScope = (value: string) => {
  const next = value === "system" ? "system" : "user"
  if (next === scope.value) return
  router.replace({ path: "/settings", query: { ...route.query, scope: next } })
}
</script>

<template>
  <div class="space-y-6">
    <div class="space-y-1">
      <h1 class="text-2xl font-semibold tracking-tight">Settings</h1>
      <p class="text-sm text-muted-foreground">
        Choose a scope to edit preferences and operational defaults.
      </p>
    </div>

    <Tabs :model-value="scope" class="w-full" @update:model-value="setScope">
      <TabsList class="grid w-full max-w-sm grid-cols-2">
        <TabsTrigger value="user">User</TabsTrigger>
        <TabsTrigger value="system">System</TabsTrigger>
      </TabsList>

      <TabsContent value="user" class="mt-4 space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Interface</CardTitle>
            <CardDescription>Personal UI preferences and layout behavior.</CardDescription>
          </CardHeader>
          <CardContent>
            <ul class="list-disc pl-5 text-sm text-muted-foreground">
              <li>Theme and contrast</li>
              <li>Sidebar density and labels</li>
              <li>Default landing page</li>
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Notifications</CardTitle>
            <CardDescription>Alert routing for your session.</CardDescription>
          </CardHeader>
          <CardContent>
            <ul class="list-disc pl-5 text-sm text-muted-foreground">
              <li>Sound and toast levels</li>
              <li>Quiet hours</li>
              <li>Telemetry anomaly alerts</li>
            </ul>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="system" class="mt-4 space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Telemetry</CardTitle>
            <CardDescription>System-wide defaults for data ingestion.</CardDescription>
          </CardHeader>
          <CardContent>
            <ul class="list-disc pl-5 text-sm text-muted-foreground">
              <li>Sampling intervals</li>
              <li>Field validation rules</li>
              <li>Retention and export</li>
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Comms</CardTitle>
            <CardDescription>Operational defaults for link monitoring.</CardDescription>
          </CardHeader>
          <CardContent>
            <ul class="list-disc pl-5 text-sm text-muted-foreground">
              <li>Stale thresholds</li>
              <li>Health scoring</li>
              <li>Alert escalation</li>
            </ul>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  </div>
</template>
