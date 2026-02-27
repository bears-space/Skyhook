<script setup lang="ts">
import { computed, reactive } from "vue"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Separator } from "@/components/ui/separator"
import { Loader2, Lock, Rocket, ShieldCheck } from "lucide-vue-next"

type FormState = {
  email: string
  password: string
  remember: boolean
}

const props = defineProps<{
  loading?: boolean
  error?: string | null
  defaultEmail?: string | null
}>()

const emit = defineEmits<{
  (event: "submit", payload: FormState): void
}>()

const state = reactive<FormState>({
  email: props.defaultEmail ?? "",
  password: "",
  remember: true,
})

const canSubmit = computed(() => state.email.trim().length > 3 && state.password.trim().length > 3)

const handleSubmit = () => {
  if (!canSubmit.value || props.loading) return
  emit("submit", { ...state })
}
</script>

<template>
  <div class="relative min-h-svh w-full overflow-hidden bg-slate-950 text-foreground">
    <!-- animated background fields -->
    <div class="pointer-events-none absolute inset-0">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="orb orb-3"></div>
      <div class="orb orb-4"></div>
    </div>

    <div class="relative mx-auto flex min-h-svh max-w-5xl flex-col items-center justify-center px-4 py-10">
      <div class="mb-10 flex items-center gap-3 text-slate-50">
        <div class="grid size-11 place-content-center rounded-xl bg-primary/20 text-primary shadow-lg ring-1 ring-primary/40">
          <Rocket class="size-6" />
        </div>
        <div>
          <p class="text-xs uppercase tracking-[0.2em] text-primary/80">Skyhook Control</p>
          <h1 class="text-2xl font-semibold leading-tight">Mission Operations Console</h1>
        </div>
      </div>

      <Card class="w-full max-w-2xl border-slate-800/60 bg-slate-900/70 text-slate-50 shadow-2xl backdrop-blur">
        <CardHeader class="pb-4">
          <CardTitle class="text-xl">Sign in</CardTitle>
          <CardDescription class="text-slate-300">Authenticate to access live telemetry and command.</CardDescription>
        </CardHeader>
        <CardContent class="space-y-6">
          <div class="grid gap-4 md:grid-cols-2">
            <div class="space-y-3">
              <div class="space-y-2">
                <Label for="email" class="text-slate-200">Email</Label>
                <Input
                  id="email"
                  v-model="state.email"
                  type="email"
                  inputmode="email"
                  autocomplete="email"
                  placeholder="you@mission.io"
                  class="bg-white/5 text-slate-50 placeholder:text-slate-500"
                  :aria-invalid="!state.email"
                />
              </div>
              <div class="space-y-2">
                <Label for="password" class="text-slate-200">Password</Label>
                <div class="relative">
                  <Input
                    id="password"
                    v-model="state.password"
                    type="password"
                    autocomplete="current-password"
                    placeholder="••••••••"
                    class="bg-white/5 pr-10 text-slate-50 placeholder:text-slate-500"
                    :aria-invalid="!state.password"
                    @keyup.enter="handleSubmit"
                  />
                  <Lock class="absolute right-3 top-1/2 size-4 -translate-y-1/2 text-slate-500" />
                </div>
              </div>
              <div class="flex items-center gap-2 text-sm text-slate-200">
                <Checkbox id="remember" v-model:checked="state.remember" />
                <Label for="remember" class="cursor-pointer">Remember this device</Label>
              </div>
            </div>

            <div class="space-y-3 rounded-lg border border-white/10 bg-slate-950/50 p-4">
              <div class="flex items-center gap-2 text-sm font-semibold text-primary">
                <ShieldCheck class="size-4" />
                Operational security brief
              </div>
              <p class="text-sm text-slate-300">
                Skyhook console is restricted to authorized launch operators. Credentials are encrypted in transit;
                avoiding shared workstations is recommended. Device trust is refreshed every 24 hours.
              </p>
              <Separator class="bg-white/10" />
              <ul class="space-y-2 text-sm text-slate-300">
                <li class="flex items-center gap-2"><span class="size-1.5 rounded-full bg-primary" /> Live telemetry visibility</li>
                <li class="flex items-center gap-2"><span class="size-1.5 rounded-full bg-primary" /> Command uplink privileges</li>
                <li class="flex items-center gap-2"><span class="size-1.5 rounded-full bg-primary" /> Audit logging enabled</li>
              </ul>
            </div>
          </div>

          <div class="space-y-3">
            <Button
              class="w-full gap-2 text-base relative"
              size="lg"
              :disabled="!canSubmit || loading"
              @click="handleSubmit"
            >
              <Loader2
                v-if="loading"
                class="pointer-events-none absolute left-4 size-4 animate-spin"
              />
              <span :class="loading ? 'opacity-70' : ''">
                {{ loading ? "Signing in..." : "Enter Mission Console" }}
              </span>
            </Button>

            <Alert v-if="props.error" variant="destructive" class="border-red-500/40 bg-red-500/10 text-red-100">
              <AlertDescription>{{ props.error }}</AlertDescription>
            </Alert>

            <p class="text-center text-xs text-slate-400">
              By continuing, you acknowledge operational safety protocols and agree to abide by launch commit rules.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<style scoped>
@keyframes driftA {
  0% { transform: translate3d(-10%, -5%, 0) scale(1); opacity: 0.35; }
  50% { transform: translate3d(15%, 10%, 0) scale(1.1); opacity: 0.55; }
  100% { transform: translate3d(-8%, -6%, 0) scale(1); opacity: 0.35; }
}

@keyframes driftB {
  0% { transform: translate3d(20%, 5%, 0) scale(0.9) rotate(0deg); opacity: 0.35; }
  50% { transform: translate3d(-10%, -15%, 0) scale(1.05) rotate(10deg); opacity: 0.5; }
  100% { transform: translate3d(18%, 6%, 0) scale(0.9) rotate(0deg); opacity: 0.35; }
}

@keyframes driftC {
  0% { transform: translate3d(0%, 15%, 0) scale(1.05); opacity: 0.3; }
  50% { transform: translate3d(-5%, -10%, 0) scale(1.2); opacity: 0.5; }
  100% { transform: translate3d(2%, 18%, 0) scale(1.05); opacity: 0.3; }
}

.orb {
  position: absolute;
  filter: blur(80px);
  mix-blend-mode: screen;
  will-change: transform;
  transition: opacity 0.6s ease;
}

.orb-1 {
  width: 40vw;
  height: 40vw;
  top: -10%;
  left: -10%;
  background: radial-gradient(circle at 30% 30%, rgba(99, 102, 241, 0.7), rgba(14, 165, 233, 0));
  animation: driftA 18s ease-in-out infinite;
}

.orb-2 {
  width: 32vw;
  height: 32vw;
  top: 10%;
  right: -12%;
  background: radial-gradient(circle at 40% 40%, rgba(16, 185, 129, 0.6), rgba(59, 130, 246, 0));
  animation: driftB 22s ease-in-out infinite;
}

.orb-3 {
  width: 38vw;
  height: 38vw;
  bottom: -16%;
  left: -8%;
  background: radial-gradient(circle at 60% 60%, rgba(244, 63, 94, 0.5), rgba(56, 189, 248, 0));
  animation: driftC 26s ease-in-out infinite;
}

.orb-4 {
  width: 28vw;
  height: 28vw;
  bottom: -12%;
  right: 4%;
  background: radial-gradient(circle at 50% 50%, rgba(236, 72, 153, 0.45), rgba(14, 165, 233, 0));
  animation: driftB 20s ease-in-out reverse infinite;
}
</style>
