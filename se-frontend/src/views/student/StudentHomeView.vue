<template>
    <div class="min-h-screen flex flex-col bg-main-gradient">
        <!-- 顶部栏 -->
        <header class="p-6 lg:p-8 bg-white/30 backdrop-blur-sm shadow flex items-center justify-between relative">
            <h1 class="text-xl lg:text-2xl font-bold text-gray-800">
                {{ greeting }}
            </h1>
            <div class="flex items-center gap-4">
                <!-- AI 学习助手入口 -->
                <a href="http://localhost:8001/llms" target="_blank" rel="noopener noreferrer"
                   class="bg-indigo-600/90 text-white px-4 py-2 rounded-lg text-sm hover:bg-indigo-700 transition shadow-card">
                    学习有困难？大模型来帮忙！
                </a>
            </div>
        </header>

        <!-- 主体 -->
        <main class="flex-1 p-4 lg:p-8 grid lg:grid-cols-[260px_1fr_260px] gap-6">
            <!-- 待办任务 -->
            <section class="bg-glass p-6 overflow-y-auto">
                <h2 class="text-lg font-semibold text-indigo-700 mb-4">待办任务</h2>
                <ul class="space-y-3">
                    <li v-for="todo in todos" :key="todo.id" class="text-sm text-gray-800">
                        • {{ todo.title }}
                    </li>
                    <li v-if="!todos.length" class="text-gray-500 text-sm">暂无任务</li>
                </ul>
            </section>

            <!-- 课程列表 -->
            <section class="bg-glass p-6 overflow-y-auto">
                <h2 class="text-lg font-semibold text-indigo-700 mb-4">我的课程</h2>
                <ul class="space-y-3">
                    <li v-for="course in courses" :key="course.id" class="flex justify-between items-center">
                        <router-link :to="`/course/${course.id}`" class="link hover:font-medium">
                            {{ course.name }}
                        </router-link>
                        <span @click="dropCourse(course.id)" class="text-red-600 text-xs cursor-pointer ml-2">[退课]</span>
                    </li>
                    <li v-if="!courses.length" class="text-gray-500 text-sm">暂无课程</li>
                </ul>
            </section>

            <!-- 消息 -->
            <section class="bg-glass p-6 overflow-y-auto">
                <h2 class="text-lg font-semibold text-indigo-700 mb-4">老师评语</h2>
                <ul class="space-y-3">
                    <li v-for="msg in messages" :key="msg.id" class="text-sm text-gray-800">
                        {{ msg.content }}
                    </li>
                    <li v-if="!messages.length" class="text-gray-500 text-sm">暂无消息</li>
                </ul>
            </section>
        </main>
    </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import axios from 'axios';
import { useUserStore } from '@/stores/user';

/* ---------- 状态 ---------- */
const store     = useUserStore();
const display   = computed(() => store.username || store.useremail || '同学');
const greeting  = computed(() => `${display.value}同学，欢迎回来！`);

interface Course   { id: string; name: string }
interface Todo     { id: string; title: string }
interface Message  { id: string; content: string }

const courses     = ref<Course[]>([]);
const todos       = ref<Todo[]>([]);
const messages    = ref<Message[]>([]);
const showJoinForm = ref(false);
const newCourseId  = ref('');
const joining      = ref(false);
const joinError    = ref('');

/* ---------- 数据拉取 ---------- */
async function fetchStudentData() {
    try {
        const {data} = await axios.get('/api/student/dashboard', {
            params: {
                useremail: store.useremail,
                token: store.token
            },
        });
        courses.value = data.courses || [];
    } catch (error) {
        console.error('获取教师数据失败:', error);
    }
}
onMounted(fetchStudentData);

</script>
