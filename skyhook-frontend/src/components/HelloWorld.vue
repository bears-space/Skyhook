<script setup>
import { ref, onMounted, onBeforeUnmount } from "vue";
import { socket } from "../socket";

defineProps({
  msg: String,
})

const count = ref(0)


const messages = ref([]);

function onMessage(payload) {
  messages.value.push(payload);
}

onMounted(() => {
  socket.on("message", onMessage);

  // example emit
  socket.emit("hello", { from: "vue" });
});

onBeforeUnmount(() => {
  socket.off("message", onMessage); // important: remove handler
});

</script>

<template>
  <h1>{{ msg }}</h1>

  <div class="card">
    <button type="button" @click="count++">count is {{ count }}</button>
    <p>
      Edit
      <code>components/HelloWorld.vue</code> to test HMR
    </p>
  </div>

  <div>
    <h3>WS_Messages</h3>
    <pre>{{ messages }}</pre>
  </div>
</template>

<style scoped>
.read-the-docs {
  color: #888;
}
</style>
