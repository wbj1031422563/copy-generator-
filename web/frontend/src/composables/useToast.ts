import { useToastStore } from '@/stores/toast'

export function useToast() {
  const store = useToastStore()
  return {
    message: store.message,
    visible: store.visible,
    toast: store.show,
  }
}
