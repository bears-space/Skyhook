<script setup lang="ts">
import { computed, type PropType } from "vue"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"

const props = defineProps({
  title: { type: String, default: "Gradient Line Chart" },
  series: {
    type: Array as PropType<Array<{ name: string; type?: string; data: Array<number | null> }>>,
    default: () => [],
  },
  categories: {
    type: Array as PropType<string[]>,
    default: () => [],
  },
  yLabelFormatter: {
    type: Function as PropType<(val: number) => string>,
    default: (val: number) => `${val.toFixed(1)} kbit/s`,
  },
})

const chartOptions = computed(() => ({
  chart: {
    type: "line",
    toolbar: { show: false },
    zoom: { enabled: false },
  },

  legend: { show: false },

  colors: ["#22c55e"],

  stroke: {
    curve: "smooth",
    width: [0, 4], // no area outline, keep line outline
  },

  // Area fades vertically towards 0 (more transparent near baseline)
  fill: {
    type: "gradient",
    gradient: {
      shade: "dark",
      type: "horizontal", // keep the nice left->right hue shift
      shadeIntensity: 1,
      gradientToColors: ["#3b82f6", "#3b82f6"],

      // per-series opacity: [area, line]
      opacityFrom: [0.28, 1],
      opacityTo:   [0.00, 1], // <-- fade down to transparent

      stops: [0, 100],
    },
  },

  dataLabels: { enabled: false },
  markers: { size: 0 },

  grid: { borderColor: "rgba(255,255,255,0.08)" },

  xaxis: {
    categories: props.categories,
    labels: { style: { colors: "rgba(255,255,255,0.6)" } },
  },

  yaxis: {
    min: 0, // <-- makes the fade go towards 0, not towards your min data value
    labels: {
      formatter: props.yLabelFormatter,
      style: { colors: "rgba(255,255,255,0.6)" },
    },
  },

  tooltip: { theme: "dark" },
}))
</script>

<template>
  <Card class="gap-0">
    <CardHeader>
      <CardTitle>{{ props.title }}</CardTitle>
    </CardHeader>
    <CardContent>
      <apexchart type="line" :options="chartOptions" :series="props.series" />
    </CardContent>
    <CardFooter>
      <slot />
    </CardFooter>
  </Card>
</template>
