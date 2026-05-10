import { mount, flushPromises } from '@vue/test-utils'
import { h } from 'vue'
import { describe, test, expect, vi } from 'vitest'
import GardenPage from '../src/views/GardenPage.vue'

// Mock the API module
vi.mock('@/api', () => ({
  getGarden: vi.fn()
}))

import { getGarden } from '@/api'

const GardenSceneStub = {
  name: 'GardenScene',
  props: ['plants', 'overview', 'selectedPlantId'],
  emits: ['select-plant', 'clear-selection'],
  setup(props, { emit }) {
    return () => h('div', {
      'data-testid': 'garden-scene-stub',
      'data-selected-plant-id': props.selectedPlantId || '',
      onClick: () => emit('clear-selection')
    })
  }
}

describe('GardenPage', () => {
  test('loading resolves to summary containing 花园概览', async () => {
    getGarden.mockResolvedValue({
      data: [
        {
          id: '1',
          title: '第一篇日记',
          content: '今天天气真好',
          mood_label: '开心',
          mood_score: 80,
          created_at: '2026-05-01'
        },
        {
          id: '2',
          title: '第二篇日记',
          content: '有些疲惫的一天',
          mood_label: '平静',
          mood_score: 60,
          created_at: '2026-05-02'
        }
      ]
    })

    const wrapper = mount(GardenPage, {
      global: { stubs: ['router-link'] }
    })

    // Wait for the async onMounted to complete
    await flushPromises()

    // Summary card should contain 花园概览
    expect(wrapper.text()).toContain('花园概览')
  })

  test('two mocked diaries render as plant cards with titles', async () => {
    getGarden.mockResolvedValue({
      data: [
        {
          id: '1',
          title: '第一篇日记',
          content: '今天天气真好',
          mood_label: '开心',
          mood_score: 80,
          created_at: '2026-05-01'
        },
        {
          id: '2',
          title: '第二篇日记',
          content: '有些疲惫的一天',
          mood_label: '平静',
          mood_score: 60,
          created_at: '2026-05-02'
        }
      ]
    })

    const wrapper = mount(GardenPage, {
      global: { stubs: ['router-link'] }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('第一篇日记')
    expect(wrapper.text()).toContain('第二篇日记')
  })

  test('high score renders a happy/bright plant label or emoji', async () => {
    getGarden.mockResolvedValue({
      data: [
        {
          id: '1',
          title: '开心的一天',
          content: '今天非常开心',
          mood_label: '开心',
          mood_score: 85,
          created_at: '2026-05-01'
        }
      ]
    })

    const wrapper = mount(GardenPage, {
      global: { stubs: ['router-link'] }
    })

    await flushPromises()

    // High score (85 >= 75) should show a happy emoji
    const happyEmojis = ['😊', '🌻', '🌺', '🌸', '🌿']
    const hasHappyEmoji = happyEmojis.some(emoji => wrapper.text().includes(emoji))
    expect(hasHappyEmoji).toBe(true)
  })

  test('clicking a plant index card opens the detail panel', async () => {
    getGarden.mockResolvedValue({
      data: [
        {
          id: '1',
          title: '第一篇日记',
          content: '今天天气真好',
          mood_label: '开心',
          mood_score: 80,
          created_at: '2026-05-01'
        }
      ]
    })

    const wrapper = mount(GardenPage, {
      global: { stubs: ['router-link'] }
    })

    await flushPromises()

    const indexButton = wrapper.findAll('button').find(button => button.text().includes('第一篇日记'))
    expect(indexButton).toBeTruthy()

    await indexButton.trigger('click')

    const panel = wrapper.find('[data-testid="detail-panel"]')
    expect(panel.exists()).toBe(true)
    expect(panel.text()).toContain('日记之花')
    expect(panel.text()).toContain('这朵向日葵来自“第一篇日记”')
  })

  test('clicking a plant index card syncs the selected plant id into the 3D scene', async () => {
    getGarden.mockResolvedValue({
      data: [
        {
          id: '1',
          title: '第一篇日记',
          content: '今天天气真好',
          mood_label: '开心',
          mood_score: 80,
          created_at: '2026-05-01'
        }
      ]
    })

    const wrapper = mount(GardenPage, {
      global: {
        stubs: {
          'router-link': true,
          GardenScene: GardenSceneStub
        }
      }
    })

    await flushPromises()

    const indexButton = wrapper.findAll('button').find(button => button.text().includes('第一篇日记'))
    expect(indexButton).toBeTruthy()

    await indexButton.trigger('click')

    expect(wrapper.find('[data-testid="detail-panel"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="garden-scene-stub"]').attributes('data-selected-plant-id')).toBe('1')
  })

  test('GardenScene clear-selection closes the detail panel and clears the selected scene id', async () => {
    getGarden.mockResolvedValue({
      data: [
        {
          id: '1',
          title: '第一篇日记',
          content: '今天天气真好',
          mood_label: '开心',
          mood_score: 80,
          created_at: '2026-05-01'
        }
      ]
    })

    const wrapper = mount(GardenPage, {
      global: {
        stubs: {
          'router-link': true,
          GardenScene: GardenSceneStub
        }
      }
    })

    await flushPromises()

    const indexButton = wrapper.findAll('button').find(button => button.text().includes('第一篇日记'))
    expect(indexButton).toBeTruthy()

    await indexButton.trigger('click')
    expect(wrapper.find('[data-testid="detail-panel"]').exists()).toBe(true)

    await wrapper.find('[data-testid="garden-scene-stub"]').trigger('click')

    expect(wrapper.find('[data-testid="detail-panel"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="garden-scene-stub"]').attributes('data-selected-plant-id')).toBe('')
  })

  test('empty garden renders existing empty-state message', async () => {
    getGarden.mockResolvedValue({
      data: []
    })

    const wrapper = mount(GardenPage, {
      global: { stubs: ['router-link'] }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('你的花园还是空地，种下第一篇日记吧')
  })
})
