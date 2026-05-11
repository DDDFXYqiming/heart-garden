<template>
  <section
    class="relative overflow-hidden border-[3px] border-pencil bg-gradient-to-b from-[#fff8ec] via-[#f7f0df] to-[#e9f7dc] shadow-hard wobbly-lg"
    aria-label="3D 记忆花园"
  >
    <div
      ref="container"
      data-testid="garden-scene"
      class="h-[520px] min-h-[440px] w-full cursor-grab active:cursor-grabbing md:h-[620px]"
    ></div>

    <div class="pointer-events-none absolute left-4 top-4 max-w-xs border-[2px] border-pencil bg-white/88 px-4 py-3 text-sm shadow-hard-sm backdrop-blur wobbly-sm">
      <div class="font-bold" style="font-family: 'Kalam', cursive;">🌿 3D 记忆花园</div>
      <div class="text-pencil/70">纸模花圃里，记忆正在慢慢发光。</div>
    </div>

    <div
      v-if="overview"
      class="pointer-events-none absolute right-4 top-4 hidden border-[2px] border-pencil bg-white/88 px-4 py-3 text-sm shadow-hard-sm backdrop-blur wobbly-sm md:block"
    >
      <div class="text-pencil/60">花园状态</div>
      <div class="text-xl font-bold" style="font-family: 'Kalam', cursive;">
        {{ overview.statusEmoji }} {{ overview.statusText }}
      </div>
      <div class="text-pencil/70">{{ overview.totalCount }} 朵记忆花 · 平均 {{ overview.avgScore }}</div>
    </div>

    <div
      v-if="hoveredPlant"
      data-testid="garden-hover-card"
      class="pointer-events-none absolute bottom-4 left-1/2 max-w-sm -translate-x-1/2 border-[2px] border-pencil bg-white/92 px-4 py-3 text-center shadow-hard-sm backdrop-blur wobbly-sm"
    >
      <div class="text-base font-bold" style="font-family: 'Kalam', cursive;">{{ hoveredPlant.title }}</div>
      <div class="text-sm text-pencil/70">{{ hoveredPlant.moodLabel }} · 情绪 {{ hoveredPlant.moodScore }}</div>
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
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

const PLOT_WIDTH = 16
const PLOT_DEPTH = 10
const CAMERA_LIMITS = {
  minDistance: 3.4,
  maxDistance: 34,
  minPolarAngle: Math.PI * 0.08,
  maxPolarAngle: Math.PI * 0.84,
  focusCompleteDistance: 0.07
}
const CLICK_DRAG_THRESHOLD = 4
const HOME_CAMERA_POSITION = new THREE.Vector3(0, 6.4, 12.6)
const HOME_LOOK_AT = new THREE.Vector3(0, 0.62, 0)
const OUTLINE_COLOR = '#2d2d2d'

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
  }
})

const emit = defineEmits(['select-plant', 'clear-selection'])

const container = ref(null)
const hoveredPlant = ref(null)
const webglError = ref('')

let renderer
let scene
let camera
let controls
let raycaster
let pointer
let animationId
let staticRoot
let plantsRoot
let resizeObserver
let targetCameraPosition
let targetLookAt
let selectedPlantId = null
let autoFocusActive = false
let pointerDownPosition = null
let pointerMovedBeyondClick = false
let suppressNextNullSelectionSync = false
const clock = new THREE.Clock()

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
    webglError.value = '当前环境没有可用 WebGL，因此先展示温柔的降级提示；在正常浏览器里会渲染可交互的 3D 花园。'
    return
  }

  scene = new THREE.Scene()
  scene.background = new THREE.Color('#fff8ec')
  scene.fog = new THREE.Fog('#fff8ec', 18, 54)

  camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100)
  camera.position.copy(HOME_CAMERA_POSITION)
  targetCameraPosition = HOME_CAMERA_POSITION.clone()
  targetLookAt = HOME_LOOK_AT.clone()

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  renderer.outputColorSpace = THREE.SRGBColorSpace
  renderer.domElement.style.width = '100%'
  renderer.domElement.style.height = '100%'
  renderer.domElement.style.display = 'block'
  container.value.appendChild(renderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.08
  controls.minDistance = CAMERA_LIMITS.minDistance
  controls.maxDistance = CAMERA_LIMITS.maxDistance
  controls.minPolarAngle = CAMERA_LIMITS.minPolarAngle
  controls.maxPolarAngle = CAMERA_LIMITS.maxPolarAngle
  controls.target.copy(targetLookAt)
  controls.addEventListener('start', stopAutoFocus)

  raycaster = new THREE.Raycaster()
  pointer = new THREE.Vector2()

  addLights()
  staticRoot = new THREE.Group()
  scene.add(staticRoot)
  addLayeredTerrain()
  addGardenDecor()

  plantsRoot = new THREE.Group()
  scene.add(plantsRoot)
  rebuildPlants()
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

function addLights() {
  const hemi = new THREE.HemisphereLight('#fff4cf', '#8fbf8f', 2.7)
  scene.add(hemi)

  const sun = new THREE.DirectionalLight('#fff0b8', 2.8)
  sun.position.set(-5.5, 9.5, 6.2)
  sun.castShadow = true
  sun.shadow.mapSize.set(1536, 1536)
  sun.shadow.camera.near = 1
  sun.shadow.camera.far = 28
  sun.shadow.camera.left = -12
  sun.shadow.camera.right = 12
  sun.shadow.camera.top = 12
  sun.shadow.camera.bottom = -12
  scene.add(sun)

  const fill = new THREE.PointLight('#ffd8ea', 1.2, 18)
  fill.position.set(5, 4, -4)
  scene.add(fill)
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

function outlineMaterial() {
  return new THREE.MeshBasicMaterial({
    color: OUTLINE_COLOR,
    side: THREE.BackSide
  })
}

function addOutlinedMesh(parent, mesh, outlineScale = 1.035) {
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

function seededRandom(seed) {
  let t = (seed + 0x6D2B79F5) >>> 0
  t = Math.imul(t ^ (t >>> 15), t | 1)
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296
}

function makePaperShape(width, depth, seed = 1, wobble = 0.25) {
  const points = []
  const steps = 5
  for (let i = 0; i <= steps; i++) points.push(new THREE.Vector2(-width / 2 + (width * i) / steps, -depth / 2 + wobble * (seededRandom(seed + i) - 0.5)))
  for (let i = 1; i <= steps; i++) points.push(new THREE.Vector2(width / 2 + wobble * (seededRandom(seed + 20 + i) - 0.5), -depth / 2 + (depth * i) / steps))
  for (let i = 1; i <= steps; i++) points.push(new THREE.Vector2(width / 2 - (width * i) / steps, depth / 2 + wobble * (seededRandom(seed + 40 + i) - 0.5)))
  for (let i = 1; i < steps; i++) points.push(new THREE.Vector2(-width / 2 + wobble * (seededRandom(seed + 60 + i) - 0.5), depth / 2 - (depth * i) / steps))

  const shape = new THREE.Shape(points)
  const geometry = new THREE.ExtrudeGeometry(shape, { depth: 0.18, bevelEnabled: false })
  geometry.rotateX(-Math.PI / 2)
  geometry.translate(0, -0.09, 0)
  return geometry
}

function addLayeredTerrain() {
  const base = new THREE.Mesh(makePaperShape(PLOT_WIDTH + 2.2, PLOT_DEPTH + 2.1, 10, 0.38), toonMaterial('#b8ec80'))
  base.position.y = -0.18
  addOutlinedMesh(staticRoot, base, 1.01)

  const paperEdge = new THREE.Mesh(makePaperShape(PLOT_WIDTH + 1.35, PLOT_DEPTH + 1.25, 24, 0.28), toonMaterial('#f7e7c8'))
  paperEdge.position.y = -0.06
  addOutlinedMesh(staticRoot, paperEdge, 1.012)

  const soil = new THREE.Mesh(makePaperShape(PLOT_WIDTH - 1.2, PLOT_DEPTH - 1.2, 36, 0.32), toonMaterial('#c99a5c'))
  soil.position.y = 0.03
  addOutlinedMesh(staticRoot, soil, 1.012)

  const leftBed = new THREE.Mesh(makePaperShape(4.1, 2.6, 71, 0.22), toonMaterial('#d7b06b'))
  leftBed.position.set(-4.9, 0.16, 1.2)
  addOutlinedMesh(staticRoot, leftBed, 1.02)

  const rightBed = new THREE.Mesh(makePaperShape(4.8, 2.45, 83, 0.22), toonMaterial('#d6ad6a'))
  rightBed.position.set(3.3, 0.17, 1.7)
  addOutlinedMesh(staticRoot, rightBed, 1.02)

  addCurvedPath()
  addPond()
  addFence()
  addSignBoard()
}

function addCurvedPath() {
  const curve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(-7.1, 0.23, 4.0),
    new THREE.Vector3(-4.1, 0.24, 2.3),
    new THREE.Vector3(-2.4, 0.25, 0.2),
    new THREE.Vector3(0.4, 0.24, -1.1),
    new THREE.Vector3(3.5, 0.24, -2.7),
    new THREE.Vector3(6.8, 0.24, -3.5)
  ])
  const path = new THREE.Mesh(new THREE.TubeGeometry(curve, 44, 0.36, 10, false), toonMaterial('#fff4a5'))
  path.scale.y = 0.18
  addOutlinedMesh(staticRoot, path, 1.018)

  for (let i = 0; i < 12; i++) {
    const point = curve.getPoint(i / 11)
    const marker = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.05, 0.09), toonMaterial(i % 2 ? '#f1cf78' : '#ffeab0'))
    marker.position.set(point.x, point.y + 0.09, point.z)
    marker.rotation.y = seededRandom(200 + i) * Math.PI
    staticRoot.add(marker)
  }
}

function addPond() {
  const pond = new THREE.Mesh(
    new THREE.CylinderGeometry(1.05, 1.15, 0.08, 36),
    toonMaterial('#8fd4ff', { emissive: '#4aaee8', emissiveIntensity: 0.16 })
  )
  pond.position.set(4.7, 0.28, -0.6)
  pond.scale.z = 0.62
  addOutlinedMesh(staticRoot, pond, 1.04)

  const shine = new THREE.Mesh(new THREE.BoxGeometry(0.75, 0.025, 0.08), toonMaterial('#dff7ff'))
  shine.position.set(4.45, 0.36, -0.82)
  shine.rotation.y = -0.15
  staticRoot.add(shine)
}

function addGardenDecor() {
  const stoneMat = toonMaterial('#d8d0c2')
  for (let i = 0; i < 26; i++) {
    const x = -7 + seededRandom(400 + i) * 14
    const z = -4.2 + seededRandom(600 + i) * 8.4
    if (Math.abs(x) < 1.1 && z < 1.5 && z > -3.3) continue
    const stone = new THREE.Mesh(new THREE.SphereGeometry(0.09 + seededRandom(800 + i) * 0.08, 8, 5), stoneMat)
    stone.scale.y = 0.28
    stone.position.set(x, 0.31, z)
    stone.rotation.y = seededRandom(900 + i) * Math.PI
    staticRoot.add(stone)
  }

  const scrapColors = ['#fff9c4', '#ffd6e7', '#d7f7a8', '#d8ecff']
  for (let i = 0; i < 10; i++) {
    const scrap = new THREE.Mesh(
      new THREE.BoxGeometry(0.42, 0.025, 0.26),
      toonMaterial(scrapColors[i % scrapColors.length])
    )
    scrap.position.set(-7 + seededRandom(1200 + i) * 14, 0.34, -4.2 + seededRandom(1400 + i) * 8.4)
    scrap.rotation.y = seededRandom(1600 + i) * Math.PI
    staticRoot.add(scrap)
  }
}

function addFence() {
  const postMat = toonMaterial('#8b5a2b')
  const railMat = toonMaterial('#d9973a')
  const postGeo = new THREE.BoxGeometry(0.18, 0.72, 0.18)
  const railGeoX = new THREE.BoxGeometry(1.08, 0.13, 0.12)
  const railGeoZ = new THREE.BoxGeometry(0.12, 0.13, 1.08)
  const y = 0.54
  const minX = -PLOT_WIDTH / 2 - 0.48
  const maxX = PLOT_WIDTH / 2 + 0.48
  const minZ = -PLOT_DEPTH / 2 - 0.46
  const maxZ = PLOT_DEPTH / 2 + 0.46

  for (let x = minX; x <= maxX + 0.01; x += 1.25) {
    addFencePost(x, minZ)
    addFencePost(x, maxZ)
    addFenceRail(x, minZ, true)
    addFenceRail(x, maxZ, true)
  }
  for (let z = minZ; z <= maxZ + 0.01; z += 1.25) {
    addFencePost(minX, z)
    addFencePost(maxX, z)
    addFenceRail(minX, z, false)
    addFenceRail(maxX, z, false)
  }

  function addFencePost(x, z) {
    const post = new THREE.Mesh(postGeo, postMat)
    post.position.set(x, y, z)
    post.rotation.z = (seededRandom(Math.round((x + z) * 1000)) - 0.5) * 0.12
    staticRoot.add(post)
  }

  function addFenceRail(x, z, alongX) {
    const rail = new THREE.Mesh(alongX ? railGeoX : railGeoZ, railMat)
    rail.position.set(x, y + 0.12, z)
    rail.rotation.y = alongX ? 0 : Math.PI / 2
    staticRoot.add(rail)
  }
}

function addSignBoard() {
  const sign = new THREE.Group()
  const post = new THREE.Mesh(new THREE.BoxGeometry(0.16, 1.05, 0.16), toonMaterial('#7a4d28'))
  post.position.y = 0.58
  const board = new THREE.Mesh(new THREE.BoxGeometry(2.5, 0.72, 0.12), toonMaterial('#fff0a8'))
  board.position.y = 1.22
  const pin = new THREE.Mesh(new THREE.SphereGeometry(0.09, 10, 8), toonMaterial('#ff4d4d'))
  pin.position.set(-0.9, 1.34, 0.08)
  sign.add(post, board, pin)
  sign.position.set(-6.55, 0.1, -3.85)
  sign.rotation.y = 0.34
  staticRoot.add(sign)
}

function rebuildPlants() {
  if (!plantsRoot) return
  disposeGroup(plantsRoot)
  plantsRoot.clear()
  props.plants.forEach((plant) => {
    plantsRoot.add(createPlantGroup(plant))
  })
}

function createPlantGroup(plant) {
  const group = new THREE.Group()
  group.userData.plant = plant
  group.userData.seed = Number(plant.id?.split('').reduce((sum, c) => sum + c.charCodeAt(0), 0) || 1)
  group.position.set(plant.x - PLOT_WIDTH / 2, 0.33, plant.z - PLOT_DEPTH / 2)
  group.rotation.y = THREE.MathUtils.degToRad(plant.rotationY || 0)

  const selectionRing = createSelectionRing(plant)
  group.userData.selectionRing = selectionRing
  group.add(selectionRing)

  addPlantBed(group, plant)
  if (plant.modelType === 'sunflower') addSunflower(group, plant)
  else if (plant.modelType === 'leafBloom' || plant.modelType === 'flower') addBloomCluster(group, plant)
  else if (plant.modelType === 'sprout') addSprout(group, plant)
  else if (plant.modelType === 'duskLeaf') addDuskLeaf(group, plant)
  else addCactus(group, plant)
  addPlantTag(group, plant)

  const sparkles = createSparkles(plant)
  group.userData.sparkles = sparkles
  group.add(sparkles)

  group.traverse((child) => {
    if (child.isMesh) {
      child.castShadow = true
      child.receiveShadow = true
      child.userData.plant = plant
    }
  })

  return group
}

function createSelectionRing(plant) {
  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(0.58, 0.025, 8, 48),
    toonMaterial(plant.accentColor || '#fff9c4', { transparent: true, opacity: 0.0, emissive: plant.accentColor || '#fff9c4', emissiveIntensity: 0.18 })
  )
  ring.name = 'selectionRing'
  ring.rotation.x = Math.PI / 2
  ring.position.y = 0.08
  ring.visible = false
  return ring
}

function createSparkles(plant) {
  const root = new THREE.Group()
  root.name = 'confettiRoot'
  root.visible = false
  const colors = [plant.accentColor || '#fff9c4', plant.primaryColor || '#ffd166', '#ffffff', '#ffb7c8']
  for (let i = 0; i < 8; i++) {
    const petal = new THREE.Mesh(new THREE.BoxGeometry(0.11, 0.018, 0.2), toonMaterial(colors[i % colors.length], { transparent: true, opacity: 0.9 }))
    const angle = (i / 8) * Math.PI * 2
    petal.position.set(Math.cos(angle) * 0.88, 0.55 + (i % 3) * 0.13, Math.sin(angle) * 0.88)
    petal.rotation.set(0.4, angle, 0.6)
    root.add(petal)
  }
  return root
}

function addPlantBed(group, plant) {
  const bedColors = {
    round: '#b88352',
    ribbon: '#d8b36f',
    patch: '#9fcf73',
    stone: '#d5c9b8'
  }
  const color = bedColors[plant.bedType] || '#b88352'
  const bed = new THREE.Mesh(new THREE.CylinderGeometry(0.66, 0.76, 0.16, plant.bedType === 'stone' ? 10 : 20), toonMaterial(color))
  bed.name = 'plantBed'
  bed.position.y = 0.04
  bed.scale.z = plant.bedType === 'ribbon' ? 0.62 : 0.82
  addOutlinedMesh(group, bed, 1.025)
}

function addStem(group, height, color = '#3d8b46', curve = 0.12) {
  const path = new THREE.CatmullRomCurve3([
    new THREE.Vector3(0, 0.1, 0),
    new THREE.Vector3(curve, height * 0.42, 0.03),
    new THREE.Vector3(-curve * 0.35, height * 0.76, -0.02),
    new THREE.Vector3(0, height, 0)
  ])
  const stem = new THREE.Mesh(new THREE.TubeGeometry(path, 12, 0.045, 8, false), toonMaterial(color))
  addOutlinedMesh(group, stem, 1.04)
  return stem
}

function addLeaves(group, plant, height, options = {}) {
  const leafMat = toonMaterial(options.color || '#4fa85b')
  const count = Math.max(plant.leafCount || 4, 2)
  const leafGeo = new THREE.SphereGeometry(0.22, 12, 8)
  for (let i = 0; i < count; i++) {
    const side = i % 2 === 0 ? -1 : 1
    const leaf = new THREE.Mesh(leafGeo, leafMat)
    leaf.position.set(side * (0.16 + (i % 3) * 0.05), 0.3 + (height * (i + 1)) / (count + 2), 0)
    leaf.scale.set(1.05, 0.2, 0.46)
    leaf.rotation.set(0.14, 0, side * (0.75 + i * 0.06))
    addOutlinedMesh(group, leaf, 1.035)
  }
}

function addSunflower(group, plant) {
  const height = Number(plant.height || 2.2)
  addStem(group, height, '#3f9149', 0.08)
  addLeaves(group, plant, height)
  addFlowerHead(group, plant, height + 0.12, 0.42, 0.22)
}

function addBloomCluster(group, plant) {
  const height = Number(plant.height || 1.6)
  addStem(group, height, '#3f9149', 0.12)
  addLeaves(group, plant, height, { color: '#5eaa63' })
  addFlowerHead(group, plant, height + 0.05, 0.29, 0.16)
  for (const [x, y, scale] of [[-0.36, height * 0.78, 0.72], [0.34, height * 0.68, 0.64]]) {
    const mini = new THREE.Group()
    mini.position.set(x, y, 0)
    mini.scale.setScalar(scale)
    group.add(mini)
    addFlowerHead(mini, plant, 0, 0.24, 0.12)
  }
}

function addSprout(group, plant) {
  const height = Number(plant.height || 1.1)
  addStem(group, height * 0.72, '#3f9149', 0.07)
  addLeaves(group, { ...plant, leafCount: Math.max(plant.leafCount || 4, 6) }, height, { color: '#66b95d' })
  const bud = new THREE.Mesh(new THREE.SphereGeometry(0.14, 12, 8), toonMaterial(plant.accentColor || '#d7f7a8', { emissive: plant.accentColor || '#d7f7a8', emissiveIntensity: 0.08 }))
  bud.position.y = height * 0.82
  addOutlinedMesh(group, bud, 1.05)
}

function addDuskLeaf(group, plant) {
  const leafGeo = new THREE.SphereGeometry(0.34, 14, 8)
  for (let i = 0; i < Math.max(plant.leafCount || 5, 5); i++) {
    const angle = -0.9 + i * 0.45
    const leaf = new THREE.Mesh(leafGeo, toonMaterial(i % 2 ? plant.primaryColor : plant.accentColor))
    leaf.position.set(Math.sin(angle) * 0.3, 0.35 + i * 0.08, Math.cos(angle) * 0.08)
    leaf.scale.set(0.48, 1.02, 0.18)
    leaf.rotation.set(0.2, angle, -0.55 + i * 0.2)
    addOutlinedMesh(group, leaf, 1.035)
  }
}

function addCactus(group, plant) {
  const height = Number(plant.height || 0.8)
  const cactusMat = toonMaterial(plant.primaryColor || '#5f9ea0')
  const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.23, height, 6, 12), cactusMat)
  body.position.y = height / 2 + 0.24
  addOutlinedMesh(group, body, 1.035)

  for (const side of [-1, 1]) {
    const arm = new THREE.Mesh(new THREE.CapsuleGeometry(0.08, 0.42, 5, 8), cactusMat)
    arm.position.set(side * 0.23, height * 0.74, 0)
    arm.rotation.z = side * 0.92
    addOutlinedMesh(group, arm, 1.04)
  }

  const bud = new THREE.Mesh(
    new THREE.SphereGeometry(0.12, 12, 8),
    toonMaterial(plant.accentColor || '#c78dd7', { emissive: plant.accentColor || '#c78dd7', emissiveIntensity: 0.08 })
  )
  bud.position.y = height + 0.58
  addOutlinedMesh(group, bud, 1.05)
}

function addFlowerHead(group, plant, y, radius, centerRadius) {
  const petalCount = Math.max(plant.petalCount || 5, 4)
  const petalLayers = Math.max(plant.petalLayers || 1, 1)
  const flowerHead = new THREE.Group()
  flowerHead.position.y = y

  for (let layer = 0; layer < petalLayers; layer++) {
    const layerRadius = radius * (1 - layer * 0.12)
    const layerScale = (plant.petalScale || 1) * (1 - layer * 0.08)
    for (let i = 0; i < petalCount; i++) {
      const angle = ((i + layer * 0.5) / petalCount) * Math.PI * 2
      const color = layer % 2 ? (plant.accentColor || plant.primaryColor) : plant.primaryColor
      const petal = new THREE.Mesh(new THREE.SphereGeometry(0.18 * layerScale, 16, 10), toonMaterial(color, {
        emissive: color,
        emissiveIntensity: Math.min(Number(plant.glowIntensity || 0) * 0.12, 0.16)
      }))
      petal.position.set(Math.cos(angle) * layerRadius, Math.sin(angle) * layerRadius, -layer * 0.015)
      petal.scale.set(0.7, 1.22, 0.2)
      petal.rotation.z = angle
      addOutlinedMesh(flowerHead, petal, 1.025)
    }
  }

  const center = new THREE.Mesh(new THREE.SphereGeometry(centerRadius, 18, 12), toonMaterial(plant.secondaryColor || '#8b5a2b'))
  center.scale.z = 0.55
  addOutlinedMesh(flowerHead, center, 1.03)
  group.add(flowerHead)
}

function addPlantTag(group, plant) {
  const tag = new THREE.Group()
  tag.name = 'plantTag'
  const post = new THREE.Mesh(new THREE.BoxGeometry(0.045, 0.36, 0.045), toonMaterial('#7a4d28'))
  post.position.y = 0.2
  const board = new THREE.Mesh(new THREE.BoxGeometry(0.48, 0.2, 0.045), toonMaterial('#fff9c4'))
  board.position.y = 0.42
  tag.add(post, board)
  tag.position.set(0.48, 0.06, 0.36)
  tag.rotation.y = -0.35
  tag.userData.plant = plant
  group.add(tag)
}

function handlePointerMove(event) {
  const hit = pickPlant(event)
  hoveredPlant.value = hit?.userData?.plant || null
  if (renderer?.domElement) {
    renderer.domElement.style.cursor = hoveredPlant.value ? 'pointer' : 'grab'
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
  if (!renderer || !camera || !plantsRoot) return null
  const rect = renderer.domElement.getBoundingClientRect()
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1
  raycaster.setFromCamera(pointer, camera)
  const hits = raycaster.intersectObjects(plantsRoot.children, true)
  return hits.find((hit) => hit.object.userData?.plant)?.object || null
}

function focusPlant(plant) {
  const x = plant.x - PLOT_WIDTH / 2
  const z = plant.z - PLOT_DEPTH / 2
  targetLookAt = new THREE.Vector3(x + 0.9, Math.max((plant.height || 1.2) * 0.72, 1.0), z)
  targetCameraPosition = new THREE.Vector3(x + 4.25, 4.05, z + 5.05)
  autoFocusActive = true
}

function resetToOverview() {
  targetCameraPosition = HOME_CAMERA_POSITION.clone()
  targetLookAt = HOME_LOOK_AT.clone()
  autoFocusActive = true
}

function stopAutoFocus() {
  autoFocusActive = false
}

function clearSelection({ notify = false, resetView = true } = {}) {
  selectedPlantId = null
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

  const plant = props.plants.find(item => String(item.id) === String(plantId))
  selectedPlantId = plantId
  if (plant && options.focus !== false) focusPlant(plant)
}

function animate() {
  animationId = window.requestAnimationFrame(animate)
  const elapsed = clock.getElapsedTime()

  if (plantsRoot) {
    plantsRoot.children.forEach((group) => {
      const plant = group.userData.plant
      const seed = group.userData.seed || 1
      const hovered = hoveredPlant.value?.id === plant.id
      const selected = selectedPlantId === plant.id
      const active = hovered || selected
      const targetScale = selected ? (plant.focusScale || 1.18) : hovered ? 1.12 : 1
      group.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.12)
      group.position.y = 0.33 + Math.sin(elapsed * (plant.swaySpeed || 1) + seed) * (active ? 0.052 : 0.03)
      group.rotation.z = Math.sin(elapsed * ((plant.swaySpeed || 1) * 0.65) + seed) * (active ? 0.045 : 0.024)

      const ring = group.userData.selectionRing
      if (ring) {
        ring.visible = active
        ring.material.opacity = THREE.MathUtils.lerp(ring.material.opacity || 0, active ? 0.82 : 0, 0.16)
        const pulse = 1 + Math.sin(elapsed * 3.2 + seed) * (plant.pulseIntensity || 0.15) * 0.2
        ring.scale.setScalar(active ? pulse : 1)
      }

      const sparkles = group.userData.sparkles
      if (sparkles) {
        sparkles.visible = selected
        sparkles.rotation.y += selected ? 0.018 : 0
        sparkles.children.forEach((child, index) => {
          child.position.y += Math.sin(elapsed * 1.8 + index) * 0.0007
          child.rotation.z += selected ? 0.012 + index * 0.001 : 0
        })
      }
    })
  }

  if (camera && controls) {
    if (autoFocusActive) {
      camera.position.lerp(targetCameraPosition, 0.04)
      controls.target.lerp(targetLookAt, 0.06)
      if (
        camera.position.distanceTo(targetCameraPosition) < CAMERA_LIMITS.focusCompleteDistance &&
        controls.target.distanceTo(targetLookAt) < CAMERA_LIMITS.focusCompleteDistance
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
  renderer.setSize(width, height, false)
  camera.aspect = width / height
  camera.updateProjectionMatrix()
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
  if (plantsRoot) disposeGroup(plantsRoot)
  if (staticRoot) disposeGroup(staticRoot)
  if (renderer) {
    renderer.dispose()
    renderer.domElement.remove()
  }
}

watch(() => props.plants, () => {
  rebuildPlants()
  if (props.selectedPlantId) syncSelectedPlant(props.selectedPlantId, { focus: false })
}, { deep: true })
watch(() => props.selectedPlantId, (plantId) => syncSelectedPlant(plantId))

onMounted(initScene)
onBeforeUnmount(cleanup)
</script>
