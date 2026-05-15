<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchAuthStatus, login } from '@/api/auth'
import UiButton from '@/components/ui/UiButton.vue'

const route = useRoute()
const router = useRouter()

const user = ref('admin')
const password = ref('')
const loading = ref(false)
const error = ref('')

onMounted(async () => {
  try {
    const s = await fetchAuthStatus()
    if (!s.enabled || s.authenticated) {
      const redirect = (route.query.redirect as string) || '/dashboard'
      await router.replace(redirect)
    }
  } catch {
    /* show form */
  }
})

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await login(user.value.trim(), password.value)
    const redirect = (route.query.redirect as string) || '/dashboard'
    await router.replace(redirect)
  } catch (e) {
    error.value = (e as Error).message || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-brand">
        <span class="login-mark" aria-hidden="true">鱼</span>
        <div>
          <h1>闲鱼文案工坊</h1>
          <p>请输入管理员分配的账号密码</p>
        </div>
      </div>

      <form class="login-form" @submit.prevent="submit">
        <label>
          <span>用户名</span>
          <input v-model="user" type="text" autocomplete="username" required />
        </label>
        <label>
          <span>密码</span>
          <input
            v-model="password"
            type="password"
            autocomplete="current-password"
            required
          />
        </label>
        <p v-if="error" class="login-error" role="alert">{{ error }}</p>
        <UiButton type="submit" variant="primary" block :disabled="loading">
          {{ loading ? '登录中…' : '登录' }}
        </UiButton>
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background:
    radial-gradient(ellipse 80% 50% at 50% -20%, rgba(255, 106, 0, 0.12), transparent),
    var(--bg);
}
.login-card {
  width: min(400px, 100%);
  padding: 32px 28px;
  border-radius: var(--radius-lg);
  background: var(--surface);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-lg);
}
.login-brand {
  display: flex;
  gap: 14px;
  align-items: center;
  margin-bottom: 28px;
}
.login-mark {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--accent), #ff8c42);
  color: #fff;
  font-size: 22px;
  font-weight: 700;
  display: grid;
  place-items: center;
}
.login-brand h1 {
  margin: 0;
  font-size: 1.25rem;
}
.login-brand p {
  margin: 4px 0 0;
  font-size: 0.85rem;
  color: var(--muted);
}
.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.login-form label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 0.85rem;
  color: var(--muted);
}
.login-form input {
  padding: 10px 12px;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--text);
  font-size: 1rem;
}
.login-form input:focus {
  outline: 2px solid rgba(255, 106, 0, 0.35);
  border-color: var(--accent);
}
.login-error {
  margin: 0;
  font-size: 0.85rem;
  color: var(--danger);
}
</style>
