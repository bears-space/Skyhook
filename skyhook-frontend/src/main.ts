import { createApp } from "vue"
import "./style.css"
import "vue-sonner/style.css"
import App from "./App.vue"
import { router } from "./router"
import { createPinia } from "pinia"

createApp(App).use(router).use(createPinia()).mount("#app")
//when mounted, simulate data in the launchpad store for testing
import { useLaunchpadStore } from "./stores/launchpad"
const launchpadStore = useLaunchpadStore()
launchpadStore.simulateData()