import { mount } from '@vue/test-utils'
import { describe, test, expect } from 'vitest'
import DiaryCard from '../src/components/DiaryCard.vue'

describe('DiaryCard', () => {
  const defaultDiary = {
    id: '1',
    title: 'Test Diary',
    content: 'This is test content',
    mood_label: '开心',
    created_at: '2026-05-02'
  }

  test('renders diary title and content', () => {
    const wrapper = mount(DiaryCard, {
      props: { diary: defaultDiary },
      global: { stubs: ['router-link'] }
    })
    expect(wrapper.text()).toContain('Test Diary')
    expect(wrapper.text()).toContain('This is test content')
  })

  test('shows mood label', () => {
    const wrapper = mount(DiaryCard, {
      props: { diary: defaultDiary },
      global: { stubs: ['router-link'] }
    })
    expect(wrapper.text()).toContain('开心')
  })

  test('shows edit and delete buttons when showActions is true', () => {
    const wrapper = mount(DiaryCard, {
      props: { diary: defaultDiary, showActions: true },
      global: { stubs: { 'router-link': { template: '<a><slot /></a>' } } }
    })
    expect(wrapper.find('a').exists()).toBe(true)
    expect(wrapper.find('button').exists()).toBe(true)
  })

  test('hides actions when showActions is false', () => {
    const wrapper = mount(DiaryCard, {
      props: { diary: defaultDiary, showActions: false },
      global: { stubs: { 'router-link': { template: '<a><slot /></a>' } } }
    })
    expect(wrapper.find('a').exists()).toBe(false)
    expect(wrapper.find('button').exists()).toBe(false)
  })

  test('emits delete event when delete button clicked', async () => {
    const wrapper = mount(DiaryCard, {
      props: { diary: defaultDiary, showActions: true },
      global: { stubs: ['router-link'] }
    })
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('delete')).toBeTruthy()
    expect(wrapper.emitted('delete')[0]).toEqual(['1'])
  })

  test('renders garden variant correctly', () => {
    const wrapper = mount(DiaryCard, {
      props: { diary: defaultDiary, variant: 'garden' },
      global: { stubs: ['router-link'] }
    })
    expect(wrapper.text()).toContain('Test Diary')
    expect(wrapper.find('.bg-white\\/80').exists()).toBe(true)
  })
})
