<template>
    <div
        class="bg-white/50 backdrop-blur-sm rounded-2xl p-6 shadow-card transition hover:shadow-lg flex flex-col gap-3"
    >
        <!-- 课程标题 -->
        <h3 class="text-lg font-semibold text-gray-800">
            {{ course.name }}
        </h3>

        <!-- 课程简介 -->
        <p
            v-if="course.description"
            class="text-sm text-gray-700 whitespace-pre-line flex-1"
        >
            {{ course.description }}
        </p>
        <p v-else class="text-sm text-gray-500 flex-1">暂无课程简介</p>

        <!-- 时间 & 授课教师 -->
        <div class="text-xs text-gray-600 space-y-1">
            <p>
                开课时间：
                <span>
                    {{ course.startDate || '—' }}
                    <span v-if="course.endDate"> — {{ course.endDate }}</span>
                </span>
            </p>
            <p>授课教师：{{ course.teacher || '—' }}</p>
        </div>

        <!-- 操作按钮 -->
        <div class="mt-4 flex gap-3">
            <router-link
                :to="`/course/${course.id}`"
                class="bg-indigo-600/90 hover:bg-indigo-700 text-white rounded-lg px-4 py-1 text-xs shadow-card"
            >
                进入课程
            </router-link>

            <!-- 具名插槽：父组件可插入额外操作 -->
            <slot name="actions" />
        </div>
    </div>
</template>

<script setup lang="ts">
defineProps<{
    course: {
        id: string;
        name: string;
        description?: string;
        startDate?: string;
        endDate?: string;
        teacher?: string;
    };
}>();
</script>
