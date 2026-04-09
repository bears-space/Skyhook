<script setup lang="ts">
import { computed, reactive } from "vue"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select"
import { notify } from "@/lib/notifications"
import {
  LANDING_PAGE_OPTIONS,
  type UserPreferencesSnapshot,
  useUserPreferencesStore,
} from "@/stores/userPreferences"

const breadcrumbs = ["Settings", "User"]

const preferences = useUserPreferencesStore()
preferences.initFromStorage()

const snapshot = (): UserPreferencesSnapshot => preferences.snapshot()

const form = reactive<UserPreferencesSnapshot>(snapshot())
const savedPreferences = computed(() => snapshot())
const formError = computed(() => {
  if (!form.callsign.trim()) {
    return "Callsign is required."
  }

  if (!LANDING_PAGE_OPTIONS.some((option) => option.value === form.defaultLanding)) {
    return "Choose a valid landing page."
  }

  return null
})

const isDirty = computed(
  () => JSON.stringify(form) !== JSON.stringify(savedPreferences.value),
)

const resetDraft = () => {
  Object.assign(form, savedPreferences.value)
}

const saveChanges = () => {
  if (formError.value) {
    notify({
      title: "Unable to save settings",
      description: formError.value,
      variant: "destructive",
      channel: "user",
    })
    return
  }

  preferences.replacePreferences({
    ...form,
    callsign: form.callsign.trim(),
    quietHours: form.quietHours.trim(),
  })
  resetDraft()
  notify({
    title: "Preferences updated",
    description: "Your user settings were saved to this browser.",
    variant: "success",
    channel: "user",
  })
}
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
            <NativeSelect id="theme-preference" v-model="form.themePreference">
              <NativeSelectOption value="system">System</NativeSelectOption>
              <NativeSelectOption value="light">Light</NativeSelectOption>
              <NativeSelectOption value="dark">Dark</NativeSelectOption>
            </NativeSelect>
          </div>

          <div class="flex items-center justify-between gap-3">
            <div class="space-y-1">
              <Label for="compact-sidebar">Compact sidebar</Label>
              <p class="text-xs text-muted-foreground">Use a denser sidebar layout.</p>
            </div>
            <Switch id="compact-sidebar" v-model:checked="form.compactSidebar" />
          </div>

          <div class="flex items-center justify-between gap-3">
            <div class="space-y-1">
              <Label for="sidebar-labels">Sidebar labels</Label>
              <p class="text-xs text-muted-foreground">Collapse the sidebar to icons when labels are off.</p>
            </div>
            <Switch id="sidebar-labels" v-model:checked="form.showSidebarLabels" />
          </div>

          <div class="space-y-2">
            <Label for="default-landing">Default landing page</Label>
            <NativeSelect id="default-landing" v-model="form.defaultLanding">
              <NativeSelectOption
                v-for="option in LANDING_PAGE_OPTIONS"
                :key="option.value"
                :value="option.value"
              >
                {{ option.label }}
              </NativeSelectOption>
            </NativeSelect>
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
            <Input id="callsign" v-model="form.callsign" placeholder="Skyhook Operator" />
          </div>
          <div
            v-if="formError"
            class="rounded-md border border-destructive/50 bg-destructive/10 px-3 py-2 text-xs text-destructive"
          >
            {{ formError }}
          </div>
          <div class="flex gap-2">
            <Button variant="secondary" :disabled="!isDirty" @click="resetDraft">Reset</Button>
            <Button :disabled="!isDirty || !!formError" @click="saveChanges">Save changes</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
