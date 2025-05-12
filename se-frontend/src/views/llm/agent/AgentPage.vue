<template>
    <div class="min-h-screen flex flex-col bg-main-gradient">
        <!-- 顶部栏 -->
        <header class="p-6 lg:p-8 bg-white/30 backdrop-blur-sm shadow flex items-center gap-4">
            <button @click="$router.back()" class="text-emerald-600 hover:underline text-sm">
                ← 返回
            </button>
            <h1 class="text-xl lg:text-2xl font-bold text-gray-800 flex-1">
                {{ agentName || '智能体' }}
            </h1>
            <button
                class="btn-primary px-6"
                :disabled="running"
                @click="runAgent"
            >
                {{ running ? '运行中…' : '运行任务' }}
            </button>
        </header>

        <!-- 主体 -->
        <main class="flex-1 p-4 lg:p-8 grid lg:grid-cols-[300px_1fr] gap-6">
            <!-- 配置 / 说明 -->
            <section class="bg-glass p-6 space-y-4">
                <h2 class="text-lg font-semibold text-emerald-700">任务说明</h2>
                <p class="text-gray-700 whitespace-pre-line">{{ description }}</p>
            </section>

            <!-- 日志输出 -->
            <section class="bg-glass p-6 overflow-y-auto">
                <h2 class="text-lg font-semibold text-emerald-700 mb-4">执行日志</h2>
                <pre class="whitespace-pre-wrap text-sm leading-6">{{ logs }}</pre>
            </section>
        </main>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';

/* ---------- 路由 & 状态 ---------- */
const route      = useRoute();
const agentId    = route.params.id as string;

const agentName   = ref('');
const description = ref('');
const logs        = ref('');
const running     = ref(false);

/* 拉取元数据 */
async function fetchAgentMeta() {
    const { data } = await axios.get(`/api/llm/agent/meta/${agentId}`);
    agentName.value   = data.name || `Agent ${agentId}`;
    description.value = data.description || '暂无说明';
}
onMounted(fetchAgentMeta);

/* 运行任务 */
async function runAgent() {
    running.value = true;
    logs.value    = '任务启动...\n';
    try {
        const { data } = await axios.post(`/api/llm/agent/${agentId}/run`);
        // 假设后端返回 streamingLog / log 数组
        logs.value += data.log || data.streamingLog || '任务完成';
    } catch (err) {
        logs.value += '\n❌ 运行失败，请稍后再试';
    } finally {
        running.value = false;
    }
}
</script>