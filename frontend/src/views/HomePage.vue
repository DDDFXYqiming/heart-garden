<template>
  <div class="text-center py-10 md:py-16">
    <div class="relative inline-block">
      <div class="text-7xl md:text-8xl mb-4 animate-gentle-bounce">🌸</div>
      <div class="absolute -top-2 -right-4 w-6 h-6 bg-accent border-[2px] border-pencil rounded-full"></div>
    </div>
    <h1 class="text-5xl md:text-6xl mb-4" style="font-family: 'Kalam', cursive; font-weight: 700;">心语花园</h1>
    <p class="text-xl md:text-2xl text-pencil/70 mb-8">你的 AI 情感陪伴空间</p>

    <div class="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
      <router-link to="/register" class="px-8 py-3 text-xl border-[3px] border-pencil bg-white shadow-hard hover:shadow-hard-hover hover:translate-x-[2px] hover:translate-y-[2px] active:shadow-none active:translate-x-[4px] active:translate-y-[4px] transition-all wobbly no-underline text-pencil">开始旅程</router-link>
      <router-link to="/login" class="px-8 py-3 text-xl border-[3px] border-pencil bg-muted shadow-hard hover:shadow-hard-hover hover:translate-x-[2px] hover:translate-y-[2px] active:shadow-none active:translate-x-[4px] active:translate-y-[4px] transition-all wobbly no-underline text-pencil">回到花园</router-link>
    </div>

    <div class="grid md:grid-cols-3 gap-6 text-left">
      <div class="bg-white border-[3px] border-pencil p-6 wobbly-md shadow-hard-sm card-hover relative">
        <div class="tape"></div>
        <div class="text-3xl mb-2">📝</div>
        <h3 class="text-xl mb-2" style="font-family: 'Kalam', cursive; font-weight: 700;">日记记录</h3>
        <p class="text-base text-pencil/70">记录你的每一天，让心事变成文字，让回忆有迹可循。</p>
      </div>
      <div class="bg-white border-[3px] border-pencil p-6 wobbly-md shadow-hard-sm card-hover relative">
        <div class="tape"></div>
        <div class="text-3xl mb-2">💬</div>
        <h3 class="text-xl mb-2" style="font-family: 'Kalam', cursive; font-weight: 700;">AI 陪伴</h3>
        <p class="text-base text-pencil/70">24 小时在线的贴心伴侣，认真倾听你的每一句话。</p>
      </div>
      <div class="bg-white border-[3px] border-pencil p-6 wobbly-md shadow-hard-sm card-hover relative">
        <div class="tape"></div>
        <div class="text-3xl mb-2">📊</div>
        <h3 class="text-xl mb-2" style="font-family: 'Kalam', cursive; font-weight: 700;">情绪追踪</h3>
        <p class="text-base text-pencil/70">用数据看见自己的情绪曲线，更了解自己的内心世界。</p>
      </div>
    </div>
  </div>
</template>
