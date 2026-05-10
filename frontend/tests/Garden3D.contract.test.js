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
    expect(source).toContain('createGardenPlants')
    expect(source).toContain('buildGardenOverview')
    expect(source).toContain('@select-plant="selectPlant"')
  })

  test('GardenScene owns the Three.js scene and click-selection contract', () => {
    const source = readFrontendFile('src/components/garden/GardenScene.vue')

    expect(source).toContain("import * as THREE from 'three'")
    expect(source).toContain('OrbitControls')
    expect(source).toContain("defineEmits(['select-plant', 'clear-selection'])")
    expect(source).toContain('selectedPlantId')
    expect(source).toContain('function pickPlant')
    expect(source).toContain('function focusPlant')
    expect(source).toContain('function clearSelection')
    expect(source).toContain('function handleWheel')
    expect(source).toContain('autoFocusActive')
    expect(source).toContain('stopAutoFocus')
    expect(source).toContain('data-testid="garden-scene"')
  })

  test('GardenScene keeps camera controls free after focus and supports wider zoom/orbit bounds', () => {
    const source = readFrontendFile('src/components/garden/GardenScene.vue')

    expect(source).toContain('CAMERA_LIMITS')
    expect(source).toContain('minDistance: 2.8')
    expect(source).toContain('maxDistance: 48')
    expect(source).toContain('maxPolarAngle: Math.PI * 0.92')
    expect(source).toContain('controls.addEventListener(\'start\', stopAutoFocus)')
    expect(source).toContain("renderer.domElement.addEventListener('wheel', handleWheel)")
    expect(source).toContain('event.deltaY > 0')
    expect(source).toContain('clearSelection({ notify: true, resetView: false })')
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
