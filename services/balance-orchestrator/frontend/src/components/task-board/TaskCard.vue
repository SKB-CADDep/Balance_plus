<template>
  <div class="task-card" @click="$emit('click')">
    
    <!-- HEADER: Заголовок и Статус -->
    <div class="card-header">
      <h3 class="card-title" :title="task.title">{{ task.title }}</h3>
      
      <div class="status-badge" :style="{ borderColor: task.business_status.color }">
        <span 
          class="status-dot" 
          :style="{ backgroundColor: task.business_status.color }"
        ></span>
        <span 
          class="status-text" 
          :style="{ color: task.business_status.color }"
        >
          {{ task.business_status.text }}
        </span>
      </div>
    </div>

    <!-- BODY: Описание -->
    <p class="card-desc">
      {{ task.description || 'Нет описания' }}
    </p>

    <!-- FOOTER: Даты, Кнопки, Проект -->
    <div class="card-footer">
      
      <div class="footer-meta">
        <div class="dates">
          <span class="date-item">📅 {{ task.formatted_date }}</span>
          <span v-if="task.due_date" class="date-item overdue">⏳ {{ formatDate(task.due_date) }}</span>
        </div>
        
        <div class="actions">
           <button class="btn-submit" @click.stop="$emit('submit', task)" title="Создать Merge Request">
             🏁 Завершить
           </button>
        </div>
      </div>

      <div class="project-row" :title="task.project_name">
        <span class="project-icon">🏭</span>
        <span class="project-name">{{ task.project_name }}</span>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ task: any }>()
defineEmits(['click', 'submit'])

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: '2-digit' })
}
</script>

<style scoped>
.task-card {
  background: #FFFFFF;
  border: 1px solid #E6E6E6;
  border-radius: 8px;
  padding: 16px;
  height: 240px;
  display: flex; 
  flex-direction: column; 
  justify-content: space-between;
  cursor: pointer; 
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}

.task-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0,0,0,0.08);
  border-color: #ccc;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.card-title {
  margin: 0;
  font-weight: 600;
  font-size: 16px;
  line-height: 1.3;
  color: #111;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 12px;
  border: 1px solid;
  background: #fff;
  flex-shrink: 0;
}

.status-dot {
  width: 8px; height: 8px; border-radius: 50%;
}

.status-text {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  white-space: nowrap;
}

.card-desc {
  font-size: 14px;
  line-height: 1.4;
  color: #666;
  flex-grow: 1;
  margin: 0 0 16px 0;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.card-footer {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.footer-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #888;
}

.dates { display: flex; gap: 10px; }
.date-item.overdue { color: #d32f2f; font-weight: 500; }

.btn-submit {
  background: white;
  border: 1px solid #28a745;
  color: #28a745;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-submit:hover { background: #28a745; color: white; }

.project-row {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #F5F5F5;
  padding: 6px 10px;
  border-radius: 4px;
  width: 100%;
}

.project-icon { font-size: 14px; }

.project-name {
  font-size: 12px;
  font-weight: 600;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
}
</style>