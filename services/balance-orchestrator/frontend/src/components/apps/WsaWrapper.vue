<template>
  <div class="iframe-container">
    <div v-if="saving" class="overlay">
      <div class="loader-box">
        <div class="spinner"></div>
        <p>💾 Сохранение результатов в GitLab...</p>
      </div>
    </div>

    <iframe
        ref="iframeRef"
        :src="iframeSrc"
        class="app-frame"
    ></iframe>
  </div>
</template>

<script setup lang="ts">
import {ref, computed, onMounted, onUnmounted} from 'vue'
import axios from 'axios'

const props = defineProps<{ taskIid: number | string, projectId: number | string }>()
const emit = defineEmits(['back'])

const saving = ref(false)
const iframeRef = ref<HTMLIFrameElement | null>(null)

const EXTERNAL_APP_URL = 'http://10.202.220.143:5252/calculator'

const iframeSrc = computed(() => {
  return `${EXTERNAL_APP_URL}?taskId=${props.taskIid}&projectId=${props.projectId}&embedded=true`
})

const restoreState = async () => {
  try {
    const res = await axios.get('/api/v1/calculations/latest', {
      params: {
        task_iid: props.taskIid, 
        project_id: props.projectId, 
        app_type: 'valves'
      }
    })

    if (res.data && res.data.found) {
      console.log("✅ Найдены сохраненные данные, отправляем в приложение...")

      const message = {
        type: 'WSA_RESTORE_STATE',
        payload: {
          input: res.data.input_data,
          output: res.data.output_data
        }
      }

      iframeRef.value?.contentWindow?.postMessage(message, '*')
    } else {
      console.log("ℹ️ Сохраненных данных нет, начинаем с чистого листа.")
    }
  } catch (e) {
    console.warn("Ошибка при проверке сохраненных данных:", e)
  }
}

const handleMessage = async (event: MessageEvent) => {
  const {type, payload} = event.data

  if (type === 'WSA_READY') {
    console.log("🔹 Iframe готов (WSA_READY), пробуем восстановить состояние...")
    await restoreState()
  }

  if (type === 'WSA_CALCULATION_COMPLETE') {
    await saveResult(payload)
  }

  if (type === 'WSA_CLOSE') {
    emit('back')
  }
}

const saveResult = async (data: any) => {
  saving.value = true
  
  try {
    console.log("📥 Получено от Iframe:", data)

    const tId = Number(props.taskIid)
    const pId = Number(props.projectId)

    if (isNaN(tId) || isNaN(pId)) {
      throw new Error(`Некорректный ID (NaN). taskIid: ${props.taskIid}, projectId: ${props.projectId}`)
    }

    const requestPayload = {
      task_iid: tId,
      project_id: pId,
      app_type: 'valves',
      input_data: data?.input || null,
      output_data: data?.output || null,
      commit_message: `Расчёт из приложения`
    }

    console.log("📤 Отправляем на бэкенд:", requestPayload)

    await axios.post('/api/v1/calculations/save', requestPayload)
    
    console.log(`✅ Результаты сохранены в задачу #${tId}!`)
  } catch (e: any) {
    console.error("❌ Ошибка сохранения:", e)

    if (e.response && e.response.data) {
      const errorDetails = JSON.stringify(e.response.data, null, 2)
      alert(`Сервер отклонил запрос (400):\n${errorDetails}`)
    } else {
      alert('Ошибка сохранения: ' + e.message)
    }
  } finally {
    saving.value = false
  }
}

onMounted(() => window.addEventListener('message', handleMessage))
onUnmounted(() => window.removeEventListener('message', handleMessage))
</script>

<style scoped>
.iframe-container {
  width: 100%;
  height: 100%;
  display: flex;
  position: relative;
}

.app-frame {
  width: 100%;
  height: 100%;
  border: none;
  display: block;
}

.overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
  backdrop-filter: blur(2px);
}

.loader-box {
  text-align: center;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.spinner {
  width: 40px;
  height: 40px;
  margin: 0 auto 15px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>