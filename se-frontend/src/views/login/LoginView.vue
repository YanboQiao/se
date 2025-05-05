<template>
    <!-- 整屏背景 -->
    <div class="min-h-screen flex flex-col bg-main-gradient">

        <!-- 顶部品牌 -->
        <header class="p-6 lg:p-10">
            <h1 class="text-3xl lg:text-4xl font-extrabold tracking-widest text-white drop-shadow">
                SE&nbsp;助手
            </h1>
        </header>

        <!-- 登录卡片 -->
        <main class="flex-1 flex items-center justify-center px-4 lg:px-8">
            <div class="w-full max-w-3xl bg-glass p-8 sm:p-12 lg:p-16">

                <!-- 标题 -->
                <section class="mb-12">
                    <h2 class="text-3xl lg:text-4xl font-extrabold text-gray-800">
                        欢迎登录&nbsp;SE&nbsp;助手
                    </h2>
                    <p class="mt-2 text-gray-600">请使用邮箱 + 密码登录系统</p>
                </section>

                <!-- 角色切换 -->
                <section class="mb-12">
                    <div class="flex gap-4">
                        <button
                            type="button"
                            :class="role === 'student' ? activeTab : inactiveTab"
                            @click="role = 'student'">学生</button>
                        <button
                            type="button"
                            :class="role === 'teacher' ? activeTab : inactiveTab"
                            @click="role = 'teacher'">教师</button>
                    </div>
                </section>

                <!-- 表单 -->
                <form @submit.prevent="handleSubmit" class="space-y-8">
                    <div>
                        <label for="email" class="block text-sm font-medium text-gray-700 mb-2">
                            邮箱&nbsp;/&nbsp;Email
                        </label>
                        <input id="email" v-model="useremail" type="email"
                               class="input-control" required />
                    </div>

                    <div>
                        <label for="password" class="block text-sm font-medium text-gray-700 mb-2">
                            密码
                        </label>
                        <input id="password" v-model="password" type="password"
                               class="input-control" required />
                    </div>

                    <button type="submit" class="btn-primary w-full" :disabled="loading">
                        {{ loading ? '登录中…' : '登录' }}
                    </button>
                </form>

                <!-- 底部链接 -->
                <footer class="mt-10 text-center space-y-4">
                    <router-link to="/reset-password" class="link">忘记密码？</router-link>
                    <br />
                    <router-link to="/register" class="link">还没有账号？去注册</router-link>
                    <p v-if="error" class="text-red-600 text-sm mt-4">{{ error }}</p>
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
const store  = useUserStore();

const useremail = ref('');
const password  = ref('');
const role      = ref<'student' | 'teacher'>('student');
const error     = ref('');
const loading   = ref(false);

const activeTab =
    'tab-active';
const inactiveTab =
    'tab-inactive';

async function handleSubmit() {
    error.value   = '';
    loading.value = true;
    try {
        await store.login({ useremail: useremail.value, password: password.value, role: role.value });
        const target = role.value === 'student' ? '/student/home' : '/teacher/home';
        await router.push(target);
    } catch {
        error.value = '登录失败，请检查邮箱或密码';
    } finally {
        loading.value = false;
    }
}
</script>