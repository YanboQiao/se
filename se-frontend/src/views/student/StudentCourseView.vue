<template>
    <div class="min-h-screen flex flex-col bg-main-gradient">
        <!-- 顶部栏：返回按钮和课程名称 -->
        <header class="p-6 lg:p-8 bg-white/30 backdrop-blur-sm shadow flex items-center gap-4">
            <button @click="$router.back()" class="text-indigo-600 hover:underline text-sm">
                ← 返回
            </button>
            <h1 class="text-xl lg:text-2xl font-bold text-gray-800 flex-1">
                {{ courseName || '我的课程' }}
            </h1>
        </header>

        <!-- 主体：作业列表 -->
        <main class="flex-1 p-4 lg:p-8">
            <section class="bg-glass p-6 rounded-2xl">
                <h2 class="text-lg font-semibold text-indigo-700 mb-4">课程作业</h2>

                <ul class="space-y-3">
                    <li v-for="asm in assignments" :key="asm.id">
                        <router-link
                            :to="`/student/course/${courseId}/assignment/${asm.id}`"
                            class="link font-medium"
                        >
                            {{ asm.title }}
                        </router-link>

                        <span class="ml-2 text-sm text-gray-600">
                            截止: {{ asm.dueDate || '无' }}
                        </span>

                        <span
                            v-if="asm.submitted"
                            class="ml-2 text-emerald-700 text-sm"
                        >
                            已提交
                            <span v-if="asm.score != null">，得分：{{ asm.score }}</span>
                            <span v-else>，待批改</span>
                        </span>

                        <span
                            v-else
                            class="ml-2 text-red-600 text-sm"
                        >
                            未提交
                        </span>
                    </li>

                    <li
                        v-if="!assignments.length"
                        class="text-gray-500 text-sm"
                    >
                        暂无作业
                    </li>
                </ul>
            </section>
        </main>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';

/* ---------- 路由参数与状态 ---------- */
const route       = useRoute();
const courseId    = route.params.id as string;

const courseName  = ref('');
interface Assignment {
    id: string;
    title: string;
    dueDate?: string;
    submitted?: boolean;
    score?: number;
}
const assignments = ref<Assignment[]>([]);

/* ---------- 获取课程作业列表 ---------- */
async function fetchCourseData() {
    try {
        const { data } = await axios.get(`/api/student/course/${courseId}`);
        courseName.value  = data.course?.name || `课程 ${courseId}`;
        assignments.value = data.assignments || [];
    } catch (err) {
        console.error('课程作业加载失败', err);
    }
}
onMounted(fetchCourseData);
</script>
