<template>
    <div class="h-screen overflow-y-scroll snap-y snap-mandatory">
        <!-- 首屏欢迎语 -->
        <section class="welcome-section flex items-center justify-center bg-main-gradient">
            <h1 class="welcome-slide slide-from-right text-4xl font-extrabold text-white drop-shadow">
                欢迎来到 SE 助手
            </h1>
        </section>

        <!-- 多智能体，教师批改 -->
        <section class="welcome-section flex items-center justify-center bg-indigo-600 text-white">
            <div class="welcome-slide slide-from-left space-y-4 text-center">
                <h2 class="text-3xl font-bold">多智能体协同</h2>
                <p>帮助教师一键批改作业</p>
            </div>
        </section>

        <!-- 学生掌握概念，理解错题 -->
        <section class="welcome-section flex items-center justify-center bg-purple-600 text-white">
            <div class="welcome-slide slide-from-right space-y-4 text-center">
                <h2 class="text-3xl font-bold">学习辅助</h2>
                <p>帮助学生掌握概念，理解错题</p>
            </div>
        </section>

        <!-- 入口按钮 -->
        <section class="welcome-section flex flex-col items-center justify-center bg-gray-800 text-white">
            <p class="welcome-slide slide-from-left mb-8 text-2xl">立即开启你的旅程</p>
            <router-link to="/login" class="welcome-slide slide-from-right btn-primary">开始使用</router-link>
        </section>
    </div>
</template>

<script setup lang="ts">
import {onMounted, onUnmounted} from 'vue';

onMounted(() => {
    const slides = document.querySelectorAll<HTMLElement>('.welcome-slide');
    const observer = new IntersectionObserver(
        entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('active');
                    observer.unobserve(entry.target);
                }
            });
        },
        {threshold: 0.4}
    );
    slides.forEach(el => observer.observe(el));
    onUnmounted(() => observer.disconnect());
});
</script>

<style scoped>
/* 单独的全屏分段，用于滚动吸附 */
.welcome-section {
    @apply h-screen snap-start;
}

/* 横向滑入动画 */
.welcome-slide {
    @apply transform opacity-0 transition-all duration-700;
}

.slide-from-left {
    transform: translateX(-50%);
}

.slide-from-right {
    transform: translateX(50%);
}

.welcome-slide.active {
    transform: translateX(0);
    opacity: 1;
}
</style>