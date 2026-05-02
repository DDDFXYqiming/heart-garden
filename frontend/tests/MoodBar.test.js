import { mount } from '@vue/test-utils'
import { describe, test, expect } from 'vitest'
import MoodBar from '../src/components/MoodBar.vue'

describe('MoodBar', () => {
  test('renders trend type correctly', () => {
    const data = { label: '开心', score: 80, timestamp: '2026-05-02' }
    const wrapper = mount(MoodBar, {
      props: { type: 'trend', data }
    })
    expect(wrapper.find('.bg-yellow-400').exists()).toBe(true)
  })

  test('renders distribution type correctly', () => {
    const wrapper = mount(MoodBar, {
      props: {
        type: 'distribution',
        label: '开心',
        count: 10,
        maxValue: 20
      }
    })
    expect(wrapper.text()).toContain('开心')
    expect(wrapper.text()).toContain('10')
  })

  test('applies correct color for different moods', () => {
    const moods = [
      { label: '开心', color: 'bg-yellow-400' },
      { label: '平静', color: 'bg-green-400' },
      { label: '中性', color: 'bg-blue-400' },
      { label: '焦虑', color: 'bg-orange-400' },
      { label: '悲伤', color: 'bg-purple-400' }
    ]

    for (const mood of moods) {
      const wrapper = mount(MoodBar, {
        props: {
          type: 'trend',
          data: { label: mood.label, score: 50, timestamp: '2026-05-02' }
        }
      })
      expect(wrapper.find('.' + mood.color).exists()).toBe(true)
    }
  })
})
