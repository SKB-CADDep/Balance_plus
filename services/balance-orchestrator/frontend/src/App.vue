<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

import Header from './components/layout/Header.vue'
import TaskCard from './components/task-board/TaskCard.vue'
import NewTaskCard from './components/task-board/NewTaskCard.vue'
import CreateTaskModal from './components/task-board/CreateTaskModal.vue'
import WsaWrapper from './components/apps/WsaWrapper.vue'

// --- ТИПЫ ---
interface Task {
  iid: number
  project_id: number
  project_name: string
  created_at: string
  business_status: { text: string; color: string; key: string }
  title: string
  description?: string
  formatted_date: string
  calc_type: string | null
  calc_type_human?: string
  bureau?: { code: string; name: string; color: string } | null
  labels: string[]
  state: string
  due_date?: string
}

interface Bureau {
  id: string
  label: string
  color: string
  modules: { id: string; label: string }[]
}

// --- CONSTANTS ---
const BUREAUS: Bureau[] = [
  {
    id: 'btr',
    label: 'БТР',
    color: '#1976D2',
    modules: [
      { id: 'btr-balances', label: 'Балансы' },
      { id: 'btr-velocity-triangles', label: 'Треугольники скоростей' },
      { id: 'btr-steam-distribution', label: 'Парораспределение' },
      { id: 'btr-condensers', label: 'Конденсаторы' },
      { id: 'btr-valve-stems', label: 'Штоки клапанов' },
      { id: 'btr-aux-calcs', label: 'Вспомогательные' },
      { id: 'btr-wsprop', label: 'WSProp' },
      { id: 'btr-gasdynamics-ansys', label: 'Газодинамика (Ansys)' },
      { id: 'btr-thermal-expansions', label: 'Тепловые перемещения' }
    ]
  },
  {
    id: 'bpr',
    label: 'БПР',
    color: '#26A69A',
    modules: [
      { id: 'bpr-flowpath-design', label: 'Проектирование ПЧ' },
      { id: 'bpr-cylinders', label: 'Цилиндры' },
      { id: 'bpr-heat-exchangers', label: 'Теплообменники' },
      { id: 'bpr-materials', label: 'Материалы' },
      { id: 'bpr-acts', label: 'Акты' }
    ]
  },
  {
    id: 'bvp',
    label: 'БВП',
    color: '#7E57C2',
    modules: [
      { id: 'bvp-static-shaft-deflection', label: 'Прогибы' },
      { id: 'bvp-static-alignment', label: 'Центровка' },
      { id: 'bvp-dynamic-bending-vibration', label: 'Изгибные колебания' },
      { id: 'bvp-dynamic-torsional-vibration', label: 'Крутильные колебания' },
      { id: 'bvp-working-blades', label: 'Рабочие лопатки' }
    ]
  }
]

// --- STATE ---
const currentUser = ref({ name: 'Загрузка...', avatar_url: '' })
const tasks = ref<Task[]>([])
const activeBureauId = ref<string | null>(null) // null = Все задачи
const activeModuleId = ref<string | null>(null) // null = Все модули выбранного бюро
const showCreateModal = ref(false)
const searchQuery = ref('')
const loading = ref(true)
const sortOrder = ref<'desc' | 'asc'>('desc')

const activeView = ref<'dashboard' | 'app-valves'>('dashboard')
const currentTaskIid = ref(0)
const currentProjectId = ref(0)

// --- API ---
const fetchData = async () => {
  try {
    const [userRes, tasksRes] = await Promise.all([
      axios.get('/api/v1/user/me'),
      axios.get('/api/v1/tasks?state=opened')
    ])
    currentUser.value = userRes.data
    tasks.value = tasksRes.data
  } catch (e) { console.error(e) } 
  finally { loading.value = false }
}

const createTask = async (data: any) => {
  try {
    const res = await axios.post('/api/v1/tasks', {
      title: data.title,
      description: data.description,
      labels: data.labels,
      project_id: data.project_id
    })

    const newTaskId = res.data.iid
    const newProjectId = data.project_id

    // Автоматически создаём ветку после создания задачи
    await axios.post(`/api/v1/tasks/${newTaskId}/branch`, {
      project_id: newProjectId
    })

    alert(`✅ Задача #${newTaskId} создана, ветка готова!`)
    showCreateModal.value = false
    await fetchData()
  } catch (e: any) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  }
}

const handleTaskClick = (task: Task) => {
  // Обновлено для новых кодов модулей
  if (task.calc_type === 'btr-valve-stems' || task.calc_type === 'valves' || task.labels.includes('valves') || task.title.toLowerCase().includes('шток')) {
    if (!confirm(`Открыть приложение "Расчёт штоков" для задачи #${task.iid}?`)) return;
    currentTaskIid.value = task.iid
    currentProjectId.value = task.project_id
    activeView.value = 'app-valves'
  } else {
    alert(`Для типа "${task.calc_type || 'неизвестно'}" интерфейс еще не готов.`)
  }
}

const handleSubmitTask = async (task: Task) => {
  if (!confirm(`Вы уверены, что хотите завершить задачу "${task.title}" и создать Merge Request?`)) return;
  
  try {
    loading.value = true
    const res = await axios.post(`/api/v1/tasks/${task.iid}/submit`, null, { params: { project_id: task.project_id } })
    alert(`✅ Merge Request создан!\nСсылка: ${res.data.mr_url}`)
    // Можно открыть ссылку в новой вкладке
    window.open(res.data.mr_url, '_blank')
  } catch (e: any) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}

// --- COMPUTED ---
const activeBureau = computed(() => {
  if (!activeBureauId.value) return null
  return BUREAUS.find(b => b.id === activeBureauId.value) || null
})

const filteredTasks = computed(() => {
  let result = [...tasks.value]

  // 1. Фильтр по Бюро
  if (activeBureauId.value) {
    result = result.filter(t => t.bureau?.code === activeBureauId.value)
  }

  // 2. Фильтр по Модулю
  if (activeModuleId.value) {
    result = result.filter(t => t.calc_type === activeModuleId.value)
  }

  // 3. Поиск
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(t => 
      t.title.toLowerCase().includes(q) || 
      t.project_name.toLowerCase().includes(q) ||
      (t.calc_type_human && t.calc_type_human.toLowerCase().includes(q))
    )
  }

  // 4. Сортировка
  result.sort((a, b) => {
    const dateA = new Date(a.created_at).getTime()
    const dateB = new Date(b.created_at).getTime()
    return sortOrder.value === 'asc' ? dateA - dateB : dateB - dateA
  })
  return result
})

const selectBureau = (bureauId: string | null) => {
  activeBureauId.value = bureauId
  activeModuleId.value = null // Сбрасываем модуль при смене бюро
}

const toggleSort = () => {
  sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
}

onMounted(fetchData)
</script>

<template>
  <!-- Обертка layout должна быть всегда -->
  <div class="layout">
    
    <!-- БЛОК 1: ДАШБОРД -->
    <!-- v-show лучше чем v-if здесь, чтобы не терять скролл при возврате, но v-if надежнее для изоляции -->
    <div v-if="activeView === 'dashboard'" class="dashboard-wrapper">
      <Header :user="currentUser" />
      
      <main class="main-container">
        <!-- УРОВЕНЬ 1: БЮРО -->
        <nav class="bureau-nav">
          <a 
            href="#" 
            class="nav-link" 
            :class="{ active: activeBureauId === null }"
            @click.prevent="selectBureau(null)"
          >
            Все задачи
          </a>
          
          <a 
            v-for="b in BUREAUS" :key="b.id" 
            href="#"
            class="nav-link"
            :class="{ active: activeBureauId === b.id }"
            :style="{ 
              borderColor: activeBureauId === b.id ? b.color : 'transparent', 
              color: activeBureauId === b.id ? b.color : 'inherit' 
            }"
            @click.prevent="selectBureau(b.id)"
          >
            {{ b.label }}
          </a>
        </nav>

        <!-- УРОВЕНЬ 2: МОДУЛИ (Показываем только если выбрано Бюро) -->
        <div v-if="activeBureau" class="modules-nav">
          <button 
            class="module-chip" 
            :class="{ active: activeModuleId === null }"
            @click="activeModuleId = null"
          >
            Все модули
          </button>
          
          <button 
            v-for="mod in activeBureau.modules" :key="mod.id"
            class="module-chip"
            :class="{ active: activeModuleId === mod.id }"
            @click="activeModuleId = mod.id"
          >
            {{ mod.label }}
          </button>
        </div>

        <div class="actions-row">
          <div class="search-input">
            <span class="icon">🔍</span>
            <input v-model="searchQuery" type="text" placeholder="Поиск..." />
          </div>
          <button class="action-btn" @click="toggleSort"><span class="icon">⇅</span> Сортировка</button>
          <button class="action-btn primary" @click="fetchData">↻ Обновить</button>
        </div>

        <div class="task-grid">
          <NewTaskCard @click="showCreateModal = true" />
          <div v-if="loading">Загрузка...</div>
          <TaskCard 
            v-for="task in filteredTasks" :key="task.iid" :task="task"
            @click="handleTaskClick(task)"
            @submit="handleSubmitTask"  
          />
        </div>
      </main>
    </div>

    <!-- БЛОК 2: ПРИЛОЖЕНИЕ (ПОЛНЫЙ ЭКРАН ПОВЕРХ ВСЕГО) -->
    <div v-else-if="activeView === 'app-valves'" class="fullscreen-app">
      <WsaWrapper 
        :taskIid="currentTaskIid"
        :projectId="currentProjectId"
        @back="activeView = 'dashboard'" 
      />
    </div>

    <CreateTaskModal v-if="showCreateModal" @close="showCreateModal = false" @create="createTask" />
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* === ГЛОБАЛЬНЫЙ СБРОС (Самое важное для фикса верстки) === */
*, *::before, *::after {
  box-sizing: border-box;
}

body {
  margin: 0;
  padding: 0;
  font-family: 'Inter', sans-serif;
  background-color: #FFFFFF;
  /* Возвращаем нормальный скролл для страницы */
  overflow-y: auto; 
  overflow-x: hidden;
}

.layout {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
}

/* === СТИЛИ ДАШБОРДА === */
.dashboard-wrapper {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.top-bar { 
  width: 100%;
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  height: 56px; 
  padding: 0 32px; 
  border-bottom: 1px solid #E6E6E6; 
  background: #fff; 
}

.main-container { 
  width: 100%;
  max-width: 100%; /* Защита от вылезания */
  padding: 32px; 
  flex: 1;
}

.bureau-nav { 
  display: flex; 
  gap: 30px; 
  margin-bottom: 20px; 
  border-bottom: 1px solid #eee; 
  overflow-x: auto; /* Если меню длинное, добавляем скролл */
}

.nav-link { 
  text-decoration: none; color: #000; font-size: 16px; 
  padding-bottom: 12px; border-bottom: 2px solid transparent; 
  transition: all 0.2s; white-space: nowrap; 
}
.nav-link:hover { color: #666; }
.nav-link.active { font-weight: 600; border-bottom-width: 2px; border-bottom-style: solid; }

.modules-nav {
  display: flex;
  gap: 12px;
  margin-bottom: 30px;
  flex-wrap: wrap;
}

.module-chip {
  padding: 8px 16px;
  border: 1px solid #D9D9D9;
  border-radius: 20px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
  font-family: inherit;
  transition: all 0.2s;
  white-space: nowrap;
}

.module-chip:hover {
  background: #F5F5F5;
  border-color: #999;
}

.module-chip.active {
  background: #000;
  color: #fff;
  border-color: #000;
}

.actions-row { display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }

.search-input { 
  flex-grow: 1; display: flex; align-items: center; 
  padding: 0 12px; height: 40px; border: 1px solid #D9D9D9; 
  border-radius: 4px; background: #fff; min-width: 200px; 
}
.search-input input { border: none; outline: none; width: 100%; font-size: 16px; font-family: inherit; }

.action-btn { 
  display: flex; align-items: center; justify-content: center; 
  padding: 0 20px; height: 40px; background: #F2F2F2; 
  border: none; border-radius: 4px; cursor: pointer; 
  font-size: 15px; font-family: inherit; gap: 8px; 
  transition: background 0.2s; white-space: nowrap;
}
.action-btn:hover { background: #e0e0e0; }
.action-btn.primary { background: #000; color: #fff; }
.action-btn.primary:hover { background: #333; }

.task-grid { 
  display: grid; 
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); 
  gap: 24px; 
  padding-bottom: 50px; 
}

/* === СТИЛИ ПОЛНОЭКРАННОГО ПРИЛОЖЕНИЯ === */
.fullscreen-app {
  position: fixed; /* Фиксируем поверх всего */
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: #fff;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* Внутри приложения свои скроллы */
}
</style>