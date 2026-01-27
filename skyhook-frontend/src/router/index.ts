import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router"
import { h } from "vue"
import Overview from "@/view/Overview.vue"

const PlaceholderView = {
  name: "PlaceholderView",
  render() {
    return h(
      "div",
      { class: "p-6 text-sm text-muted-foreground" },
      "Select a sidebar item.",
    )
  },
}

const routes: RouteRecordRaw[] = [
  { path: "/", name: "Overview", component: Overview },
  { path: "/data", name: "data", component: PlaceholderView },
  { path: "/comms", name: "comms", component: PlaceholderView },
  { path: "/ground-station", name: "ground-station", component: PlaceholderView },
  { path: "/pad-station", name: "pad-station", component: PlaceholderView },
  { path: "/engine", name: "engine", component: PlaceholderView },
  { path: "/airbrakes", name: "airbrakes", component: PlaceholderView },
  { path: "/fins", name: "fins", component: PlaceholderView },
  { path: "/on-board", name: "on-board", component: PlaceholderView },
  { path: "/ground-cams", name: "ground", component: PlaceholderView },
  { path: "/settings", name: "settings", component: PlaceholderView },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})
