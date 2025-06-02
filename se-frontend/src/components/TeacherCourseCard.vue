<template>
    <div
        class="bg-white/50 backdrop-blur-sm rounded-2xl p-6 shadow-card transition hover:shadow-lg flex flex-col gap-3"
    >
        <!-- 课程标题 -->
        <h3 class="text-lg font-semibold text-gray-800">
            {{ course.name }}
            <span
                v-if="course.status"
                class="text-xs text-gray-600 ml-1"
            >
                [{{ course.status }}]
            </span>
        </h3>

        <!-- 课程简介 -->
        <p
            v-if="course.description"
            class="text-sm text-gray-700 whitespace-pre-line flex-1"
        >
            {{ course.description }}
        </p>
        <p v-else class="text-sm text-gray-500 flex-1">暂无课程简介</p>

        <!-- 统计信息 -->
        <div class="text-xs text-gray-600 space-y-1">
            <p>
                时间：
                {{ course.startDate || '—' }}
                <span v-if="course.endDate"> — {{ course.endDate }}</span>
            </p>
            <p>选课人数：{{ course.studentCount ?? '—' }}</p>
            <p>待批改作业：{{ course.ungradedCount ?? 0 }}</p>
        </div>

        <!-- 操作 -->
        <div class="mt-4 flex gap-3">
            <router-link
                :to="`/teacher/course/${course.id}`"
                class="bg-emerald-600/90 hover:bg-emerald-700 text-white rounded-lg px-4 py-1 text-xs shadow-card"
            >
                进入课程
            </router-link>
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
        status?: string;
        studentCount?: number;
        ungradedCount?: number;
    };
}>();
</script>