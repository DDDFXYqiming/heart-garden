import { mount } from '@vue/test-utils'
import { describe, test, expect } from 'vitest'
import ChatBubble from '../src/components/ChatBubble.vue'

describe('ChatBubble', () => {
  test('renders user message correctly', () => {
    const msg = { role: 'user', content: 'Hello' }
    const wrapper = mount(ChatBubble, { props: { msg } })
    expect(wrapper.text()).toContain('Hello')
    expect(wrapper.find('.bg-sticky').exists()).toBe(true)
  })

  test('renders assistant message correctly', () => {
    const msg = { role: 'assistant', content: 'Hi there' }
    const wrapper = mount(ChatBubble, { props: { msg } })
    expect(wrapper.text()).toContain('Hi there')
    expect(wrapper.find('.bg-white').exists()).toBe(true)
  })

  test('shows mood_label when provided', () => {
    const msg = { role: 'assistant', content: 'Hi', mood_label: '开心' }
    const wrapper = mount(ChatBubble, { props: { msg } })
    expect(wrapper.text()).toContain('开心')
  })

  test('shows response_mode badge for llm', () => {
    const msg = { role: 'assistant', content: 'Hi', response_mode: 'llm' }
    const wrapper = mount(ChatBubble, { props: { msg } })
    expect(wrapper.find('.bg-blue-100').exists()).toBe(true)
    expect(wrapper.text()).toContain('AI')
  })

  test('shows response_mode badge for rule engine', () => {
    const msg = { role: 'assistant', content: 'Hi', response_mode: 'rule' }
    const wrapper = mount(ChatBubble, { props: { msg } })
    expect(wrapper.find('.bg-gray-100').exists()).toBe(true)
    expect(wrapper.text()).toContain('规则')
  })
})
