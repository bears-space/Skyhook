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
