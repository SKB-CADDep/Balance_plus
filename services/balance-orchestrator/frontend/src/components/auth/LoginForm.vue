<script setup lang="ts">
import { ref } from 'vue'

import { login } from '../../api/axios'


const emit = defineEmits<{ authenticated: [] }>()
const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

const submit = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    await login(username.value.trim(), password.value)
    password.value = ''
    emit('authenticated')
  } catch (error: unknown) {
    const responseError = error as { response?: { data?: { detail?: string } } }
    errorMessage.value = responseError.response?.data?.detail || 'Не удалось войти в систему'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="auth-page">
    <form class="login-card" @submit.prevent="submit">
      <div class="login-mark">Б+</div>
      <h1>Вход в Баланс+</h1>
      <p>Используйте учётную запись УТЗ</p>

      <label for="username">Имя пользователя</label>
      <input
        id="username"
        v-model="username"
        autocomplete="username"
        autofocus
        required
      />

      <label for="password">Пароль</label>
      <input
        id="password"
        v-model="password"
        type="password"
        autocomplete="current-password"
        required
      />

      <div v-if="errorMessage" class="login-error" role="alert">{{ errorMessage }}</div>
      <button type="submit" :disabled="loading">
        {{ loading ? 'Проверяем…' : 'Войти' }}
      </button>
    </form>
  </main>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: #f4f5f7;
}
.login-card {
  width: min(100%, 400px);
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 36px;
  border: 1px solid #e1e3e6;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.08);
}
.login-mark {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  background: #111;
  color: #fff;
  font-weight: 700;
}
h1 { margin: 8px 0 0; font-size: 26px; }
p { margin: 0 0 14px; color: #666; }
label { margin-top: 6px; font-size: 14px; font-weight: 600; }
input {
  width: 100%;
  height: 42px;
  padding: 0 12px;
  border: 1px solid #cfd2d6;
  border-radius: 6px;
  font: inherit;
}
input:focus { outline: 2px solid #111; outline-offset: 1px; }
button {
  height: 44px;
  margin-top: 12px;
  border: 0;
  border-radius: 6px;
  background: #111;
  color: #fff;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}
button:disabled { opacity: 0.6; cursor: wait; }
.login-error {
  padding: 10px 12px;
  border-radius: 6px;
  background: #fff0f0;
  color: #b42318;
  font-size: 14px;
}
</style>
