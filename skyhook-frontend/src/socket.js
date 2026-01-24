import { io } from "socket.io-client";

const URL = window.location.origin.split(":").slice(0, 2).join(":") + ":3000";

// Create ONE shared socket instance for the whole app
export const socket = io(URL, {
  autoConnect: false,          // connect manually when you want
  transports: ["websocket"],   // prefer websocket (optional)
  withCredentials: true,       // if you use cookies/auth (optional)
  reconnection: true,
  reconnectionAttempts: 10,
  reconnectionDelay: 500,
});
