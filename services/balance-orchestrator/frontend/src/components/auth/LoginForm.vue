<script setup lang="ts">
import { login } from '../../api/axios'


defineProps<{ error?: string }>()

const submit = () => {
  login()
}
</script>

<template>
  <main class="auth-page">
    <div class="login-card">
      <div class="login-mark">Б+</div>
      <h1>Вход в Баланс+</h1>
      <p>Вход выполняется через заводской GitLab и учётную запись УТЗ</p>

      <div v-if="error" class="login-error" role="alert">{{ error }}</div>
      <button type="button" autofocus @click="submit">
        Войти через GitLab
      </button>
    </div>
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
.login-error {
  padding: 10px 12px;
  border-radius: 6px;
  background: #fff0f0;
  color: #b42318;
  font-size: 14px;
}
</style>
