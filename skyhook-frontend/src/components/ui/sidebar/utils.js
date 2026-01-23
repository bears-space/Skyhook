import { createContext } from 'radix-vue';

export const SIDEBAR_COOKIE_NAME = 'sidebar:state';
export const SIDEBAR_COOKIE_MAX_AGE = 60 * 60 * 24 * 7;
export const SIDEBAR_WIDTH = 'clamp(14rem, 18vw, 18rem)';
export const SIDEBAR_WIDTH_MIN = 224; // px
export const SIDEBAR_WIDTH_MAX = 360; // px
export const SIDEBAR_WIDTH_MOBILE = 'min(18rem, 88vw)';
export const SIDEBAR_WIDTH_ICON = '3rem';
export const SIDEBAR_KEYBOARD_SHORTCUT = 'b';

export const [useSidebar, provideSidebarContext] = createContext('Sidebar');
