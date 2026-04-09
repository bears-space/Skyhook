<script setup lang="ts">
import type { ColumnDef, FilterFn } from "@tanstack/vue-table"
import { computed, h, onMounted, reactive, ref, watch } from "vue"
import { Ban, Pencil, Plus, Power, RefreshCw, Trash2 } from "lucide-vue-next"
import { DataTable } from "@/components/data-table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { createUser, deleteUserApi, listUsers, updateUserApi, type UserRecord } from "@/lib/api"
import { notify } from "@/lib/notifications"

const props = defineProps<{
  token: string | null
}>()

type RoleName = "admin" | "engineer" | "operator"

const availableRoles: RoleName[] = ["admin", "engineer", "operator"]
const normalizeRole = (value?: string | null): RoleName => {
  const normalized = String(value ?? "").toLowerCase() as RoleName
  return availableRoles.includes(normalized) ? normalized : "operator"
}
const searchFilter: FilterFn<UserRecord> = (row, _columnId, value) => {
  const haystack = `${row.original.username} ${row.original.email || ""}`.toLowerCase()
  return haystack.includes(String(value ?? "").toLowerCase())
}

const users = ref<UserRecord[]>([])
const loading = ref(false)
const listError = ref<string | null>(null)
const formError = ref<string | null>(null)
const formOpen = ref(false)
const deleting = ref<UserRecord | null>(null)
const deleteDialogOpen = computed({
  get: () => !!deleting.value,
  set: (value: boolean) => {
    if (!value) deleting.value = null
  },
})
const saving = ref(false)
const refreshing = ref(false)
const editId = ref<number | null>(null)
const form = reactive({
  username: "",
  email: "",
  password: "",
  role: "operator" as RoleName,
  is_active: true,
})

const hasToken = computed(() => !!props.token)

const resetForm = () => {
  form.username = ""
  form.email = ""
  form.password = ""
  form.role = "operator"
  form.is_active = true
}

const loadUsers = async () => {
  if (!props.token) return
  loading.value = true
  listError.value = null
  try {
    users.value = await listUsers(props.token)
  } catch (err: any) {
    listError.value = err?.message || "Unable to load users"
  } finally {
    loading.value = false
  }
}

const refreshUsers = async () => {
  if (!props.token) return
  refreshing.value = true
  try {
    await loadUsers()
    notify({ title: "Users refreshed", variant: "success" })
  } finally {
    refreshing.value = false
  }
}

const startCreate = () => {
  editId.value = null
  resetForm()
  formError.value = null
  formOpen.value = true
}

const startEdit = (user: UserRecord) => {
  editId.value = user.id
  form.username = user.username
  form.email = user.email || ""
  form.password = ""
  form.role = normalizeRole(user.roles?.[0])
  form.is_active = !!user.is_active
  formError.value = null
  formOpen.value = true
}

const upsertLocal = (updated: UserRecord) => {
  const idx = users.value.findIndex((u) => u.id === updated.id)
  if (idx >= 0) users.value[idx] = updated
  else users.value.unshift(updated)
}

const removeLocal = (id: number) => {
  users.value = users.value.filter((u) => u.id !== id)
}

const submitForm = async () => {
  if (!props.token) return
  saving.value = true
  formError.value = null
  try {
    if (!form.username || !form.email) {
      throw new Error("Username and email are required")
    }

    if (editId.value === null && !form.password) {
      throw new Error("Password is required when creating a user")
    }

    const payload: any = {
      username: form.username.trim(),
      email: form.email.trim(),
      roles: [form.role],
      is_active: form.is_active,
    }
    if (form.password) {
      payload.password = form.password
    }

    const updated =
      editId.value === null
        ? await createUser(props.token, payload)
        : await updateUserApi(props.token, editId.value, payload)

    upsertLocal(updated)
    await loadUsers()
    notify({
      title: editId.value === null ? "User created" : "User updated",
      variant: "success",
    })
    formOpen.value = false
  } catch (err: any) {
    formError.value = err?.message || "Unable to save user"
    notify({ title: "Save failed", description: formError.value || undefined, variant: "destructive" })
  } finally {
    saving.value = false
  }
}

const toggleActive = async (user: UserRecord) => {
  if (!props.token) return
  try {
    const updated = await updateUserApi(props.token, user.id, { is_active: !user.is_active })
    upsertLocal(updated)
    await loadUsers()
    notify({
      title: updated.is_active ? "User activated" : "User deactivated",
      variant: "success",
    })
  } catch (err: any) {
    notify({ title: "Update failed", description: err?.message, variant: "destructive" })
  }
}

const confirmDelete = async () => {
  const target = deleting.value
  if (!props.token || !target) return
  try {
    await deleteUserApi(props.token, target.id)
    removeLocal(target.id)
    await loadUsers()
    notify({ title: "User deleted", variant: "success" })
  } catch (err: any) {
    notify({ title: "Delete failed", description: err?.message, variant: "destructive" })
  } finally {
    deleting.value = null
  }
}

const formatDate = (value?: string | null) => {
  if (!value) return "—"
  const dt = new Date(value)
  if (Number.isNaN(dt.getTime())) return value
  return dt.toLocaleString()
}

const columns = computed<ColumnDef<UserRecord>[]>(() => [
  {
    accessorKey: "username",
    header: "User",
    filterFn: searchFilter,
    cell: ({ row }) =>
      h("div", { class: "space-y-1" }, [
        h("div", { class: "font-semibold text-foreground" }, row.original.username),
        h("div", { class: "text-xs text-muted-foreground" }, row.original.email ?? "—"),
      ]),
  },
  {
    accessorKey: "roles",
    header: "Roles",
    cell: ({ row }) =>
      h(
        "div",
        { class: "flex flex-wrap gap-1" },
        (row.original.roles || []).map((role) =>
          h(Badge, { variant: "outline", class: "capitalize" }, () => role),
        ),
      ),
  },
  {
    accessorKey: "is_active",
    header: "Status",
    cell: ({ row }) =>
      h(
        Badge,
        { variant: row.original.is_active ? "secondary" : "destructive", class: "capitalize" },
        () => (row.original.is_active ? "active" : "disabled"),
      ),
  },
  {
    id: "updated",
    header: "Updated",
    cell: ({ row }) => formatDate(row.original.updated_at ?? row.original.created_at),
  },
  {
    id: "actions",
    header: "",
    cell: ({ row }) =>
      h("div", { class: "flex items-center gap-1" }, [
        h(
          Button,
          { variant: "ghost", size: "icon", onClick: () => startEdit(row.original) },
          () => h(Pencil, { class: "h-4 w-4" }),
        ),
        h(
          Button,
          {
            variant: "ghost",
            size: "icon",
            title: row.original.is_active ? "Disable" : "Enable",
            onClick: () => toggleActive(row.original),
          },
          () => h(row.original.is_active ? Ban : Power, { class: "h-4 w-4" }),
        ),
        h(
          Button,
          {
            variant: "ghost",
            size: "icon",
            class: "text-destructive",
            onClick: () => (deleting.value = row.original),
          },
          () => h(Trash2, { class: "h-4 w-4" }),
        ),
      ]),
  },
])

onMounted(loadUsers)
watch(() => props.token, (next) => next && loadUsers())
</script>

<template>
  <div class="space-y-3">
    <div class="flex flex-wrap items-center gap-2">
      <div class="font-semibold">User directory</div>
      <div class="text-xs text-muted-foreground">Manage accounts via API (not websocket).</div>
      <div class="ml-auto flex items-center gap-2">
        <Button variant="secondary" size="sm" :disabled="!hasToken || refreshing" @click="refreshUsers">
          <RefreshCw class="mr-2 h-3.5 w-3.5" />
          Refresh
        </Button>
        <Button size="sm" :disabled="!hasToken" @click="startCreate">
          <Plus class="mr-2 h-4 w-4" />
          New user
        </Button>
      </div>
    </div>

    <div v-if="!hasToken" class="rounded-lg border border-dashed bg-muted/40 px-4 py-3 text-sm text-muted-foreground">
      Authenticate to manage users.
    </div>

    <div v-else class="space-y-2">
      <div v-if="listError" class="rounded-md border border-destructive/50 bg-destructive/10 px-3 py-2 text-sm text-destructive">
        {{ listError }}
      </div>
      <DataTable
        :columns="columns"
        :data="users"
        :filter-column="'username'"
        search-placeholder="Search by name or email"
      />
      <div v-if="loading" class="text-xs text-muted-foreground">Loading users…</div>
    </div>

    <Dialog v-model:open="formOpen">
      <DialogContent class="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{{ editId === null ? "Create user" : "Edit user" }}</DialogTitle>
          <DialogDescription>
            Provide credentials and a role. Password is required when creating; optional when editing.
          </DialogDescription>
        </DialogHeader>

        <div class="space-y-3">
          <div class="space-y-2">
            <Label for="username">Username</Label>
            <Input id="username" v-model="form.username" placeholder="mission.operator" autocomplete="username" />
          </div>
          <div class="space-y-2">
            <Label for="email">Email</Label>
            <Input id="email" v-model="form.email" type="email" placeholder="operator@skyhook.local" autocomplete="email" />
          </div>
          <div class="space-y-2">
            <Label for="password">Password</Label>
            <Input
              id="password"
              v-model="form.password"
              type="password"
              :placeholder="editId === null ? 'Set an initial password' : 'Leave blank to keep current'"
              autocomplete="new-password"
            />
          </div>
          <div class="space-y-2">
            <Label for="role">Role</Label>
            <NativeSelect id="role" v-model="form.role">
              <NativeSelectOption v-for="role in availableRoles" :key="role" :value="role">
                {{ role.charAt(0).toUpperCase() + role.slice(1) }}
              </NativeSelectOption>
            </NativeSelect>
          </div>
          <div v-if="formError" class="rounded-md border border-destructive/50 bg-destructive/10 px-3 py-2 text-xs text-destructive">
            {{ formError }}
          </div>
        </div>

        <DialogFooter class="gap-2 sm:justify-end">
          <Button variant="ghost" @click="formOpen = false">Cancel</Button>
          <Button :disabled="saving" @click="submitForm">{{ saving ? "Saving…" : "Save" }}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <AlertDialog v-model:open="deleteDialogOpen">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete user</AlertDialogTitle>
          <AlertDialogDescription>
            This will remove {{ deleting?.username }} and their role assignments. This cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel @click="deleting = null">Cancel</AlertDialogCancel>
          <Button variant="destructive" @click="confirmDelete">Delete</Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  </div>
</template>
