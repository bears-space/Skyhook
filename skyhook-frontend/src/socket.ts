import { io, type Socket } from "socket.io-client"

const socketUrl =
  import.meta.env.VITE_WS_URL || import.meta.env.VITE_API_URL || ""

const getToken = () => localStorage.getItem("skyhook-auth-token") || undefined

export const socket: Socket = io(socketUrl, {
  autoConnect: false,
  auth: { token: getToken() },
})

export const setSocketAuthToken = (token: string | null | undefined) => {
  socket.auth = { token }
  if (socket.connected) {
    socket.disconnect()
  }
  socket.connect()
}
