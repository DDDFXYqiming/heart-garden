<template>
  <section
    class="relative overflow-hidden border-[3px] border-pencil bg-gradient-to-b from-amber-50 via-lime-50 to-emerald-50 shadow-hard wobbly-lg"
    aria-label="3D 记忆花园"
  >
    <div
      ref="container"
      data-testid="garden-scene"
      class="h-[520px] min-h-[420px] w-full cursor-grab active:cursor-grabbing"
    ></div>

    <div class="pointer-events-none absolute left-4 top-4 max-w-xs border-[2px] border-pencil bg-white/85 px-4 py-3 text-sm shadow-hard-sm backdrop-blur wobbly-sm">
      <div class="font-bold" style="font-family: 'Kalam', cursive;">🌿 3D 记忆花园</div>
      <div class="text-pencil/70">拖拽旋转 · 滚轮缩放 · 点击花朵唤醒记忆</div>
    </div>

    <div
      v-if="overview"
      class="pointer-events-none absolute right-4 top-4 hidden border-[2px] border-pencil bg-white/85 px-4 py-3 text-sm shadow-hard-sm backdrop-blur wobbly-sm md:block"
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
      class="pointer-events-none absolute bottom-4 left-1/2 max-w-sm -translate-x-1/2 border-[2px] border-pencil bg-white/90 px-4 py-3 text-center shadow-hard-sm backdrop-blur wobbly-sm"
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
  minDistance: 2.8,
  maxDistance: 48,
  minPolarAngle: Math.PI * 0.04,
  maxPolarAngle: Math.PI * 0.92,
  focusCompleteDistance: 0.08
}
const CLICK_DRAG_THRESHOLD = 4
const HOME_CAMERA_POSITION = new THREE.Vector3(0, 8.8, 16)
const HOME_LOOK_AT = new THREE.Vector3(0, 0.7, 0)

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
  scene.fog = new THREE.Fog('#fff8ec', 24, 72)

  camera = new THREE.PerspectiveCamera(42, 1, 0.1, 120)
  camera.position.copy(HOME_CAMERA_POSITION)
  targetCameraPosition = HOME_CAMERA_POSITION.clone()
  targetLookAt = HOME_LOOK_AT.clone()

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  renderer.outputColorSpace = THREE.SRGBColorSpace
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
  addGardenPlot()
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
  const hemi = new THREE.HemisphereLight('#fff6d7', '#8fbf8f', 2.8)
  scene.add(hemi)

  const sun = new THREE.DirectionalLight('#fff1b8', 2.6)
  sun.position.set(-5, 9, 7)
  sun.castShadow = true
  sun.shadow.mapSize.set(1024, 1024)
  sun.shadow.camera.near = 1
  sun.shadow.camera.far = 25
  sun.shadow.camera.left = -12
  sun.shadow.camera.right = 12
  sun.shadow.camera.top = 12
  sun.shadow.camera.bottom = -12
  scene.add(sun)

  const fill = new THREE.PointLight('#ffd6e7', 1.1, 18)
  fill.position.set(5, 4, -4)
  scene.add(fill)
}

function toonMaterial(color, options = {}) {
  return new THREE.MeshToonMaterial({
    color,
    emissive: options.emissive || '#000000',
    emissiveIntensity: options.emissiveIntensity || 0
  })
}

function addGardenPlot() {
  const ground = new THREE.Mesh(
    new THREE.BoxGeometry(PLOT_WIDTH + 1.1, 0.18, PLOT_DEPTH + 1.1),
    toonMaterial('#8fce72')
  )
  ground.position.y = -0.12
  ground.receiveShadow = true
  scene.add(ground)

  const soil = new THREE.Mesh(
    new THREE.BoxGeometry(PLOT_WIDTH - 1.5, 0.08, PLOT_DEPTH - 1.5),
    toonMaterial('#b99062')
  )
  soil.position.y = -0.04
  soil.receiveShadow = true
  scene.add(soil)

  const path = new THREE.Mesh(
    new THREE.BoxGeometry(1.15, 0.1, PLOT_DEPTH - 0.4),
    toonMaterial('#f3d99b')
  )
  path.position.set(-PLOT_WIDTH * 0.25, 0.02, 0)
  path.receiveShadow = true
  scene.add(path)

  const pond = new THREE.Mesh(
    new THREE.CylinderGeometry(1.15, 1.15, 0.09, 32),
    toonMaterial('#8fd4ff', { emissive: '#4aaee8', emissiveIntensity: 0.18 })
  )
  pond.position.set(PLOT_WIDTH * 0.28, 0.04, -PLOT_DEPTH * 0.25)
  pond.scale.z = 0.62
  pond.receiveShadow = true
  scene.add(pond)

  addFence()
  addSignBoard()
}

function addFence() {
  const postMat = toonMaterial('#8b5a2b')
  const railMat = toonMaterial('#b98046')
  const postGeo = new THREE.BoxGeometry(0.22, 0.85, 0.22)
  const railGeoX = new THREE.BoxGeometry(1.25, 0.16, 0.16)
  const railGeoZ = new THREE.BoxGeometry(0.16, 0.16, 1.25)
  const y = 0.28
  const minX = -PLOT_WIDTH / 2 - 0.45
  const maxX = PLOT_WIDTH / 2 + 0.45
  const minZ = -PLOT_DEPTH / 2 - 0.45
  const maxZ = PLOT_DEPTH / 2 + 0.45

  for (let x = minX; x <= maxX + 0.01; x += 1.4) {
    addFencePost(x, minZ)
    addFencePost(x, maxZ)
    addFenceRail(x, minZ, true)
    addFenceRail(x, maxZ, true)
  }
  for (let z = minZ; z <= maxZ + 0.01; z += 1.4) {
    addFencePost(minX, z)
    addFencePost(maxX, z)
    addFenceRail(minX, z, false)
    addFenceRail(maxX, z, false)
  }

  function addFencePost(x, z) {
    const post = new THREE.Mesh(postGeo, postMat)
    post.position.set(x, y, z)
    post.castShadow = true
    scene.add(post)
  }

  function addFenceRail(x, z, alongX) {
    const rail = new THREE.Mesh(alongX ? railGeoX : railGeoZ, railMat)
    rail.position.set(x, y + 0.12, z)
    rail.castShadow = true
    scene.add(rail)
  }
}

function addSignBoard() {
  const sign = new THREE.Group()
  const post = new THREE.Mesh(new THREE.BoxGeometry(0.18, 1.1, 0.18), toonMaterial('#7a4d28'))
  post.position.y = 0.52
  const board = new THREE.Mesh(new THREE.BoxGeometry(2.8, 0.8, 0.16), toonMaterial('#f2c37a'))
  board.position.y = 1.18
  board.castShadow = true
  post.castShadow = true
  sign.add(post, board)
  sign.position.set(-PLOT_WIDTH / 2 + 1.9, 0, -PLOT_DEPTH / 2 + 1)
  sign.rotation.y = 0.25
  scene.add(sign)
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
  group.position.set(plant.x - PLOT_WIDTH / 2, 0, plant.z - PLOT_DEPTH / 2)
  group.rotation.y = THREE.MathUtils.degToRad(plant.rotationY || 0)

  if (plant.modelType === 'cactus') {
    addCactus(group, plant)
  } else {
    addFlower(group, plant)
  }

  group.traverse((child) => {
    if (child.isMesh) {
      child.castShadow = true
      child.receiveShadow = true
      child.userData.plant = plant
    }
  })

  return group
}

function addFlower(group, plant) {
  const height = Number(plant.height || 1.2)
  const stem = new THREE.Mesh(
    new THREE.CylinderGeometry(0.045, 0.065, height, 10),
    toonMaterial('#3d8b46')
  )
  stem.position.y = height / 2
  group.add(stem)

  const leafMat = toonMaterial('#4fa85b')
  const leafGeo = new THREE.SphereGeometry(0.24, 12, 8)
  for (const side of [-1, 1]) {
    const leaf = new THREE.Mesh(leafGeo, leafMat)
    leaf.scale.set(1.15, 0.22, 0.48)
    leaf.position.set(side * 0.22, height * 0.48, 0)
    leaf.rotation.set(0.15, 0, side * 0.72)
    group.add(leaf)
  }

  const petalCount = Math.max(plant.petalCount || 5, 4)
  const petalMat = toonMaterial(plant.primaryColor || '#ffd166', {
    emissive: plant.primaryColor || '#ffd166',
    emissiveIntensity: Math.min(Number(plant.glowIntensity || 0) * 0.18, 0.18)
  })
  const centerMat = toonMaterial(plant.secondaryColor || '#8b5a2b')
  const petalGeo = new THREE.SphereGeometry(0.18 * (plant.petalScale || 1), 16, 10)
  const radius = plant.modelType === 'sunflower' ? 0.34 : 0.25

  const flowerHead = new THREE.Group()
  flowerHead.position.y = height + 0.1
  for (let i = 0; i < petalCount; i++) {
    const angle = (i / petalCount) * Math.PI * 2
    const petal = new THREE.Mesh(petalGeo, petalMat)
    petal.position.set(Math.cos(angle) * radius, Math.sin(angle) * radius, 0)
    petal.scale.set(0.72, 1.2, 0.22)
    petal.rotation.z = angle
    flowerHead.add(petal)
  }

  const center = new THREE.Mesh(
    new THREE.SphereGeometry(plant.modelType === 'sunflower' ? 0.22 : 0.17, 18, 12),
    centerMat
  )
  center.scale.z = 0.55
  flowerHead.add(center)
  group.add(flowerHead)
}

function addCactus(group, plant) {
  const height = Number(plant.height || 0.8)
  const cactusMat = toonMaterial(plant.primaryColor || '#5f9ea0')
  const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.22, height, 6, 12), cactusMat)
  body.position.y = height / 2 + 0.18
  group.add(body)

  for (const side of [-1, 1]) {
    const arm = new THREE.Mesh(new THREE.CapsuleGeometry(0.08, 0.38, 5, 8), cactusMat)
    arm.position.set(side * 0.22, height * 0.72, 0)
    arm.rotation.z = side * 0.9
    group.add(arm)
  }

  const bud = new THREE.Mesh(
    new THREE.SphereGeometry(0.12, 12, 8),
    toonMaterial(plant.secondaryColor || '#c78dd7', { emissive: '#c78dd7', emissiveIntensity: 0.08 })
  )
  bud.position.y = height + 0.55
  group.add(bud)
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
  // Scrolling outward from a focused flower is the intentional gesture for leaving the active memory.
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
  targetLookAt = new THREE.Vector3(x, Math.max(plant.height || 1.2, 1), z)
  targetCameraPosition = new THREE.Vector3(x + 3.2, 3.4, z + 4.2)
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
      const active = hoveredPlant.value?.id === plant.id || selectedPlantId === plant.id
      const targetScale = active ? 1.14 : 1
      group.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.12)
      group.position.y = Math.sin(elapsed * 1.4 + seed) * 0.035
      group.rotation.z = Math.sin(elapsed * 0.9 + seed) * 0.025
    })
  }

  if (camera && controls) {
    if (autoFocusActive) {
      camera.position.lerp(targetCameraPosition, 0.035)
      controls.target.lerp(targetLookAt, 0.055)
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
