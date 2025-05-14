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

        <!-- 主体：作业详情和提交/反馈 -->
        <main class="flex-1 p-4 lg:p-8 space-y-6">
            <!-- 作业信息 -->
            <section class="bg-glass p-6 rounded-2xl">
                <h2 class="text-lg font-semibold text-gray-800 mb-2">作业要求</h2>
                <p class="text-sm text-gray-700 whitespace-pre-line">{{ assignmentDesc || '无' }}</p>
                <p class="text-sm text-gray-600 mt-2">截止日期: {{ assignmentDue || '无' }}</p>
            </section>
            <!-- 提交作业或查看反馈 -->
            <section class="bg-glass p-6 rounded-2xl">
                <h2 v-if="!mySubmission" class="text-lg font-semibold text-gray-800 mb-4">提交作业</h2>
                <template v-if="!mySubmission">
                    <form @submit.prevent="submitAssignment">
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-2" for="answer">答案内容</label>
                            <textarea id="answer" v-model="answerText" rows="4" class="input-control"></textarea>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-2">附件上传 (可选)</label>
                            <input type="file" @change="onFileChange" class="text-sm text-gray-700" />
                        </div>
                        <button type="submit" class="btn-primary px-6 py-2" :disabled="submitting">
                            提交
                        </button>
                        <p v-if="submitError" class="text-red-600 text-sm mt-2">{{ submitError }}</p>
                    </form>
                </template>
                <template v-else>
                    <h2 class="text-lg font-semibold text-gray-800 mb-2">我的提交</h2>
                    <p class="text-sm text-gray-800">您已提交此作业。</p>
                    <p class="text-sm text-gray-600 mt-1">提交时间: {{ mySubmission.submitTime || '—' }}</p>
                    <p v-if="mySubmission.score != null" class="text-sm text-indigo-700 mt-2">
                        得分：<span class="font-semibold">{{ mySubmission.score }}</span>
                    </p>
                    <p v-if="mySubmission.feedback" class="text-sm text-indigo-700 mt-1">
                        评语：{{ mySubmission.feedback }}
                    </p>
                    <p v-else-if="mySubmission.score == null" class="text-sm text-gray-600 mt-2">
                        作业已提交，等待老师批改。
                    </p>
                    <div class="mt-4">
                        <span class="text-sm text-gray-800">提交内容：</span>
                        <span v-if="mySubmission.content">
                            <span v-if="mySubmission.content.startsWith('http')">
                                <a :href="mySubmission.content" target="_blank" class="text-indigo-600 hover:underline">查看附件</a>
                            </span>
                            <span v-else>{{ mySubmission.content }}</span>
                        </span>
                    </div>
                </template>
            </section>
        </main>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import { useUserStore } from '@/stores/user';

/* ---------- 路由参数与状态 ---------- */
const route            = useRoute();
const courseId         = route.params.id as string;
const assignmentId     = route.params.assignmentId as string;
const store            = useUserStore();
const assignmentTitle  = ref('');
const assignmentDesc   = ref('');
const assignmentDue    = ref('');
interface Submission { content: string; submitTime?: string; score?: number; feedback?: string }
const mySubmission     = ref<Submission | null>(null);
const answerText       = ref('');
const selectedFile     = ref<File | null>(null);
const submitting       = ref(false);
const submitError      = ref('');

/* ---------- 加载作业详情及我的提交 ---------- */
async function fetchAssignmentData() {
    try {
        const { data } = await axios.get(`/api/student/assignment/${assignmentId}`);
        assignmentTitle.value = data.assignment?.title || `作业 ${assignmentId}`;
        assignmentDesc.value  = data.assignment?.description || '';
        assignmentDue.value   = data.assignment?.dueDate || '';
        if (data.submission) {
            mySubmission.value = data.submission;
        }
    } catch (err) {
        console.error('加载作业详情失败', err);
    }
}
onMounted(fetchAssignmentData);

/* ---------- 文件选择处理 ---------- */
function onFileChange(event: Event) {
    const files = (event.target as HTMLInputElement).files;
    if (files && files.length > 0) {
        selectedFile.value = files[0];
    }
}

/* ---------- 提交作业 ---------- */
async function submitAssignment() {
    submitError.value = '';
    if (!selectedFile.value && !answerText.value.trim()) {
        submitError.value = '请填写答案或上传附件';
        return;
    }
    submitting.value = true;
    try {
        let contentData: string | null = null;
        if (selectedFile.value) {
            // 上传文件
            const formData = new FormData();
            formData.append('file', selectedFile.value);
            formData.append('fileType', '1');  // 1表示作业文件
            formData.append('userId', store.useremail || '');
            formData.append('uploaderId', store.useremail || '');
            formData.append('userGroup', '1');
            formData.append('uploadTime', Date.now().toString());
            const res = await axios.post('/api/v1/uploadfile', formData);
            const fileId = res.data?.data?.fileId;
            contentData = fileId ? fileId : selectedFile.value.name;
        } else {
            contentData = answerText.value;
        }
        // 提交作业记录
        const payload = { content: contentData };
        const { data } = await axios.post(`/api/student/assignment/${assignmentId}/submit`, payload);
        // 将提交结果保存并更新界面
        mySubmission.value = data.submission || {
            content: contentData,
            submitTime: new Date().toISOString(),
            score: null,
            feedback: ''
        };
    } catch (err) {
        console.error('提交作业失败', err);
        submitError.value = '提交失败，请稍后重试';
    } finally {
        submitting.value = false;
    }
}
</script>