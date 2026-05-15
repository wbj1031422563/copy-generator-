import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './styles/main.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)

app.config.errorHandler = (err, _instance, info) => {
  console.error('[文案工坊]', info, err)
}

router.onError((err) => {
  console.error('[路由错误]', err)
})

app.mount('#app')
