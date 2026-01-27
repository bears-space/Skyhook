import http from "http";
import { Server } from "socket.io";

const server = http.createServer();

const io = new Server(server, {
  cors: {
    origin: "http://localhost:5173",
    credentials: true,
  },
});

io.on("connection", (socket) => {
  console.log("client connected", socket.id);

  socket.on("hello", (data) => {
    console.log("hello", data);
    socket.emit("message", { msg: "hi from server", at: Date.now() });
  });

  const t = setInterval(() => {
    socket.emit("message", { msg: "tick", at: Date.now() });
  }, 1000);

  socket.on("disconnect", () => clearInterval(t));
});

server.listen(3000, () => console.log("Socket.IO on :3000"));
