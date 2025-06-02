<template>
    <div class="min-h-screen flex flex-col bg-main-gradient">
        <!-- 顶部栏 -->
        <header
            class="p-6 lg:p-8 bg-white/30 backdrop-blur-sm shadow flex items-center justify-between relative"
        >
            <h1 class="text-xl lg:text-2xl font-bold text-gray-800">
                {{ greeting }}
            </h1>

            <div class="flex items-center gap-4">
                <button
                    @click="logout"
                    class="text-red-600 hover:underline text-sm whitespace-nowrap"
                >
                    退出登录
                </button>
            </div>
        </header>

        <!-- 主体 -->
        <main
            class="flex-1 p-4 lg:p-8 grid lg:grid-cols-[260px_1fr_260px] gap-6"
        >
            <!-- 待批改 -->
            <section class="bg-glass p-6 overflow-y-auto">
                <h2 class="text-lg font-semibold text-emerald-700 mb-4">
                    待批改作业
                </h2>
                <ul class="space-y-3">
                    <li
                        v-for="task in gradingList"
                        :key="task.id"
                        class="text-sm text-gray-800"
                    >
                        • {{ task.title }}
                    </li>
                    <li
                        v-if="!gradingList.length"
                        class="text-gray-500 text-sm"
                    >
                        暂无待批改
                    </li>
                </ul>
            </section>

            <!-- 课程卡片区 -->
            <section class="bg-glass p-6 overflow-y-auto">
                <h2 class="text-lg font-semibold text-emerald-700 mb-4">
                    我的课程
                </h2>

                <div
                    class="grid gap-4 md:grid-cols-2 xl:grid-cols-3 auto-rows-fr"
                >
                    <TeacherCourseCard
                        v-for="course in courses"
                        :key="course.id"
                        :course="course"
                    />
                </div>

                <p v-if="!courses.length" class="text-gray-500 text-sm">
                    暂无课程
                </p>
            </section>

            <!-- 学生消息 -->
            <section class="bg-glass p-6 overflow-y-auto">
                <h2 class="text-lg font-semibold text-emerald-700 mb-4">
                    学生消息
                </h2>
                <ul class="space-y-3">
                    <li
                        v-for="msg in messages"
                        :key="msg.id"
                        class="text-sm text-gray-800"
                    >
                        {{ msg.content }}
                    </li>
                    <li v-if="!messages.length" class="text-gray-500 text-sm">
                        暂无消息
                    </li>
                </ul>
            </section>
        </main>
    </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { useUserStore } from '@/stores/user';
import TeacherCourseCard from '@/components/TeacherCourseCard.vue';

/* ---------- Pinia & Router ---------- */
const store = useUserStore();
const router = useRouter();

/* ---------- 计算属性 ---------- */
const greeting = computed(
    () => `${store.username || store.useremail || '老师'}老师，欢迎回来！`,
);

/* ---------- 类型 ---------- */
interface CourseDetail {
    id: string;
    name: string;
    description?: string;
    startDate?: string;
    endDate?: string;
    status?: string;
    studentCount?: number;
    ungradedCount?: number;
}
interface Task {
    id: string;
    title: string;
}
interface Message {
    id: string;
    content: string;
}

/* ---------- 状态 ---------- */
const courses = ref<CourseDetail[]>([]);
const gradingList = ref<Task[]>([]);
const messages = ref<Message[]>([]);

/* ---------- 数据拉取 ---------- */
async function fetchTeacherData() {
    try {
        const { data } = await axios.get('/api/teacher/dashboard', {
            params: { useremail: store.useremail, token: store.token },
        });
        courses.value = (data.courses || []) as CourseDetail[];
        gradingList.value = data.gradingList || [];
        messages.value = data.messages || [];
    } catch (error) {
        console.error('获取教师数据失败:', error);
    }
}
onMounted(fetchTeacherData);

/* ---------- 退出登录 ---------- */
function logout() {
    if (typeof store.logout === 'function') {
        store.logout();
    } else if (typeof store.$reset === 'function') {
        store.$reset();
    } else {
        store.token = '';
        store.useremail = '';
        store.username = '';
    }
    router.replace('/login');
}
</script>
