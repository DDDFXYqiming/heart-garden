<template>
  <div class="garden-page">
    <div class="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="mb-1 text-sm text-pencil/60">一本会生长的私人立体绘本</p>
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

    <div v-else-if="plants.length === 0" class="border-[3px] border-pencil bg-white/80 p-8 text-center shadow-hard-sm wobbly-md">
      <div class="text-6xl mb-3">🌱</div>
      <p class="text-xl">你的花园还是空地，种下第一篇日记吧</p>
      <p class="mt-2 text-pencil/60">等第一颗种子落下，这里会长出属于你的 3D 记忆花。</p>
    </div>

    <template v-else>
      <section
        data-testid="garden-world-summary"
        class="relative mb-5 overflow-hidden border-[3px] border-pencil bg-white/88 p-4 shadow-hard-sm wobbly-md"
      >
        <div class="tape"></div>
        <div class="grid gap-4 lg:grid-cols-[0.9fr_1fr_1.35fr] lg:items-center">
          <article class="flex items-center gap-4 border-b-[3px] border-dashed border-pencil/15 pb-4 lg:border-b-0 lg:border-r-[3px] lg:pb-0 lg:pr-5">
            <div class="flex h-20 w-20 items-center justify-center border-[2px] border-pencil bg-sticky text-4xl shadow-hard-sm wobbly">
              {{ climate.icon }}
            </div>
            <div>
              <div class="text-sm text-pencil/55">平均情绪分</div>
              <div class="text-5xl font-bold leading-none" style="font-family: 'Kalam', cursive;">{{ overview.avgScore }}</div>
              <div class="mt-1 text-sm text-pencil/55">最近 {{ overview.activeDays || 1 }} 天</div>
            </div>
          </article>

          <article class="border-b-[3px] border-dashed border-pencil/15 pb-4 lg:border-b-0 lg:border-r-[3px] lg:pb-0 lg:pr-5">
            <div class="text-sm text-pencil/55">当前花园</div>
            <div class="mt-1 flex items-center gap-3">
              <span class="text-4xl">🪴</span>
              <div>
                <h2 class="text-2xl font-bold" style="font-family: 'Kalam', cursive;">{{ overview.statusText }}</h2>
                <p class="text-sm text-pencil/60">你的心灵花园正在站出来生长</p>
              </div>
            </div>
          </article>

          <article class="flex items-center gap-4">
            <div class="flex h-20 w-24 items-center justify-center border-[2px] border-pencil bg-[#d8ecff] text-4xl shadow-hard-sm wobbly-md">
              {{ weatherIcon }}
            </div>
            <div>
              <div class="text-sm text-pencil/55">今日气候</div>
              <h2 class="text-2xl font-bold" style="font-family: 'Kalam', cursive;">{{ climate.label }}</h2>
              <p class="text-sm text-pencil/60">{{ climate.summary }}</p>
            </div>
          </article>
        </div>
      </section>

      <section class="grid gap-5 xl:grid-cols-[260px_minmax(0,1fr)]">
        <aside
          data-testid="garden-legend-note"
          class="relative h-max border-[3px] border-pencil bg-white/86 p-5 shadow-hard-sm wobbly-md xl:sticky xl:top-24"
        >
          <div class="tape"></div>
          <div class="mb-5">
            <div class="mb-3 text-3xl">🌿</div>
            <h2 class="text-2xl font-bold" style="font-family: 'Kalam', cursive;">3D 记忆花园</h2>
            <p class="mt-2 text-pencil/65">纸模花园里，记忆正在慢慢发光。</p>
          </div>

          <div class="space-y-4 border-y-[3px] border-dashed border-pencil/15 py-5">
            <div class="flex items-center gap-3">
              <span class="text-2xl">🌱</span>
              <div><b>植物</b><span class="ml-2 text-pencil/55">记忆的生长</span></div>
            </div>
            <div class="flex items-center gap-3">
              <span class="text-2xl">☁️</span>
              <div><b>天气</b><span class="ml-2 text-pencil/55">情绪的气候</span></div>
            </div>
            <div class="flex items-center gap-3">
              <span class="text-2xl">🪨</span>
              <div><b>路径</b><span class="ml-2 text-pencil/55">时间的足迹</span></div>
            </div>
          </div>

          <div class="mt-5 space-y-3">
            <div
              v-for="zone in zones.slice(0, 3)"
              :key="zone.key"
              class="border-[2px] border-pencil/40 bg-paper px-3 py-2 shadow-hard-sm wobbly-sm"
            >
              <span class="mr-2">{{ zone.icon }}</span>
              <b>{{ zone.label }}</b>
              <span class="ml-1 text-pencil/55">{{ zone.count }} 段</span>
            </div>
          </div>

          <p class="mt-6 text-pen-blue">用心照料，每一段记忆都会开花。</p>
        </aside>

        <div class="min-w-0">
          <GardenScene
            :plants="plants"
            :overview="overview"
            :world="world"
            :selected-plant-id="selectedPlant?.id || null"
            @select-plant="selectPlant"
            @clear-selection="clearSelection"
          />

          <div
            data-testid="garden-narration"
            class="mx-auto mt-4 flex max-w-2xl flex-col items-center justify-between gap-3 border-[2px] border-pencil bg-white/88 px-5 py-3 text-center shadow-hard-sm wobbly md:flex-row md:text-left"
          >
            <p class="text-pencil/75">🌿 {{ world.narration }}</p>
            <button
              class="shrink-0 border-[2px] border-pencil bg-sticky px-4 py-2 shadow-hard-sm transition-all hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-none wobbly-sm"
              @click="careGarden"
            >
              照料花园
            </button>
          </div>
        </div>
      </section>

      <section class="mt-5 border-[2px] border-dashed border-pencil bg-white/60 p-4 shadow-hard-sm wobbly-md">
        <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
          <h2 class="text-xl font-bold" style="font-family: 'Kalam', cursive;">🌷 记忆花朵索引</h2>
          <span class="border-[2px] border-pencil bg-paper px-3 py-0.5 text-sm wobbly-sm">最近 {{ plants.length }} 条</span>
        </div>
        <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
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
              <span class="border-[2px] border-pencil/30 bg-paper px-2 py-0.5 wobbly-sm">{{ plant.themeLabel }}</span>
              <span>{{ plant.timeLayerLabel }}</span>
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
import { getGarden, getGardenWorld } from '@/api'
import GardenScene from '@/components/garden/GardenScene.vue'
import PlantDetailPanel from '@/components/garden/PlantDetailPanel.vue'
import { buildGardenWorld } from '@/utils/gardenMapping'

const loading = ref(true)
const fallbackItems = ref([])
const gardenWorld = ref(buildGardenWorld([]))
const selectedPlant = ref(null)

const world = computed(() => gardenWorld.value)
const plants = computed(() => world.value.plants || [])
const overview = computed(() => world.value.overview || buildGardenWorld([]).overview)
const climate = computed(() => world.value.climate || buildGardenWorld([]).climate)
const zones = computed(() => world.value.zones || [])

const weatherIcon = computed(() => {
  const icons = {
    sunny: '☀️',
    breezy: '🌤️',
    cloudy: '☁️',
    mist: '🌫️',
    rainy: '🌧️'
  }
  return icons[climate.value.type] || climate.value.icon || '☁️'
})

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

function careGarden() {
  window.location.hash = '#/diary/new'
}

function openSourceRecord(plant) {
  if (!plant?.id) return
  if (plant.sourceType === 'diary') {
    window.location.hash = `#/diary/${plant.id}`
  }
}

onMounted(async () => {
  try {
    const res = await getGardenWorld()
    gardenWorld.value = buildGardenWorld(res.data?.items || [])
  } catch {
    try {
      const res = await getGarden()
      fallbackItems.value = res.data || []
      gardenWorld.value = buildGardenWorld(fallbackItems.value)
    } catch { /* empty */ }
  } finally {
    loading.value = false
  }
})
</script>
