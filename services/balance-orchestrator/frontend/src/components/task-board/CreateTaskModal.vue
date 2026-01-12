<template>
    <div class="modal-overlay" @click.self="$emit('close')">
      <div class="modal-content">
        <h2>Новая задача</h2>
        
        <!-- 1. Название -->
        <div class="form-group">
          <label>Название задачи</label>
          <input v-model="form.title" placeholder="Краткая суть задачи" ref="titleInput" />
        </div>

        <!-- 2. Проект (Autocomplete) -->
        <div class="form-group relative">
          <label>Проект (Турбина)</label>
          <input 
            v-model="projectSearch" 
            @focus="showProjectDropdown = true"
            @input="fetchProjects"
            @blur="closeDropdown"
            placeholder="Начните вводить название..." 
            :class="{ 'has-value': form.project_id }"
          />
          <!-- Выпадающий список -->
          <div v-if="showProjectDropdown" class="dropdown-list">
            <div v-if="loadingProjects" class="dropdown-item disabled">Загрузка...</div>
            <div v-else-if="projects.length === 0" class="dropdown-item disabled">Ничего не найдено</div>
            
            <div 
              v-for="p in projects" :key="p.id" 
              class="dropdown-item"
              @mousedown.prevent="selectProject(p)"
            >
              {{ p.name }}
            </div>
          </div>
        </div>

        <!-- 3. Модуль -->
        <div class="form-group">
          <label>Модуль (Тип расчёта)</label>
          <select v-model="form.type">
            <option disabled value="">Выберите модуль...</option>
            
            <optgroup label="БТР (Теплотехника)">
              <option value="module::btr-balances">Балансы</option>
              <option value="module::btr-velocity-triangles">Треугольники скоростей</option>
              <option value="module::btr-steam-distribution">Парораспределение</option>
              <option value="module::btr-condensers">Конденсаторы</option>
              <option value="module::btr-valve-stems">Штоки клапанов</option>
              <option value="module::btr-aux-calcs">Вспомогательные</option>
              <option value="module::btr-wsprop">WSProp</option>
              <option value="module::btr-gasdynamics-ansys">Газодинамика (Ansys)</option>
              <option value="module::btr-thermal-expansions">Тепловые перемещения</option>
            </optgroup>

            <optgroup label="БПР (Прочность)">
              <option value="module::bpr-flowpath-design">Проектирование ПЧ</option>
              <option value="module::bpr-cylinders">Цилиндры</option>
              <option value="module::bpr-heat-exchangers">Теплообменники</option>
              <option value="module::bpr-materials">Материалы</option>
              <option value="module::bpr-acts">Акты</option>
            </optgroup>

            <optgroup label="БВП (Вибрация)">
              <option value="module::bvp-static-shaft-deflection">Прогибы</option>
              <option value="module::bvp-static-alignment">Центровка</option>
              <option value="module::bvp-dynamic-bending-vibration">Изгибные колебания</option>
              <option value="module::bvp-dynamic-torsional-vibration">Крутильные колебания</option>
              <option value="module::bvp-working-blades">Рабочие лопатки</option>
            </optgroup>
          </select>
        </div>

        <!-- 4. Описание -->
        <div class="form-group">
          <label>Описание</label>
          <textarea v-model="form.description" rows="3" placeholder="Детали задачи..."></textarea>
        </div>

        <div class="actions">
          <button @click="$emit('close')" class="btn-cancel">Отмена</button>
          <button @click="submit" class="btn-submit" :disabled="!isFormValid">Создать</button>
        </div>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { reactive, ref, onMounted, computed } from 'vue'
  import axios from 'axios'
  
  const emit = defineEmits(['close', 'create'])
  
  const form = reactive({
    title: '',
    project_id: null as number | null,
    type: '',
    description: ''
  })
  
  // Логика поиска проектов
  const projectSearch = ref('')
  const projects = ref<any[]>([])
  const showProjectDropdown = ref(false)
  const loadingProjects = ref(false)
  
  const fetchProjects = async () => {
    loadingProjects.value = true
    try {
      const res = await axios.get('/api/v1/projects', { params: { search: projectSearch.value } })
      projects.value = res.data
    } catch (e) {
      console.error(e)
      projects.value = []
    } finally {
      loadingProjects.value = false
    }
  }
  
  const selectProject = (project: any) => {
    form.project_id = project.id
    projectSearch.value = project.name // Показываем имя в поле
    showProjectDropdown.value = false
  }
  
  // Закрытие дропдауна при клике снаружи
  const closeDropdown = () => {
    setTimeout(() => {
      showProjectDropdown.value = false
    }, 200)
  }
  
  const isFormValid = computed(() => form.title && form.project_id && form.type)
  
  const submit = () => {
    // Определяем лейблы
    let bureauLabel = ''
    if (form.type.includes('btr-')) bureauLabel = 'bureau::btr'
    if (form.type.includes('bpr-')) bureauLabel = 'bureau::bpr'
    if (form.type.includes('bvp-')) bureauLabel = 'bureau::bvp'
    
    // Отправляем
    emit('create', {
      title: form.title,
      description: form.description,
      project_id: form.project_id,
      labels: [form.type, bureauLabel] // Только модуль и бюро. Проект задается через project_id
    })
  }
  
  onMounted(() => {
    fetchProjects() // Загрузить список сразу
  })
  </script>
  
  <style scoped>
  .modal-overlay {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.5);
    display: flex; justify-content: center; align-items: center;
    z-index: 1000;
  }
  .modal-content {
    background: white; padding: 30px; border-radius: 8px; width: 500px;
    max-height: 90vh;
    overflow-y: auto;
  }
  .form-group { margin-bottom: 15px; }
  .form-group label { display: block; margin-bottom: 5px; font-weight: 500; font-size: 14px;}
  input, select, textarea { 
    width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; font-family: inherit;
    box-sizing: border-box;
  }
  .relative { position: relative; }
  
  .dropdown-list {
    position: absolute; top: 100%; left: 0; right: 0;
    background: white; border: 1px solid #ccc; border-radius: 4px;
    max-height: 200px; overflow-y: auto; z-index: 10;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin-top: 2px;
  }
  
  .dropdown-item {
    padding: 8px 12px; cursor: pointer; font-size: 14px;
  }
  .dropdown-item:hover { background: #f0f0f0; }
  .dropdown-item.disabled { color: #999; cursor: default; }
  
  .has-value { border-color: #28a745 !important; }
  
  .actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
  button { padding: 8px 16px; border-radius: 4px; border: none; cursor: pointer; }
  .btn-cancel { background: #eee; }
  .btn-submit { background: #000; color: white; }
  .btn-submit:disabled { background: #ccc; cursor: not-allowed; }
  </style>