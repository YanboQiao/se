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
                <!-- 布置作业按钮 -->
                <button
                    @click="openCreateModal"
                    class="bg-blue-600/90 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 transition shadow-card"
                >
                    布置作业
                </button>

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
                        <!-- 作业概要统计 -->
                        <div class="mb-6">
                            <ul class="text-sm space-y-2">
                                <li>总人数：{{ summary.total }}</li>
                                <li>已提交：{{ summary.submitted }}</li>
                                <li>未提交：{{ summary.total - summary.submitted }}</li>
                                <li>待批改：{{ summary.ungraded }}</li>
                            </ul>

                        </div>

                        <!-- 学生作业情况列表 -->
                        <div class="border-t pt-6">
                            <h3 class="text-base font-semibold text-gray-800 mb-4">学生作业情况</h3>
                            
                            <template v-if="submissionsLoading">
                                <p class="text-center text-gray-500 text-sm">加载学生提交情况...</p>
                            </template>
                            
                            <template v-else-if="submissions.length">
                                <div class="space-y-3">
                                    <div
                                        v-for="submission in submissions"
                                        :key="submission.studentEmail"
                                        class="bg-gray-50 rounded-lg p-4 cursor-pointer hover:bg-gray-100 transition"
                                        @click="openGradeModal(submission)"
                                    >
                                        <!-- 学生信息 -->
                                        <div class="flex items-center justify-between mb-2">
                                            <h4 class="font-medium text-gray-800">
                                                {{ submission.studentName || submission.studentEmail }}
                                            </h4>
                                            <span
                                                :class="submission.score !== null ? 'text-emerald-600' : 'text-orange-600'"
                                                class="text-xs px-2 py-1 rounded-full bg-white"
                                            >
                                                {{ submission.score !== null ? `${submission.score}分` : '待审阅' }}
                                            </span>
                                        </div>

                                        <!-- 作业内容预览 -->
                                        <p class="text-sm text-gray-600 mb-2">
                                            作业答案：{{ getContentPreview(submission.content) }}
                                        </p>

                                        <!-- 评语 -->
                                        <p v-if="submission.feedback" class="text-xs text-gray-500">
                                            评语：{{ submission.feedback }}
                                        </p>
                                        <p v-else class="text-xs text-gray-400">
                                            暂无评语
                                        </p>
                                    </div>
                                </div>
                            </template>
                            
                            <template v-else>
                                <p class="text-center text-gray-500 text-sm">暂无学生提交</p>
                            </template>
                        </div>
                    </template>

                    <template v-else>
                        <p class="text-center text-red-500 text-sm">加载失败</p>
                    </template>
                </div>
            </aside>
        </transition>

        <!-- 评分弹窗 --------------------------------------------------- -->
        <transition name="modal">
            <div
                v-if="gradeModalOpen"
                class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
                @click.self="gradeModalOpen = false"
            >
                <div class="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                    <!-- 弹窗头部 -->
                    <div class="p-6 border-b flex items-center justify-between">
                        <h2 class="text-lg font-semibold text-gray-800">作业详情与评分</h2>
                        <button @click="gradeModalOpen = false" class="text-xl text-gray-500 hover:text-gray-700">&times;</button>
                    </div>

                    <!-- 弹窗内容 -->
                    <div class="p-6" v-if="currentSubmission">
                        <!-- 学生信息 -->
                        <div class="mb-4">
                            <h3 class="font-medium text-gray-800 mb-2">学生信息</h3>
                            <p class="text-sm text-gray-600">
                                姓名：{{ currentSubmission.studentName || currentSubmission.studentEmail }}
                            </p>
                            <p class="text-sm text-gray-600">
                                邮箱：{{ currentSubmission.studentEmail }}
                            </p>
                        </div>

                        <!-- 作业内容 -->
                        <div class="mb-6">
                            <h3 class="font-medium text-gray-800 mb-2">作业内容</h3>
                            <div class="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
                                <p class="text-sm text-gray-700 whitespace-pre-wrap">{{ currentSubmission.content || '无内容' }}</p>
                            </div>
                        </div>

                        <!-- 评分表单 -->
                        <div class="space-y-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">评分</label>
                                <input
                                    v-model.number="gradeForm.score"
                                    type="number"
                                    min="0"
                                    max="100"
                                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
                                    placeholder="请输入分数 (0-100)"
                                />
                            </div>

                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">评语</label>
                                <textarea
                                    v-model="gradeForm.feedback"
                                    rows="4"
                                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
                                    placeholder="请输入评语..."
                                ></textarea>
                            </div>

                            <!-- 操作按钮 -->
                            <div class="flex gap-3 pt-4">
                                <button
                                    @click="submitGrade"
                                    class="bg-emerald-600 text-white px-4 py-2 rounded-md hover:bg-emerald-700 transition"
                                >
                                    保存评分
                                </button>
                                <button
                                    @click="gradeModalOpen = false"
                                    class="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400 transition"
                                >
                                    取消
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </transition>

        <!-- 创建作业弹窗 --------------------------------------------------- -->
        <transition name="modal">
            <div
                v-if="createModalOpen"
                class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
                @click.self="createModalOpen = false"
            >
                <div class="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                    <!-- 弹窗头部 -->
                    <div class="p-6 border-b flex items-center justify-between">
                        <h2 class="text-lg font-semibold text-gray-800">创建新作业</h2>
                        <button @click="createModalOpen = false" class="text-xl text-gray-500 hover:text-gray-700">&times;</button>
                    </div>

                    <!-- 弹窗内容 -->
                    <div class="p-6">
                        <form @submit.prevent="submitCreateAssignment" class="space-y-4">
                            <!-- 作业标题 -->
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">作业标题 *</label>
                                <input
                                    v-model="createForm.title"
                                    type="text"
                                    required
                                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="请输入作业标题"
                                />
                            </div>

                            <!-- 作业描述 -->
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">作业描述</label>
                                <textarea
                                    v-model="createForm.description"
                                    rows="3"
                                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="请输入作业描述和要求..."
                                ></textarea>
                            </div>

                            <!-- 作业内容 -->
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">作业内容 *</label>
                                <textarea
                                    v-model="createForm.question"
                                    rows="4"
                                    required
                                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="请输入具体的作业题目内容..."
                                ></textarea>
                            </div>

                            <!-- 截止日期 -->
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">截止日期</label>
                                <input
                                    v-model="createForm.dueDate"
                                    type="datetime-local"
                                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>

                            <!-- 参考答案 -->
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">参考答案</label>
                                <textarea
                                    v-model="createForm.referenceAnswer"
                                    rows="6"
                                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="请输入参考答案（用于AI自动批改）..."
                                ></textarea>
                            </div>

                            <!-- 操作按钮 -->
                            <div class="flex gap-3 pt-4">
                                <button
                                    type="submit"
                                    class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition"
                                >
                                    创建作业
                                </button>
                                <button
                                    type="button"
                                    @click="createModalOpen = false"
                                    class="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400 transition"
                                >
                                    取消
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
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
    id: string;
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

interface StudentSubmission {
    studentEmail: string;
    studentName: string;
    content: string;
    score: number | null;
    feedback: string;
}

/* ---------- 状态 ---------- */
const courseName  = ref('');
const assignments = ref<Assignment[]>([]);

const drawerOpen     = ref(false);
const drawerAsm      = ref<Assignment | null>(null);
const summary        = ref<SummaryResp | null>(null);
const summaryLoading = ref(false);

// 学生提交列表相关状态
const submissions = ref<StudentSubmission[]>([]);
const submissionsLoading = ref(false);

// 评分弹窗相关状态
const gradeModalOpen = ref(false);
const currentSubmission = ref<StudentSubmission | null>(null);
const gradeForm = ref({
    score: 0,
    feedback: ''
});

// 创建作业弹窗相关状态
const createModalOpen = ref(false);
const createForm = ref({
    title: '',
    description: '',
    question: '',
    dueDate: '',
    referenceAnswer: ''
});

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
    submissions.value = [];
    submissionsLoading.value = true;

    try {
        // 获取作业概要统计
        const summaryRes = await axios.post(
            '/api/teacher/assignment/summary',
            {
                role:     'teacher',
                useremail: store.useremail,
                token:    store.token,
                course_id: courseId,
                assign_no: asm.assignNo,
            },
        );
        summary.value = summaryRes.data;

        // 获取学生提交详情
        const detailRes = await axios.post('/api/teacher/assignment/info', {
            course_id: courseId,
            assign_no: asm.assignNo
        }, {
            params: { useremail: store.useremail, token: store.token },
        });
        submissions.value = detailRes.data.submissions || [];
    } catch (err) {
        console.error('加载作业数据失败', err);
    } finally {
        summaryLoading.value = false;
        submissionsLoading.value = false;
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

/* ---------- 评分相关功能 ---------- */
function openGradeModal(submission: StudentSubmission) {
    currentSubmission.value = submission;
    gradeForm.value.score = submission.score ?? 0;
    gradeForm.value.feedback = submission.feedback || '';
    gradeModalOpen.value = true;
}

async function submitGrade() {
    if (!currentSubmission.value || !drawerAsm.value) return;
    
    try {
        await axios.post('/api/teacher/assignment/grade', {
            course_id: courseId,
            assign_no: drawerAsm.value.assignNo,
            studentEmail: currentSubmission.value.studentEmail,
            score: gradeForm.value.score,
            feedback: gradeForm.value.feedback,
        }, {
            params: { useremail: store.useremail, token: store.token },
        });
        
        alert('评分已保存！');
        gradeModalOpen.value = false;
        
        // 刷新数据
        if (drawerAsm.value) {
            openDrawer(drawerAsm.value);
        }
    } catch (err) {
        console.error('评分失败', err);
        alert('评分失败，请稍后再试');
    }
}

/* ---------- 创建作业相关功能 ---------- */
function openCreateModal() {
    createModalOpen.value = true;
    // 重置表单
    createForm.value = {
        title: '',
        description: '',
        question: '',
        dueDate: '',
        referenceAnswer: ''
    };
}

async function submitCreateAssignment() {
    if (!createForm.value.title.trim()) {
        alert('请输入作业标题');
        return;
    }
    if (!createForm.value.question.trim()) {
        alert('请输入作业内容');
        return;
    }
    
    try {
        await axios.post('/api/teacher/assignment/create', {
            course_id: courseId,
            title: createForm.value.title,
            description: createForm.value.description,
            question: createForm.value.question,
            dueDate: createForm.value.dueDate,
            referenceAnswer: createForm.value.referenceAnswer,
            useremail: store.useremail,
            token: store.token,
        });
        
        alert('作业创建成功！');
        createModalOpen.value = false;
        
        // 刷新作业列表
        fetchCourseData();
    } catch (err) {
        console.error('创建作业失败', err);
        alert('创建作业失败，请稍后再试');
    }
}

// 简略显示作业内容（最多10个字符）
function getContentPreview(content: string): string {
    if (!content) return '无内容';
    if (content.length <= 10) return content;
    return content.substring(0, 10) + '...';
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

/* 弹窗过渡效果 */
.modal-enter-active,
.modal-leave-active {
    transition: opacity 0.25s ease;
}
.modal-enter-from,
.modal-leave-to {
    opacity: 0;
}
</style>
