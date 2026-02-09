<script setup lang="ts">
import { ref } from "vue"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select"

const breadcrumbs = ["Settings", "User"]

const themePreference = ref<"system" | "light" | "dark">("system")
const compactSidebar = ref(false)
const showSidebarLabels = ref(true)
const defaultLanding = ref("overview")
const notificationLevel = ref<"all" | "critical" | "silent">("all")
const notificationSound = ref(true)
const telemetryAlerts = ref(true)
const quietHours = ref("22:00-07:00")
const callsign = ref("Skyhook Operator")
</script>

<template>
  <div class="space-y-6">
    <div class="space-y-1">
      <div class="text-xs uppercase tracking-wide text-muted-foreground">
        {{ breadcrumbs.join(" / ") }}
      </div>
      <h1 class="text-2xl font-semibold tracking-tight">User Settings</h1>
      <p class="text-sm text-muted-foreground">
        Personal interface preferences for your session.
      </p>
    </div>

    <div class="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Interface</CardTitle>
          <CardDescription>Personal UI preferences and layout behavior.</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="space-y-2">
            <Label for="theme-preference">Theme preference</Label>
            <NativeSelect id="theme-preference" v-model="themePreference">
              <NativeSelectOption value="system">System</NativeSelectOption>
              <NativeSelectOption value="light">Light</NativeSelectOption>
              <NativeSelectOption value="dark">Dark</NativeSelectOption>
            </NativeSelect>
          </div>

          <div class="flex items-center justify-between gap-3">
            <div class="space-y-1">
              <Label for="compact-sidebar">Compact sidebar</Label>
              <p class="text-xs text-muted-foreground">Reduce padding for dense navigation.</p>
            </div>
            <Switch id="compact-sidebar" v-model:checked="compactSidebar" />
          </div>

          <div class="flex items-center justify-between gap-3">
            <div class="space-y-1">
              <Label for="sidebar-labels">Sidebar labels</Label>
              <p class="text-xs text-muted-foreground">Show text labels under icons.</p>
            </div>
            <Switch id="sidebar-labels" v-model:checked="showSidebarLabels" />
          </div>

          <div class="space-y-2">
            <Label for="default-landing">Default landing page</Label>
            <Input id="default-landing" v-model="defaultLanding" placeholder="overview" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Notifications</CardTitle>
          <CardDescription>Alert routing for your session.</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="space-y-2">
            <Label for="notification-level">Notification level</Label>
            <NativeSelect id="notification-level" v-model="notificationLevel">
              <NativeSelectOption value="all">All alerts</NativeSelectOption>
              <NativeSelectOption value="critical">Critical only</NativeSelectOption>
              <NativeSelectOption value="silent">Silent mode</NativeSelectOption>
            </NativeSelect>
          </div>

          <div class="flex items-center justify-between gap-3">
            <div class="space-y-1">
              <Label for="notification-sound">Notification sounds</Label>
              <p class="text-xs text-muted-foreground">Play sound on critical events.</p>
            </div>
            <Switch id="notification-sound" v-model:checked="notificationSound" />
          </div>

          <div class="flex items-center justify-between gap-3">
            <div class="space-y-1">
              <Label for="telemetry-alerts">Telemetry anomaly alerts</Label>
              <p class="text-xs text-muted-foreground">Surface unusual telemetry spikes.</p>
            </div>
            <Switch id="telemetry-alerts" v-model:checked="telemetryAlerts" />
          </div>

          <div class="space-y-2">
            <Label for="quiet-hours">Quiet hours</Label>
            <Input id="quiet-hours" v-model="quietHours" placeholder="22:00-07:00" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription>Operator identity and display name.</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="space-y-2">
            <Label for="callsign">Callsign</Label>
            <Input id="callsign" v-model="callsign" placeholder="Skyhook Operator" />
          </div>
          <div class="flex gap-2">
            <Button variant="secondary">Reset</Button>
            <Button>Save changes</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
