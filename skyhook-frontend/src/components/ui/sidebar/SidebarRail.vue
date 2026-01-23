<script setup>
import { cn } from '@/lib/utils';
import { useSidebar } from './utils';

const props = defineProps({
  class: { type: null, required: false },
});

const { toggleSidebar, setSidebarWidth, isMobile } = useSidebar();

let didDrag = false;

function onPointerDown(event) {
  if (isMobile.value) return;
  didDrag = false;
  event.preventDefault();

  const startX = event.clientX;

  const handleMove = (moveEvent) => {
    const delta = Math.abs(moveEvent.clientX - startX);
    if (delta > 2) didDrag = true;
    setSidebarWidth(moveEvent.clientX);
  };

  const handleUp = () => {
    window.removeEventListener('pointermove', handleMove);
    window.removeEventListener('pointerup', handleUp);
  };

  window.addEventListener('pointermove', handleMove);
  window.addEventListener('pointerup', handleUp);
}

function onClick(event) {
  if (didDrag) {
    didDrag = false;
    event.preventDefault();
    return;
  }
  toggleSidebar();
}
</script>

<template>
  <button
    data-sidebar="rail"
    aria-label="Toggle Sidebar"
    :tabindex="-1"
    title="Toggle Sidebar"
    :class="
      cn(
        'absolute inset-y-0 z-20 hidden w-4 -translate-x-1/2 transition-all ease-linear after:absolute after:inset-y-0 after:left-1/2 after:w-[2px] hover:after:bg-sidebar-border group-data-[side=left]:-right-4 group-data-[side=right]:left-0 sm:flex',
        '[[data-side=left]_&]:cursor-w-resize [[data-side=right]_&]:cursor-e-resize',
        '[[data-side=left][data-state=collapsed]_&]:cursor-e-resize [[data-side=right][data-state=collapsed]_&]:cursor-w-resize',
        'group-data-[collapsible=offcanvas]:translate-x-0 group-data-[collapsible=offcanvas]:after:left-full group-data-[collapsible=offcanvas]:hover:bg-sidebar',
        '[[data-side=left][data-collapsible=offcanvas]_&]:-right-2',
        '[[data-side=right][data-collapsible=offcanvas]_&]:-left-2',
        props.class,
      )
    "
    @pointerdown="onPointerDown"
    @click="onClick"
  >
    <slot />
  </button>
</template>
