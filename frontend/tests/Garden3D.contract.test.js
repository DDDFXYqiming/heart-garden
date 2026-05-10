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
    expect(source).toContain("defineEmits(['select-plant'])")
    expect(source).toContain('function pickPlant')
    expect(source).toContain('function focusPlant')
    expect(source).toContain('data-testid="garden-scene"')
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
