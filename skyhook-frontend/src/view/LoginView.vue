<script setup lang="ts">
import LoginPage from "@/components/auth/LoginPage.vue"
import { useAuthStore } from "@/stores/auth"
import { storeToRefs } from "pinia"
import { useRouter, useRoute } from "vue-router"

const auth = useAuthStore()
auth.initFromStorage()

const { loginLoading, loginError, userEmail } = storeToRefs(auth)
const router = useRouter()
const route = useRoute()

const handleSubmit = async (payload: { email: string; password: string; remember: boolean }) => {
  const ok = await auth.login(payload)
  if (ok) {
    const redirect = (route.query.redirect as string) || "/"
    router.replace(redirect)
  }
}
</script>

<template>
  <LoginPage
    :loading="loginLoading"
    :error="loginError"
    :default-email="userEmail"
    @submit="handleSubmit"
  />
</template>
