import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router"
import { h } from "vue"
import Overview from "@/view/Overview.vue"
import Narrowband from "@/view/Narrowband.vue"
import Broadband from "@/view/Broadband.vue"
import SettingsUserView from "@/view/SettingsUser.vue"
import SettingsSystemView from "@/view/SettingsSystem.vue"
import LoginView from "@/view/LoginView.vue"
import { useAuthStore } from "@/stores/auth"

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
  { path: "/login", name: "login", component: LoginView, meta: { layout: "auth" } },
  { path: "/", name: "Overview", component: Overview, meta: { requiresAuth: true } },
  { path: "/data", name: "data", component: PlaceholderView, meta: { requiresAuth: true } },
  { path: "/narrowband", name: "Narrowband Communications", component: Narrowband, meta: { requiresAuth: true } },
  { path: "/broadband", name: "Broadband Communications", component: Broadband, meta: { requiresAuth: true } },
  { path: "/ground-station", name: "ground-station", component: PlaceholderView, meta: { requiresAuth: true } },
  { path: "/pad-station", name: "pad-station", component: PlaceholderView, meta: { requiresAuth: true } },
  { path: "/engine", name: "engine", component: PlaceholderView, meta: { requiresAuth: true } },
  { path: "/airbrakes", name: "airbrakes", component: PlaceholderView, meta: { requiresAuth: true } },
  { path: "/fins", name: "fins", component: PlaceholderView, meta: { requiresAuth: true } },
  { path: "/on-board", name: "on-board", component: PlaceholderView, meta: { requiresAuth: true } },
  { path: "/ground-cams", name: "ground", component: PlaceholderView, meta: { requiresAuth: true } },
  { path: "/settings", redirect: "/settings/user" },
  { path: "/settings/user", name: "settings-user", component: SettingsUserView, meta: { requiresAuth: true } },
  { path: "/settings/system", name: "settings-system", component: SettingsSystemView, meta: { requiresAuth: true } },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()
  auth.initFromStorage()

  const authed = !!auth.isAuthenticated

  if (to.meta.requiresAuth && !authed) {
    return next({ path: "/login", query: { redirect: to.fullPath } })
  }

  if (to.path === "/login" && authed) {
    const redirect = (to.query.redirect as string) || "/"
    return next(redirect)
  }

  return next()
})
