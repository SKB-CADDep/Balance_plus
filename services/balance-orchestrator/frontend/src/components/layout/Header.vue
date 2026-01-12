<template>
    <header class="top-bar">
      <div class="logo-section">
        <div class="icon-box"></div>
        <span class="logo-text">Баланс +</span>
      </div>
      
      <div class="profile-section">
        <span class="profile-name">{{ user.name }}</span>
        <div class="avatar" :style="{ backgroundImage: `url(${user.avatar_url})` }"></div>
      </div>
    </header>
  </template>
  
  <script setup lang="ts">
  defineProps<{ user: { name: string, avatar_url: string } }>()
  </script>
  
  <style scoped>
  .top-bar {
    display: flex; justify-content: space-between; align-items: center;
    height: 56px; padding: 0 16px; border-bottom: 1px solid #E6E6E6;
  }
  .logo-section, .profile-section { display: flex; align-items: center; gap: 16px; }
  .icon-box { width: 24px; height: 24px; background: #D9D9D9; border-radius: 4px; }
  .logo-text { font-weight: 600; font-size: 16px; }
  .profile-name { font-size: 16px; }
  .avatar { width: 24px; height: 24px; background: #D9D9D9; border-radius: 12px; background-size: cover; }
  </style>