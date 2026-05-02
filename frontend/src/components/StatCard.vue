<template>
  <div class="bg-white border-[3px] border-pencil p-5 wobbly-md shadow-hard-sm card-hover text-center">
    <div class="text-3xl mb-1">{{ icon }}</div>
    <div class="text-2xl font-bold" style="font-family: 'Kalam', cursive;">
      {{ value }}
    </div>
    <div class="text-sm text-pencil/60">{{ label }}</div>
  </div>
</template>

<script setup>
defineProps({
  icon: {
    type: String,
    required: true
  },
  value: {
    type: [String, Number],
    required: true
  },
  label: {
    type: String,
    required: true
  }
})
</script>
