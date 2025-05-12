<template>
    <div class="min-h-screen flex flex-col bg-main-gradient">
        <!-- 顶部栏 -->
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
            <!-- 历史记录 -->
            <div ref="scrollContainer"
                 class="flex-1 overflow-y-auto space-y-6 pr-2">
                <div
                    v-for="(msg, idx) in messages"
                    :key="idx"
                    :class="msg.role === 'user' ? 'text-right' : 'text-left'"
                >
                    <div
                        :class="['inline-block max-w-[75%] px-4 py-2 rounded-lg',
                                 msg.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-white shadow']">
                        {{ msg.content }}
                    </div>
                </div>
            </div>

            <!-- 输入框 -->
            <form @submit.prevent="sendMessage" class="mt-6 flex gap-2">
                <input v-model="input" placeholder="输入消息..."
                       class="flex-1 input-control" />
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

/* ---------- 路由 & 状态 ---------- */
const route      = useRoute();
const modelId    = route.params.id as string;
const modelName  = ref('');                 // 可后台返回
const input      = ref('');
const loading    = ref(false);

interface Msg { role: 'user' | 'assistant'; content: string }
const messages = ref<Msg[]>([]);

/* 自动滚动到底部 */
const scrollContainer = ref<HTMLElement>();
watch(messages, () => nextTick(() =>
    scrollContainer.value?.scrollTo({ top: scrollContainer.value.scrollHeight })
));

/* 初次可拉取 model meta 信息 */
async function fetchModelMeta() {
    const { data } = await axios.get(`/api/llm/meta/${modelId}`);
    modelName.value = data.name || `模型 ${modelId}`;
}
onMounted(fetchModelMeta);

/* 发送消息 */
async function sendMessage() {
    const content = input.value.trim();
    if (!content) return;
    messages.value.push({ role: 'user', content });
    input.value   = '';
    loading.value = true;

    try {
        const { data } = await axios.post(`/api/llm/chat/${modelId}`, {
            message: content,
            history: messages.value,       // 或仅最近若干
        });
        messages.value.push({ role: 'assistant', content: data.reply });
    } catch (err) {
        messages.value.push({ role: 'assistant', content: '❌ 出错了，请稍后再试' });
    } finally {
        loading.value = false;
    }
}
</script>