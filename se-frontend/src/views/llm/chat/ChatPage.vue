<template>
    <!-- 全屏渐变背景 -->
    <div class="min-h-screen flex flex-col bg-main-gradient">
        <!-- 顶部栏：返回按钮和模型名称 -->
        <header class="p-6 lg:p-8 bg-white/30 backdrop-blur-sm shadow flex items-center gap-4">
            <button @click="$router.back()" class="text-indigo-600 hover:underline text-sm">
                ← 返回
            </button>
            <h1 class="text-xl lg:text-2xl font-bold text-gray-800 flex-1">
                {{ modelName || '对话模型' }}
            </h1>
        </header>

        <!-- 主体：聊天窗口 -->
        <main class="flex-1 flex flex-col p-4 lg:p-8">
            <!-- 历史消息记录 -->
            <div ref="scrollContainer" class="flex-1 overflow-y-auto space-y-6 pr-2">
                <div v-for="(msg, idx) in messages" :key="idx"
                     :class="msg.role === 'user' ? 'text-right'
                             : msg.role === 'assistant' ? 'text-left'
                             : 'text-center'">
                    <div :class="[
                            'inline-block max-w-[75%] px-4 py-2 rounded-lg',
                            msg.role === 'user'
                                ? 'bg-indigo-600 text-white'
                                : msg.role === 'assistant'
                                    ? 'bg-white shadow'
                                    : 'bg-gray-200 text-gray-700 text-sm italic'
                        ]">
                        {{ msg.content }}
                    </div>
                </div>
            </div>

            <!-- 输入区域：角色选择和消息输入框 -->
            <form @submit.prevent="sendMessage" class="mt-6 flex items-center gap-2">
                <select v-model="newRole" class="px-4 py-2 rounded border border-gray-300 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
                    <option value="user">用户</option>
                    <option value="system">系统</option>
                </select>
                <input v-model="input" :disabled="loading"
                       placeholder="输入消息..." class="flex-1 input-control" />
                <button type="submit" class="btn-primary px-6" :disabled="loading || !input.trim()">
                    发送
                </button>
            </form>
        </main>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';

/* ---------- 路由参数与状态 ---------- */
const route     = useRoute();
const modelId   = route.params.id as string;
const modelName = ref('');
const input     = ref('');
const newRole   = ref<'user' | 'system'>('user');  // 下条消息的角色（用户 或 系统）
const loading   = ref(false);

interface Msg { role: 'user' | 'assistant' | 'system'; content: string }
const messages  = ref<Msg[]>([]);

/* ---------- 消息更新后自动滚动到底部 ---------- */
const scrollContainer = ref<HTMLElement>();
watch(messages, () => nextTick(() => {
    scrollContainer.value?.scrollTo({ top: scrollContainer.value.scrollHeight });
}));

/* ---------- 获取模型元数据（名称等） ---------- */
async function fetchModelMeta() {
    try {
        const { data } = await axios.get(`/api/llm/meta/${modelId}`);
        modelName.value = data.name || `模型 ${modelId}`;
    } catch (err) {
        console.error('模型信息加载失败', err);
    }
}
onMounted(fetchModelMeta);

/* ---------- 发送消息（根据角色调用接口） ---------- */
async function sendMessage() {
    const content = input.value.trim();
    if (!content) return;
    // 将新消息添加到历史记录
    messages.value.push({ role: newRole.value, content });
    // 如果发送的是系统角色消息，则仅添加到上下文，不请求回复
    if (newRole.value === 'system') {
        input.value = '';
        newRole.value = 'user';  // 系统消息发送后切换回用户角色
        return;
    }
    // 否则为用户提问，调用后端接口获取回复
    input.value = '';
    loading.value = true;
    try {
        const { data } = await axios.post(`/api/llm/chat/${modelId}`, {
            message: content,
            history: messages.value
        });
        // 将助手回复加入消息列表
        messages.value.push({ role: 'assistant', content: data.reply });
    } catch (err) {
        console.error('聊天接口调用失败', err);
        messages.value.push({ role: 'assistant', content: '❌ 出错了，请稍后再试' });
    } finally {
        loading.value = false;
    }
}
</script>