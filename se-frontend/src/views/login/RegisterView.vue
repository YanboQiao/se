<template>
    <div class="min-h-screen flex flex-col gradient-bg">
        <header class="p-6 lg:p-10">
            <h1 class="text-3xl lg:text-4xl font-extrabold tracking-widest text-white drop-shadow">
                SE&nbsp;助手
            </h1>
        </header>

        <main class="flex-1 flex items-center justify-center px-4 lg:px-8">
            <div class="w-full max-w-xl glass-card p-8 sm:p-12 lg:p-16">
                <section class="mb-10 text-center">
                    <h2 class="text-3xl lg:text-4xl font-extrabold text-gray-800">用户注册</h2>
                    <p class="mt-2 text-gray-600">请填写以下信息完成注册</p>
                </section>

                <form @submit.prevent="handleRegister" class="space-y-8">
                    <div>
                        <label for="username" class="block text-sm font-medium text-gray-700 mb-2">用户名</label>
                        <input id="username" v-model="username" type="text" class="form-input" required />
                    </div>
                    <div>
                        <label for="useremail" class="block text-sm font-medium text-gray-700 mb-2">邮箱 / Email</label>
                        <input 
                            id="useremail" 
                            v-model="useremail" 
                            type="email" 
                            class="form-input" 
                            placeholder=""
                            @blur="validateEmailFormat" 
                            required 
                        />
                        <p class="mt-1 text-xs text-gray-500">
                            支持的邮箱: qq.com, 163.com, gmail.com, outlook.com, 126.com, foxmail.com
                        </p>
                        <p v-if="emailError" class="mt-1 text-xs text-red-600">{{ emailError }}</p>
                    </div>
                    <!-- 身份选择 -->
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-2">注册身份</label>
                      <div class="flex gap-4">
                        <label>
                          <input type="radio" v-model="role" value="student" />
                          学生
                        </label>
                        <label>
                          <input type="radio" v-model="role" value="teacher" />
                          教师
                        </label>
                      </div>
                    </div>
                    
                    <div>
                        <label for="password" class="block text-sm font-medium text-gray-700 mb-2">密码</label>
                        <input id="password" v-model="password" type="password" class="form-input" required />
                    </div>
                    <button type="submit" :disabled="loading || !!emailError" class="btn-primary w-full">
                        {{ loading ? '注册中…' : '注册' }}
                    </button>
                </form>

                <div class="mt-8 text-center">
                    <router-link to="/login" class="text-sm text-indigo-700 hover:underline">
                        已有账号？返回登录
                    </router-link>
                    <p v-if="error" class="mt-4 text-sm text-red-600">{{ error }}</p>
                    <p v-if="success" class="mt-4 text-sm text-green-600">{{ success }}</p>
                </div>
            </div>
        </main>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();

const username = ref('');
const useremail = ref('');
const emailError = ref('');
const password = ref('');
const role = ref<'student' | 'teacher'>('student'); // 默认学生
const loading = ref(false);
const error = ref('');
const success = ref('');

// 邮箱验证函数
function validateEmailFormat() {
    emailError.value = '';
    
    if (!useremail.value) return;
    
    const validDomains = ['qq.com', '163.com', 'gmail.com', 'outlook.com', '126.com', 'foxmail.com'];
    const emailRegex = /^[^\s@]+@([^\s@]+)\.[^\s@]+$/;
    
    if (!emailRegex.test(useremail.value)) {
        emailError.value = '请输入有效的邮箱地址';
        return;
    }
    
    const domain = useremail.value.split('@')[1];
    if (!validDomains.includes(domain)) {
        emailError.value = '目前只支持：' + validDomains.join(', ');
        return;
    }
}

async function handleRegister() {
    error.value = '';
    success.value = '';
    
    // 再次验证邮箱
    validateEmailFormat();
    if (emailError.value) {
        return;
    }
    
    loading.value = true;
    try {
        await axios.post('/api/register', {
            username: username.value,
            useremail: useremail.value,
            password: password.value,
            role: role.value,
        });
        success.value = '注册成功，正在跳转到登录…';
        setTimeout(() => router.push('/login'), 1500);
    } catch (err) {
        if (axios.isAxiosError(err) && err.response) {
            error.value = err.response.data?.message || '注册失败，请检查信息后重试';
        } else {
            error.value = '注册失败，请检查信息后重试';
        }
    } finally {
        loading.value = false;
    }
}
</script>
