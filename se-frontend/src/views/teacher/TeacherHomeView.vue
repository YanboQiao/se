<template>
    <div class="min-h-screen flex flex-col bg-main-gradient">
        <!-- 顶部栏 -->
        <header class="p-6 lg:p-8 bg-white/30 backdrop-blur-sm shadow">
            <h1 class="text-xl lg:text-2xl font-bold text-gray-800">
                {{ greeting }}
            </h1>
        </header>

        <!-- 主体 -->
        <main class="flex-1 p-4 lg:p-8 grid lg:grid-cols-[260px_1fr_260px] gap-6">
            <!-- 待批改 -->
            <section class="bg-glass p-6 overflow-y-auto">
                <h2 class="text-lg font-semibold text-emerald-700 mb-4">待批改作业</h2>
                <ul class="space-y-3">
                    <li v-for="task in gradingList" :key="task.id" class="text-sm text-gray-800">
                        • {{ task.title }}
                    </li>
                    <li v-if="!gradingList.length" class="text-gray-500 text-sm">暂无待批改</li>
                </ul>
            </section>

            <!-- 课程列表 -->
            <section class="bg-glass p-6 overflow-y-auto">
                <h2 class="text-lg font-semibold text-emerald-700 mb-4">我的课程</h2>
                <ul class="space-y-3">
                    <li v-for="course in courses" :key="course.id">
                        <router-link
                            :to="`/course/${course.id}`"
                            class="link hover:font-medium"
                        >
                            {{ course.name }}
                        </router-link>
                    </li>
                    <li v-if="!courses.length" class="text-gray-500 text-sm">暂无课程</li>
                </ul>
            </section>

            <!-- 消息 -->
            <section class="bg-glass p-6 overflow-y-auto">
                <h2 class="text-lg font-semibold text-emerald-700 mb-4">学生消息</h2>
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
const store      = useUserStore();
const display    = computed(() => store.username || store.useremail || '老师');
const greeting   = computed(() => `${display.value}老师，欢迎回来！`);

interface Course   { id: string; name: string }
interface Task     { id: string; title: string }
interface Message  { id: string; content: string }

const courses      = ref<Course[]>([]);
const gradingList  = ref<Task[]>([]);
const messages     = ref<Message[]>([]);

/* ---------- 数据拉取 ---------- */
async function fetchTeacherData() {
    // TODO: 替换为真实后端接口
    const { data } = await axios.get('/api/teacher/dashboard');
    courses.value     = data.courses      || [];
    gradingList.value = data.gradingList  || [];
    messages.value    = data.messages     || [];
}

onMounted(fetchTeacherData);
</script>