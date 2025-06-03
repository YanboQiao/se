<template>
    <div class="min-h-screen flex flex-col bg-main-gradient">
        <!-- 顶部栏 ---------------------------------------------------- -->
        <header
            class="p-6 lg:p-8 bg-white/30 backdrop-blur-sm shadow flex items-center justify-between"
        >
            <div class="flex items-center gap-4">
                <button @click="$router.back()" class="text-indigo-600 hover:underline text-sm">
                    ← 返回
                </button>
                <h1 class="text-xl lg:text-2xl font-bold text-gray-800">
                    {{ courseName || '课程详情' }}
                </h1>
            </div>

            <div class="flex items-center gap-4">
                <!-- AI 学习助手入口 -->
                <a
                    :href="llmsUrl"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="bg-emerald-600/90 text-white px-4 py-2 rounded-lg text-sm hover:bg-emerald-700 transition shadow-card"
                >
                    大模型
                </a>

                <button @click="logout" class="text-red-600 hover:underline text-sm whitespace-nowrap">
                    退出登录
                </button>
            </div>
        </header>

        <!-- 主体 ------------------------------------------------------ -->
        <main class="flex-1 p-4 lg:p-8">
            <!-- 作业卡片网格 -->
            <section class="bg-glass p-6 rounded-2xl">
                <h2 class="text-lg font-semibold text-emerald-700 mb-4">作业列表</h2>

                <div class="grid gap-6 md:grid-cols-2 xl:grid-cols-3 auto-rows-fr">
                    <div
                        v-for="asm in assignments"
                        :key="asm.id"
                        class="bg-white/50 backdrop-blur-sm rounded-xl p-5 flex flex-col justify-between shadow-card hover:shadow-lg cursor-pointer transition"
                        @click="openDrawer(asm)"
                    >
                        <div>
                            <h3 class="text-base font-semibold text-gray-800 mb-1">
                                {{ asm.title }}
                            </h3>
                            <p class="text-xs text-gray-600">
                                截止：{{ asm.dueDate || '无' }}
                            </p>
                        </div>

                        <div class="mt-4 flex items-center justify-between">
                            <span
                                :class="asm.status === '已截止' ? 'text-red-600' : 'text-emerald-600'"
                                class="text-xs"
                            >
                                {{ asm.status }}
                            </span>

                            <button
                                @click.stop="autoGrade(asm)"
                                class="text-xs bg-emerald-600/80 text-white px-3 py-1 rounded hover:bg-emerald-700 transition shadow-card"
                            >
                                一键批改
                            </button>
                        </div>
                    </div>

                    <p
                        v-if="!assignments.length"
                        class="text-gray-500 text-sm"
                    >
                        暂无作业
                    </p>
                </div>
            </section>

            <!-- 选课学生 / 新建作业模块（如需） -->
            <!-- 保持原实现 -->
        </main>

        <!-- 右侧抽屉 --------------------------------------------------- -->
        <transition name="slide">
            <aside
                v-if="drawerOpen"
                class="fixed top-0 right-0 h-full w-full sm:w-[420px] bg-white shadow-2xl z-50 flex flex-col"
            >
                <header class="p-6 border-b flex items-center justify-between">
                    <h2 class="text-lg font-semibold text-gray-800">
                        {{ drawerAsm?.title || '作业详情' }}
                    </h2>
                    <button @click="drawerOpen = false" class="text-xl">&times;</button>
                </header>

                <div class="p-6 flex-1 overflow-y-auto">
                    <template v-if="summaryLoading">
                        <p class="text-center text-gray-500 text-sm">加载中...</p>
                    </template>

                    <template v-else-if="summary">
                        <ul class="text-sm space-y-2">
                            <li>总人数：{{ summary.total }}</li>
                            <li>已提交：{{ summary.submitted }}</li>
                            <li>未提交：{{ summary.total - summary.submitted }}</li>
                            <li>待批改：{{ summary.ungraded }}</li>
                        </ul>

                        <router-link
                            v-if="drawerAsm"
                            :to="`/teacher/course/${courseId}/assignment/${drawerAsm.id}`"
                            class="inline-block mt-6 text-emerald-700 hover:underline text-sm"
                        >
                            进入批改页面 →
                        </router-link>
                    </template>

                    <template v-else>
                        <p class="text-center text-red-500 text-sm">加载失败</p>
                    </template>
                </div>
            </aside>
        </transition>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
import { useUserStore } from '@/stores/user';

/* ---------- Store / Router / 路由参数 ---------- */
const store    = useUserStore();
const router   = useRouter();
const route    = useRoute();
const courseId = route.params.id as string;

/* ---------- 类型 ---------- */
interface Assignment {
    id: string;       // 'rg_01_hw_1'
    title: string;
    dueDate?: string;
    status?: string;
    assignNo: number; // 1
}

interface SummaryResp {
    total: number;
    submitted: number;
    ungraded: number;
}

/* ---------- 状态 ---------- */
const courseName  = ref('');
const assignments = ref<Assignment[]>([]);

const drawerOpen     = ref(false);
const drawerAsm      = ref<Assignment | null>(null);
const summary        = ref<SummaryResp | null>(null);
const summaryLoading = ref(false);

/* ---------- 计算：AI 跳转链接 ---------- */
const llmsUrl = computed(() => {
    const p = new URLSearchParams({
        useremail: store.useremail ?? '',
        role: store.role ?? 'teacher',
        token: store.token ?? '',
    }).toString();
    return `http://localhost:8001/llms?${p}`;
});

/* ---------- 生命周期：拉课程基本信息 ---------- */
onMounted(fetchCourseData);

function extractAssignNo(id: string): number {
    const m = id.match(/_hw_(\d+)$/);
    return m ? Number(m[1]) : NaN;
}

async function fetchCourseData() {
    try {
        const { data } = await axios.get(`/api/teacher/course/${courseId}`, {
            params: { useremail: store.useremail, token: store.token },
        });
        courseName.value  = data.course?.name || `课程 ${courseId}`;
        assignments.value = (data.assignments || []).map((a: any) => ({
            id: a.id,
            title: a.title,
            dueDate: a.dueDate,
            status: a.status,
            assignNo: extractAssignNo(a.id),
        }));
    } catch (err) {
        console.error('获取课程数据失败:', err);
    }
}

/* ---------- 打开抽屉：请求概要 ---------- */
async function openDrawer(asm: Assignment) {
    drawerAsm.value  = asm;
    drawerOpen.value = true;
    summary.value    = null;
    summaryLoading.value = true;

    try {
        const { data } = await axios.post(
            '/api/teacher/assignment/summary',
            {
                role:     'teacher',
                useremail: store.useremail,
                token:    store.token,
                course_id: courseId,
                assign_no: asm.assignNo,
            },
        );
        summary.value = data;
    } catch (err) {
        console.error('加载作业概要失败', err);
    } finally {
        summaryLoading.value = false;
    }
}

/* ---------- 一键批改 ---------- */
async function autoGrade(asm: Assignment) {
    if (!confirm(`确定一键批改「${asm.title}」吗？`)) return;
    try {
        await axios.post('/api/teacher/assignment/auto-grade', {
            role:     'teacher',
            useremail: store.useremail,
            token:    store.token,
            course_id: courseId,
            assign_no: asm.assignNo,
        });
        alert('批改完成！');
        fetchCourseData();
        if (drawerOpen.value && drawerAsm.value?.id === asm.id) {
            openDrawer(asm); // 刷新抽屉数据
        }
    } catch (err) {
        console.error('一键批改失败', err);
        alert('批改失败，请稍后再试');
    }
}

/* ---------- 退出登录 ---------- */
function logout() {
    (store.logout ?? store.$reset ?? (() => {
        store.token = ''; store.useremail = ''; store.username = '';
    }))();
    router.replace('/login');
}
</script>

<style scoped>
/* 右侧抽屉过渡效果 */
.slide-enter-active,
.slide-leave-active {
    transition: transform 0.25s ease;
}
.slide-enter-from,
.slide-leave-to {
    transform: translateX(100%);
}
</style>
