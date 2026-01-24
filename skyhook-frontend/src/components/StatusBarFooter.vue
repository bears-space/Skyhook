<script setup>
import Badge from "@/components/ui/badge/Badge.vue";
import { ArrowDownToLine, ArrowUpFromLine } from "lucide-vue-next";
import { computed, ref, onMounted, onBeforeUnmount } from "vue";
import { socket } from "@/socket";

const TOTAL_SECONDS = 5 * 60 * 60;
const remainingSeconds = ref(TOTAL_SECONDS);

const formatRemainingTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `T-${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
};

const timer = ref(formatRemainingTime(remainingSeconds.value));

const tickTimer = () => {
    if (remainingSeconds.value > 0) {
        remainingSeconds.value -= 1;
    }
    timer.value = formatRemainingTime(remainingSeconds.value);
};
const uplinkSpeed = ref("");
const nbSpeed = ref("");
const bbSpeed = ref("");
const wsStatus = ref(socket.connected ? "Online" : "Offline");
const isOnline = computed(() => wsStatus.value === "Online");
const wsBadgeClass = computed(() => {
    if (wsStatus.value === "Online") {
        return "bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300";
    }
    if (wsStatus.value === "Connecting..." || wsStatus.value === "Reconnecting...") {
        return "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300";
    }
    return "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300";
});

const formatSpeed = (minKb, maxKb) =>
    `${(Math.random() * (maxKb - minKb) + minKb).toFixed(1)}kb/s`;

const updateMetrics = () => {
    tickTimer();
    uplinkSpeed.value = formatSpeed(30, 140);
    nbSpeed.value = formatSpeed(90, 260);
    bbSpeed.value = `${(Math.random() * 6).toFixed(1)}mb/s`;
};

let intervalId
onMounted(() => {
    const setOnline = () => wsStatus.value = "Online";
    const setOffline = () => wsStatus.value = "Offline";
    const setReconnecting = () => wsStatus.value = "Reconnecting...";

    updateMetrics();
    intervalId = setInterval(updateMetrics, 1000);

    // Keep the badge in sync with the socket connection status.
    wsStatus.value = socket.connected ? "Online" : "Connecting...";
    socket.on("connect", setOnline);
    socket.on("disconnect", setOffline);
    socket.on("connect_error", setOffline);
    socket.io.on("reconnect_attempt", setReconnecting);
    socket.io.on("reconnect", setOnline);
    socket.io.on("reconnect_error", setOffline);
});
onBeforeUnmount(() => {
    clearInterval(intervalId);
    socket.off("connect");
    socket.off("disconnect");
    socket.off("connect_error");
    socket.io.off("reconnect_attempt");
    socket.io.off("reconnect");
    socket.io.off("reconnect_error");
});

</script>

<template>
    <div class="h-[40px] shrink-0 flex items-center border-t gap-2 px-2">
        <Badge variant="outline" class="cursor-pointer">{{ timer }}</Badge>
        <Badge variant="outline" class="cursor-pointer bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300">
        <ArrowUpFromLine class="h-4 w-4" />
            {{ uplinkSpeed }}
        </Badge>
        <Badge variant="outline" class="cursor-pointer bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300">
        <ArrowDownToLine class="h-4 w-4" />
            {{ nbSpeed }}
        </Badge>
        <Badge variant="outline" class="cursor-pointer bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300">
        <ArrowDownToLine class="h-4 w-4" />
            {{ bbSpeed }}
        </Badge>
        <Badge
            variant="outline"
            class="cursor-pointer ml-auto"
            :class="wsBadgeClass"
            :aria-live="isOnline ? 'off' : 'polite'"
        >
            {{ wsStatus }}
        </Badge>
    </div>
</template>
