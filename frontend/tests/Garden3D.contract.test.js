import { mount } from '@vue/test-utils'
import { describe, expect, test } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'
import GardenScene from '../src/components/garden/GardenScene.vue'

const __dirname = dirname(fileURLToPath(import.meta.url))
const frontendRoot = resolve(__dirname, '..')

function readFrontendFile(relativePath) {
  return readFileSync(resolve(frontendRoot, relativePath), 'utf8')
}

describe('3D garden MVP contract', () => {
  test('GardenPage is wired to the 3D scene, detail panel, and mapping layer', () => {
    const source = readFrontendFile('src/views/GardenPage.vue')

    expect(source).toContain('GardenScene')
    expect(source).toContain('PlantDetailPanel')
    expect(source).toContain('getGardenWorld')
    expect(source).toContain('buildGardenWorld')
    expect(source).toContain('@select-plant="selectPlant"')
  })

  test('GardenScene owns the Three.js scene and click-selection contract', () => {
    const source = readFrontendFile('src/components/garden/GardenScene.vue')

    expect(source).toContain("import * as THREE from 'three'")
    expect(source).toContain('OrbitControls')
    expect(source).toContain("defineEmits(['select-plant', 'clear-selection'])")
    expect(source).toContain('world')
    expect(source).toContain('selectedPlantId')
    expect(source).toContain('function pickPlant')
    expect(source).toContain('function focusPlant')
    expect(source).toContain('function clearSelection')
    expect(source).toContain('function handleWheel')
    expect(source).toContain('function createGardenDiorama')
    expect(source).toContain('function createPaperTray')
    expect(source).toContain('function createSoftBackdrop')
    expect(source).toContain('function createTerrainPatches')
    expect(source).toContain('function createStonePathSystem')
    expect(source).toContain('function createCheerfulFlowerField')
    expect(source).toContain('function createMemoryTree')
    expect(source).toContain('function createCalmPond')
    expect(source).toContain('function createTransformingVines')
    expect(source).toContain('function createPaperDetails')
    expect(source).toContain('function createAtmosphereLayer')
    expect(source).toContain('autoFocusActive')
    expect(source).toContain('stopAutoFocus')
    expect(source).toContain('data-testid="garden-scene"')
  })

  test('GardenScene uses a fixed orthographic stage camera with zoom-only controls', () => {
    const source = readFrontendFile('src/components/garden/GardenScene.vue')

    expect(source).toContain('OrthographicCamera')
    expect(source).toContain('FRUSTUM_SIZE = 6.2')
    expect(source).toContain('HOME_CAMERA_POSITION = new THREE.Vector3(0.8, 4.7, 7.2)')
    expect(source).toContain('HOME_LOOK_AT = new THREE.Vector3(0, 0.35, 0)')
    expect(source).toContain('HOME_ZOOM = 1.05')
    expect(source).toContain('controls.enableRotate = false')
    expect(source).toContain('controls.enablePan = false')
    expect(source).toContain('controls.enableZoom = true')
    expect(source).toContain('controls.minZoom = 0.9')
    expect(source).toContain('controls.maxZoom = 1.28')
    expect(source).toContain('controls.addEventListener(\'start\', stopAutoFocus)')
    expect(source).toContain("renderer.domElement.addEventListener('wheel', handleWheel)")
    expect(source).toContain('event.deltaY > 0')
    expect(source).toContain('clearSelection({ notify: true, resetView: false })')
  })

  test('GardenScene includes paper-model terrain and selected plant effects', () => {
    const source = readFrontendFile('src/components/garden/GardenScene.vue')

    expect(source).toContain('makePaperShape')
    expect(source).toContain('deterministicPointInEllipse')
    expect(source).toContain('garden-canvas-shell')
    expect(source).toContain('paperTray')
    expect(source).toContain('softPaperTrayShadow')
    expect(source).toContain('cheerfulFlowerZone')
    expect(source).toContain('flowerFieldGrassBlade')
    expect(source).toContain('memoryTreeZone')
    expect(source).toContain('memoryLeafCluster')
    expect(source).toContain('memoryLamp')
    expect(source).toContain('calmPondZone')
    expect(source).toContain('calmPondWaterHighlight')
    expect(source).toContain('transformingVinesZone')
    expect(source).toContain('transformVineLeaf')
    expect(source).toContain('softBackdrop')
    expect(source).toContain('atmosphereLayer')
    expect(source).toContain('paperDetails')
    expect(source).toContain('paperWateringCan')
    expect(source).toContain('frontMemoryCard')
    expect(source).toContain('paperCloud')
    expect(source).not.toContain('paperSkyBackdrop')
    expect(source).not.toContain('softIllustrationLightBeam')
    expect(source).toContain('floatingLightPoint')
    expect(source).toContain('steppingStone')
    expect(source).toContain('paperBoat')
    expect(source).toContain('transformingVine')
    expect(source).toContain('memoryGlow')
    expect(source).toContain('garden-chip')
  })

  test('GardenScene exposes weather badge and keeps the scene visually inspectable', () => {
    const source = readFrontendFile('src/components/garden/GardenScene.vue')

    expect(source).toContain('data-testid="garden-weather-badge"')
    expect(source).toContain('activeClimate')
    expect(source).toContain('activeOverview')
    expect(source).toContain('今日气候')
  })

  test('GardenScene pins the WebGL canvas to the visible container to keep the plot centered', () => {
    const source = readFrontendFile('src/components/garden/GardenScene.vue')

    expect(source).toContain("renderer.domElement.style.width = '100%'")
    expect(source).toContain("renderer.domElement.style.height = '100%'")
    expect(source).toContain("renderer.domElement.style.display = 'block'")
    expect(source).toContain('renderer.setSize(width, height, false)')
  })

  test('GardenPage syncs selected flower state into and out of GardenScene', () => {
    const source = readFrontendFile('src/views/GardenPage.vue')

    expect(source).toContain(':selected-plant-id="selectedPlant?.id || null"')
    expect(source).toContain('@clear-selection="clearSelection"')
    expect(source).toContain('function clearSelection')
  })

  test('GardenScene shows a gentle fallback when WebGL is unavailable', async () => {
    const originalWebGL = window.WebGLRenderingContext
    window.WebGLRenderingContext = undefined

    const wrapper = mount(GardenScene, {
      props: {
        plants: [],
        overview: { totalCount: 0, avgScore: '0.0', statusText: '需要浇水', statusEmoji: '🌱' }
      }
    })

    await new Promise(resolve => setTimeout(resolve, 0))

    expect(wrapper.find('[data-testid="garden-scene-fallback"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('3D 花园正在等浏览器阳光')

    window.WebGLRenderingContext = originalWebGL
  })
})
