<template>
  <section
    class="garden-canvas-shell relative overflow-hidden border-[3px] border-pencil bg-gradient-to-b from-[#fff8ec] via-[#eef7f0] to-[#f7f0df] shadow-hard wobbly-lg"
    aria-label="3D 记忆花园"
  >
    <div
      ref="container"
      data-testid="garden-scene"
      class="h-[560px] min-h-[460px] w-full cursor-zoom-in md:h-[690px]"
    ></div>

    <div class="pointer-events-none absolute left-4 top-4 max-w-xs border-[2px] border-pencil bg-white/88 px-4 py-3 text-sm shadow-hard-sm backdrop-blur wobbly-sm">
      <div class="font-bold" style="font-family: 'Kalam', cursive;">🌿 3D 记忆花园</div>
      <div class="text-pencil/70">固定纸模沙盘里，记忆正在慢慢发光。</div>
    </div>

    <div
      v-if="activeClimate"
      data-testid="garden-weather-badge"
      class="pointer-events-none absolute right-4 top-4 hidden border-[2px] border-pencil bg-white/88 px-4 py-3 text-sm shadow-hard-sm backdrop-blur wobbly-sm md:block"
    >
      <div class="text-pencil/60">今日气候</div>
      <div class="text-xl font-bold" style="font-family: 'Kalam', cursive;">
        {{ activeClimate.icon }} {{ activeClimate.label }}
      </div>
      <div class="text-pencil/70">{{ activeOverview.totalCount }} 段记忆 · 波动 {{ activeOverview.volatility }}</div>
    </div>

    <div class="pointer-events-none absolute inset-0" data-testid="garden-diorama-labels">
      <div class="garden-chip garden-chip-happy">😊 开心</div>
      <div class="garden-chip garden-chip-memory">⭐ 重要回忆</div>
      <div class="garden-chip garden-chip-calm">平静</div>
      <div class="garden-chip garden-chip-transform">工作压力 → 正在转化</div>
    </div>

    <div
      v-if="hoveredPlant"
      data-testid="garden-hover-card"
      class="pointer-events-none absolute bottom-4 left-1/2 max-w-sm -translate-x-1/2 border-[2px] border-pencil bg-white/92 px-4 py-3 text-center shadow-hard-sm backdrop-blur wobbly-sm"
    >
      <div class="text-base font-bold" style="font-family: 'Kalam', cursive;">{{ hoveredPlant.title }}</div>
      <div class="text-sm text-pencil/70">{{ hoveredPlant.themeLabel || hoveredPlant.moodLabel }} · {{ hoveredPlant.zoneLabel || '记忆植物' }}</div>
    </div>

    <div
      v-if="webglError"
      data-testid="garden-scene-fallback"
      class="absolute inset-0 flex flex-col items-center justify-center bg-amber-50/95 px-6 text-center"
    >
      <div class="mb-3 text-6xl">🌷</div>
      <h2 class="text-2xl font-bold" style="font-family: 'Kalam', cursive;">3D 花园正在等浏览器阳光</h2>
      <p class="mt-2 max-w-md text-pencil/70">{{ webglError }}</p>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

const PLOT_WIDTH = 8.8
const PLOT_DEPTH = 5.1
const FRUSTUM_SIZE = 6.2
const CLICK_DRAG_THRESHOLD = 4
const HOME_CAMERA_POSITION = new THREE.Vector3(0.8, 4.7, 7.2)
const HOME_LOOK_AT = new THREE.Vector3(0, 0.35, 0)
const HOME_ZOOM = 1.05
const OUTLINE_COLOR = '#2f2a22'

const ZONE_FOCUS = {
  cheerfulFlowerZone: {
    camera: new THREE.Vector3(0.45, 4.4, 6.8),
    target: new THREE.Vector3(-2.3, 0.25, 0.25),
    zoom: 1.22
  },
  memoryTreeZone: {
    camera: new THREE.Vector3(0.6, 4.5, 6.8),
    target: new THREE.Vector3(0.15, 0.5, -0.35),
    zoom: 1.25
  },
  calmPondZone: {
    camera: new THREE.Vector3(0.75, 4.4, 6.8),
    target: new THREE.Vector3(2.35, 0.25, 0.45),
    zoom: 1.2
  },
  transformingVinesZone: {
    camera: new THREE.Vector3(0.55, 4.4, 6.9),
    target: new THREE.Vector3(-0.25, 0.2, 1.35),
    zoom: 1.22
  }
}

const DEFAULT_CLIMATE = {
  type: 'breezy',
  icon: '🌤️',
  label: '微风晴间多云',
  summary: '适合回顾与整理，情绪趋于平稳。',
  skyColor: '#d7eef2',
  horizonColor: '#fff2bd',
  groundTint: '#d8e9a8',
  lightColor: '#ffe9b6',
  sunlightIntensity: 2.75,
  fogColor: '#fff8ec',
  fogNear: 15,
  fogFar: 36,
  windSpeed: 0.8,
  rainIntensity: 0,
  mistIntensity: 0.12,
  leafDrift: 0.62
}

const PALETTE = {
  cream: '#fff3c9',
  paper: '#fff8df',
  traySide: '#e9d990',
  trayInner: '#eef6b5',
  grass: '#cfe3a0',
  grassDark: '#91a86b',
  warmSoil: '#d8a65d',
  sand: '#f2cf86',
  yellow: '#ffdf6b',
  flowerWhite: '#fffbf1',
  pondBlue: '#9dd9e9',
  pondDeep: '#67adc7',
  vineBlue: '#8da8a4',
  vineDark: '#5f7779',
  wood: '#aa7435',
  ink: '#2c2923',
  glow: '#ffd66b'
}

const props = defineProps({
  plants: {
    type: Array,
    default: () => []
  },
  overview: {
    type: Object,
    default: null
  },
  selectedPlantId: {
    type: [String, Number],
    default: null
  },
  world: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['select-plant', 'clear-selection'])

const container = ref(null)
const hoveredPlant = ref(null)
const webglError = ref('')

const activeClimate = computed(() => currentWorld().climate)
const activeOverview = computed(() => currentWorld().overview)

let renderer
let scene
let camera
let controls
let raycaster
let pointer
let animationId
let staticRoot
let weatherRoot
let resizeObserver
let hemiLight
let sunLight
let fillLight
let targetCameraPosition
let targetLookAt
let targetZoom = 1
let selectedPlantId = null
let selectedZoneKey = null
let autoFocusActive = false
let pointerDownPosition = null
let pointerMovedBeyondClick = false
let suppressNextNullSelectionSync = false
let interactiveMeshes = []
const zoneRoots = new Map()
const zoneHighlights = new Map()
const clock = new THREE.Clock()

function currentWorld() {
  return {
    plants: props.world?.plants || props.plants || [],
    overview: props.world?.overview || props.overview || { totalCount: 0, avgScore: '0.0', volatility: '0.0', statusText: '需要浇水', statusEmoji: '🌱' },
    climate: props.world?.climate || DEFAULT_CLIMATE,
    zones: props.world?.zones || [],
    timeLayers: props.world?.timeLayers || [],
    landmarks: props.world?.landmarks || []
  }
}

function scenePlants() {
  return currentWorld().plants || []
}

function webglAvailable() {
  try {
    const canvas = document.createElement('canvas')
    return Boolean(window.WebGLRenderingContext && (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')))
  } catch {
    return false
  }
}

function initScene() {
  if (!container.value) return
  if (!webglAvailable()) {
    webglError.value = '当前环境没有可用 WebGL，因此先展示温柔的降级提示；在正常浏览器里会渲染固定构图的 3D 纸模花园。'
    return
  }

  scene = new THREE.Scene()
  applyClimateToScene()

  camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 100)
  camera.position.copy(HOME_CAMERA_POSITION)
  camera.zoom = HOME_ZOOM
  camera.lookAt(HOME_LOOK_AT)
  targetCameraPosition = HOME_CAMERA_POSITION.clone()
  targetLookAt = HOME_LOOK_AT.clone()
  targetZoom = HOME_ZOOM

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  renderer.setClearColor(0xd7eef2, 0)
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  renderer.outputColorSpace = THREE.SRGBColorSpace
  renderer.domElement.style.width = '100%'
  renderer.domElement.style.height = '100%'
  renderer.domElement.style.display = 'block'
  container.value.appendChild(renderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableRotate = false
  controls.enablePan = false
  controls.enableZoom = true
  controls.minZoom = 0.9
  controls.maxZoom = 1.28
  controls.enableDamping = true
  controls.dampingFactor = 0.08
  controls.target.copy(targetLookAt)
  controls.addEventListener('start', stopAutoFocus)

  raycaster = new THREE.Raycaster()
  pointer = new THREE.Vector2()

  addLights()
  staticRoot = new THREE.Group()
  scene.add(staticRoot)
  rebuildStaticScene()
  resizeRenderer()

  renderer.domElement.addEventListener('pointermove', handlePointerMove)
  renderer.domElement.addEventListener('pointerleave', handlePointerLeave)
  renderer.domElement.addEventListener('pointerdown', handlePointerDown)
  renderer.domElement.addEventListener('pointerup', handlePointerUp)
  renderer.domElement.addEventListener('wheel', handleWheel)
  renderer.domElement.addEventListener('click', handleClick)
  window.addEventListener('keydown', handleKeydown)

  syncSelectedPlant(props.selectedPlantId, { focus: Boolean(props.selectedPlantId) })

  resizeObserver = new ResizeObserver(resizeRenderer)
  resizeObserver.observe(container.value)

  animate()
}

function applyClimateToScene() {
  if (!scene) return
  const climate = currentWorld().climate
  scene.background = null
  scene.fog = new THREE.Fog(climate.fogColor || '#fff8ec', climate.fogNear || 15, climate.fogFar || 36)
  updateLights()
}

function addLights() {
  const climate = currentWorld().climate
  hemiLight = new THREE.HemisphereLight('#fff8e6', '#8fb3bd', 2.1)
  scene.add(hemiLight)

  sunLight = new THREE.DirectionalLight(climate.lightColor || '#ffe4a3', Math.min(climate.sunlightIntensity || 2.0, 2.25))
  sunLight.position.set(-3.5, 6, 4)
  sunLight.castShadow = true
  sunLight.shadow.mapSize.set(1536, 1536)
  sunLight.shadow.camera.near = 1
  sunLight.shadow.camera.far = 24
  sunLight.shadow.camera.left = -8
  sunLight.shadow.camera.right = 8
  sunLight.shadow.camera.top = 8
  sunLight.shadow.camera.bottom = -8
  scene.add(sunLight)

  fillLight = new THREE.DirectionalLight('#ccecff', 0.7)
  fillLight.position.set(4, 3, -3)
  scene.add(fillLight)
  updateLights()
}

function updateLights() {
  const climate = currentWorld().climate
  if (hemiLight) hemiLight.intensity = climate.type === 'rainy' ? 1.75 : 2.1
  if (sunLight) {
    sunLight.color = new THREE.Color(climate.lightColor || '#ffe4a3')
    sunLight.intensity = Math.min(climate.sunlightIntensity || 2.0, 2.25)
  }
  if (fillLight) fillLight.intensity = climate.type === 'sunny' ? 0.82 : 0.7
}

function toonMaterial(color, options = {}) {
  return new THREE.MeshToonMaterial({
    color,
    emissive: options.emissive || '#000000',
    emissiveIntensity: options.emissiveIntensity || 0,
    transparent: Boolean(options.transparent),
    opacity: options.opacity ?? 1,
    side: options.side || THREE.FrontSide
  })
}

function lineMaterial(color = PALETTE.ink, opacity = 0.45) {
  return new THREE.LineBasicMaterial({ color, transparent: true, opacity })
}

function outlineMaterial() {
  return new THREE.MeshBasicMaterial({ color: OUTLINE_COLOR, side: THREE.BackSide })
}

function addOutlinedMesh(parent, mesh, outlineScale = 1.028) {
  mesh.castShadow = true
  mesh.receiveShadow = true
  parent.add(mesh)

  const outline = new THREE.Mesh(mesh.geometry, outlineMaterial())
  outline.position.copy(mesh.position)
  outline.rotation.copy(mesh.rotation)
  outline.scale.copy(mesh.scale).multiplyScalar(outlineScale)
  outline.castShadow = false
  outline.receiveShadow = false
  parent.add(outline)
  return mesh
}

function addInkOutline(mesh, color = PALETTE.ink, opacity = 0.45) {
  const edges = new THREE.EdgesGeometry(mesh.geometry)
  const line = new THREE.LineSegments(edges, lineMaterial(color, opacity))
  mesh.add(line)
  return mesh
}

function seededRandom(seed) {
  let t = (seed + 0x6D2B79F5) >>> 0
  t = Math.imul(t ^ (t >>> 15), t | 1)
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296
}

function deterministicPointInEllipse(seed, rx, rz) {
  const angle = seededRandom(seed) * Math.PI * 2
  const radius = Math.sqrt(seededRandom(seed + 37))
  return {
    x: Math.cos(angle) * rx * radius,
    z: Math.sin(angle) * rz * radius
  }
}

function makePaperShape(width, depth, seed = 1, wobble = 0.18) {
  const points = []
  const steps = 6
  for (let i = 0; i <= steps; i++) points.push(new THREE.Vector2(-width / 2 + (width * i) / steps, -depth / 2 + wobble * (seededRandom(seed + i) - 0.5)))
  for (let i = 1; i <= steps; i++) points.push(new THREE.Vector2(width / 2 + wobble * (seededRandom(seed + 20 + i) - 0.5), -depth / 2 + (depth * i) / steps))
  for (let i = 1; i <= steps; i++) points.push(new THREE.Vector2(width / 2 - (width * i) / steps, depth / 2 + wobble * (seededRandom(seed + 40 + i) - 0.5)))
  for (let i = 1; i < steps; i++) points.push(new THREE.Vector2(-width / 2 + wobble * (seededRandom(seed + 60 + i) - 0.5), depth / 2 - (depth * i) / steps))
  return new THREE.Shape(points)
}

function makeFlatPaperGeometry(width, depth, seed, wobble = 0.18) {
  const geometry = new THREE.ShapeGeometry(makePaperShape(width, depth, seed, wobble))
  geometry.rotateX(-Math.PI / 2)
  return geometry
}

function makeExtrudedPaperGeometry(width, depth, seed, thickness = 0.14, wobble = 0.18) {
  const geometry = new THREE.ExtrudeGeometry(makePaperShape(width, depth, seed, wobble), { depth: thickness, bevelEnabled: false })
  geometry.rotateX(-Math.PI / 2)
  geometry.translate(0, -thickness / 2, 0)
  return geometry
}

function rebuildStaticScene() {
  if (!staticRoot) return
  disposeGroup(staticRoot)
  staticRoot.clear()
  interactiveMeshes = []
  zoneRoots.clear()
  zoneHighlights.clear()
  weatherRoot = null
  applyClimateToScene()
  staticRoot.add(createGardenDiorama())
}

function createGardenDiorama() {
  const root = new THREE.Group()
  root.name = 'gardenDioramaScene'
  root.add(createPaperTray())
  root.add(createSoftBackdrop())
  root.add(createTerrainPatches())
  root.add(createStonePathSystem())
  root.add(createCheerfulFlowerField())
  root.add(createMemoryTree())
  root.add(createCalmPond())
  root.add(createTransformingVines())
  root.add(createPaperDetails())
  root.add(createAtmosphereLayer())
  return root
}

function createPaperTray() {
  const tray = new THREE.Group()
  tray.name = 'paperTray'
  const base = new THREE.Mesh(new THREE.BoxGeometry(PLOT_WIDTH + 1.1, 0.34, PLOT_DEPTH + 0.82), toonMaterial(PALETTE.traySide))
  base.position.y = -0.28
  addInkOutline(base, PALETTE.ink, 0.28)
  addOutlinedMesh(tray, base, 1.008)

  const floor = new THREE.Mesh(makeExtrudedPaperGeometry(PLOT_WIDTH, PLOT_DEPTH, 12, 0.1, 0.16), toonMaterial(PALETTE.trayInner))
  floor.position.y = -0.04
  addOutlinedMesh(tray, floor, 1.012)

  const rimMat = toonMaterial(PALETTE.cream)
  const frontRimGeo = new THREE.BoxGeometry(PLOT_WIDTH + 0.86, 0.4, 0.28)
  const backRimGeo = new THREE.BoxGeometry(PLOT_WIDTH + 0.56, 0.18, 0.16)
  const sideRimGeo = new THREE.BoxGeometry(0.22, 0.32, PLOT_DEPTH + 0.48)
  const rims = [
    [new THREE.Mesh(backRimGeo, rimMat), 0, -0.02, -PLOT_DEPTH / 2 - 0.18],
    [new THREE.Mesh(frontRimGeo, rimMat), 0, 0.08, PLOT_DEPTH / 2 + 0.26],
    [new THREE.Mesh(sideRimGeo, rimMat), -PLOT_WIDTH / 2 - 0.26, 0.04, 0],
    [new THREE.Mesh(sideRimGeo, rimMat), PLOT_WIDTH / 2 + 0.26, 0.04, 0]
  ]
  rims.forEach(([rim, x, y, z]) => {
    rim.position.set(x, y, z)
    addInkOutline(rim, PALETTE.ink, 0.24)
    addOutlinedMesh(tray, rim, 1.01)
  })
  const innerShadow = new THREE.Mesh(makeExtrudedPaperGeometry(PLOT_WIDTH - 0.24, PLOT_DEPTH - 0.22, 19, 0.035, 0.12), toonMaterial('#d5c783', { transparent: true, opacity: 0.22 }))
  innerShadow.name = 'softPaperTrayShadow'
  innerShadow.position.y = 0.095
  tray.add(innerShadow)
  return tray
}

function createTerrainPatches() {
  const group = new THREE.Group()
  group.name = 'groundPatches'
  const grass = new THREE.Mesh(makeExtrudedPaperGeometry(PLOT_WIDTH - 0.55, PLOT_DEPTH - 0.46, 31, 0.08, 0.2), toonMaterial(PALETTE.grass))
  grass.position.y = 0.05
  addOutlinedMesh(group, grass, 1.01)

  addPatch(group, 'cheerfulPatch', -2.7, 0.08, 2.55, 1.78, PALETTE.sand, 51, 0.82)
  addPatch(group, 'pondPatch', 2.55, 0.22, 2.9, 2.05, '#b8d6c3', 71, 0.78)
  addPatch(group, 'vinePatch', -0.16, 1.46, 3.45, 1.34, PALETTE.vineBlue, 91, 0.9)
  addPatch(group, 'treePatch', 0.18, -0.54, 2.28, 1.72, '#a7c579', 111, 0.78)
  addPatch(group, 'pathDustPatch', -0.36, 0.92, 2.7, 1.0, '#efddb4', 131, 0.38)
  return group
}

function addPatch(parent, name, x, z, width, depth, color, seed, opacity = 1) {
  const patch = new THREE.Mesh(
    makeExtrudedPaperGeometry(width, depth, seed, 0.055, 0.22),
    toonMaterial(color, { transparent: opacity < 1, opacity })
  )
  patch.name = name
  patch.position.set(x, 0.14, z)
  addOutlinedMesh(parent, patch, 1.012)
}

function createStonePathSystem() {
  const group = new THREE.Group()
  group.name = 'stonePath'
  addSteppingStones(group, [
    new THREE.Vector3(-0.45, 0.24, 2.42),
    new THREE.Vector3(-0.24, 0.25, 1.64),
    new THREE.Vector3(-0.08, 0.25, 0.78),
    new THREE.Vector3(0.16, 0.25, -0.34)
  ], 25, 240)
  addSteppingStones(group, [
    new THREE.Vector3(0.06, 0.26, -0.3),
    new THREE.Vector3(-0.9, 0.26, -0.08),
    new THREE.Vector3(-1.75, 0.26, 0.08),
    new THREE.Vector3(-2.72, 0.26, 0.12)
  ], 18, 320)
  addSteppingStones(group, [
    new THREE.Vector3(0.18, 0.26, -0.28),
    new THREE.Vector3(0.96, 0.26, -0.02),
    new THREE.Vector3(1.74, 0.26, 0.14),
    new THREE.Vector3(2.62, 0.26, 0.22)
  ], 18, 390)
  return group
}

function addSteppingStones(parent, points, count, seedBase) {
  const curve = new THREE.CatmullRomCurve3(points)
  const colors = ['#efe2ca', '#d8cdb8', '#ead8b7', '#f4ead5']
  for (let i = 0; i < count; i++) {
    const point = curve.getPoint(count === 1 ? 0 : i / (count - 1))
    const stone = new THREE.Mesh(new THREE.CylinderGeometry(0.09 + seededRandom(seedBase + i) * 0.08, 0.12 + seededRandom(seedBase + 80 + i) * 0.09, 0.045, 9), toonMaterial(colors[i % colors.length]))
    stone.name = 'steppingStone'
    stone.position.copy(point)
    stone.scale.z = 0.62 + seededRandom(seedBase + 160 + i) * 0.38
    stone.rotation.y = seededRandom(seedBase + 240 + i) * Math.PI
    addInkOutline(stone, PALETTE.ink, 0.26)
    parent.add(stone)
  }
}

function createCheerfulFlowerField() {
  const group = new THREE.Group()
  group.name = 'cheerfulFlowerZone'
  group.position.set(-2.66, 0.22, 0.1)
  const plant = zonePlant('cheerfulFlowerZone')
  group.userData.plant = plant

  const flowerCount = Math.min(180, 126 + Math.max(0, activeOverview.value.totalCount || 0) * 10)
  const stemMat = toonMaterial('#5f9a46')
  const centerMat = toonMaterial('#9b6b2d')
  const grassMat = toonMaterial('#7fa45b')
  const petalMats = [
    toonMaterial(PALETTE.yellow),
    toonMaterial('#fff0a6'),
    toonMaterial(PALETTE.flowerWhite),
    toonMaterial('#ffc574')
  ]

  for (let i = 0; i < flowerCount; i++) {
    const point = deterministicPointInEllipse(500 + i * 11, 1.08, 0.68)
    const x = point.x
    const z = point.z - 0.03
    const foregroundBoost = THREE.MathUtils.clamp((z + 0.6) / 1.25, 0, 1)
    const height = 0.16 + seededRandom(900 + i) * 0.32 + foregroundBoost * 0.08
    const flowerScale = 0.78 + seededRandom(930 + i) * 0.55 + foregroundBoost * 0.22
    const flower = new THREE.Group()
    flower.name = 'cheerfulTinyFlower'
    flower.position.set(x, 0, z)
    flower.rotation.y = seededRandom(1100 + i) * Math.PI
    const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.018, height, 5), stemMat)
    stem.position.y = height / 2
    flower.add(stem)
    const center = new THREE.Mesh(new THREE.SphereGeometry(0.045, 8, 6), centerMat)
    center.position.y = height + 0.03
    center.scale.setScalar(flowerScale)
    center.scale.y *= 0.45
    flower.add(center)
    const petalCount = i % 5 === 0 ? 6 : 5
    for (let p = 0; p < petalCount; p++) {
      const angle = (p / petalCount) * Math.PI * 2
      const petal = new THREE.Mesh(new THREE.SphereGeometry(0.032, 8, 5), petalMats[(i + p) % petalMats.length])
      petal.position.set(Math.cos(angle) * 0.054 * flowerScale, height + 0.035 + Math.sin(angle) * 0.004, Math.sin(angle) * 0.054 * flowerScale)
      petal.scale.set(1.15 * flowerScale, 0.34, 0.72 * flowerScale)
      flower.add(petal)
    }
    if (i % 4 === 0) addTinyLeafPair(flower, height * 0.52, stemMat, flowerScale)
    makeInteractive(flower, plant)
    group.add(flower)
  }

  for (let i = 0; i < 12; i++) {
    const point = deterministicPointInEllipse(1320 + i * 23, 0.92, 0.46)
    addTallDaisy(group, point.x, point.z - 0.08, 0.48 + seededRandom(1360 + i) * 0.24, i, plant)
  }

  for (let i = 0; i < 58; i++) {
    const point = deterministicPointInEllipse(1800 + i * 13, 1.2, 0.72)
    addGrassBlade(group, point.x, point.z - 0.04, 0.12 + seededRandom(1900 + i) * 0.18, grassMat, 1950 + i, plant)
  }

  addSemiFence(group, 1.12, 0.74, plant)
  addPaperNote(group, -0.66, 0.26, 0.84, 'happySign', plant)
  addZoneHighlight(group, 'cheerfulFlowerZone', 1.2, 0.72)
  return group
}

function addTallDaisy(parent, x, z, height, seed, plant) {
  const daisy = new THREE.Group()
  daisy.name = 'cheerfulTallDaisy'
  daisy.position.set(x, 0.02, z)
  daisy.rotation.y = seededRandom(1390 + seed) * Math.PI
  const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.026, height, 6), toonMaterial('#5f9a46'))
  stem.position.y = height / 2
  daisy.add(stem)
  const center = new THREE.Mesh(new THREE.SphereGeometry(0.07, 10, 7), toonMaterial('#9b6b2d'))
  center.position.y = height + 0.04
  center.scale.y = 0.5
  daisy.add(center)
  const petalMat = toonMaterial(seed % 3 === 0 ? '#fff6c8' : PALETTE.yellow)
  for (let p = 0; p < 10; p++) {
    const angle = (p / 10) * Math.PI * 2
    const petal = new THREE.Mesh(new THREE.SphereGeometry(0.05, 8, 5), petalMat)
    petal.position.set(Math.cos(angle) * 0.1, height + 0.045 + Math.sin(angle) * 0.003, Math.sin(angle) * 0.1)
    petal.scale.set(1.35, 0.28, 0.7)
    daisy.add(petal)
  }
  addTinyLeafPair(daisy, height * 0.48, toonMaterial('#6f9d4c'), 1.2)
  makeInteractive(daisy, plant)
  parent.add(daisy)
}

function addTinyLeafPair(parent, y, material, scale = 1) {
  for (const side of [-1, 1]) {
    const leaf = new THREE.Mesh(new THREE.SphereGeometry(0.036, 7, 5), material)
    leaf.position.set(side * 0.035, y, 0.012)
    leaf.scale.set(1.25 * scale, 0.28, 0.55 * scale)
    leaf.rotation.z = side * 0.7
    parent.add(leaf)
  }
}

function addGrassBlade(parent, x, z, height, material, seed, plant) {
  const blade = new THREE.Mesh(new THREE.ConeGeometry(0.018, height, 5), material)
  blade.name = 'flowerFieldGrassBlade'
  blade.position.set(x, height / 2, z)
  blade.rotation.z = (seededRandom(seed) - 0.5) * 0.34
  blade.rotation.x = (seededRandom(seed + 10) - 0.5) * 0.22
  makeInteractive(blade, plant)
  parent.add(blade)
}

function addSemiFence(parent, radiusX, radiusZ, plant) {
  const postMat = toonMaterial(PALETTE.wood)
  const railMat = toonMaterial('#d49a4a')
  for (let i = 0; i < 15; i++) {
    const angle = Math.PI * (0.1 + (i / 14) * 0.9)
    const x = Math.cos(angle) * radiusX
    const z = Math.sin(angle) * radiusZ - 0.05
    const post = new THREE.Mesh(new THREE.BoxGeometry(0.055, 0.36, 0.055), postMat)
    post.position.set(x, 0.18, z)
    post.rotation.z = (seededRandom(1400 + i) - 0.5) * 0.15
    makeInteractive(post, plant)
    parent.add(post)
  }
  for (let i = 0; i < 10; i++) {
    const rail = new THREE.Mesh(new THREE.BoxGeometry(0.36, 0.035, 0.04), railMat)
    const angle = Math.PI * (0.15 + (i / 9) * 0.8)
    rail.position.set(Math.cos(angle) * radiusX, 0.28, Math.sin(angle) * radiusZ - 0.05)
    rail.rotation.y = -angle
    makeInteractive(rail, plant)
    parent.add(rail)
  }
}

function createMemoryTree() {
  const group = new THREE.Group()
  group.name = 'memoryTreeZone'
  group.position.set(0.22, 0.24, -0.36)
  const plant = zonePlant('memoryTreeZone')
  group.userData.plant = plant

  const trunkMat = toonMaterial('#8b5a2b')
  const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.34, 1.34, 8), trunkMat)
  trunk.position.y = 0.72
  addInkOutline(trunk, PALETTE.ink, 0.42)
  addOutlinedMesh(group, trunk, 1.026)

  for (let i = 0; i < 6; i++) {
    const branch = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.07, 0.82, 6), trunkMat)
    branch.position.set((i % 2 ? 0.24 : -0.24), 0.98 + i * 0.07, 0)
    branch.rotation.z = (i % 2 ? -0.72 : 0.72)
    branch.rotation.y = i * 0.62
    addOutlinedMesh(group, branch, 1.02)
  }

  const leafColors = ['#8fbf5f', '#a7cf6f', '#6f9d4e', '#b7d982', '#7fae59']
  for (let i = 0; i < 24; i++) {
    const leaf = new THREE.Mesh(
      new THREE.SphereGeometry(0.25 + seededRandom(1700 + i) * 0.13, 12, 8),
      toonMaterial(leafColors[i % leafColors.length])
    )
    const angle = (i / 24) * Math.PI * 2
    leaf.name = 'memoryLeafCluster'
    leaf.userData.kind = 'leafCluster'
    leaf.userData.seed = 1700 + i
    leaf.position.set(Math.cos(angle) * (0.36 + seededRandom(1710 + i) * 0.58), 1.18 + seededRandom(1720 + i) * 0.78, Math.sin(angle) * (0.28 + seededRandom(1730 + i) * 0.18))
    leaf.scale.set(1.12 + seededRandom(1740 + i) * 0.22, 0.68 + seededRandom(1750 + i) * 0.18, 0.78)
    addOutlinedMesh(group, leaf, 1.018)
  }

  for (let i = 0; i < 6; i++) {
    const glow = new THREE.Mesh(
      new THREE.SphereGeometry(0.06, 12, 8),
      toonMaterial(PALETTE.glow, { emissive: PALETTE.glow, emissiveIntensity: 0.62 })
    )
    glow.name = 'memoryGlow'
    glow.position.set(-0.4 + i * 0.16, 1.14 + (i % 3) * 0.24, 0.28 + (i % 2) * 0.08)
    group.add(glow)
    if (i < 3) {
      const light = new THREE.PointLight(PALETTE.glow, 0.18, 1.2)
      light.position.copy(glow.position)
      group.add(light)
    }
  }

  addPaperNote(group, -0.48, 0.16, 0.68, 'memoryBook', plant)
  addBench(group, 0.38, 0.12, 0.58, plant)
  addMemoryLamp(group, 0.12, 0.14, 0.66, plant)
  for (let i = 0; i < 16; i++) {
    const point = deterministicPointInEllipse(5300 + i * 17, 0.76, 0.38)
    addTinyWhiteFlower(group, new THREE.Vector3(point.x, 0.18, point.z + 0.52), plant)
  }
  addZoneHighlight(group, 'memoryTreeZone', 0.9, 0.68)
  makeInteractive(group, plant)
  return group
}

function addMemoryLamp(parent, x, y, z, plant) {
  const lamp = new THREE.Group()
  lamp.name = 'memoryLamp'
  lamp.position.set(x, y, z)
  const post = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.024, 0.34, 6), toonMaterial(PALETTE.wood))
  post.position.y = 0.17
  const shade = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.09, 0.12, 6), toonMaterial('#fff4b8', { emissive: PALETTE.glow, emissiveIntensity: 0.28 }))
  shade.position.y = 0.37
  lamp.add(post, shade)
  const light = new THREE.PointLight(PALETTE.glow, 0.12, 0.8)
  light.position.y = 0.36
  lamp.add(light)
  makeInteractive(lamp, plant)
  parent.add(lamp)
}

function addBench(parent, x, y, z, plant) {
  const seat = new THREE.Mesh(new THREE.BoxGeometry(0.48, 0.07, 0.16), toonMaterial('#d8b36f'))
  seat.position.set(x, y + 0.16, z)
  addInkOutline(seat, PALETTE.ink, 0.3)
  makeInteractive(seat, plant)
  parent.add(seat)
  for (const dx of [-0.16, 0.16]) {
    const leg = new THREE.Mesh(new THREE.BoxGeometry(0.045, 0.18, 0.045), toonMaterial(PALETTE.wood))
    leg.position.set(x + dx, y + 0.06, z)
    makeInteractive(leg, plant)
    parent.add(leg)
  }
}

function createCalmPond() {
  const group = new THREE.Group()
  group.name = 'calmPondZone'
  group.position.set(2.55, 0.22, 0.2)
  const plant = zonePlant('calmPondZone')
  group.userData.plant = plant

  const water = new THREE.Mesh(makeFlatPaperGeometry(2.34, 1.52, 2100, 0.3), toonMaterial(PALETTE.pondBlue, { transparent: true, opacity: 0.88, emissive: PALETTE.pondDeep, emissiveIntensity: 0.08 }))
  water.name = 'calmPondWater'
  water.position.y = 0.08
  addOutlinedMesh(group, water, 1.018)
  makeInteractive(water, plant)

  const waterTop = new THREE.Mesh(makeFlatPaperGeometry(1.68, 0.9, 2110, 0.22), toonMaterial('#c5f3f4', { transparent: true, opacity: 0.42, emissive: '#ffffff', emissiveIntensity: 0.08 }))
  waterTop.name = 'calmPondWaterHighlight'
  waterTop.position.set(0.1, 0.18, -0.05)
  group.add(waterTop)

  for (let i = 0; i < 26; i++) {
    const angle = (i / 26) * Math.PI * 2
    const stone = new THREE.Mesh(new THREE.SphereGeometry(0.075 + seededRandom(2200 + i) * 0.045, 8, 5), toonMaterial(i % 2 ? '#d8cdb8' : '#efe2ca'))
    stone.name = 'pondStone'
    stone.scale.y = 0.28
    stone.position.set(Math.cos(angle) * (1.2 + seededRandom(2300 + i) * 0.18), 0.15, Math.sin(angle) * (0.76 + seededRandom(2400 + i) * 0.14))
    makeInteractive(stone, plant)
    group.add(stone)
  }

  for (let i = 0; i < 12; i++) {
    const lily = new THREE.Mesh(new THREE.CylinderGeometry(0.085, 0.12, 0.018, 12), toonMaterial(i % 2 ? '#8fb56b' : '#a9cc7c'))
    lily.name = 'pondLilyPad'
    lily.position.set(-0.82 + seededRandom(2500 + i) * 1.68, 0.19, -0.46 + seededRandom(2600 + i) * 0.92)
    lily.scale.z = 0.56
    lily.rotation.y = seededRandom(2700 + i) * Math.PI
    makeInteractive(lily, plant)
    group.add(lily)
  }

  for (let i = 0; i < 3; i++) {
    const ripple = new THREE.Mesh(new THREE.TorusGeometry(0.3 + i * 0.18, 0.008, 6, 48), toonMaterial('#ffffff', { transparent: true, opacity: 0.66 }))
    ripple.name = 'pondRipple'
    ripple.rotation.x = Math.PI / 2
    ripple.scale.z = 0.56
    ripple.position.set(-0.12 + i * 0.2, 0.19, -0.02 + i * 0.08)
    group.add(ripple)
  }

  addPaperBoat(group, 0.38, 0.24, -0.04, plant)
  addPaperNote(group, 0.94, 0.17, 0.66, 'pondNote', plant)
  addZoneHighlight(group, 'calmPondZone', 0.96, 0.62)
  return group
}

function addPaperBoat(parent, x, y, z, plant) {
  const boat = new THREE.Group()
  boat.name = 'paperBoat'
  boat.position.set(x, y, z)
  const hull = new THREE.Mesh(new THREE.ConeGeometry(0.18, 0.42, 4), toonMaterial(PALETTE.paper))
  hull.rotation.set(Math.PI / 2, 0, Math.PI / 4)
  hull.scale.z = 0.42
  boat.add(hull)
  const sail = new THREE.Mesh(new THREE.ConeGeometry(0.11, 0.28, 3), toonMaterial('#fff9c4'))
  sail.position.set(0.02, 0.12, 0)
  sail.rotation.z = -0.26
  boat.add(sail)
  makeInteractive(boat, plant)
  parent.add(boat)
}

function createTransformingVines() {
  const group = new THREE.Group()
  group.name = 'transformingVinesZone'
  group.position.set(-0.18, 0.23, 1.38)
  const plant = zonePlant('transformingVinesZone')
  group.userData.plant = plant

  for (let i = 0; i < 40; i++) {
    const startPoint = deterministicPointInEllipse(3000 + i * 9, 1.5, 0.56)
    const startX = startPoint.x
    const startZ = startPoint.z
    const curve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(startX, 0.13, startZ),
      new THREE.Vector3(startX + (seededRandom(3200 + i) - 0.5) * 0.38, 0.18, startZ + 0.12),
      new THREE.Vector3(startX + (seededRandom(3300 + i) - 0.5) * 0.56, 0.17, startZ + 0.3),
      new THREE.Vector3(startX + (seededRandom(3350 + i) - 0.5) * 0.46, 0.16, startZ + 0.46)
    ])
    const vine = new THREE.Mesh(new THREE.TubeGeometry(curve, 8, 0.014, 6, false), toonMaterial(i % 2 ? PALETTE.vineDark : '#7f989c'))
    vine.name = 'transformingVine'
    makeInteractive(vine, plant)
    group.add(vine)
    if (i % 2 === 0) addTinyWhiteFlower(group, curve.getPoint(0.82), plant)
    if (i % 3 === 0) addVineLeaf(group, curve.getPoint(0.45), 3700 + i, plant)
  }

  for (let i = 0; i < 42; i++) {
    const point = deterministicPointInEllipse(3800 + i * 7, 1.48, 0.56)
    if (i < 32) addVineLeaf(group, new THREE.Vector3(point.x, 0.17, point.z), 3900 + i, plant)
    if (i < 36) addTinyWhiteFlower(group, new THREE.Vector3(point.x + 0.03, 0.18, point.z - 0.02), plant)
  }

  for (let i = 0; i < 18; i++) {
    const stone = new THREE.Mesh(new THREE.SphereGeometry(0.055 + seededRandom(3400 + i) * 0.04, 8, 5), toonMaterial('#b9bec0'))
    stone.name = 'transformStone'
    stone.scale.y = 0.32
    stone.position.set(-1.48 + seededRandom(3500 + i) * 2.96, 0.13, -0.56 + seededRandom(3600 + i) * 1.12)
    makeInteractive(stone, plant)
    group.add(stone)
  }

  addPaperNote(group, 0.68, 0.17, 0.48, 'transformNote', plant)
  addZoneHighlight(group, 'transformingVinesZone', 1.62, 0.58)
  return group
}

function addTinyWhiteFlower(parent, point, plant) {
  const flower = new THREE.Group()
  flower.name = 'tinyTransformFlower'
  flower.position.copy(point)
  for (let p = 0; p < 5; p++) {
    const angle = (p / 5) * Math.PI * 2
    const petal = new THREE.Mesh(new THREE.SphereGeometry(0.026, 7, 5), toonMaterial(PALETTE.flowerWhite))
    petal.position.set(Math.cos(angle) * 0.04, 0.04, Math.sin(angle) * 0.04)
    petal.scale.y = 0.35
    flower.add(petal)
  }
  const center = new THREE.Mesh(new THREE.SphereGeometry(0.018, 7, 5), toonMaterial('#f2d26f'))
  center.position.y = 0.042
  flower.add(center)
  makeInteractive(flower, plant)
  parent.add(flower)
}

function addVineLeaf(parent, point, seed, plant) {
  const leaf = new THREE.Mesh(new THREE.SphereGeometry(0.042, 7, 5), toonMaterial(seed % 2 ? '#779392' : '#6f8989'))
  leaf.name = 'transformVineLeaf'
  leaf.position.copy(point)
  leaf.position.y += 0.025
  leaf.scale.set(1.4, 0.26, 0.62)
  leaf.rotation.y = seededRandom(seed) * Math.PI
  leaf.rotation.z = (seededRandom(seed + 9) - 0.5) * 0.8
  makeInteractive(leaf, plant)
  parent.add(leaf)
}

function addPaperNote(parent, x, y, z, name, plant) {
  const note = new THREE.Group()
  note.name = name
  note.position.set(x, y, z)
  note.rotation.set(-0.18, -0.2, 0.08)
  const post = new THREE.Mesh(new THREE.BoxGeometry(0.035, 0.28, 0.035), toonMaterial(PALETTE.wood))
  post.position.y = 0.08
  const board = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.26, 0.035), toonMaterial('#fff9c4'))
  board.position.y = 0.27
  addInkOutline(board, PALETTE.ink, 0.3)
  note.add(post, board)
  makeInteractive(note, plant)
  parent.add(note)
}

function createPaperDetails() {
  const group = new THREE.Group()
  group.name = 'paperDetails'
  const memoryPlant = zonePlant('memoryTreeZone')
  const meadowGrass = toonMaterial('#7f9c5d')
  const meadowDetails = new THREE.Group()
  meadowDetails.name = 'meadowPaperDetails'
  meadowDetails.position.y = 0.23
  group.add(meadowDetails)

  const entryNote = new THREE.Group()
  entryNote.name = 'frontMemoryCard'
  entryNote.position.set(0.92, 0.26, 2.06)
  entryNote.rotation.set(-0.12, -0.06, 0.02)
  const card = new THREE.Mesh(new THREE.BoxGeometry(0.68, 0.32, 0.035), toonMaterial('#fff3c9'))
  card.position.y = 0.2
  addInkOutline(card, PALETTE.ink, 0.24)
  const post = new THREE.Mesh(new THREE.CylinderGeometry(0.016, 0.022, 0.32, 6), toonMaterial(PALETTE.wood))
  post.position.y = 0.05
  entryNote.add(post, card)
  group.add(entryNote)

  const wateringCan = new THREE.Group()
  wateringCan.name = 'paperWateringCan'
  wateringCan.position.set(3.52, 0.24, 1.98)
  wateringCan.rotation.y = -0.42
  const body = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.2, 0.28, 10), toonMaterial('#d7ddd8'))
  body.rotation.z = Math.PI / 2
  addInkOutline(body, PALETTE.ink, 0.18)
  const spout = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.035, 0.44, 8), toonMaterial('#d7ddd8'))
  spout.position.set(0.28, 0.06, 0)
  spout.rotation.z = Math.PI / 2.6
  const handle = new THREE.Mesh(new THREE.TorusGeometry(0.16, 0.018, 6, 24), toonMaterial('#d7ddd8'))
  handle.position.set(-0.18, 0.04, 0)
  handle.rotation.y = Math.PI / 2
  wateringCan.add(body, spout, handle)
  group.add(wateringCan)

  for (let i = 0; i < 18; i++) {
    const point = deterministicPointInEllipse(6200 + i * 19, 4.0, 2.0)
    const scrap = new THREE.Mesh(new THREE.BoxGeometry(0.08 + seededRandom(6300 + i) * 0.06, 0.01, 0.1 + seededRandom(6400 + i) * 0.08), toonMaterial(i % 2 ? '#fff8df' : '#fff3c9', { transparent: true, opacity: 0.82 }))
    scrap.name = 'tinyPaperScrap'
    scrap.position.set(point.x, 0.3 + seededRandom(6500 + i) * 0.22, point.z)
    scrap.rotation.set(0.2, seededRandom(6600 + i) * Math.PI, seededRandom(6700 + i) * Math.PI)
    group.add(scrap)
  }

  for (let i = 0; i < 34; i++) {
    const point = deterministicPointInEllipse(6900 + i * 29, 2.8, 1.55)
    if (point.x < -1.42 && point.z < 0.82) continue
    if (point.x > 1.54 && point.z > -0.72) continue
    addGrassBlade(meadowDetails, point.x, point.z, 0.1 + seededRandom(7000 + i) * 0.18, meadowGrass, 7040 + i, memoryPlant)
    if (i % 3 === 0) {
      addTinyWhiteFlower(meadowDetails, new THREE.Vector3(point.x + 0.06, 0.03, point.z - 0.04), memoryPlant)
    }
  }

  return group
}

function createSoftBackdrop() {
  weatherRoot = new THREE.Group()
  weatherRoot.name = 'softBackdrop'
  weatherRoot.position.set(0, 0.25, -0.2)

  const sun = new THREE.Mesh(new THREE.SphereGeometry(0.28, 18, 12), new THREE.MeshBasicMaterial({ color: PALETTE.glow, transparent: true, opacity: 0.92 }))
  sun.name = 'paperSun'
  sun.scale.set(1, 0.18, 1)
  sun.position.set(-2.48, 1.54, -2.18)
  addOutlinedMesh(weatherRoot, sun, 1.025)

  addPaperCloud(weatherRoot, -2.02, 1.76, -2.12, 0.56, 4100)
  addPaperCloud(weatherRoot, 2.1, 2.02, -2.08, 0.7, 4200)
  addPaperCloud(weatherRoot, 0.28, 2.22, -2.16, 0.38, 4300)
  addPaperCloud(weatherRoot, 3.2, 1.66, -1.86, 0.35, 4400)
  addWindLines(weatherRoot)
  return weatherRoot
}

function addPaperCloud(parent, x, y, z, scale, seed) {
  const group = new THREE.Group()
  group.name = 'paperCloud'
  group.userData.kind = 'cloud'
  group.userData.seed = seed
  group.userData.baseX = x
  group.position.set(x, y, z)
  const mat = toonMaterial('#ffffff', { transparent: true, opacity: 0.9 })
  for (let i = 0; i < 4; i++) {
    const puff = new THREE.Mesh(new THREE.SphereGeometry(0.22 + i * 0.025, 12, 7), mat)
    puff.position.set((i - 1.5) * 0.23, Math.sin(i) * 0.05, 0)
    puff.scale.set(1.2, 0.55, 0.18)
    group.add(puff)
  }
  group.scale.setScalar(scale)
  parent.add(group)
}

function addWindLines(parent) {
  for (let i = 0; i < 8; i++) {
    const curve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(-2.8 + i * 0.72, 1.72 + (i % 3) * 0.16, -2.25),
      new THREE.Vector3(-2.5 + i * 0.72, 1.77 + (i % 3) * 0.16, -2.25),
      new THREE.Vector3(-2.15 + i * 0.72, 1.72 + (i % 3) * 0.16, -2.25)
    ])
    const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(curve.getPoints(20)), lineMaterial('#ffffff', 0.68))
    line.name = 'paperWindLine'
    parent.add(line)
  }
}

function createAtmosphereLayer() {
  const group = new THREE.Group()
  group.name = 'atmosphereLayer'
  const count = Math.round(24 + (currentWorld().climate.leafDrift || 0.5) * 16)
  for (let i = 0; i < count; i++) {
    const petal = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.012, 0.15), toonMaterial(i % 2 ? '#fff9c4' : '#ffffff', { transparent: true, opacity: 0.86 }))
    petal.name = 'floatingPetal'
    petal.position.set(-3.8 + seededRandom(4500 + i) * 7.6, 0.86 + seededRandom(4600 + i) * 1.1, -1.75 + seededRandom(4700 + i) * 3.7)
    petal.rotation.set(0.5, seededRandom(4800 + i) * Math.PI, 0.7)
    petal.userData.kind = 'petal'
    petal.userData.seed = i
    group.add(petal)
  }
  for (let i = 0; i < 26; i++) {
    const mote = new THREE.Mesh(new THREE.SphereGeometry(0.028, 8, 5), new THREE.MeshBasicMaterial({ color: PALETTE.glow, transparent: true, opacity: 0.72 }))
    mote.name = 'floatingLightPoint'
    mote.position.set(-2.1 + seededRandom(4900 + i) * 4.1, 0.98 + seededRandom(5000 + i) * 1.05, -1.0 + seededRandom(5100 + i) * 1.9)
    mote.userData.kind = 'lightPoint'
    mote.userData.seed = 500 + i
    group.add(mote)
  }
  return group
}

function addZoneHighlight(parent, zoneKey, width, depth) {
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.5, 0.018, 6, 48), toonMaterial('#fff3a8', { transparent: true, opacity: 0.0, emissive: '#fff3a8', emissiveIntensity: 0.28 }))
  ring.name = `${zoneKey}SelectionRing`
  ring.rotation.x = Math.PI / 2
  ring.position.y = 0.1
  ring.scale.set(width, depth, 1)
  ring.userData.baseScaleX = width
  ring.userData.baseScaleY = depth
  ring.visible = false
  parent.add(ring)
  zoneHighlights.set(zoneKey, ring)
  zoneRoots.set(zoneKey, parent)
}

function makeInteractive(object, plant) {
  object.traverse((child) => {
    if (child.isMesh || child.isLine || child.isLineSegments) {
      child.userData.plant = plant
      interactiveMeshes.push(child)
    }
  })
}

function zonePlant(zoneKey) {
  const plants = scenePlants()
  const synthetic = {
    id: `zone-${zoneKey}`,
    sourceType: 'zone',
    title: {
      cheerfulFlowerZone: '开心花田',
      memoryTreeZone: '重要回忆树',
      calmPondZone: '平静池塘',
      transformingVinesZone: '工作压力正在转化'
    }[zoneKey],
    content: {
      cheerfulFlowerZone: '一片明亮花田，安放高能量和开心的记忆。',
      memoryTreeZone: '花园中央的记忆树，承载最值得回看的片段。',
      calmPondZone: '平静的水域，给情绪留出可呼吸的空间。',
      transformingVinesZone: '困难情绪没有被删除，而是在慢慢开出小白花。'
    }[zoneKey],
    contentPreview: {
      cheerfulFlowerZone: '一片明亮花田，安放高能量和开心的记忆。',
      memoryTreeZone: '花园中央的记忆树，承载最值得回看的片段。',
      calmPondZone: '平静的水域，给情绪留出可呼吸的空间。',
      transformingVinesZone: '困难情绪没有被删除，而是在慢慢开出小白花。'
    }[zoneKey],
    moodScore: Number(activeOverview.value.avgScore || 0),
    moodLabel: activeClimate.value.label,
    themeLabel: {
      cheerfulFlowerZone: '高能量',
      memoryTreeZone: '重要回忆',
      calmPondZone: '平静',
      transformingVinesZone: '正在转化'
    }[zoneKey],
    zoneKey,
    zoneLabel: '沙盘区域',
    modelType: zoneKey === 'calmPondZone' ? 'sprout' : 'leafBloom',
    growthStory: {
      cheerfulFlowerZone: '开心的记忆在这里聚成花田。',
      memoryTreeZone: '重要记忆在这里沉淀成树。',
      calmPondZone: '平静情绪在这里变成水面。',
      transformingVinesZone: '压力和低落在这里被安放，并慢慢转化。'
    }[zoneKey]
  }

  if (zoneKey === 'cheerfulFlowerZone') {
    return plants.find(plant => Number(plant.moodScore || 0) >= 75) || synthetic
  }
  if (zoneKey === 'memoryTreeZone') {
    return plants.find(plant => Number(plant.memoryWeight || 0) >= 2.05) || plants[0] || synthetic
  }
  if (zoneKey === 'calmPondZone') {
    return plants.find(plant => plant.themeKey === 'rest' || (Number(plant.moodScore || 0) >= 40 && Number(plant.moodScore || 0) < 75)) || synthetic
  }
  if (zoneKey === 'transformingVinesZone') {
    return plants.find(plant => plant.themeKey === 'work' || Number(plant.moodScore || 0) <= 35) || synthetic
  }
  return synthetic
}

function zoneKeyForPlant(plant) {
  if (plant?.zoneKey) return plant.zoneKey
  if (plant?.themeKey === 'work' || Number(plant?.moodScore || 0) <= 35) return 'transformingVinesZone'
  if (plant?.themeKey === 'rest' || (Number(plant?.moodScore || 0) >= 40 && Number(plant?.moodScore || 0) < 75)) return 'calmPondZone'
  if (Number(plant?.memoryWeight || 0) >= 2.05) return 'memoryTreeZone'
  if (Number(plant?.moodScore || 0) >= 75) return 'cheerfulFlowerZone'
  return 'memoryTreeZone'
}

function handlePointerMove(event) {
  const hit = pickPlant(event)
  hoveredPlant.value = hit?.userData?.plant || null
  if (renderer?.domElement) {
    renderer.domElement.style.cursor = hoveredPlant.value ? 'pointer' : 'zoom-in'
  }
}

function handlePointerLeave() {
  hoveredPlant.value = null
  pointerDownPosition = null
  pointerMovedBeyondClick = false
}

function handlePointerDown(event) {
  pointerDownPosition = { x: event.clientX, y: event.clientY }
  pointerMovedBeyondClick = false
}

function handlePointerUp(event) {
  if (!pointerDownPosition) return
  const distance = Math.hypot(event.clientX - pointerDownPosition.x, event.clientY - pointerDownPosition.y)
  pointerMovedBeyondClick = distance > CLICK_DRAG_THRESHOLD
  pointerDownPosition = null
}

function handleWheel(event) {
  stopAutoFocus()
  if (selectedPlantId && event.deltaY > 0) {
    clearSelection({ notify: true, resetView: false })
  }
}

function handleKeydown(event) {
  if (event.key === 'Escape' && selectedPlantId) {
    clearSelection({ notify: true, resetView: true })
  }
}

function handleClick(event) {
  if (pointerMovedBeyondClick) {
    pointerMovedBeyondClick = false
    pointerDownPosition = null
    return
  }

  const hit = pickPlant(event)
  const plant = hit?.userData?.plant
  if (!plant) {
    if (selectedPlantId) clearSelection({ notify: true, resetView: false })
    return
  }

  selectedPlantId = plant.id
  focusPlant(plant)
  emit('select-plant', plant)
}

function pickPlant(event) {
  if (!renderer || !camera || !interactiveMeshes.length) return null
  const rect = renderer.domElement.getBoundingClientRect()
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1
  raycaster.setFromCamera(pointer, camera)
  const hits = raycaster.intersectObjects(interactiveMeshes, true)
  return hits.find((hit) => hit.object.userData?.plant)?.object || null
}

function focusPlant(plant) {
  const zoneKey = zoneKeyForPlant(plant)
  selectedZoneKey = zoneKey
  const focus = ZONE_FOCUS[zoneKey] || ZONE_FOCUS.memoryTreeZone
  targetCameraPosition = focus.camera.clone()
  targetLookAt = focus.target.clone()
  targetZoom = focus.zoom
  autoFocusActive = true
}

function resetToOverview() {
  targetCameraPosition = HOME_CAMERA_POSITION.clone()
  targetLookAt = HOME_LOOK_AT.clone()
  targetZoom = HOME_ZOOM
  autoFocusActive = true
}

function stopAutoFocus() {
  autoFocusActive = false
}

function clearSelection({ notify = false, resetView = true } = {}) {
  selectedPlantId = null
  selectedZoneKey = null
  if (resetView) resetToOverview()
  if (notify) {
    suppressNextNullSelectionSync = true
    emit('clear-selection')
  }
}

function syncSelectedPlant(plantId, options = {}) {
  if (!plantId) {
    if (suppressNextNullSelectionSync) {
      suppressNextNullSelectionSync = false
      selectedPlantId = null
      return
    }
    clearSelection({ notify: false, resetView: true })
    return
  }

  const plant = scenePlants().find(item => String(item.id) === String(plantId))
  selectedPlantId = plantId
  if (plant) selectedZoneKey = zoneKeyForPlant(plant)
  if (plant && options.focus !== false) focusPlant(plant)
}

function animateDiorama(elapsed) {
  if (weatherRoot) {
    weatherRoot.traverse((child) => {
      if (child.userData.kind === 'cloud') {
        child.position.x = child.userData.baseX + Math.sin(elapsed * 0.18 + child.userData.seed) * 0.05
      }
    })
  }

  zoneHighlights.forEach((ring, zoneKey) => {
    const active = selectedZoneKey === zoneKey
    const hovered = hoveredPlant.value && zoneKeyForPlant(hoveredPlant.value) === zoneKey
    const visible = active || hovered
    ring.visible = visible
    ring.material.opacity = THREE.MathUtils.lerp(ring.material.opacity || 0, visible ? 0.68 : 0, 0.14)
    ring.scale.z = 1
    const pulse = 1 + Math.sin(elapsed * 2.6) * 0.03
    ring.scale.x = ring.userData.baseScaleX * pulse
    ring.scale.y = ring.userData.baseScaleY * pulse
  })

  staticRoot?.traverse((child) => {
    if (child.name === 'memoryGlow') {
      child.position.y += Math.sin(elapsed * 1.2 + child.id) * 0.0008
      if (child.material) child.material.emissiveIntensity = 0.48 + Math.sin(elapsed * 1.4 + child.id) * 0.12
    }
    if (child.name === 'pondRipple') {
      const scale = 1 + Math.sin(elapsed * 0.9 + child.id) * 0.035
      child.scale.x = scale
      child.scale.y = scale
    }
    if (child.userData.kind === 'petal') {
      child.position.x += 0.003 * (currentWorld().climate.windSpeed || 0.8)
      child.position.y += Math.sin(elapsed * 0.8 + child.userData.seed) * 0.0014
      child.rotation.z += 0.006
      if (child.position.x > 4.0) child.position.x = -4.0
    }
    if (child.userData.kind === 'lightPoint') {
      child.position.y += Math.sin(elapsed * 1.1 + child.userData.seed) * 0.0012
      if (child.material) child.material.opacity = 0.48 + Math.sin(elapsed * 1.2 + child.userData.seed) * 0.16
    }
    if (child.userData.kind === 'leafCluster') {
      child.rotation.z = Math.sin(elapsed * 0.55 + child.userData.seed) * 0.018
    }
  })
}

function animate() {
  animationId = window.requestAnimationFrame(animate)
  const elapsed = clock.getElapsedTime()
  animateDiorama(elapsed)

  if (camera && controls) {
    if (autoFocusActive) {
      camera.position.lerp(targetCameraPosition, 0.045)
      controls.target.lerp(targetLookAt, 0.06)
      camera.zoom = THREE.MathUtils.lerp(camera.zoom, targetZoom, 0.055)
      camera.updateProjectionMatrix()
      if (
        camera.position.distanceTo(targetCameraPosition) < 0.04 &&
        controls.target.distanceTo(targetLookAt) < 0.04 &&
        Math.abs(camera.zoom - targetZoom) < 0.01
      ) {
        autoFocusActive = false
      }
    }
    controls.update()
  }

  renderer?.render(scene, camera)
}

function resizeRenderer() {
  if (!container.value || !renderer || !camera) return
  const width = container.value.clientWidth || 1
  const height = container.value.clientHeight || 1
  const aspect = width / height
  camera.left = (FRUSTUM_SIZE * aspect) / -2
  camera.right = (FRUSTUM_SIZE * aspect) / 2
  camera.top = FRUSTUM_SIZE / 2
  camera.bottom = FRUSTUM_SIZE / -2
  camera.updateProjectionMatrix()
  renderer.setSize(width, height, false)
}

function disposeGroup(group) {
  group.traverse((child) => {
    if (child.geometry) child.geometry.dispose()
    if (child.material) {
      if (Array.isArray(child.material)) {
        child.material.forEach((material) => material.dispose())
      } else {
        child.material.dispose()
      }
    }
  })
}

function cleanup() {
  if (animationId) window.cancelAnimationFrame(animationId)
  if (resizeObserver && container.value) resizeObserver.unobserve(container.value)
  if (renderer?.domElement) {
    renderer.domElement.removeEventListener('pointermove', handlePointerMove)
    renderer.domElement.removeEventListener('pointerleave', handlePointerLeave)
    renderer.domElement.removeEventListener('pointerdown', handlePointerDown)
    renderer.domElement.removeEventListener('pointerup', handlePointerUp)
    renderer.domElement.removeEventListener('wheel', handleWheel)
    renderer.domElement.removeEventListener('click', handleClick)
  }
  window.removeEventListener('keydown', handleKeydown)
  controls?.removeEventListener('start', stopAutoFocus)
  if (staticRoot) disposeGroup(staticRoot)
  if (renderer) {
    renderer.dispose()
    renderer.domElement.remove()
  }
}

watch(() => props.plants, () => {
  rebuildStaticScene()
  if (props.selectedPlantId) syncSelectedPlant(props.selectedPlantId, { focus: false })
}, { deep: true })

watch(() => props.world, () => {
  rebuildStaticScene()
  if (props.selectedPlantId) syncSelectedPlant(props.selectedPlantId, { focus: false })
}, { deep: true })

watch(() => props.selectedPlantId, (plantId) => syncSelectedPlant(plantId))

onMounted(initScene)
onBeforeUnmount(cleanup)
</script>

<style scoped>
.garden-canvas-shell {
  border-radius: 28px;
  background:
    radial-gradient(circle at 28% 18%, rgba(255, 236, 154, 0.35), transparent 24%),
    radial-gradient(circle at 52% 60%, rgba(255, 255, 255, 0.12), transparent 48%),
    linear-gradient(180deg, #cfe9ee 0%, #d9eff0 45%, #f6efcc 100%);
}

.garden-canvas-shell::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: 2;
  pointer-events: none;
  border-radius: inherit;
  opacity: 0.16;
  background-image:
    repeating-linear-gradient(
      0deg,
      rgba(80, 60, 30, 0.035) 0,
      rgba(80, 60, 30, 0.035) 1px,
      transparent 1px,
      transparent 6px
    );
  mix-blend-mode: multiply;
}

.garden-canvas-shell::after {
  content: "";
  position: absolute;
  inset: 0;
  z-index: 2;
  pointer-events: none;
  border-radius: inherit;
  background:
    radial-gradient(circle at 30% 18%, rgba(255, 244, 190, 0.28), transparent 28%),
    radial-gradient(circle at 50% 60%, rgba(255, 255, 255, 0.12), transparent 48%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.14), rgba(255, 255, 255, 0.02));
  mix-blend-mode: soft-light;
}

.garden-chip {
  position: absolute;
  z-index: 4;
  padding: 6px 12px;
  border: 1.5px solid rgba(44, 41, 35, 0.55);
  border-radius: 999px;
  background: rgba(255, 250, 232, 0.94);
  box-shadow: 0 5px 12px rgba(54, 42, 22, 0.15);
  color: #2f2a22;
  font-size: 13px;
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
  backdrop-filter: blur(4px);
}

.garden-chip-happy {
  left: 23%;
  top: 41%;
  transform: rotate(-2deg);
}

.garden-chip-memory {
  left: 51%;
  top: 33%;
  transform: translateX(-50%) rotate(1deg);
}

.garden-chip-calm {
  right: 18%;
  top: 48%;
  transform: rotate(-1deg);
}

.garden-chip-transform {
  left: 49%;
  bottom: 24%;
  transform: translateX(-50%) rotate(1deg);
}

@media (max-width: 768px) {
  .garden-chip {
    font-size: 11px;
    padding: 5px 9px;
  }

  .garden-chip-transform {
    bottom: 22%;
  }
}
</style>
