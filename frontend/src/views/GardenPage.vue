<template>
  <div>
    <div class="mb-5 flex flex-wrap items-end justify-between gap-3">
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
      <section class="relative mb-5 overflow-hidden border-[3px] border-pencil bg-white/85 p-4 shadow-hard-sm wobbly-md">
        <div class="tape"></div>
        <div class="grid gap-4 md:grid-cols-[1.3fr_0.8fr_0.8fr] md:items-center">
          <div>
            <span class="text-sm text-pencil/60">花园概览</span>
            <div class="mt-1 flex flex-wrap items-center gap-3">
              <span class="text-3xl">{{ overview.statusEmoji }}</span>
              <h2 class="text-2xl font-bold" style="font-family: 'Kalam', cursive;">{{ overview.statusText }}</h2>
              <span class="border-[2px] border-pencil bg-sticky px-3 py-0.5 text-sm shadow-hard-sm wobbly-sm">
                {{ overview.totalCount }} 朵记忆花
              </span>
            </div>
            <p class="mt-2 text-sm text-pencil/65">颜色、高度、花型与动效由记录的情绪分和内容稳定生成。</p>
          </div>
          <div class="border-l-0 border-pencil/20 md:border-l-[3px] md:pl-5">
            <div class="text-sm text-pencil/60">平均情绪分</div>
            <div class="text-4xl font-bold" style="font-family: 'Kalam', cursive;">{{ overview.avgScore }}</div>
          </div>
          <div class="border-l-0 border-pencil/20 md:border-l-[3px] md:pl-5">
            <div class="text-sm text-pencil/60">当前选中</div>
            <div class="text-xl font-bold truncate" style="font-family: 'Kalam', cursive;">
              {{ selectedPlant ? selectedPlant.title : '整座花园' }}
            </div>
          </div>
        </div>
      </section>

      <GardenScene
        :plants="plants"
        :overview="overview"
        :selected-plant-id="selectedPlant?.id || null"
        @select-plant="selectPlant"
        @clear-selection="clearSelection"
      />

      <section class="mt-5 border-[2px] border-dashed border-pencil bg-white/60 p-4 shadow-hard-sm wobbly-md">
        <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
          <h2 class="text-xl font-bold" style="font-family: 'Kalam', cursive;">🌷 记忆花朵索引</h2>
          <span class="border-[2px] border-pencil bg-paper px-3 py-0.5 text-sm wobbly-sm">最近 {{ plants.length }} 条</span>
        </div>
        <div class="grid gap-3 md:grid-cols-3">
          <button
            v-for="plant in plants"
            :key="plant.id"
            class="group border-[2px] border-pencil bg-white/82 p-4 text-left shadow-hard-sm transition-all hover:-rotate-1 hover:translate-x-[1px] hover:translate-y-[1px] hover:bg-sticky hover:shadow-none wobbly-sm"
            :class="selectedPlant?.id === plant.id ? 'bg-sticky -rotate-1 shadow-hard-hover' : ''"
            @click="selectPlant(plant)"
          >
            <div class="flex items-start justify-between gap-3">
              <h3 class="text-base font-bold leading-tight" style="font-family: 'Kalam', cursive;">{{ plant.title }}</h3>
              <span class="text-xl">{{ plantIcon(plant.modelType) }}</span>
            </div>
            <p class="mt-2 line-clamp-2 text-sm text-pencil/65">{{ plant.contentPreview }}</p>
            <div class="mt-3 flex flex-wrap items-center gap-2 text-xs text-pencil/55">
              <span>{{ plant.createdAt }}</span>
              <span class="border-[2px] border-pencil/30 bg-paper px-2 py-0.5 wobbly-sm">{{ plant.moodLabel }}</span>
              <span>情绪 {{ plant.moodScore }}</span>
            </div>
          </button>
        </div>
      </section>
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
    leafBloom: '🌼',
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
