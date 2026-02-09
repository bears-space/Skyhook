<script setup lang="ts">
import { ref } from "vue"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select"

const breadcrumbs = ["Settings", "System"]

const telemetryIntervalMs = ref(200)
const telemetryRetentionDays = ref(14)
const telemetryValidation = ref(true)
const commsStaleMs = ref(5000)
const commsDegradedPct = ref(12)
const commsEscalation = ref<"page" | "notify" | "silent">("notify")
const auditLogging = ref(true)
const apiAccess = ref(true)
const defaultTimezone = ref("UTC")
const maintenanceWindow = ref("Sun 02:00-04:00")
</script>

<template>
  <div class="space-y-6">
    <div class="space-y-1">
      <div class="text-xs uppercase tracking-wide text-muted-foreground">
        {{ breadcrumbs.join(" / ") }}
      </div>
      <h1 class="text-2xl font-semibold tracking-tight">System Settings</h1>
      <p class="text-sm text-muted-foreground">
        Operational defaults that affect all users.
      </p>
    </div>

    <div class="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Telemetry</CardTitle>
          <CardDescription>System-wide defaults for data ingestion.</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="space-y-2">
            <Label for="telemetry-interval">Sampling interval (ms)</Label>
            <Input id="telemetry-interval" v-model="telemetryIntervalMs" type="number" min="50" />
          </div>
          <div class="space-y-2">
            <Label for="telemetry-retention">Retention (days)</Label>
            <Input id="telemetry-retention" v-model="telemetryRetentionDays" type="number" min="1" />
          </div>
          <div class="flex items-center justify-between gap-3">
            <div class="space-y-1">
              <Label for="telemetry-validation">Field validation</Label>
              <p class="text-xs text-muted-foreground">Reject out-of-range values.</p>
            </div>
            <Switch id="telemetry-validation" v-model:checked="telemetryValidation" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Comms</CardTitle>
          <CardDescription>Operational defaults for link monitoring.</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="space-y-2">
            <Label for="comms-stale">Stale threshold (ms)</Label>
            <Input id="comms-stale" v-model="commsStaleMs" type="number" min="1000" />
          </div>
          <div class="space-y-2">
            <Label for="comms-degraded">Degraded threshold (%)</Label>
            <Input id="comms-degraded" v-model="commsDegradedPct" type="number" min="1" max="100" />
          </div>
          <div class="space-y-2">
            <Label for="comms-escalation">Alert escalation</Label>
            <NativeSelect id="comms-escalation" v-model="commsEscalation">
              <NativeSelectOption value="page">Page on-call</NativeSelectOption>
              <NativeSelectOption value="notify">Notify dashboard</NativeSelectOption>
              <NativeSelectOption value="silent">Silent</NativeSelectOption>
            </NativeSelect>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Access</CardTitle>
          <CardDescription>Roles, permissions, and audit defaults.</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="flex items-center justify-between gap-3">
            <div class="space-y-1">
              <Label for="audit-logging">Audit logging</Label>
              <p class="text-xs text-muted-foreground">Track settings changes and access.</p>
            </div>
            <Switch id="audit-logging" v-model:checked="auditLogging" />
          </div>
          <div class="flex items-center justify-between gap-3">
            <div class="space-y-1">
              <Label for="api-access">API access</Label>
              <p class="text-xs text-muted-foreground">Allow external API integrations.</p>
            </div>
            <Switch id="api-access" v-model:checked="apiAccess" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Operations</CardTitle>
          <CardDescription>Defaults for system-level scheduling.</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="space-y-2">
            <Label for="timezone">Default timezone</Label>
            <Input id="timezone" v-model="defaultTimezone" placeholder="UTC" />
          </div>
          <div class="space-y-2">
            <Label for="maintenance-window">Maintenance window</Label>
            <Input id="maintenance-window" v-model="maintenanceWindow" placeholder="Sun 02:00-04:00" />
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
