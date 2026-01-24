import { createApp } from "vue"
import App from "./App.vue"
import { socket } from "./socket"
import "./assets/index.css"
import router from "./router"
import { alertsPlugin } from "./lib/alerts"

const app = createApp(App)

socket.connect()
socket.on("connect", () => console.log("socket connected", socket.id))
socket.on("disconnect", (reason) => console.log("socket disconnected", reason))

app.use(router)
app.use(alertsPlugin)
app.mount("#app")
