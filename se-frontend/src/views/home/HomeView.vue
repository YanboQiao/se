<template>
    <div class="min-h-screen bg-gray-50">
        <!-- 顶栏 -->
        <header class="flex items-center justify-between bg-white px-6 py-4 shadow-md">
            <h1 class="text-xl font-bold">SE 智能学习助手</h1>
            <div class="flex items-center gap-4">
                <span>欢迎，{{ userStore.username }}</span>
                <button
                    class="rounded-md bg-red-500 px-4 py-2 text-white transition-colors hover:bg-red-600"
                    @click="logout"
                >
                    退出
                </button>
            </div>
        </header>

        <!-- 主内容 -->
        <main class="p-6">
            <h2 class="mb-4 text-lg font-semibold">主面板</h2>
            <!-- 在此集成概念解释、课程问答、习题解析等组件 -->
            <p class="text-gray-700">
                这是主界面占位内容。后续可在此处挂载多智能体功能与聊天面板。
            </p>
        </main>
    </div>
</template>

<script setup lang="ts">
import {useRouter} from 'vue-router';
import {useUserStore} from '@/stores/user';

const router = useRouter();
const userStore = useUserStore();

function logout() {
    userStore.logout();
    router.push('/login');
}
</script>