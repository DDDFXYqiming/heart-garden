import { mount } from '@vue/test-utils'
import { describe, test, expect } from 'vitest'
import PlantDetailPanel from '../src/components/garden/PlantDetailPanel.vue'

describe('PlantDetailPanel', () => {
  const basePlant = {
    id: '1',
    title: '开心的一天',
    content: '今天去公园散步，阳光很好，心情愉快。还遇到了小猫咪，非常开心。',
    mood_label: '开心',
    mood_score: 85,
    created_at: '2026-05-01',
    sourceType: 'diary',
    growthStory: '你的快乐让花朵绽放，继续记录美好吧！',
    modelType: 'sunflower'
  }

  test('renders nothing when plant is null', () => {
    const wrapper = mount(PlantDetailPanel, {
      props: { plant: null }
    })
    // Should not render main panel content
    expect(wrapper.find('[data-testid="detail-panel"]').exists()).toBe(false)
  })

  test('renders title when plant is provided', () => {
    const wrapper = mount(PlantDetailPanel, {
      props: { plant: basePlant }
    })
    expect(wrapper.text()).toContain('开心的一天')
  })

  test('renders mood score and mood label', () => {
    const wrapper = mount(PlantDetailPanel, {
      props: { plant: basePlant }
    })
    expect(wrapper.text()).toContain('85')
    expect(wrapper.text()).toContain('开心')
  })

  test('renders growth story', () => {
    const wrapper = mount(PlantDetailPanel, {
      props: { plant: basePlant }
    })
    expect(wrapper.text()).toContain('你的快乐让花朵绽放，继续记录美好吧！')
  })

  test('shows sourceType diary as 日记之花', () => {
    const wrapper = mount(PlantDetailPanel, {
      props: { plant: basePlant }
    })
    expect(wrapper.text()).toContain('日记之花')
  })

  test('shows modelType sunflower as 向日葵', () => {
    const wrapper = mount(PlantDetailPanel, {
      props: { plant: basePlant }
    })
    expect(wrapper.text()).toContain('向日葵')
  })

  test('maps modelType sprout to 新芽', () => {
    const wrapper = mount(PlantDetailPanel, {
      props: {
        plant: { ...basePlant, modelType: 'sprout' }
      }
    })
    expect(wrapper.text()).toContain('新芽')
  })

  test('maps modelType cactus to 仙人掌', () => {
    const wrapper = mount(PlantDetailPanel, {
      props: {
        plant: { ...basePlant, modelType: 'cactus' }
      }
    })
    expect(wrapper.text()).toContain('仙人掌')
  })

  test('maps modelType duskLeaf to 暮叶', () => {
    const wrapper = mount(PlantDetailPanel, {
      props: {
        plant: { ...basePlant, modelType: 'duskLeaf' }
      }
    })
    expect(wrapper.text()).toContain('暮叶')
  })

  test('maps modelType flower to 花叶', () => {
    const wrapper = mount(PlantDetailPanel, {
      props: {
        plant: { ...basePlant, modelType: 'flower' }
      }
    })
    expect(wrapper.text()).toContain('花叶')
  })

  test('maps modelType leafBloom to 花叶', () => {
    const wrapper = mount(PlantDetailPanel, {
      props: {
        plant: { ...basePlant, modelType: 'leafBloom' }
      }
    })
    expect(wrapper.text()).toContain('花叶')
  })

  test('renders created_at date', () => {
    const wrapper = mount(PlantDetailPanel, {
      props: { plant: basePlant }
    })
    expect(wrapper.text()).toContain('2026-05-01')
  })

  test('supports camelCase createdAt', () => {
    const wrapper = mount(PlantDetailPanel, {
      props: {
        plant: {
          ...basePlant,
          createdAt: '2026-06-15',
          created_at: undefined
        }
      }
    })
    expect(wrapper.text()).toContain('2026-06-15')
  })

  test('emits close when close button is clicked', async () => {
    const wrapper = mount(PlantDetailPanel, {
      props: { plant: basePlant }
    })
    const closeBtn = wrapper.find('button[aria-label="关闭详情"]')
    expect(closeBtn.exists()).toBe(true)
    await closeBtn.trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  test('emits open-source with plant when 查看原记录 is clicked', async () => {
    const wrapper = mount(PlantDetailPanel, {
      props: { plant: basePlant }
    })
    const viewBtn = wrapper.find('button[aria-label="查看原记录"]')
    expect(viewBtn.exists()).toBe(true)
    await viewBtn.trigger('click')
    expect(wrapper.emitted('open-source')).toBeTruthy()
    expect(wrapper.emitted('open-source')[0][0]).toEqual(basePlant)
  })
})
