import { createApp } from "vue"
import "./style.css"
import "vue-sonner/style.css"
import App from "./App.vue"
import { router } from "./router"
import { createPinia } from "pinia"
import VueApexCharts from "vue3-apexcharts"
import { useLaunchpadStore } from "./stores/launchpad"
import { useTelemetryStore } from "./stores/telemetry"
import { useCommsStore } from "./stores/comms"
import { useAuthStore } from "./stores/auth"
import { socket } from "./socket"
import { notify } from "./lib/notifications"

const app = createApp(App)
const pinia = createPinia()

app.use(router).use(pinia).use(VueApexCharts)
app.mount("#app")

// start derived timer ticks (based on launch.t0EpochMs)
const launchpadStore = useLaunchpadStore(pinia)
launchpadStore.startClock()

// start comms stale-age ticks
const commsStore = useCommsStore(pinia)
commsStore.startClock()

// wire telemetry (CDC -> Pinia) via Socket.IO
const telemetryStore = useTelemetryStore(pinia)
telemetryStore.connect()

// Handle socket auth errors: redirect to login and notify
const authStore = useAuthStore(pinia)
let authErrorNotified = false
socket.on("connect_error", (err) => {
  const message = (err?.message || "").toString().toLowerCase()
  if (message.includes("token") || message.includes("jwt") || message.includes("auth")) {
    if (authErrorNotified) return
    authErrorNotified = true
    authStore.signOut()
    notify({
      title: "Session expired",
      description: "Please sign in again to restore telemetry.",
      variant: "error",
    })
    const redirect = router.currentRoute.value.fullPath
    if (router.currentRoute.value.path !== "/login") {
      router.replace({ path: "/login", query: { redirect } })
    }
    setTimeout(() => { authErrorNotified = false }, 1500)
  }
})
