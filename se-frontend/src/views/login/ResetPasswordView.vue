<template>
    <div class="flex min-h-screen items-center justify-center bg-gray-100">
        <div class="w-full max-w-md rounded-xl bg-white p-8 shadow-2xl">
            <h1 class="mb-6 text-center text-2xl font-bold">重置密码</h1>

            <form @submit.prevent="handleSubmit">
                <!-- 邮箱 -->
                <div class="mb-4">
                    <label for="email" class="mb-2 block text-sm font-medium">邮箱</label>
                    <input
                        id="email"
                        v-model="email"
                        type="email"
                        class="w-full rounded-lg border p-2"
                        placeholder="请输入有效的邮箱地址"
                        required
                    />
                    <p v-if="emailError" class="mt-1 text-xs text-red-600">{{ emailError }}</p>
                </div>

                <!-- 验证码 -->
                <div class="mb-4">
                    <label for="verifyCode" class="mb-2 block text-sm font-medium">验证码</label>
                    <div class="flex gap-2">
                        <input
                            id="verifyCode"
                            v-model="verifyCode"
                            type="text"
                            class="w-full rounded-lg border p-2"
                            required
                        />
                        <button 
                            type="button"
                            @click="requestVerifyCode"
                            class="whitespace-nowrap rounded-lg bg-blue-500 px-3 text-white hover:bg-blue-600 disabled:bg-gray-400"
                            :disabled="cooldown > 0 || !isValidEmail"
                        >
                            {{ cooldown > 0 ? `${cooldown}秒后重试` : '获取验证码' }}
                        </button>
                    </div>
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
                    :disabled="loading || !isValidEmail || !verifyCode"
                >
                    {{ loading ? '提交中…' : '重置密码' }}
                </button>
            </form>

            <!-- 错误 / 成功信息 -->
            <p v-if="error" class="mt-4 text-sm text-red-600">{{ error }}</p>
            <p v-if="success" class="mt-4 text-sm text-green-600">{{ success }}</p>
            
            <div class="mt-4 text-center">
                <router-link to="/login" class="text-sm text-blue-600 hover:underline">
                    返回登录
                </router-link>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import {ref, computed} from 'vue';
import {useRouter} from 'vue-router';
import {useUserStore} from '@/stores/user';
import axios from 'axios';

const router = useRouter();
const userStore = useUserStore();

const email = ref('');
const emailError = ref('');
const verifyCode = ref('');
const newPassword = ref('');
const confirmPassword = ref('');
const error = ref('');
const success = ref('');
const loading = ref(false);
const cooldown = ref(0);

// 验证邮箱格式
const isValidEmail = computed(() => {
    const validDomains = ['qq.com', '163.com', 'gmail.com', 'outlook.com', '126.com', 'foxmail.com'];
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (!email.value) {
        emailError.value = '';
        return false;
    }
    
    if (!emailRegex.test(email.value)) {
        emailError.value = '请输入有效的邮箱地址';
        return false;
    }
    
    const domain = email.value.split('@')[1];
    if (!validDomains.includes(domain)) {
        emailError.value = '目前只支持：' + validDomains.join(', ');
        return false;
    }
    
    emailError.value = '';
    return true;
});

// 请求验证码
async function requestVerifyCode() {
    if (!isValidEmail.value) return;
    
    try {
        // 调用发送验证码API
        await axios.post('/api/send-verify-code', { email: email.value });
        
        // 设置倒计时
        cooldown.value = 60;
        const timer = setInterval(() => {
            cooldown.value--;
            if (cooldown.value <= 0) {
                clearInterval(timer);
            }
        }, 1000);
        
        success.value = '验证码已发送，请检查邮箱';
        setTimeout(() => {
            success.value = '';
        }, 3000);
    } catch (err) {
        error.value = '发送验证码失败，请稍后再试';
    }
}

async function handleSubmit() {
    error.value = '';
    success.value = '';
    
    if (!isValidEmail.value) {
        error.value = '请输入有效的邮箱地址';
        return;
    }
    
    if (newPassword.value !== confirmPassword.value) {
        error.value = '两次输入的密码不一致';
        return;
    }
    
    loading.value = true;
    try {
        await userStore.resetPasswordByEmail({
            email: email.value,
            verifyCode: verifyCode.value,
            newPassword: newPassword.value,
        });
        success.value = '密码已成功重置，正在跳转至登录页…';
        setTimeout(() => router.push('/login'), 2000);
    } catch (_) {
        error.value = '重置失败，请确认邮箱和验证码是否正确';
    } finally {
        loading.value = false;
    }
}
</script>
