import { mount } from '@vue/test-utils'
import { describe, test, expect } from 'vitest'
import StatCard from '../src/components/StatCard.vue'

describe('StatCard', () => {
  test('renders icon, value and label', () => {
    const wrapper = mount(StatCard, {
      props: {
        icon: '📝',
        value: 10,
        label: '日记'
      }
    })
    expect(wrapper.text()).toContain('📝')
    expect(wrapper.text()).toContain('10')
    expect(wrapper.text()).toContain('日记')
  })

  test('renders string value correctly', () => {
    const wrapper = mount(StatCard, {
      props: {
        icon: '🏆',
        value: '开心',
        label: '最常情绪'
      }
    })
    expect(wrapper.text()).toContain('开心')
  })

  test('applies correct styling classes', () => {
    const wrapper = mount(StatCard, {
      props: {
        icon: '📈',
        value: 75,
        label: '平均情绪分'
      }
    })
    expect(wrapper.find('.bg-white').exists()).toBe(true)
    expect(wrapper.find('.border-pencil').exists()).toBe(true)
  })
})
