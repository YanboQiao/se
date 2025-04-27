<template>
  <div class="flex min-h-screen items-center justify-center bg-gray-100">
    <div class="w-full max-w-md rounded-xl bg-white p-8 shadow-2xl">
      <h1 class="mb-6 text-center text-2xl font-bold">SE 助手登录</h1>

      <form @submit.prevent="handleSubmit">
        <!-- 用户名 -->
        <div class="mb-4">
          <label for="username" class="mb-2 block text-sm font-medium">用户名</label>
          <input
            id="username"
            v-model="username"
            type="text"
            class="w-full rounded-lg border p-2"
            required
          />
        </div>

        <!-- 密码 -->
        <div class="mb-6">
          <label for="password" class="mb-2 block text-sm font-medium">密码</label>
          <input
            id="password"
            v-model="password"
            type="password"
            class="w-full rounded-lg border p-2"
            required
          />
        </div>

        <!-- 登录按钮 -->
        <button
          type="submit"
          class="w-full rounded-lg bg-blue-600 py-2 font-semibold text-white transition-colors hover:bg-blue-700 disabled:opacity-60"
          :disabled="loading"
        >
          {{ loading ? '登录中…' : '登录' }}
        </button>
      </form>

      <!-- 错误信息 -->
      <p v-if="error" class="mt-4 text-sm text-red-600">{{ error }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/stores/user';

const router = useRouter();
const userStore = useUserStore();

const username = ref('');
const password = ref('');
const error    = ref('');
const loading  = ref(false);

async function handleSubmit() {
  error.value   = '';
  loading.value = true;
  try {
    await userStore.login(username.value, password.value);
    router.push('/home');
  } catch (_) {
    error.value = '登录失败，请检查用户名或密码';
  } finally {
    loading.value = false;
  }
}
</script>
