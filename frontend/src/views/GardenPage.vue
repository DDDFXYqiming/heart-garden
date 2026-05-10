<template>
  <div>
    <div class="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="mb-1 text-sm text-pencil/60">把每一段记录种进会呼吸的 3D 小花园</p>
        <h1 class="text-3xl md:text-4xl" style="font-family: 'Kalam', cursive; font-weight: 700;">记忆花园</h1>
      </div>
      <button
        v-if="selectedPlant"
        class="border-[2px] border-pencil bg-white px-4 py-2 shadow-hard-sm transition-all hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-none wobbly-sm"
        @click="clearSelection"
      >
        回到全景
      </button>
    </div>

    <div v-if="loading" class="text-center py-10">
      <div class="text-5xl animate-gentle-bounce">🌸</div>
      <p class="text-lg mt-2">花园正在生长...</p>
    </div>

    <div v-else-if="garden.length === 0" class="border-[3px] border-pencil bg-white/80 p-8 text-center shadow-hard-sm wobbly-md">
      <div class="text-6xl mb-3">🌱</div>
      <p class="text-xl">你的花园还是空地，种下第一篇日记吧</p>
      <p class="mt-2 text-pencil/60">等第一颗种子落下，这里会长出属于你的 3D 记忆花。</p>
    </div>

    <template v-else>
      <div class="grid gap-4 md:grid-cols-4 mb-6">
        <div class="bg-white border-[3px] border-pencil p-4 wobbly-md shadow-hard-sm">
          <span class="text-pencil/60">日记总数</span>
          <div class="text-3xl font-bold" style="font-family: 'Kalam', cursive;">{{ overview.totalCount }}</div>
        </div>
        <div class="bg-white border-[3px] border-pencil p-4 wobbly-md shadow-hard-sm">
          <span class="text-pencil/60">平均情绪分</span>
          <div class="text-3xl font-bold" style="font-family: 'Kalam', cursive;">{{ overview.avgScore }}</div>
        </div>
        <div class="bg-white border-[3px] border-pencil p-4 wobbly-md shadow-hard-sm md:col-span-2">
          <span class="text-pencil/60">花园概览</span>
          <div class="text-2xl font-bold" style="font-family: 'Kalam', cursive;">{{ overview.statusEmoji }} {{ overview.statusText }}</div>
          <p class="mt-1 text-sm text-pencil/60">每朵花都对应一条记录，颜色、高度和花型由情绪与内容生成。</p>
        </div>
      </div>

      <GardenScene
        :plants="plants"
        :overview="overview"
        :selected-plant-id="selectedPlant?.id || null"
        @select-plant="selectPlant"
        @clear-selection="clearSelection"
      />

      <div class="mt-6 border-[3px] border-pencil bg-white/80 p-5 shadow-hard-sm wobbly-md">
        <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
          <h2 class="text-xl font-bold" style="font-family: 'Kalam', cursive;">🌷 记忆花朵索引</h2>
          <span class="text-sm text-pencil/60">给键盘与低性能设备保留的文字入口</span>
        </div>
        <div class="grid gap-3 md:grid-cols-2">
          <button
            v-for="plant in plants"
            :key="plant.id"
            class="group border-[2px] border-pencil bg-white/80 p-4 text-left shadow-hard-sm transition-all hover:translate-x-[1px] hover:translate-y-[1px] hover:bg-amber-50 hover:shadow-none wobbly-sm"
            @click="selectPlant(plant)"
          >
            <div class="flex items-center justify-between gap-3">
              <h3 class="text-lg font-bold" style="font-family: 'Kalam', cursive;">{{ plant.title }}</h3>
              <span class="text-xl">{{ plantIcon(plant.modelType) }}</span>
            </div>
            <p class="mt-1 line-clamp-2 text-sm text-pencil/65">{{ plant.contentPreview }}</p>
            <div class="mt-2 text-xs text-pencil/50">{{ plant.createdAt }} · {{ plant.moodLabel }} · 情绪 {{ plant.moodScore }}</div>
          </button>
        </div>
      </div>
    </template>

    <PlantDetailPanel
      :plant="selectedPlant"
      @close="clearSelection"
      @open-source="openSourceRecord"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { getGarden } from '@/api'
import GardenScene from '@/components/garden/GardenScene.vue'
import PlantDetailPanel from '@/components/garden/PlantDetailPanel.vue'
import { buildGardenOverview, createGardenPlants } from '@/utils/gardenMapping'

const loading = ref(true)
const garden = ref([])
const selectedPlant = ref(null)

const plants = computed(() => createGardenPlants(garden.value))
const overview = computed(() => buildGardenOverview(plants.value))

function plantIcon(modelType) {
  const icons = {
    sunflower: '🌻',
    leafBloom: '🌸',
    flower: '🌺',
    sprout: '🌱',
    duskLeaf: '🍂',
    cactus: '🌵'
  }
  return icons[modelType] || '🌷'
}

function selectPlant(plant) {
  selectedPlant.value = plant
}

function clearSelection() {
  selectedPlant.value = null
}

function openSourceRecord(plant) {
  if (!plant?.id) return
  if (plant.sourceType === 'diary') {
    window.location.hash = `#/diary/${plant.id}`
  }
}

onMounted(async () => {
  try {
    const res = await getGarden()
    garden.value = res.data
  } catch { /* empty */ }
  finally { loading.value = false }
})
</script>
