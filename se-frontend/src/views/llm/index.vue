<template>
    <div class="min-h-screen flex flex-col bg-main-gradient">
        <!-- 顶部栏 -->
        <header class="p-6 lg:p-8 bg-white/30 backdrop-blur-sm shadow">
            <h1 class="text-2xl lg:text-3xl font-bold text-gray-800">
                可用大模型
            </h1>
        </header>

        <!-- 主体：卡片网格 -->
        <main class="flex-1 p-6 lg:p-10">
            <!-- 加载态 -->
            <div v-if="loading" class="flex justify-center items-center h-60">
                <span class="animate-spin h-8 w-8 border-4 border-indigo-500 border-t-transparent rounded-full"></span>
            </div>

            <!-- 卡片网格 -->
            <div v-else class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                <LlmCard
                    v-for="model in models"
                    :key="model.id"
                    :model="model"
                    @click="goToModel(model)"
                />
            </div>

            <!-- 空数据 -->
            <p v-if="!loading && !models.length" class="text-center text-gray-600 mt-20">
                暂无可用模型
            </p>
        </main>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { useUserStore } from '@/stores/user';
import LlmCard from './components/LlmCard.vue';  /* 相对 llm/ */

interface LlmModel {
    id: string;
    name: string;
    description: string;
    avatar?: string;               // 可选：展示图标
    type: 'chat' | 'agent';        // chat=普通对话，agent=执行任务
}

const store   = useUserStore();
const models  = ref<LlmModel[]>([]);
const loading = ref(false);

/* 获取模型列表 */
async function fetchModels() {
    loading.value = true;
    try {
        // TODO: 替换为真实后端接口（会根据 token / role 返回可用模型）
        const { data } = await axios.get('/api/llm/list');
        models.value  = data.models as LlmModel[];
    } catch (err) {
        console.error('加载模型列表失败', err);
    } finally {
        loading.value = false;
    }
}

/* 点击卡片：根据模型类型跳转不同页面 */
function goToModel(model: LlmModel) {
    const path = model.type === 'chat'
        ? `/llm/chat/${model.id}`
        : `/llm/agent/${model.id}`;
    // 使用全局路由
    window.$router?.push?.(path);          // 若项目 Router 挂载到全局
}

onMounted(fetchModels);
</script>