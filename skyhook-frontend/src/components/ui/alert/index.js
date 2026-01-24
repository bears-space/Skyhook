import { cva } from 'class-variance-authority';

export { default as Alert } from './Alert.vue';
export { default as AlertDescription } from './AlertDescription.vue';
export { default as AlertTitle } from './AlertTitle.vue';

export const alertVariants = cva(
  'relative w-full rounded-lg border p-4',
  {
    variants: {
      variant: {
        default: 'bg-card text-card-foreground border-border/70',
        destructive:
          'border-destructive/50 text-destructive bg-destructive/10 dark:border-destructive dark:bg-destructive/15',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
);
