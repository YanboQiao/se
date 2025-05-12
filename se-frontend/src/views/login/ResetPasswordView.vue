<!-- src/views/login/ResetPasswordView.vue -->
<template>
    <div class="flex min-h-screen items-center justify-center bg-gray-100">
        <div class="w-full max-w-md rounded-xl bg-white p-8 shadow-2xl">
            <h1 class="mb-6 text-center text-2xl font-bold">重置密码</h1>

            <form @submit.prevent="handleSubmit" class="space-y-6">
                <!-- 身份选择 -->
                <div>
                    <label class="mb-2 block text-sm font-medium">选择身份</label>
                    <div class="flex gap-4">
                        <button
                            type="button"
                            :class="role === 'student' ? 'tab-active' : 'tab-inactive'"
                            @click="role = 'student'">学生</button>
                        <button
                            type="button"
                            :class="role === 'teacher' ? 'tab-active' : 'tab-inactive'"
                            @click="role = 'teacher'">教师</button>
                    </div>
                </div>

                <!-- 邮箱 -->
                <div>
                    <label for="email" class="label">邮箱</label>
                    <input id="email" v-model="email" type="email"
                           class="input-control"
                           placeholder="请输入有效邮箱" required />
                    <p v-if="emailError" class="mt-1 text-xs text-red-600">{{ emailError }}</p>
                </div>

                <!-- 验证码 -->
                <div>
                    <label for="code" class="label">验证码</label>
                    <div class="flex gap-2">
                        <input id="code" v-model="verifyCode" type="text"
                               class="input-control flex-1"
                               placeholder="6 位验证码" required />
                        <button type="button" class="btn-primary whitespace-nowrap px-3"
                                :disabled="cooldown>0 || !isValidEmail"
                                @click="sendCode">
                            {{ cooldown>0 ? `${cooldown} 秒` : '获取验证码' }}
                        </button>
                    </div>
                </div>

                <!-- 新密码 -->
                <div>
                    <label for="newPwd" class="label">新密码</label>
                    <input id="newPwd" v-model="newPassword" type="password"
                           class="input-control" required />
                </div>

                <!-- 确认密码 -->
                <div>
                    <label for="confirmPwd" class="label">确认密码</label>
                    <input id="confirmPwd" v-model="confirmPassword" type="password"
                           class="input-control" required />
                </div>

                <!-- 提交 -->
                <button type="submit" class="btn-primary w-full"
                        :disabled="!formValid || loading">
                    {{ loading ? '提交中…' : '重置密码' }}
                </button>
            </form>

            <!-- 提示信息 -->
            <p v-if="error" class="mt-4 text-sm text-red-600">{{ error }}</p>
            <p v-if="success" class="mt-4 text-sm text-green-600">{{ success }}</p>

            <div class="mt-4 text-center">
                <router-link to="/login" class="link">返回登录</router-link>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
/* --------------------------------------------------------------
 *  ResetPasswordView.vue 逻辑脚本
 *  与后端接口 /api/reset-password/send-code 、
 *            /api/reset-password/email 完全对应
 * ------------------------------------------------------------ */
import { ref, computed } from 'vue';
import axios from 'axios';
import { useUserStore } from '@/stores/user';

const store  = useUserStore();

/* ------------------------ 响应式状态 ------------------------ */
const role            = ref<'student' | 'teacher'>('student');   // 身份
const email           = ref('');                                 // 邮箱
const verifyCode      = ref('');                                 // 6 位验证码
const newPassword     = ref('');                                 // 新密码
const confirmPassword = ref('');                                 // 再次确认
const emailError      = ref('');                                 // 邮箱校验提示
const success         = ref('');                                 // 成功提示
const error           = ref('');                                 // 错误提示
const loading         = ref(false);                              // 提交加载
const cooldown        = ref(0);                                  // 发送验证码倒计时
let   timer: number | null = null;                               // 计时器引用

/* ----------------------- 校验规则 -------------------------- */
const validDomains = ['qq.com','163.com','gmail.com','outlook.com','126.com','foxmail.com'];
const emailRegex   = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/* 合法邮箱校验（带提示） */
const isValidEmail = computed(() => {
    if (!email.value) { emailError.value = ''; return false; }

    if (!emailRegex.test(email.value)) {
        emailError.value = '邮箱格式错误';
        return false;
    }
    if (!validDomains.includes(email.value.split('@')[1])) {
        emailError.value = `仅支持：${validDomains.join(', ')}`;
        return false;
    }
    emailError.value = '';
    return true;
});

/* 整体表单是否可提交 */
const formValid = computed(() =>
    isValidEmail.value &&
    verifyCode.value.length === 6 &&
    !!newPassword.value &&
    newPassword.value === confirmPassword.value
);

/* -------------------- 发送邮箱验证码 ------------------------ */
async function sendCode() {
    if (!isValidEmail.value) return;

    error.value = ''; success.value = '';
    try {
        await axios.post('/api/reset-password/send-code', {
            email: email.value,
            role:  role.value,
        });

        /* 启动 60 秒倒计时 */
        cooldown.value = 60;
        if (timer) clearInterval(timer);
        timer = window.setInterval(() => {
            cooldown.value--;
            if (cooldown.value <= 0 && timer) clearInterval(timer);
        }, 1000);

        success.value = '验证码已发送，请查收邮箱';
    } catch {
        error.value = '发送验证码失败，请稍后再试';
    }
}

/* ---------------------- 提交重置 --------------------------- */
async function handleSubmit() {
    if (!formValid.value) {
        error.value = '请检查输入';
        return;
    }

    loading.value = true;
    error.value   = '';
    success.value = '';

    try {
        await store.resetPasswordByEmail({
            useremail:   email.value,
            emailCode:   verifyCode.value,   // 与后端字段一致
            newPassword: newPassword.value,
            role:        role.value,
        });

        success.value = '密码已修改，可返回登录';
    } catch {
        error.value = '重置失败，请确认验证码或稍后再试';
    } finally {
        loading.value = false;
    }
}
</script>