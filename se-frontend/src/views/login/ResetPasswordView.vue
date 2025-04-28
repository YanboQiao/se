<template>
    <div class="flex min-h-screen items-center justify-center bg-gray-100">
        <div class="w-full max-w-md rounded-xl bg-white p-8 shadow-2xl">
            <h1 class="mb-6 text-center text-2xl font-bold">重置密码</h1>

            <form @submit.prevent="handleSubmit">
                <!-- 用户名 / 邮箱 -->
                <div class="mb-4">
                    <label for="username" class="mb-2 block text-sm font-medium">用户名 / 邮箱</label>
                    <input
                        id="username"
                        v-model="username"
                        type="text"
                        class="w-full rounded-lg border p-2"
                        required
                    />
                </div>

                <!-- 新密码 -->
                <div class="mb-4">
                    <label for="newPassword" class="mb-2 block text-sm font-medium">新密码</label>
                    <input
                        id="newPassword"
                        v-model="newPassword"
                        type="password"
                        class="w-full rounded-lg border p-2"
                        required
                    />
                </div>

                <!-- 确认密码 -->
                <div class="mb-6">
                    <label for="confirmPassword" class="mb-2 block text-sm font-medium">确认密码</label>
                    <input
                        id="confirmPassword"
                        v-model="confirmPassword"
                        type="password"
                        class="w-full rounded-lg border p-2"
                        required
                    />
                </div>

                <!-- 重置按钮 -->
                <button
                    type="submit"
                    class="w-full rounded-lg bg-blue-600 py-2 font-semibold text-white transition-colors hover:bg-blue-700 disabled:opacity-60"
                    :disabled="loading"
                >
                    {{ loading ? '提交中…' : '重置密码' }}
                </button>
            </form>

            <!-- 错误 / 成功信息 -->
            <p v-if="error" class="mt-4 text-sm text-red-600">{{ error }}</p>
            <p v-if="success" class="mt-4 text-sm text-green-600">{{ success }}</p>
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
const newPassword = ref('');
const confirmPassword = ref('');
const error = ref('');
const success = ref('');
const loading = ref(false);

async function handleSubmit() {
    error.value = '';
    success.value = '';
    if (newPassword.value !== confirmPassword.value) {
        error.value = '两次输入的密码不一致';
        return;
    }
    loading.value = true;
    try {
        await userStore.resetPassword({
            username: username.value,
            newPassword: newPassword.value,
        });
        success.value = '密码已成功重置，正在跳转至登录页…';
        setTimeout(() => router.push('/'), 2000);
    } catch (_) {
        error.value = '重置失败，请确认用户名 / 邮箱';
    } finally {
        loading.value = false;
    }
}
</script>
