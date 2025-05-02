<template>
    <!-- 背景：温和渐变 + 中心光斑 -->
    <div
        class="flex min-h-screen items-center justify-center bg-gradient-to-br from-indigo-400/40 via-sky-300/40 to-teal-300/40">
        <!-- 毛玻璃卡片 -->
        <div
            class="backdrop-blur-lg/50 w-full max-w-lg rounded-3xl bg-white/70 p-10 shadow-2xl ring-1 ring-white/60"
        >
            <h1 class="mb-8 text-center text-3xl font-extrabold tracking-wide text-gray-800">
                SE&nbsp;助手登录
            </h1>

            <!-- 角色 Tabs -->
            <div class="mb-8 flex justify-center gap-4">
                <button
                    type="button"
                    :class="role === 'student' ? activeTab : inactiveTab"
                    @click="role = 'student'"
                >
                    学生登录
                </button>
                <button
                    type="button"
                    :class="role === 'teacher' ? activeTab : inactiveTab"
                    @click="role = 'teacher'"
                >
                    教师登录
                </button>
            </div>

            <!-- 登录表单 -->
            <form @submit.prevent="handleSubmit" class="space-y-6">
                <div>
                    <label for="username" class="mb-1 block text-sm font-medium text-gray-700"
                    >用户名</label
                    >
                    <input
                        id="username"
                        v-model="username"
                        type="text"
                        class="focus-visible:outline-none w-full rounded-md border border-gray-300 px-4 py-2 shadow-sm focus:ring-2 focus:ring-indigo-400"
                        required
                    />
                </div>

                <div>
                    <label for="password" class="mb-1 block text-sm font-medium text-gray-700"
                    >密码</label
                    >
                    <input
                        id="password"
                        v-model="password"
                        type="password"
                        class="focus-visible:outline-none w-full rounded-md border border-gray-300 px-4 py-2 shadow-sm focus:ring-2 focus:ring-indigo-400"
                        required
                    />
                </div>

                <button
                    type="submit"
                    class="inline-flex w-full items-center justify-center rounded-md bg-indigo-600 py-2 font-semibold text-white transition hover:bg-indigo-700 disabled:opacity-60"
                    :disabled="loading"
                >
                    {{ loading ? '登录中…' : '登录' }}
                </button>
            </form>

            <!-- 底部链接 / 提示 -->
            <div class="mt-6 text-center">
                <router-link
                    to="/reset-password"
                    class="text-sm text-indigo-700 hover:underline"
                >忘记密码？
                </router-link
                >
                <p v-if="error" class="mt-4 text-sm text-red-600">{{ error }}</p>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import {ref} from 'vue';
import {useRouter} from 'vue-router';
import {useUserStore} from '@/stores/user';

const router = useRouter();
const userStore = useUserStore();

const username = ref('');
const password = ref('');
const role = ref<'student' | 'teacher'>('student');
const error = ref('');
const loading = ref(false);

/* Tailwind class 变量 */
const activeTab =
    'rounded-full bg-indigo-600 px-6 py-2 text-sm font-semibold text-white shadow hover:bg-indigo-700';
const inactiveTab =
    'rounded-full bg-white/40 px-6 py-2 text-sm font-semibold text-indigo-600 hover:bg-white/70';

async function handleSubmit() {
    error.value = '';
    loading.value = true;
    try {
        await userStore.login({
            username: username.value,
            password: password.value,
            role: role.value,
        });

        /* 根据角色跳转 */
        const target = role.value === 'student' ? '/student/home' : '/teacher/home';
        await router.push(target);
    } catch (_) {
        error.value = '登录失败，请检查用户名或密码';
    } finally {
        loading.value = false;
    }
}
</script>