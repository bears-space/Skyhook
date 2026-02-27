const API_BASE =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.DEV ? "http://localhost:3000" : "")

type ApiOptions = {
  token: string
  method?: string
  body?: Record<string, any>
}

async function apiRequest(path: string, { token, method = "GET", body }: ApiOptions) {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: body ? JSON.stringify(body) : undefined,
  })

  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const message = data.error || data.message || `Request failed with ${res.status}`
    throw new Error(message)
  }
  return data
}

// Users -----------------------------------------------------------------------

export type UserRecord = {
  id: number
  username: string
  email: string | null
  roles: string[]
  is_active: boolean
  created_at?: string | null
  updated_at?: string | null
}

export type UserPayload = {
  username?: string
  email?: string | null
  password?: string
  roles?: string[]
  is_active?: boolean
}

export async function listUsers(token: string): Promise<UserRecord[]> {
  const data = await apiRequest("/api/users", { token })
  return (data.users ?? []) as UserRecord[]
}

export async function createUser(token: string, payload: Required<UserPayload>): Promise<UserRecord> {
  const data = await apiRequest("/api/users", { token, method: "POST", body: payload })
  return data.user as UserRecord
}

export async function updateUserApi(token: string, id: number, payload: UserPayload): Promise<UserRecord> {
  const data = await apiRequest(`/api/users/${id}`, { token, method: "PATCH", body: payload })
  return data.user as UserRecord
}

export async function deleteUserApi(token: string, id: number): Promise<void> {
  await apiRequest(`/api/users/${id}`, { token, method: "DELETE" })
}

export { API_BASE }
