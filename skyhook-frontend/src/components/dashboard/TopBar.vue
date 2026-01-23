<script setup>
import { Sun, Moon } from "lucide-vue-next"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

const props = defineProps({
  isDark: { type: Boolean, default: true },
})
const emit = defineEmits(["toggle-theme"])
</script>

<template>
  <div class="w-full flex items-center gap-3">
    <Button
      variant="ghost"
      size="icon"
      :aria-pressed="props.isDark"
      :aria-label="props.isDark ? 'Switch to light mode' : 'Switch to dark mode'"
      title="Toggle theme"
      @click="emit('toggle-theme')"
    >
      <Sun v-if="props.isDark" class="h-4 w-4" />
      <Moon v-else class="h-4 w-4" />
    </Button>

    <DropdownMenu>
      <DropdownMenuTrigger as-child>
        <Button variant="ghost" size="icon" aria-label="User menu">
          <Avatar class="h-8 w-8">
            <AvatarFallback>J</AvatarFallback>
          </Avatar>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem>Profile</DropdownMenuItem>
        <DropdownMenuItem>Billing</DropdownMenuItem>
        <DropdownMenuItem>Sign out</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  </div>
</template>
