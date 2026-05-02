<template>
  <div :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']">
    <div :class="[
      'max-w-[80%] px-4 py-2 border-[2px] border-pencil',
      msg.role === 'user' ? 'bg-sticky' : 'bg-white',
      'wobbly-sm'
    ]">
      <p class="text-base whitespace-pre-line">{{ msg.content }}</p>
      <div v-if="msg.mood_label || msg.response_mode" class="flex items-center gap-2 mt-1">
        <span v-if="msg.mood_label" class="text-xs text-pencil/50">{{ msg.mood_label }}</span>
        <span
          v-if="msg.response_mode"
          :class="[
            'text-xs px-1.5 py-0.5 border border-pencil/30 rounded',
            msg.response_mode === 'llm' ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-500'
          ]"
        >
          {{ msg.response_mode === 'llm' ? 'AI' : '规则' }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  msg: {
    type: Object,
    required: true,
    validator: (val) => val.role && val.content !== undefined
  }
})
</script>
