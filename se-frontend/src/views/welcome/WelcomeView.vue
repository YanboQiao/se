<template>
  <div class="h-screen overflow-y-scroll snap-y snap-mandatory">
    <section class="welcome-section flex items-center justify-center bg-main-gradient">
      <h1 class="text-4xl font-extrabold text-white drop-shadow">欢迎来到 SE 助手</h1>
    </section>
    <section class="welcome-section flex items-center justify-center bg-indigo-600 text-white">
      <div class="space-y-4 text-center">
        <h2 class="text-3xl font-bold">高效管理课程</h2>
        <p>丰富的工具助你一臂之力</p>
      </div>
    </section>
    <section class="welcome-section flex flex-col items-center justify-center bg-gray-800 text-white">
      <p class="mb-8 text-2xl">立即开启你的旅程</p>
      <router-link to="/login" class="btn-primary">开始使用</router-link>
    </section>
  </div>
</template>

<script setup lang="ts"></script>

<style scoped>
/* 单独的全屏分段，用于滚动吸附 */
.welcome-section {
  @apply h-screen snap-start;
}
</style>
