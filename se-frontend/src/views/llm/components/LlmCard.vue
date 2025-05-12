<template>
    <div
        class="group relative cursor-pointer overflow-hidden rounded-xl bg-white shadow-lg transition hover:shadow-2xl"
        @click="$emit('click')"
    >
        <!-- 顶部图标 -->
        <div class="h-28 bg-indigo-600 flex items-center justify-center">
            <img
                v-if="model.avatar"
                :src="model.avatar"
                alt="avatar"
                class="h-16 w-16 object-contain"
            />
            <span v-else class="text-white text-4xl">
                🤖
            </span>
        </div>

        <!-- 卡片主体 -->
        <div class="p-5 space-y-2">
            <h3 class="text-lg font-bold text-gray-800">
                {{ model.name }}
            </h3>
            <p class="text-sm text-gray-600 line-clamp-3">
                {{ model.description }}
            </p>
            <span
                class="absolute top-2 right-2 bg-indigo-100 text-indigo-600 text-xs py-1 px-2 rounded-full">
                {{ model.type === 'chat' ? '对话' : '智能体' }}
            </span>
        </div>

        <!-- Hover 遮罩 -->
        <div
            class="absolute inset-0 bg-indigo-700/70 flex items-center justify-center text-white text-sm
                   opacity-0 group-hover:opacity-100 transition">
            点击进入
        </div>
    </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue';
import type { PropType } from 'vue';

/* 与 index.vue 保持一致 */
interface LlmModel {
    id: string;
    name: string;
    description: string;
    avatar?: string;
    type: 'chat' | 'agent';
}

defineProps({
    model: {
        type: Object as PropType<LlmModel>,
        required: true,
    },
});
</script>