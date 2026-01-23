<script setup>
import { cn } from '@/lib/utils';
import { useEventListener, useMediaQuery, useVModel } from '@vueuse/core';
import { TooltipProvider } from 'radix-vue';
import { computed, ref } from 'vue';
import {
  provideSidebarContext,
  SIDEBAR_COOKIE_MAX_AGE,
  SIDEBAR_COOKIE_NAME,
  SIDEBAR_KEYBOARD_SHORTCUT,
  SIDEBAR_WIDTH_MIN,
  SIDEBAR_WIDTH_MAX,
  SIDEBAR_WIDTH,
  SIDEBAR_WIDTH_ICON,
  SIDEBAR_WIDTH_MOBILE,
} from './utils';

const props = defineProps({
  defaultOpen: { type: Boolean, required: false, default: true },
  open: { type: Boolean, required: false, default: undefined },
  class: { type: null, required: false },
});

const emits = defineEmits(['update:open']);

const isMobile = useMediaQuery('(max-width: 768px)');
const openMobile = ref(false);
const defaultWidth = ref(getResponsiveWidth());
const manualWidth = ref('');

const open = useVModel(props, 'open', emits, {
  defaultValue: props.defaultOpen ?? false,
  passive: props.open === undefined,
});

function setOpen(value) {
  open.value = value; // emits('update:open', value)

  // This sets the cookie to keep the sidebar state.
  document.cookie = `${SIDEBAR_COOKIE_NAME}=${open.value}; path=/; max-age=${SIDEBAR_COOKIE_MAX_AGE}`;
}

function setOpenMobile(value) {
  openMobile.value = value;
}

// Helper to toggle the sidebar.
function toggleSidebar() {
  return isMobile.value
    ? setOpenMobile(!openMobile.value)
    : setOpen(!open.value);
}

function getResponsiveWidth() {
  if (typeof window === 'undefined') return SIDEBAR_WIDTH;
  const vw = window.innerWidth;
  if (vw < 1024) return '14rem';
  if (vw < 1440) return '16rem';
  return '18rem';
}

function setSidebarWidth(widthPx) {
  if (isMobile.value || typeof widthPx !== 'number') return;
  const clamped = Math.min(
    Math.max(widthPx, SIDEBAR_WIDTH_MIN),
    SIDEBAR_WIDTH_MAX,
  );
  manualWidth.value = `${Math.round(clamped)}px`;
}

useEventListener('resize', () => {
  defaultWidth.value = getResponsiveWidth();
});

useEventListener('keydown', (event) => {
  if (
    event.key === SIDEBAR_KEYBOARD_SHORTCUT &&
    (event.metaKey || event.ctrlKey)
  ) {
    event.preventDefault();
    toggleSidebar();
  }
});

// We add a state so that we can do data-state="expanded" or "collapsed".
// This makes it easier to style the sidebar with Tailwind classes.
const state = computed(() => (open.value ? 'expanded' : 'collapsed'));
const appliedWidth = computed(() =>
  isMobile.value
    ? SIDEBAR_WIDTH_MOBILE
    : manualWidth.value || defaultWidth.value || SIDEBAR_WIDTH,
);

provideSidebarContext({
  state,
  open,
  setOpen,
  isMobile,
  openMobile,
  setOpenMobile,
  toggleSidebar,
  setSidebarWidth,
  sidebarWidth: appliedWidth,
});
</script>

<template>
  <TooltipProvider :delay-duration="0">
    <div
      :style="{
        '--sidebar-width': appliedWidth,
        '--sidebar-width-icon': SIDEBAR_WIDTH_ICON,
      }"
      :class="
        cn(
          'group/sidebar-wrapper flex min-h-svh w-full has-[[data-variant=inset]]:bg-sidebar',
          props.class,
        )
      "
      v-bind="$attrs"
    >
      <slot />
    </div>
  </TooltipProvider>
</template>
