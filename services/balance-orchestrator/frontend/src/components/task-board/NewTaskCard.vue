<template>
    <div class="new-task-card" @click="$emit('click')">
      <div class="plus-icon">+</div>
      <div class="label">Новая задача</div>
    </div>
  </template>
  
  <style scoped>
  .new-task-card {
    height: 230px;
    border: 2px dashed #ccc;
    border-radius: 4px;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    cursor: pointer; color: #888;
    transition: all 0.2s;
  }
  .new-task-card:hover {
    border-color: #000; color: #000; background: #fafafa;
  }
  .plus-icon { font-size: 40px; margin-bottom: 10px; }
  .label { font-size: 16px; font-weight: 500; }
  </style>