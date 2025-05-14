<template>
    <div class="min-h-screen flex flex-col bg-main-gradient">
        <!-- 顶部栏：返回按钮和作业标题 -->
        <header class="p-6 lg:p-8 bg-white/30 backdrop-blur-sm shadow flex items-center gap-4">
            <button @click="$router.back()" class="text-indigo-600 hover:underline text-sm">
                ← 返回
            </button>
            <h1 class="text-xl lg:text-2xl font-bold text-gray-800 flex-1">
                {{ assignmentTitle || '作业详情' }}
            </h1>
        </header>

        <!-- 主体：作业详情和提交列表 -->
        <main class="flex-1 p-4 lg:p-8 space-y-6">
            <!-- 作业描述 -->
            <section class="bg-glass p-6 rounded-2xl">
                <h2 class="text-lg font-semibold text-gray-800 mb-2">作业要求</h2>
                <p class="text-sm text-gray-700 whitespace-pre-line">{{ assignmentDesc || '无' }}</p>
                <p class="text-sm text-gray-600 mt-2">截止日期: {{ assignmentDue || '无' }}</p>
            </section>
            <!-- 学生提交列表 -->
            <section class="bg-glass p-6 rounded-2xl">
                <h2 class="text-lg font-semibold text-emerald-700 mb-4">学生提交情况</h2>
                <table class="w-full text-sm">
                    <thead>
                        <tr class="text-left text-gray-600">
                            <th class="pb-2">学生</th>
                            <th class="pb-2">提交内容</th>
                            <th class="pb-2">得分</th>
                            <th class="pb-2">评语</th>
                            <th class="pb-2"></th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="sub in submissions" :key="sub.studentEmail" class="border-t text-gray-800">
                            <td class="py-2">{{ sub.studentName || sub.studentEmail }}</td>
                            <td class="py-2">
                                <span v-if="sub.content">
                                    <span v-if="sub.content.startsWith('http')">
                                        <a :href="sub.content" target="_blank" class="text-indigo-600 hover:underline">查看</a>
                                    </span>
                                    <span v-else>{{ sub.content.length > 50 ? sub.content.slice(0, 50) + '…' : sub.content }}</span>
                                </span>
                            </td>
                            <td class="py-2">
                                <input v-model.number="sub.score" type="number" min="0" max="100"
                                       class="w-16 border border-gray-300 rounded px-2 py-1 focus:ring-2 focus:ring-indigo-500" />
                            </td>
                            <td class="py-2">
                                <input v-model="sub.feedback" type="text" placeholder="评语"
                                       class="border border-gray-300 rounded px-2 py-1 w-40 focus:ring-2 focus:ring-indigo-500" />
                            </td>
                            <td class="py-2">
                                <button @click="submitGrade(sub)" class="btn-primary px-4 py-1" :disabled="submitting">
                                    提交
                                </button>
                            </td>
                        </tr>
                        <tr v-if="!submissions.length">
                            <td colspan="5" class="py-6 text-center text-gray-500">暂无提交</td>
                        </tr>
                    </tbody>
                </table>
                <p v-if="gradeError" class="text-red-600 text-sm mt-2">{{ gradeError }}</p>
                <p v-if="gradeSuccess" class="text-green-600 text-sm mt-2">批改结果已提交！</p>
            </section>
        </main>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';

/* ---------- 路由参数与状态 ---------- */
const route            = useRoute();
const courseId         = route.params.id as string;
const assignmentId     = route.params.assignmentId as string;
const assignmentTitle  = ref('');
const assignmentDesc   = ref('');
const assignmentDue    = ref('');
interface Submission { studentEmail: string; studentName?: string; content: string; score?: number; feedback?: string }
const submissions      = ref<Submission[]>([]);
const submitting       = ref(false);
const gradeError       = ref('');
const gradeSuccess     = ref('');

/* ---------- 加载作业详情和提交情况 ---------- */
async function fetchAssignmentData() {
    try {
        const { data } = await axios.get(`/api/teacher/assignment/${assignmentId}`);
        assignmentTitle.value = data.assignment?.title || `作业 ${assignmentId}`;
        assignmentDesc.value  = data.assignment?.description || '';
        assignmentDue.value   = data.assignment?.dueDate || '';
        submissions.value     = data.submissions || [];
    } catch (err) {
        console.error('作业详情加载失败', err);
    }
}
onMounted(fetchAssignmentData);

/* ---------- 提交评分 ---------- */
async function submitGrade(sub: Submission) {
    gradeError.value = '';
    gradeSuccess.value = '';
    submitting.value = true;
    try {
        const payload = {
            studentEmail: sub.studentEmail,
            score: sub.score ?? 0,
            feedback: sub.feedback || ''
        };
        await axios.post(`/api/teacher/assignment/${assignmentId}/grade`, payload);
        gradeSuccess.value = '评分已保存';
    } catch (err) {
        console.error('提交成绩失败', err);
        gradeError.value = '提交成绩失败，请重试';
    } finally {
        submitting.value = false;
    }
}
</script>