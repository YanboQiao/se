<template>
    <!-- 整屏渐变背景 -->
    <div class="min-h-screen flex flex-col items-center justify-center bg-main-gradient text-center px-6">

        <!-- 404 数字 -->
        <h1 class="text-6xl lg:text-8xl font-extrabold text-white drop-shadow mb-6">
            404
        </h1>

        <!-- 提示文字 -->
        <p class="text-xl lg:text-2xl font-semibold text-white/90 mb-4">
            页面走丢了 :(
        </p>
        <p class="text-sm lg:text-base text-white/70 mb-10">
            很抱歉，无法找到你访问的内容。
        </p>

        <!-- 返回按钮 -->
        <div class="space-x-4">
            <button @click="router.back()" class="btn-primary px-8 py-3">
                返回上一页
            </button>
            <router-link to="/" class="btn-primary bg-white text-indigo-700 hover:bg-gray-100">
                回到首页
            </router-link>
        </div>
    </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';

const router = useRouter();
</script>