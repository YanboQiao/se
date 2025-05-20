<template>
    <div class="min-h-screen flex flex-col bg-main-gradient">
        <!-- 顶部栏 -->
        <header class="p-6 lg:p-8 bg-white/30 backdrop-blur-sm shadow flex items-center justify-between relative">
            <h1 class="text-xl lg:text-2xl font-bold text-gray-800">
                {{ greeting }}
            </h1>
            <div class="flex items-center gap-4">
                <button v-if="!showCourseForm" @click="showCourseForm = true" class="btn-primary px-4 py-2 whitespace-nowrap">
                    新建课程
                </button>
            </div>
            <div v-if="showCourseForm" class="absolute right-6 top-full mt-2 bg-white/90 p-4 rounded-xl shadow-card w-72 z-10">
                <h3 class="text-base font-semibold text-gray-800 mb-4">新建课程</h3>
                <form @submit.prevent="createCourse" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2" for="courseName">课程名称</label>
                        <input id="courseName" v-model="newCourseName" class="input-control" required />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2" for="courseDesc">课程简介</label>
                        <textarea id="courseDesc" v-model="newCourseDesc" rows="2" class="input-control"></textarea>
                    </div>
                    <div class="text-center">
                        <button type="submit" class="btn-primary px-6 py-2 mr-4" :disabled="creatingCourse">提交</button>
                        <button type="button" @click="cancelCourseForm" class="btn-primary bg-gray-400 hover:bg-gray-500 px-6 py-2">
                            取消
                        </button>
                    </div>
                    <p v-if="courseFormError" class="text-red-600 text-sm mt-2">{{ courseFormError }}</p>
                </form>
            </div>
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
                        <router-link :to="`/course/${course.id}`" class="link hover:font-medium">
                            {{ course.name }}
                        </router-link>
                    </li>
                    <li v-if="!courses.length" class="text-gray-500 text-sm">暂无课程</li>
                </ul>
            </section>

            <!-- 学生消息 -->
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
const store     = useUserStore();
const display   = computed(() => store.username || store.useremail || '老师');
const greeting  = computed(() => `${display.value}老师，欢迎回来！`);

interface Course   { id: string; name: string }
interface Task     { id: string; title: string }
interface Message  { id: string; content: string }

const courses        = ref<Course[]>([]);
const gradingList    = ref<Task[]>([]);
const messages       = ref<Message[]>([]);
const showCourseForm = ref(false);
const newCourseName  = ref('');
const newCourseDesc  = ref('');
const creatingCourse = ref(false);
const courseFormError = ref('');

/* ---------- 数据拉取 ---------- */
async function fetchTeacherData() {
    const { data } = await axios.get('/api/teacher/dashboard');
    courses.value     = data.courses      || [];
    gradingList.value = data.gradingList  || [];
    messages.value    = data.messages     || [];
}
onMounted(fetchTeacherData);

/* ---------- 方法 ---------- */
async function createCourse() {
    courseFormError.value = '';
    if (!newCourseName.value.trim()) {
        courseFormError.value = '名称不能为空';
        return;
    }
    creatingCourse.value = true;
    try {
        const payload = { name: newCourseName.value, description: newCourseDesc.value };
        const { data } = await axios.post('/api/teacher/courses', payload);
        const newCourse = data.course;
        if (newCourse) {
            courses.value.push(newCourse);
        }
        newCourseName.value = '';
        newCourseDesc.value = '';
        showCourseForm.value = false;
    } catch (err) {
        console.error('课程创建失败', err);
        courseFormError.value = err.response?.data?.message || '创建课程失败，请稍后重试';
    } finally {
        creatingCourse.value = false;
    }
}

function cancelCourseForm() {
    showCourseForm.value = false;
    courseFormError.value = '';
    newCourseName.value = '';
    newCourseDesc.value = '';
}
</script>
