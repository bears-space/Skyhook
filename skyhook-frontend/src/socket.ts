import { io } from "socket.io-client"

const socketUrl = import.meta.env.VITE_SOCKET_URL

export const socket = socketUrl
  ? io(socketUrl, { autoConnect: true })
  : io({ autoConnect: true })
