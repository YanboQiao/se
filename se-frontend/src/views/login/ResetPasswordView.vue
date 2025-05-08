<template>
    <div class="flex min-h-screen items-center justify-center bg-gray-100">
        <div class="w-full max-w-md rounded-xl bg-white p-8 shadow-2xl">
            <h1 class="mb-6 text-center text-2xl font-bold">重置密码</h1>

            <form @submit.prevent="handleSubmit">
                <!-- 身份选择 -->
                <div class="mb-6">
                    <label class="mb-2 block text-sm font-medium">选择身份</label>
                    <div class="flex gap-4">
                        <button
                            type="button"
                            :class="role === 'student' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'"
                            class="flex-1 rounded-lg px-4 py-2 font-medium transition-colors"
                            @click="role = 'student'"
                        >
                            学生
                        </button>
                        <button
                            type="button"
                            :class="role === 'teacher' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'"
                            class="flex-1 rounded-lg px-4 py-2 font-medium transition-colors"
                            @click="role = 'teacher'"
                        >
                            教师
                        </button>
                    </div>
                </div>
                
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
                            placeholder="输入6位验证码"
                            required
                        />
                        <button 
                            type="button"
                            @click="requestVerifyCode"
                            class="whitespace-nowrap rounded-lg bg-blue-500 px-3 text-white hover:bg-blue-600 disabled:bg-gray-400"
                            :disabled="cooldown > 0 || !isValidEmail || verifyCodeChecked"
                        >
                            {{ cooldown > 0 ? `${cooldown}秒后重试` : '获取验证码' }}
                        </button>
                    </div>
                </div>

                <!-- 验证码确认按钮 -->
                <div class="mb-6">
                    <button 
                        type="button"
                        @click="checkVerifyCode"
                        class="w-full rounded-lg bg-green-600 py-2 font-semibold text-white transition-colors hover:bg-green-700 disabled:opacity-60"
                        :disabled="!verifyCode || verifyCodeChecked || cooldown === 0"
                    >
                        确认验证码
                    </button>
                </div>

                <!-- 新密码 (只在验证成功后显示) -->
                <div v-if="verifyCodeChecked" class="mb-4">
                    <label for="newPassword" class="mb-2 block text-sm font-medium">新密码</label>
                    <input
                        id="newPassword"
                        v-model="newPassword"
                        type="password"
                        class="w-full rounded-lg border p-2"
                        required
                    />
                </div>

                <!-- 确认密码 (只在验证成功后显示) -->
                <div v-if="verifyCodeChecked" class="mb-6">
                    <label for="confirmPassword" class="mb-2 block text-sm font-medium">确认密码</label>
                    <input
                        id="confirmPassword"
                        v-model="confirmPassword"
                        type="password"
                        class="w-full rounded-lg border p-2"
                        required
                    />
                </div>

                <!-- 重置按钮 (只在验证成功后显示) -->
                <button
                    v-if="verifyCodeChecked"
                    type="submit"
                    class="w-full rounded-lg bg-blue-600 py-2 font-semibold text-white transition-colors hover:bg-blue-700 disabled:opacity-60"
                    :disabled="loading || !isValidEmail || !verifyCode || !newPassword || !confirmPassword"
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

const role = ref<'student' | 'teacher'>('student'); // 新增：身份选择
const email = ref('');
const emailError = ref('');
const verifyCode = ref('');
const newPassword = ref('');
const confirmPassword = ref('');
const error = ref('');
const success = ref('');
const loading = ref(false);
const cooldown = ref(0);
const verifyCodeChecked = ref(false); // 新增：验证码是否已验证
const verifyCodeExpired = ref(false); // 新增：验证码是否过期
let countdownTimer: number | null = null; // 新增：倒计时计时器引用

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

// 请求验证码前先检查邮箱是否已注册
async function requestVerifyCode() {
    if (!isValidEmail.value) return;
    
    // 重置验证状态
    verifyCodeChecked.value = false;
    verifyCodeExpired.value = false;
    
    try {
        // 首先检查邮箱是否已注册
        const checkResponse = await axios.post('/api/check-email', { 
            email: email.value,
            role: role.value
        });
        
        if (checkResponse.data.status === 'error') {
            error.value = `该邮箱未注册${role.value === 'student' ? '学生' : '教师'}账号，请先注册`;
            return;
        }
        
        // 如果已注册，发送验证码
        await axios.post('/api/send-verify-code', { 
            email: email.value,
            role: role.value
        });
        
        // 清除可能存在的旧计时器
        if (countdownTimer !== null) {
            clearInterval(countdownTimer);
        }

        // 设置倒计时
        cooldown.value = 60;
        const timer = setInterval(() => {
            cooldown.value--;
            if (cooldown.value <= 0) {
                clearInterval(timer);
                if (!verifyCodeChecked.value) {
                    verifyCodeExpired.value = true;
                }
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

// 新增：验证验证码
async function checkVerifyCode() {
    if (!verifyCode.value) {
        error.value = '请输入验证码';
        return;
    }
    
    if (verifyCodeExpired.value) {
        error.value = '验证码已过期，请重新获取';
        return;
    }
    
    try {
        const response = await axios.post('/api/check-verify-code', {
            email: email.value,
            verifyCode: verifyCode.value,
            role: role.value
        });
        
        if (response.data.status === 'success') {
            verifyCodeChecked.value = true;
            success.value = '验证码正确，请设置新密码';
            error.value = '';
            // 停止倒计时 - 新增
            if (countdownTimer !== null) {
                clearInterval(countdownTimer);
                countdownTimer = null;
            }
        } else {
            error.value = '验证码错误，请重新输入';
            success.value = '';
        }
    } catch (err) {
        error.value = '验证失败，请稍后再试';
    }
}

// 重置密码
async function handleSubmit() {
    error.value = '';
    success.value = '';
    
    if (!verifyCodeChecked.value) {
        error.value = '请先验证验证码';
        return;
    }
    
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
            role: role.value
        });
        success.value = '密码已成功重置，正在跳转至登录页…';
        setTimeout(() => router.push('/login'), 2000);
    } catch (_) {
        error.value = '重置失败，请确认信息是否正确';
    } finally {
        loading.value = false;
    }
}
</script>
