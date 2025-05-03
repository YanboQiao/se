<template>
    <!-- ===== 整屏背景 + 内部容器 ===== -->
    <div
        class="min-h-screen flex flex-col bg-gradient-to-br
           from-indigo-400/40 via-sky-300/40 to-teal-300/40">

        <!-- ===== 顶部品牌栏 ===== -->
        <header class="p-6 lg:p-10">
            <h1 class="text-3xl lg:text-4xl font-extrabold tracking-widest text-white drop-shadow">
                SE&nbsp;助手
            </h1>
        </header>

        <!-- ===== 主体：宽屏栅格 ===== -->
        <main
            class="flex-1 flex items-center justify-center px-4 lg:px-8">

            <!-- 宽屏容器：最大 6xl，左右留空气 -->
            <div
                class="w-full max-w-6xl bg-white/70 backdrop-blur-lg/50
               rounded-3xl shadow-card ring-1 ring-white/60
               p-8 sm:p-12 lg:p-16">

                <!-- ========== 顶部标题区 ========== -->
                <section class="mb-12">
                    <h2 class="text-3xl lg:text-4xl font-extrabold tracking-wide text-gray-800">
                        欢迎登录&nbsp;SE&nbsp;助手
                    </h2>
                    <p class="mt-2 text-gray-600">
                        请使用您的账号信息登录系统
                    </p>
                </section>

                <!-- ========== 角色 Tabs ========== -->
                <section class="mb-14">
                    <div class="flex flex-wrap gap-4">
                        <button
                            type="button"
                            :class="role === 'student' ? activeTab : inactiveTab"
                            @click="role = 'student'">
                            学生登录
                        </button>
                        <button
                            type="button"
                            :class="role === 'teacher' ? activeTab : inactiveTab"
                            @click="role = 'teacher'">
                            教师登录
                        </button>
                    </div>
                </section>

                <!-- ========== 登录表单 ========== -->
                <form @submit.prevent="handleSubmit"
                      class="grid gap-y-10 md:grid-cols-2 md:gap-x-16">

                    <!-- 用户名 -->
                    <div class="flex flex-col gap-3">
                        <label for="useremail" class="text-sm font-medium text-gray-700">
                            用户名
                        </label>
                        <input
                            id="useremail"
                            v-model="useremail"
                            type="text"
                            class="rounded-md border border-gray-300 px-5 py-4
                     text-lg shadow-sm focus:ring-2 focus:ring-indigo-500"
                            required />
                    </div>

                    <!-- 密码 -->
                    <div class="flex flex-col gap-3">
                        <label for="password" class="text-sm font-medium text-gray-700">
                            密码
                        </label>
                        <input
                            id="password"
                            v-model="password"
                            type="password"
                            class="rounded-md border border-gray-300 px-5 py-4
                     text-lg shadow-sm focus:ring-2 focus:ring-indigo-500"
                            required />
                    </div>

                    <!-- 登录按钮（在桌面端独占一行） -->
                    <div class="md:col-span-2">
                        <button
                            type="submit"
                            class="inline-flex w-full items-center justify-center rounded-md bg-indigo-600
                     py-4 text-lg font-semibold text-white transition hover:bg-indigo-700
                     disabled:opacity-60"
                            :disabled="loading">
                            {{ loading ? '登录中…' : '登录' }}
                        </button>
                    </div>
                </form>

                <!-- ========== 底部提示 ========== -->
                <footer class="mt-12 text-center">
                    <router-link to="/reset-password"
                                 class="text-sm text-indigo-700 hover:underline">
                        忘记密码？
                    </router-link>
                    <p v-if="error" class="mt-4 text-sm text-red-600">{{ error }}</p>
                </footer>
            </div>
        </main>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/stores/user';

const router = useRouter();
const userStore = useUserStore();

const useremail = ref('');
const password = ref('');
const role = ref<'student' | 'teacher'>('student');
const error = ref('');
const loading = ref(false);

/* Tailwind class 变量 */
const activeTab =
    'rounded-full bg-indigo-600 px-8 py-3 text-base font-semibold text-white shadow hover:bg-indigo-700';
const inactiveTab =
    'rounded-full bg-white/40 px-8 py-3 text-base font-semibold text-indigo-600 hover:bg-white/70';

async function handleSubmit() {
    error.value = '';
    loading.value = true;
    try {
        await userStore.login({
            useremail: useremail.value,
            password: password.value,
            role: role.value,
        });

        const target = role.value === 'student' ? '/student/home' : '/teacher/home';
        await router.push(target);
    } catch (_) {
        error.value = '登录失败，请检查用户名或密码';
    } finally {
        loading.value = false;
    }
}
</script>

<style scoped>
/* ===== 背景渐变流动 ===== */
@keyframes gradientShift {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
.bg-gradient-to-br {
    background-size: 400% 400%;
    animation: gradientShift 20s ease infinite;
}

/* ===== 毛玻璃 & 阴影 ===== */
.backdrop-blur-lg\/50 {
    backdrop-filter: blur(24px) saturate(180%);
}
.shadow-card {
    box-shadow:
        0 28px 40px -10px rgba(0,0,0,0.18),
        0 12px 18px -10px rgba(0,0,0,0.05);
}

/* ===== 按钮交互 ===== */
button[disabled] { cursor: not-allowed; }
button:active:not([disabled]) {
    transform: translateY(2px);
    transition: transform .1s;
}
</style>