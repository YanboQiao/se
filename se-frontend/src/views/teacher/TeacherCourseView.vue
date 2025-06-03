<template>
    <div class="min-h-screen flex flex-col bg-main-gradient">
        <!-- 顶部栏：返回按钮和课程名称 -->
        <header class="p-6 lg:p-8 bg-white/30 backdrop-blur-sm shadow flex items-center gap-4">
            <button @click="$router.back()" class="text-indigo-600 hover:underline text-sm">
                ← 返回
            </button>
            <h1 class="text-xl lg:text-2xl font-bold text-gray-800 flex-1">
                {{ courseName || '课程详情' }}
            </h1>
        </header>

        <!-- 主体：作业列表和发布作业 -->
        <main class="flex-1 p-4 lg:p-8">
            <!-- 作业列表 -->
            <section class="bg-glass p-6 rounded-2xl">
                <h2 class="text-lg font-semibold text-emerald-700 mb-4">作业列表</h2>
                <ul class="space-y-3">
                    <li v-for="asm in assignments" :key="asm.id" class="text-gray-800">
                        <router-link :to="`/teacher/course/${courseId}/assignment/${asm.id}`" class="link font-medium">
                            {{ asm.title }}
                        </router-link>
                        <span class="ml-2 text-sm text-gray-600">截止: {{ asm.dueDate || '无' }}</span>
                        <span v-if="asm.status" class="ml-2 text-xs text-gray-500">[{{ asm.status }}]</span>
                    </li>
                    <li v-if="!assignments.length" class="text-gray-500 text-sm">暂无作业</li>
                </ul>
                <!-- 新建作业按钮 -->
                <div class="mt-6 text-center">
                    <button @click="showForm = true" v-if="!showForm" class="btn-primary px-6 py-2">
                        布置新作业
                    </button>
                </div>
                <!-- 新作业表单 -->
                <div v-if="showForm" class="mt-6 bg-white/80 p-6 rounded-xl shadow-inner">
                    <h3 class="text-base font-semibold text-gray-800 mb-4">新建作业</h3>
                    <form @submit.prevent="createAssignment" class="space-y-4">
                        <div>
                            <label class="label" for="title">作业标题</label>
                            <input id="title" v-model="newTitle" class="input-control" required />
                        </div>
                        <div>
                            <label class="label" for="description">作业要求</label>
                            <textarea id="description" v-model="newDesc" rows="3" class="input-control"></textarea>
                        </div>
                        <div>
                            <label class="label" for="due">截止日期</label>
                            <input id="due" v-model="newDue" type="date" class="input-control" />
                        </div>
                        <div>
                            <label class="label" for="ref">参考答案 (可选)</label>
                            <textarea id="ref" v-model="newRefAnswer" rows="2" class="input-control" placeholder="可填写评分标准或参考答案"></textarea>
                        </div>
                        <div class="text-center">
                            <button type="submit" class="btn-primary px-6 py-2 mr-4" :disabled="submitting">
                                提交
                            </button>
                            <button type="button" @click="cancelForm" class="btn-primary bg-gray-400 hover:bg-gray-500 px-6 py-2">
                                取消
                            </button>
                        </div>
                        <p v-if="formError" class="text-red-600 text-sm mt-2">{{ formError }}</p>
                    </form>
                </div>
            </section>

            <!-- 学生列表部分 (新增) -->
            <section class="bg-glass p-6 rounded-2xl mt-6">
                <h2 class="text-lg font-semibold text-emerald-700 mb-4">选课学生</h2>
                <div class="overflow-x-auto">
                    <table class="min-w-full bg-white/80 rounded-lg overflow-hidden">
                        <thead class="bg-gray-100">
                            <tr>
                                <th class="py-2 px-4 border-b border-gray-200 text-left text-sm text-gray-700">学号/邮箱</th>
                                <th class="py-2 px-4 border-b border-gray-200 text-left text-sm text-gray-700">姓名</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="student in students" :key="student.email" class="hover:bg-gray-50">
                                <td class="py-2 px-4 border-b border-gray-200 text-sm">{{ student.email }}</td>
                                <td class="py-2 px-4 border-b border-gray-200 text-sm font-medium">{{ student.name }}</td>
                            </tr>
                            <tr v-if="students.length === 0">
                                <td colspan="2" class="py-4 text-center text-gray-500 text-sm">暂无学生选课</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div v-if="loadingStudents" class="text-center py-4 text-gray-500 text-sm">
                    加载中...
                </div>
                <p v-if="studentsError" class="text-red-500 text-sm mt-2">{{ studentsError }}</p>
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
const route       = useRoute();
const courseId    = route.params.id as string;
const courseName  = ref('');
interface Assignment { id: string; title: string; dueDate?: string; status?: string }
const assignments = ref<Assignment[]>([]);
const loading     = ref(false);
const store = useUserStore();

/* ---------- 学生数据 (新增) ---------- */
interface Student { email: string; name: string }
const students = ref<Student[]>([]);
const loadingStudents = ref(false);
const studentsError = ref('');

/* ---------- 新作业表单数据 ---------- */
const showForm      = ref(false);
const newTitle      = ref('');
const newDesc       = ref('');
const newDue        = ref('');
const newRefAnswer  = ref('');
const submitting    = ref(false);
const formError     = ref('');

// 修改获取课程信息的函数
async function fetchCourseData() {
  try {
    const { data } = await axios.get(`/api/teacher/course/${courseId}`, {
      params: {
        token: store.token,
        useremail: store.useremail
      }
    });
    courseName.value = data.course?.name || `课程 ${courseId}`;
    assignments.value = data.assignments || [];
  } catch (err) {
    console.error('获取课程数据失败', err);
  }
}

// 修改获取学生列表的函数 
async function fetchCourseStudents() {
  try {
    const { data } = await axios.get(`/api/teacher/course/${courseId}/students`, {
      params: {
        token: store.token,
        useremail: store.useremail
      }
    });
    students.value = data.students || [];
  } catch (err) {
    console.error('获取学生列表失败', err);
  }
}

onMounted(() => {
    fetchCourseData();
    fetchCourseStudents(); // 加载学生列表
});

/* ---------- 提交新建作业 ---------- */
async function createAssignment() {
    formError.value = '';
    if (!newTitle.value.trim()) {
        formError.value = '标题不能为空';
        return;
    }
    submitting.value = true;
    try {
        const payload = {
            title: newTitle.value,
            description: newDesc.value,
            dueDate: newDue.value,
            referenceAnswer: newRefAnswer.value
        };
        // 修改这里，添加第三个参数包含认证信息
        const { data } = await axios.post(
            `/api/teacher/course/${courseId}/assignments`, 
            payload,
            { params: { token: store.token, useremail: store.useremail } }
        );
        const created = data.assignment;
        assignments.value.push(created);
        // 重置表单并关闭
        newTitle.value = '';
        newDesc.value = '';
        newDue.value = '';
        newRefAnswer.value = '';
        showForm.value = false;
    } catch (err) {
        console.error('作业创建失败', err);
        formError.value = '创建作业失败，请稍后重试';
    } finally {
        submitting.value = false;
    }
}

/* ---------- 取消新建作业 ---------- */
function cancelForm() {
    showForm.value = false;
    formError.value = '';
}
</script>