import { io } from "socket.io-client"

const socketUrl = "localhost:3000"

export const socket = socketUrl
  ? io(socketUrl, { autoConnect: true })
  : io({ autoConnect: true })
