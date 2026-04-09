<script setup lang="ts">
import type { Component } from "vue"
import { computed, onBeforeUnmount, onMounted, ref } from "vue"
import { ArrowLeft, Database, PlugZap, RadioTower, Rocket, ShieldCheck, Users } from "lucide-vue-next"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Kbd } from "@/components/ui/kbd"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select"
import { useAuthStore } from "@/stores/auth"
import UserAdminPanel from "@/components/settings/UserAdminPanel.vue"

type SettingsCategory = {
  id: string
  label: string
  description: string
  icon: Component
  accent: string
}

const categories: SettingsCategory[] = [
  {
    id: "rocket",
    label: "Rocket",
    description: "Flight computer, avionics, and pad safety profiles.",
    icon: Rocket,
    accent: "from-orange-500 to-amber-500",
  },
  {
    id: "database",
    label: "Database",
    description: "Telemetry storage, replication, and retention rules.",
    icon: Database,
    accent: "from-sky-500 to-cyan-500",
  },
  {
    id: "users",
    label: "Users",
    description: "Roles, access policies, and audit coverage.",
    icon: Users,
    accent: "from-emerald-500 to-teal-500",
  },
  {
    id: "network",
    label: "Network",
    description: "Ground links, fallback paths, and QoS thresholds.",
    icon: RadioTower,
    accent: "from-indigo-500 to-violet-500",
  },
  {
    id: "integrations",
    label: "Integrations",
    description: "APIs, webhooks, and downstream observability.",
    icon: PlugZap,
    accent: "from-rose-500 to-pink-500",
  },
  {
    id: "safety",
    label: "Compliance",
    description: "Safeguards, encryption, and change management.",
    icon: ShieldCheck,
    accent: "from-slate-500 to-neutral-600",
  },
]

const selectedCategoryId = ref<string | null>(null)
const selectedCategory = computed(() => categories.find((category) => category.id === selectedCategoryId.value) ?? null)
const pageTitle = computed(() => selectedCategory.value?.label ?? "System Settings")
const pageDescription = computed(
  () => selectedCategory.value?.description ?? "Start by choosing which type of system surface you want to adjust.",
)
const auth = useAuthStore()
auth.initFromStorage()
const isAdmin = computed(() => auth.userRoles.includes("admin"))

const clearSelection = () => {
  selectedCategoryId.value = null
}

const handleKeydown = (event: KeyboardEvent) => {
  if (
    event.key !== "Escape" ||
    !selectedCategoryId.value ||
    event.defaultPrevented ||
    event.altKey ||
    event.ctrlKey ||
    event.metaKey ||
    event.shiftKey
  ) {
    return
  }

  if (document.querySelector('[role="dialog"][data-state="open"]')) return

  event.preventDefault()
  clearSelection()
}

onMounted(() => {
  window.addEventListener("keydown", handleKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener("keydown", handleKeydown)
})

// Rocket
const flightProfile = ref<"launch" | "test" | "safe">("launch")
const softAbortAllowed = ref(true)
const abortHoldoffMs = ref(750)
const pyroArmDelayMs = ref(300)
const padSafeRadiusM = ref(30)

// Database
const retentionDaysDb = ref(30)
const replicationFactor = ref(3)
const compressionEnabled = ref(true)
const backupWindow = ref("03:00-04:00 UTC")
const pointInTimeRecovery = ref(true)
const coldStorageAfterDays = ref(180)

// Users
const defaultRole = ref<"operator" | "engineer" | "admin">("operator")
const mfaEnforced = ref(true)
const sessionTimeoutMinutes = ref(30)
const inviteExpiryDays = ref(7)
const accountLockThreshold = ref(5)
const auditEmail = ref("security@skyhook.local")

// Network
const primaryLink = ref<"ka" | "s" | "ethernet">("ka")
const failoverThresholdMs = ref(1500)
const packetLossAlertPct = ref(5)
const qosProfile = ref<"mission" | "balanced" | "bulk">("mission")
const trafficShaping = ref(true)
const maxConcurrentStreams = ref(32)

// Integrations
const webhooksEnabled = ref(true)
const webhookEndpoint = ref("https://hooks.skyhook.local/system")
const webhookSecret = ref("shh-prod")
const observabilityProvider = ref<"datadog" | "grafana" | "newrelic">("datadog")
const tracingSampleRate = ref(20)
const outboundProxy = ref("")

// Compliance
const kmsRotationDays = ref(30)
const encryptAtRest = ref(true)
const encryptInTransit = ref(true)
const changeReviewRequired = ref(true)
const approvalWorkflow = ref<"dual" | "single" | "none">("dual")
const piiScrubbing = ref(true)
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div class="space-y-1">
        <div class="text-sm font-medium text-muted-foreground">System settings</div>
        <h1 class="text-2xl font-semibold tracking-tight">{{ pageTitle }}</h1>
        <p class="text-sm text-muted-foreground">
          {{ pageDescription }}
        </p>
      </div>
      <Button v-if="selectedCategory" variant="ghost" size="sm" class="gap-2" @click="clearSelection">
        <ArrowLeft class="h-4 w-4" />
        Back
        <Kbd>Esc</Kbd>
      </Button>
    </div>

    <Card v-if="!selectedCategory">
      <CardHeader class="pb-4">
        <CardTitle>Choose a settings domain</CardTitle>
        <CardDescription>Select where you want to make changes before editing values.</CardDescription>
      </CardHeader>
      <CardContent class="pt-0">
        <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <Button
            v-for="category in categories"
            :key="category.id"
            variant="outline"
            class="flex h-full w-full items-start justify-start gap-3 border-dashed"
            @click="selectedCategoryId = category.id"
          >
            <span
              :class="[
                'flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br text-white shadow-sm',
                category.accent,
              ]"
            >
              <component :is="category.icon" class="h-5 w-5" />
            </span>
            <span class="text-left">
              <div class="font-semibold leading-tight">{{ category.label }}</div>
              <div class="text-xs text-muted-foreground">{{ category.description }}</div>
            </span>
          </Button>
        </div>
      </CardContent>
    </Card>

    <div v-if="selectedCategory" class="grid gap-4 md:grid-cols-2">
        <Card v-if="selectedCategory.id === 'rocket'">
          <CardHeader>
            <CardTitle>Launch Controls</CardTitle>
            <CardDescription>Pad and flight-computer interlocks.</CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="space-y-2">
              <Label for="flight-profile">Flight profile</Label>
              <NativeSelect id="flight-profile" v-model="flightProfile">
                <NativeSelectOption value="launch">Launch</NativeSelectOption>
                <NativeSelectOption value="test">Test hop</NativeSelectOption>
                <NativeSelectOption value="safe">Safe</NativeSelectOption>
              </NativeSelect>
            </div>
            <div class="space-y-2">
              <Label for="abort-holdoff">Abort holdoff (ms)</Label>
              <Input id="abort-holdoff" v-model="abortHoldoffMs" type="number" min="0" />
            </div>
            <div class="space-y-2">
              <Label for="pyro-arm-delay">Pyro arm delay (ms)</Label>
              <Input id="pyro-arm-delay" v-model="pyroArmDelayMs" type="number" min="0" />
            </div>
            <div class="space-y-2">
              <Label for="pad-safe-radius">Pad safe radius (m)</Label>
              <Input id="pad-safe-radius" v-model="padSafeRadiusM" type="number" min="1" />
            </div>
            <div class="flex items-center justify-between gap-3">
              <div class="space-y-1">
                <Label for="soft-abort">Soft abort allowed</Label>
                <p class="text-xs text-muted-foreground">Graceful shutdown before hard abort.</p>
              </div>
              <Switch id="soft-abort" v-model:checked="softAbortAllowed" />
            </div>
          </CardContent>
        </Card>

        <Card v-if="selectedCategory.id === 'database'">
          <CardHeader>
            <CardTitle>Storage</CardTitle>
            <CardDescription>Retention and replication.</CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="space-y-2">
              <Label for="retention-days-db">Hot retention (days)</Label>
              <Input id="retention-days-db" v-model="retentionDaysDb" type="number" min="1" />
            </div>
            <div class="space-y-2">
              <Label for="replication-factor">Replication factor</Label>
              <Input id="replication-factor" v-model="replicationFactor" type="number" min="1" />
            </div>
            <div class="space-y-2">
              <Label for="backup-window">Backup window</Label>
              <Input id="backup-window" v-model="backupWindow" placeholder="03:00-04:00 UTC" />
            </div>
            <div class="space-y-2">
              <Label for="cold-storage">Cold storage after (days)</Label>
              <Input id="cold-storage" v-model="coldStorageAfterDays" type="number" min="1" />
            </div>
            <div class="flex items-center justify-between gap-3">
              <div class="space-y-1">
                <Label for="compression-enabled">Compression</Label>
                <p class="text-xs text-muted-foreground">Use columnar compression.</p>
              </div>
              <Switch id="compression-enabled" v-model:checked="compressionEnabled" />
            </div>
            <div class="flex items-center justify-between gap-3">
              <div class="space-y-1">
                <Label for="pitr">Point-in-time recovery</Label>
                <p class="text-xs text-muted-foreground">Allow rewind within retention window.</p>
              </div>
              <Switch id="pitr" v-model:checked="pointInTimeRecovery" />
            </div>
          </CardContent>
        </Card>

        <Card v-if="selectedCategory.id === 'users' && isAdmin">
          <CardHeader>
            <CardTitle>Access Control</CardTitle>
            <CardDescription>Identity, sessions, and MFA.</CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="space-y-2">
              <Label for="default-role">Default role</Label>
              <NativeSelect id="default-role" v-model="defaultRole">
                <NativeSelectOption value="operator">Operator</NativeSelectOption>
                <NativeSelectOption value="engineer">Engineer</NativeSelectOption>
                <NativeSelectOption value="admin">Admin</NativeSelectOption>
              </NativeSelect>
            </div>
            <div class="space-y-2">
              <Label for="session-timeout">Session timeout (minutes)</Label>
              <Input id="session-timeout" v-model="sessionTimeoutMinutes" type="number" min="5" />
            </div>
            <div class="space-y-2">
              <Label for="invite-expiry">Invite expiry (days)</Label>
              <Input id="invite-expiry" v-model="inviteExpiryDays" type="number" min="1" />
            </div>
            <div class="space-y-2">
              <Label for="lock-threshold">Lock threshold (failed attempts)</Label>
              <Input id="lock-threshold" v-model="accountLockThreshold" type="number" min="1" />
            </div>
            <div class="space-y-2">
              <Label for="audit-email">Audit notifications</Label>
              <Input id="audit-email" v-model="auditEmail" type="email" />
            </div>
            <div class="flex items-center justify-between gap-3">
              <div class="space-y-1">
                <Label for="mfa-enforced">MFA enforced</Label>
                <p class="text-xs text-muted-foreground">Require second factor on sign-in.</p>
              </div>
              <Switch id="mfa-enforced" v-model:checked="mfaEnforced" />
            </div>
          </CardContent>
        </Card>

        <Card v-if="selectedCategory.id === 'users' && isAdmin" class="md:col-span-2">
          <CardHeader>
            <CardTitle>User directory</CardTitle>
            <CardDescription>Invite, edit, or disable users via API-backed actions.</CardDescription>
          </CardHeader>
          <CardContent>
            <UserAdminPanel :token="auth.token" />
          </CardContent>
        </Card>

        <Card v-if="selectedCategory.id === 'users' && !isAdmin" class="md:col-span-2">
          <CardHeader>
            <CardTitle>Access restricted</CardTitle>
            <CardDescription>You need the admin role to view or edit users.</CardDescription>
          </CardHeader>
          <CardContent>
            <p class="text-sm text-muted-foreground">
              Contact an administrator to request access. Your current roles: {{ auth.userRoles.join(", ") || "none" }}.
            </p>
          </CardContent>
        </Card>

        <Card v-if="selectedCategory.id === 'network'">
          <CardHeader>
            <CardTitle>Link Policy</CardTitle>
            <CardDescription>Primary paths and failover.</CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="space-y-2">
              <Label for="primary-link">Primary link</Label>
              <NativeSelect id="primary-link" v-model="primaryLink">
                <NativeSelectOption value="ka">Ka-band</NativeSelectOption>
                <NativeSelectOption value="s">S-band</NativeSelectOption>
                <NativeSelectOption value="ethernet">Ethernet</NativeSelectOption>
              </NativeSelect>
            </div>
            <div class="space-y-2">
              <Label for="failover-threshold">Failover threshold (ms)</Label>
              <Input id="failover-threshold" v-model="failoverThresholdMs" type="number" min="100" />
            </div>
            <div class="space-y-2">
              <Label for="packet-loss-alert">Packet loss alert (%)</Label>
              <Input id="packet-loss-alert" v-model="packetLossAlertPct" type="number" min="0" max="100" />
            </div>
            <div class="space-y-2">
              <Label for="qos-profile">QoS profile</Label>
              <NativeSelect id="qos-profile" v-model="qosProfile">
                <NativeSelectOption value="mission">Mission critical</NativeSelectOption>
                <NativeSelectOption value="balanced">Balanced</NativeSelectOption>
                <NativeSelectOption value="bulk">Bulk transfer</NativeSelectOption>
              </NativeSelect>
            </div>
            <div class="space-y-2">
              <Label for="max-streams">Max concurrent streams</Label>
              <Input id="max-streams" v-model="maxConcurrentStreams" type="number" min="1" />
            </div>
            <div class="flex items-center justify-between gap-3">
              <div class="space-y-1">
                <Label for="traffic-shaping">Traffic shaping</Label>
                <p class="text-xs text-muted-foreground">Shape downlink during congestion.</p>
              </div>
              <Switch id="traffic-shaping" v-model:checked="trafficShaping" />
            </div>
          </CardContent>
        </Card>

        <Card v-if="selectedCategory.id === 'integrations'">
          <CardHeader>
            <CardTitle>APIs & Hooks</CardTitle>
            <CardDescription>Outbound integrations and telemetry mirroring.</CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="flex items-center justify-between gap-3">
              <div class="space-y-1">
                <Label for="webhooks-enabled">Webhooks</Label>
                <p class="text-xs text-muted-foreground">Send events to downstream systems.</p>
              </div>
              <Switch id="webhooks-enabled" v-model:checked="webhooksEnabled" />
            </div>
            <div class="space-y-2">
              <Label for="webhook-endpoint">Webhook endpoint</Label>
              <Input id="webhook-endpoint" v-model="webhookEndpoint" placeholder="https://" />
            </div>
            <div class="space-y-2">
              <Label for="webhook-secret">Signing secret</Label>
              <Input id="webhook-secret" v-model="webhookSecret" type="password" />
            </div>
            <div class="space-y-2">
              <Label for="observability-provider">Observability provider</Label>
              <NativeSelect id="observability-provider" v-model="observabilityProvider">
                <NativeSelectOption value="datadog">Datadog</NativeSelectOption>
                <NativeSelectOption value="grafana">Grafana Cloud</NativeSelectOption>
                <NativeSelectOption value="newrelic">New Relic</NativeSelectOption>
              </NativeSelect>
            </div>
            <div class="space-y-2">
              <Label for="tracing-sample">Tracing sample rate (%)</Label>
              <Input id="tracing-sample" v-model="tracingSampleRate" type="number" min="0" max="100" />
            </div>
            <div class="space-y-2">
              <Label for="outbound-proxy">Outbound proxy</Label>
              <Input id="outbound-proxy" v-model="outboundProxy" placeholder="http://proxy:8080" />
            </div>
          </CardContent>
        </Card>

        <Card v-if="selectedCategory.id === 'safety'">
          <CardHeader>
            <CardTitle>Compliance</CardTitle>
            <CardDescription>Encryption, approvals, and PII handling.</CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="space-y-2">
              <Label for="kms-rotation">KMS rotation (days)</Label>
              <Input id="kms-rotation" v-model="kmsRotationDays" type="number" min="1" />
            </div>
            <div class="space-y-2">
              <Label for="approval-workflow">Change approvals</Label>
              <NativeSelect id="approval-workflow" v-model="approvalWorkflow">
                <NativeSelectOption value="dual">Dual approval</NativeSelectOption>
                <NativeSelectOption value="single">Single approver</NativeSelectOption>
                <NativeSelectOption value="none">None</NativeSelectOption>
              </NativeSelect>
            </div>
            <div class="flex items-center justify-between gap-3">
              <div class="space-y-1">
                <Label for="encrypt-at-rest">Encrypt at rest</Label>
                <p class="text-xs text-muted-foreground">Disk and object storage encryption.</p>
              </div>
              <Switch id="encrypt-at-rest" v-model:checked="encryptAtRest" />
            </div>
            <div class="flex items-center justify-between gap-3">
              <div class="space-y-1">
                <Label for="encrypt-in-transit">Encrypt in transit</Label>
                <p class="text-xs text-muted-foreground">TLS for all links.</p>
              </div>
              <Switch id="encrypt-in-transit" v-model:checked="encryptInTransit" />
            </div>
            <div class="flex items-center justify-between gap-3">
              <div class="space-y-1">
                <Label for="change-review">Change review required</Label>
                <p class="text-xs text-muted-foreground">Require approvals before deploy.</p>
              </div>
              <Switch id="change-review" v-model:checked="changeReviewRequired" />
            </div>
            <div class="flex items-center justify-between gap-3">
              <div class="space-y-1">
                <Label for="pii-scrubbing">PII scrubbing</Label>
                <p class="text-xs text-muted-foreground">Mask identifiers in logs.</p>
              </div>
              <Switch id="pii-scrubbing" v-model:checked="piiScrubbing" />
            </div>
          </CardContent>
        </Card>
    </div>
  </div>
</template>
