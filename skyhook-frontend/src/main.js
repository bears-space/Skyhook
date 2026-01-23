import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import { socket } from "./socket";

createApp(App).mount('#app')


// Socket stuff
socket.connect();

socket.on("connect", () => console.log("✅ socket connected", socket.id));
socket.on("disconnect", (reason) => console.log("❌ socket disconnected", reason));

app.mount("#app");
