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

        <!-- 主体：作业卡片列表 -->
        <main class="flex-1 p-4 lg:p-8">
            <section class="space-y-6">
                <h2 class="text-lg font-semibold text-indigo-700 mb-6">课程作业</h2>

                <!-- 作业卡片网格 -->
                <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    <div 
                        v-for="asm in assignments" 
                        :key="asm.id"
                        class="bg-white/50 backdrop-blur-sm rounded-2xl p-6 shadow-card transition hover:shadow-lg flex flex-col gap-4"
                    >
                        <!-- 作业标题 -->
                        <h3 class="text-lg font-semibold text-gray-800">
                            {{ asm.title }}
                        </h3>

                        <!-- 作业描述（如果有） -->
                        <p 
                            v-if="asm.description" 
                            class="text-sm text-gray-700 flex-1 overflow-hidden leading-tight"
                            style="display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 3; line-clamp: 3; max-height: 4.5rem;"
                        >
                            {{ asm.description }}
                        </p>
                        <p v-else class="text-sm text-gray-500 flex-1">暂无作业描述</p>

                        <!-- 截止日期 -->
                        <div class="text-xs text-gray-600">
                            <p>截止日期：{{ asm.dueDate || '无' }}</p>
                        </div>

                        <!-- 提交状态 -->
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <span 
                                    v-if="asm.submitted"
                                    class="px-3 py-1 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700"
                                >
                                    已提交
                                </span>
                                <span 
                                    v-else
                                    class="px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700"
                                >
                                    未提交
                                </span>
                                
                                <!-- 分数显示 -->
                                <span 
                                    v-if="asm.submitted && asm.score != null"
                                    class="px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700"
                                >
                                    得分：{{ asm.score }}
                                </span>
                                <span 
                                    v-else-if="asm.submitted"
                                    class="px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-700"
                                >
                                    待批改
                                </span>
                            </div>
                        </div>

                        <!-- 操作按钮 -->
                        <div class="mt-4">
                            <router-link
                                :to="`/student/course/${courseId}/assignment/${asm.id}`"
                                class="w-full bg-indigo-600/90 hover:bg-indigo-700 text-white rounded-lg px-4 py-2 text-sm font-medium transition shadow-card text-center block"
                            >
                                {{ asm.submitted ? '查看详情' : '开始作业' }}
                            </router-link>
                        </div>
                    </div>
                </div>

                <!-- 暂无作业提示 -->
                <div 
                    v-if="!assignments.length"
                    class="bg-white/50 backdrop-blur-sm rounded-2xl p-12 text-center"
                >
                    <div class="text-gray-400 mb-4">
                        <svg class="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                        </svg>
                    </div>
                    <p class="text-gray-500 text-lg">暂无作业</p>
                    <p class="text-gray-400 text-sm mt-2">老师还没有发布任何作业</p>
                </div>
            </section>
        </main>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import http from '@/utils/http';

/* ---------- 路由参数与状态 ---------- */
const route       = useRoute();
const courseId    = route.params.id as string;

const courseName  = ref('');
interface Assignment {
    id: string;
    title: string;
    description?: string;
    dueDate?: string;
    submitted?: boolean;
    score?: number;
}
const assignments = ref<Assignment[]>([]);

/* ---------- 获取课程作业列表 ---------- */
async function fetchCourseData() {
    try {
        const { data } = await http.get(`/student/course/${courseId}`);
        courseName.value  = data.course?.name || `课程 ${courseId}`;
        assignments.value = data.assignments || [];
    } catch (err) {
        console.error('课程作业加载失败', err);
    }
}
onMounted(fetchCourseData);
</script>
