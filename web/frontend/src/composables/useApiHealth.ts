import { ref } from 'vue'
import { apiGet } from '@/api/client'

const ready = ref(false)
const online = ref(true)

export function useApiHealth() {
  async function ping() {
    try {
      const data = await apiGet<{ status: string }>('/api/health')
      online.value = data.status === 'up'
    } catch {
      online.value = false
    } finally {
      ready.value = true
    }
  }

  return { ready, online, ping }
}
