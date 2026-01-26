import { toast } from "vue-sonner"

type AlertOptions = {
  title: string
  description?: string
  variant?: "default" | "destructive"
}

export const useAlerts = () => ({
  show: ({ title, description, variant = "default" }: AlertOptions) => {
    if (variant === "destructive") {
      toast.error(title, { description })
      return
    }

    toast(title, { description })
  },
})
