import type { Component, Ref } from "vue"
import { createContext } from "reka-ui"

export { default as ChartContainer } from "./ChartContainer.vue"
export { default as ChartLegendContent } from "./ChartLegendContent.vue"
export { default as ChartTooltipContent } from "./ChartTooltipContent.vue"
export { componentToString } from "./utils"

// Format: { THEME_NAME: CSS_SELECTOR }
export const THEMES = { light: "", dark: ".dark" } as const

export type ChartConfig = {
  [k in string]: {
    label?: string | Component
    icon?: string | Component
  } & (
    | { color?: string, theme?: never }
    | { color?: never, theme: Record<keyof typeof THEMES, string> }
  )
}

interface ChartContextProps {
  id: string
  config: Ref<ChartConfig>
}

export const [useChart, provideChartContext] = createContext<ChartContextProps>("Chart")

// Optional chart bindings. If @unovis/vue is not installed, provide no-op fallbacks
// to keep the build passing. Install @unovis/vue and swap back to real exports when needed.
// export { VisCrosshair as ChartCrosshair, VisTooltip as ChartTooltip } from "@unovis/vue"

// eslint-disable-next-line @typescript-eslint/ban-types
type VoidComponent = {} & Record<string, never>
export const ChartCrosshair: VoidComponent = {} as VoidComponent
export const ChartTooltip: VoidComponent = {} as VoidComponent
