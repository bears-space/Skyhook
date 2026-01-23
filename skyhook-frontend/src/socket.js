import { io } from "socket.io-client";

const URL = import.meta.env.VITE_SOCKET_URL || window.location.origin;

// Create ONE shared socket instance for the whole app
export const socket = io(URL, {
  autoConnect: false,          // connect manually when you want
  transports: ["websocket"],   // prefer websocket (optional)
  withCredentials: true,       // if you use cookies/auth (optional)
  reconnection: true,
  reconnectionAttempts: 10,
  reconnectionDelay: 500,
});
