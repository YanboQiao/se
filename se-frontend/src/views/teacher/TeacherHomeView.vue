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
                <!-- 创建课程按钮 -->
                <button
                    @click="openCreateCourseModal"
                    class="bg-blue-600/90 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 transition shadow-card"
                >
                    创建课程
                </button>

                <!-- 学生管理按钮 -->
                <button
                    @click="openStudentManageModal"
                    class="bg-purple-600/90 text-white px-4 py-2 rounded-lg text-sm hover:bg-purple-700 transition shadow-card"
                >
                    学生管理
                </button>

                <!-- AI 学习助手入口（携带 useremail / role / token） -->
                <a
                    :href="llmUrl"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="bg-emerald-600/90 text-white px-4 py-2 rounded-lg text-sm hover:bg-emerald-700 transition shadow-card"
                >
                    大模型助手
                </a>

                <!-- 退出登录 -->
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

        <!-- 创建课程弹窗 -->
        <transition name="modal">
            <div
                v-if="createCourseModalOpen"
                class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
                @click.self="createCourseModalOpen = false"
            >
                <div class="bg-white rounded-lg max-w-md w-full">
                    <div class="p-6 border-b flex items-center justify-between">
                        <h3 class="text-lg font-semibold">创建新课程</h3>
                        <button @click="createCourseModalOpen = false" class="text-xl">&times;</button>
                    </div>
                    <div class="p-6">
                        <div class="space-y-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">课程名称 *</label>
                                <input
                                    v-model="createCourseForm.name"
                                    type="text"
                                    class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="请输入课程名称"
                                />
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">课程描述</label>
                                <textarea
                                    v-model="createCourseForm.description"
                                    rows="3"
                                    class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="请输入课程描述（可选）"
                                ></textarea>
                            </div>
                        </div>
                        <div class="mt-6 flex gap-3">
                            <button
                                @click="createCourseModalOpen = false"
                                class="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                            >
                                取消
                            </button>
                            <button
                                @click="submitCreateCourse"
                                :disabled="!createCourseForm.name.trim() || creatingCourse"
                                class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {{ creatingCourse ? '创建中...' : '创建课程' }}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </transition>

        <!-- 学生管理弹窗 -->
        <transition name="modal">
            <div
                v-if="studentManageModalOpen"
                class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
                @click.self="studentManageModalOpen = false"
            >
                <div class="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
                    <div class="p-6 border-b flex items-center justify-between">
                        <h3 class="text-lg font-semibold">学生管理</h3>
                        <button @click="studentManageModalOpen = false" class="text-xl">&times;</button>
                    </div>
                    <div class="p-6 max-h-[70vh] overflow-y-auto">
                        <!-- 搜索区域 -->
                        <div class="mb-6">
                            <div class="flex gap-3">
                                <input
                                    v-model="searchQuery"
                                    @input="handleSearchInput"
                                    type="text"
                                    class="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="按邮箱或姓名搜索学生..."
                                />
                                <button
                                    @click="searchStudents"
                                    :disabled="searching || !searchQuery.trim()"
                                    class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                                >
                                    {{ searching ? '搜索中...' : '搜索' }}
                                </button>
                            </div>
                        </div>

                        <!-- 课程选择 -->
                        <div class="mb-6" v-if="selectedStudents.length > 0">
                            <label class="block text-sm font-medium text-gray-700 mb-2">选择课程</label>
                            <select
                                v-model="selectedCourse"
                                class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="">请选择课程</option>
                                <option
                                    v-for="course in courses"
                                    :key="course.id"
                                    :value="course.id"
                                >
                                    {{ course.name }}
                                </option>
                            </select>
                        </div>

                        <!-- 搜索结果 -->
                        <div class="mb-6" v-if="searchResults.length > 0">
                            <h4 class="text-sm font-medium text-gray-700 mb-3">搜索结果</h4>
                            <div class="border border-gray-200 rounded-lg max-h-60 overflow-y-auto">
                                <div
                                    v-for="student in searchResults"
                                    :key="student.email"
                                    class="p-3 border-b border-gray-100 last:border-b-0 flex items-center justify-between hover:bg-gray-50"
                                >
                                    <div>
                                        <div class="font-medium">{{ student.name }}</div>
                                        <div class="text-sm text-gray-500">{{ student.email }}</div>
                                    </div>
                                    <button
                                        @click="toggleStudentSelection(student)"
                                        :class="[
                                            'px-3 py-1 rounded text-sm',
                                            isStudentSelected(student)
                                                ? 'bg-green-100 text-green-700'
                                                : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                                        ]"
                                    >
                                        {{ isStudentSelected(student) ? '已选中' : '选择' }}
                                    </button>
                                </div>
                            </div>
                        </div>

                        <!-- 已选择的学生 -->
                        <div class="mb-6" v-if="selectedStudents.length > 0">
                            <h4 class="text-sm font-medium text-gray-700 mb-3">
                                已选择的学生 ({{ selectedStudents.length }})
                            </h4>
                            <div class="border border-gray-200 rounded-lg max-h-40 overflow-y-auto">
                                <div
                                    v-for="student in selectedStudents"
                                    :key="student.email"
                                    class="p-3 border-b border-gray-100 last:border-b-0 flex items-center justify-between"
                                >
                                    <div>
                                        <div class="font-medium">{{ student.name }}</div>
                                        <div class="text-sm text-gray-500">{{ student.email }}</div>
                                    </div>
                                    <button
                                        @click="removeStudentSelection(student)"
                                        class="text-red-600 hover:text-red-800 text-sm"
                                    >
                                        移除
                                    </button>
                                </div>
                            </div>
                        </div>

                        <!-- 操作按钮 -->
                        <div class="flex gap-3">
                            <button
                                @click="studentManageModalOpen = false"
                                class="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                            >
                                取消
                            </button>
                            <button
                                @click="batchEnrollStudents"
                                :disabled="!selectedCourse || selectedStudents.length === 0 || enrolling"
                                class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {{ enrolling ? '添加中...' : `为${selectedStudents.length}名学生选课` }}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </transition>
    </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { useUserStore } from '@/stores/user';
import TeacherCourseCard from '@/components/TeacherCourseCard.vue';

/* ---------- Pinia & Router ---------- */
const store  = useUserStore();
const router = useRouter();

/* ---------- 计算属性 ---------- */
const greeting = computed(
    () => `${store.username || store.useremail || '老师'}老师，欢迎回来！`,
);

/* ---------- 大模型跳转 URL ---------- */
const llmUrl = computed(() => {
    if (store.useremail && store.token) {
        const q = new URLSearchParams({
            useremail: store.useremail,
            role: 'teacher',
            token: store.token,
        }).toString();
        return `http://localhost:8001/llms?${q}`;
    }
    return 'http://localhost:8001/llms';
});

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
interface Task     { id: string; title: string }
interface Message  { id: string; content: string }
interface Student  { email: string; name: string }

/* ---------- 状态 ---------- */
const courses      = ref<CourseDetail[]>([]);
const gradingList  = ref<Task[]>([]);
const messages     = ref<Message[]>([]);

// 创建课程相关状态
const createCourseModalOpen = ref(false);
const createCourseForm = ref({
    name: '',
    description: ''
});
const creatingCourse = ref(false);

// 学生管理相关状态
const studentManageModalOpen = ref(false);
const searchQuery = ref('');
const searching = ref(false);
const searchResults = ref<Student[]>([]);
const selectedStudents = ref<Student[]>([]);
const selectedCourse = ref('');
const enrolling = ref(false);

let searchTimeout: number;

/* ---------- 数据拉取 ---------- */
async function fetchTeacherData() {
    try {
        const { data } = await axios.get('/api/teacher/dashboard', {
            params: { useremail: store.useremail, token: store.token },
        });
        courses.value     = (data.courses || []) as CourseDetail[];
        gradingList.value = data.gradingList || [];
        messages.value    = data.messages    || [];
    } catch (e) {
        console.error('获取教师数据失败:', e);
    }
}
onMounted(fetchTeacherData);

/* ---------- 创建课程相关功能 ---------- */
function openCreateCourseModal() {
    createCourseModalOpen.value = true;
    createCourseForm.value = {
        name: '',
        description: ''
    };
}

async function submitCreateCourse() {
    if (!createCourseForm.value.name.trim()) {
        alert('请输入课程名称');
        return;
    }
    
    creatingCourse.value = true;
    try {
        const response = await axios.post('/api/teacher/course/create', {
            name: createCourseForm.value.name,
            description: createCourseForm.value.description,
            useremail: store.useremail,
            token: store.token
        });
        
        if (response.data.status === 'success') {
            alert('课程创建成功！');
            createCourseModalOpen.value = false;
            await fetchTeacherData(); // 刷新课程列表
        } else {
            alert(response.data.message || '创建失败');
        }
    } catch (error: any) {
        console.error('创建课程失败:', error);
        alert(error.response?.data?.message || '创建课程失败，请稍后再试');
    } finally {
        creatingCourse.value = false;
    }
}

/* ---------- 学生管理相关功能 ---------- */
function openStudentManageModal() {
    studentManageModalOpen.value = true;
    // 重置状态
    searchQuery.value = '';
    searchResults.value = [];
    selectedStudents.value = [];
    selectedCourse.value = '';
}

function handleSearchInput() {
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }
    searchTimeout = window.setTimeout(() => {
        if (searchQuery.value.trim()) {
            searchStudents();
        } else {
            searchResults.value = [];
        }
    }, 500);
}

async function searchStudents() {
    if (!searchQuery.value.trim()) {
        searchResults.value = [];
        return;
    }
    
    searching.value = true;
    try {
        const response = await axios.get('/api/teacher/search-students', {
            params: {
                query: searchQuery.value,
                limit: 20,
                useremail: store.useremail,
                token: store.token
            }
        });
        
        searchResults.value = response.data.students || [];
    } catch (error: any) {
        console.error('搜索学生失败:', error);
        alert(error.response?.data?.message || '搜索失败，请稍后再试');
    } finally {
        searching.value = false;
    }
}

function isStudentSelected(student: Student): boolean {
    return selectedStudents.value.some(s => s.email === student.email);
}

function toggleStudentSelection(student: Student) {
    const index = selectedStudents.value.findIndex(s => s.email === student.email);
    if (index === -1) {
        selectedStudents.value.push(student);
    } else {
        selectedStudents.value.splice(index, 1);
    }
}

function removeStudentSelection(student: Student) {
    const index = selectedStudents.value.findIndex(s => s.email === student.email);
    if (index !== -1) {
        selectedStudents.value.splice(index, 1);
    }
}

async function batchEnrollStudents() {
    if (!selectedCourse.value || selectedStudents.value.length === 0) {
        alert('请选择课程和学生');
        return;
    }
    
    enrolling.value = true;
    try {
        const response = await axios.post('/api/teacher/batch-enroll', {
            course_id: selectedCourse.value,
            student_emails: selectedStudents.value.map(s => s.email),
            useremail: store.useremail,
            token: store.token
        });
        
        if (response.data.success_count > 0) {
            alert(`成功为 ${response.data.success_count} 名学生选课！`);
            
            // 显示失败的学生信息
            if (response.data.failed_students?.length > 0) {
                const failedList = response.data.failed_students
                    .map((f: any) => `${f.email}: ${f.reason}`)
                    .join('\n');
                alert(`部分学生选课失败：\n${failedList}`);
            }
            
            // 清空选择
            selectedStudents.value = [];
            selectedCourse.value = '';
        } else {
            alert(response.data.message || '选课失败');
        }
    } catch (error: any) {
        console.error('批量选课失败:', error);
        alert(error.response?.data?.message || '批量选课失败，请稍后再试');
    } finally {
        enrolling.value = false;
    }
}

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

<style scoped>
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
