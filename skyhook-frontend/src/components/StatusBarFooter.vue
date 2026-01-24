<script setup>
import Badge from "@/components/ui/badge/Badge.vue";
import { ArrowDownToLine, ArrowUpFromLine } from "lucide-vue-next";
</script>

<template>
    <div class="h-[40px] shrink-0 flex items-center border-t gap-2 px-2">
        <Badge variant="outline">T-5:23:49</Badge>
        <Badge variant="outline" class="bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300">
        <ArrowUpFromLine class="h-4 w-4" />
        44.3kb/s
        </Badge>
        <Badge variant="outline" class="bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300">
        <ArrowDownToLine class="h-4 w-4" />
        NB 120.5kb/s
        </Badge>
        <Badge variant="outline" class="bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300">
        <ArrowDownToLine class="h-4 w-4" />
        BB 2.1mb/s
        </Badge>
        <Badge variant="outline" class="bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300">
        WS
        </Badge>
    </div>
</template>