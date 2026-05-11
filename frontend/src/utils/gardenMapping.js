/**
 * 心语花园 — 3D 记忆花园数据映射层
 * 将后端日记数据映射为 3D 场景可用的植物配置
 */

/**
 * 对字符串执行稳定哈希，返回非负整数
 * 相同字符串总是得到相同结果
 */
export function hashStringToSeed(value) {
  let hash = 0
  const str = String(value)
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash // Convert to 32-bit integer
  }
  // Ensure strictly positive, even for empty strings or zero-hash inputs.
  return Math.max(1, Math.abs(hash))
}

/**
 * 根据情绪分数返回植物视觉配置
 */
export function moodToPlantProfile(score) {
  if (score >= 75) {
    return {
      modelType: 'sunflower',
      growthLevel: 'radiant',
      primaryColor: '#FFD700',
      secondaryColor: '#FF8C00',
      accentColor: '#FFE88A',
      height: 2.5,
      petalCount: 16,
      petalLayers: 3,
      petalScale: 1.2,
      leafCount: 6,
      glowIntensity: 0.8,
      pulseIntensity: 0.42,
      swaySpeed: 1.25,
      focusScale: 1.22,
      moodLabel: '高能量'
    }
  }
  if (score >= 60) {
    return {
      modelType: 'leafBloom',
      growthLevel: 'bloom',
      primaryColor: '#7EC850',
      secondaryColor: '#F5DEB3',
      accentColor: '#FF9FB6',
      height: 1.8,
      petalCount: 8,
      petalLayers: 2,
      petalScale: 1.0,
      leafCount: 5,
      glowIntensity: 0.5,
      pulseIntensity: 0.3,
      swaySpeed: 1.05,
      focusScale: 1.18,
      moodLabel: '温暖'
    }
  }
  if (score >= 40) {
    return {
      modelType: 'sprout',
      growthLevel: 'sprout',
      primaryColor: '#4CAF50',
      secondaryColor: '#8BC34A',
      accentColor: '#D7F7A8',
      height: 1.2,
      petalCount: 4,
      petalLayers: 1,
      petalScale: 0.7,
      leafCount: 4,
      glowIntensity: 0.3,
      pulseIntensity: 0.2,
      swaySpeed: 0.88,
      focusScale: 1.16,
      moodLabel: '平静'
    }
  }
  if (score >= 25) {
    return {
      modelType: 'duskLeaf',
      growthLevel: 'bud',
      primaryColor: '#8B6F9E',
      secondaryColor: '#6B4423',
      accentColor: '#D9B6E8',
      height: 0.9,
      petalCount: 3,
      petalLayers: 1,
      petalScale: 0.5,
      leafCount: 5,
      glowIntensity: 0.2,
      pulseIntensity: 0.16,
      swaySpeed: 0.72,
      focusScale: 1.14,
      moodLabel: '沉思'
    }
  }
  // score < 25
  return {
    modelType: 'cactus',
    growthLevel: 'survivor',
    primaryColor: '#5F9EA0',
    secondaryColor: '#2F4F4F',
    accentColor: '#C78DD7',
    height: 0.7,
    petalCount: 0,
    petalLayers: 0,
    petalScale: 0.3,
    leafCount: 3,
    glowIntensity: 0.1,
    pulseIntensity: 0.12,
    swaySpeed: 0.62,
    focusScale: 1.12,
    moodLabel: '坚韧'
  }
}

/**
 * 截取内容预览，最多 64 个字符
 */
function truncatePreview(content, maxLen = 64) {
  if (!content) return ''
  if (content.length <= maxLen) return content
  return content.slice(0, maxLen) + '...'
}

/**
 * 根据种子值生成 [min, max] 范围内的小数（确定性的伪随机）
 */
function seededRandom(seed) {
  // Simple mulberry32 PRNG
  let t = (seed + 0x6D2B79F5) >>> 0
  t = Math.imul(t ^ (t >>> 15), t | 1)
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296
}

/**
 * 在范围内生成微小的 jitter 偏移量
 */
function jitter(seed, range = 0.4) {
  return (seededRandom(seed) - 0.5) * range
}

function pickFromSeed(seed, values) {
  return values[Math.floor(seededRandom(seed) * values.length) % values.length]
}

/**
 * 将后端日记数据数组映射为 3D 花园植物数组
 *
 * @param {Array} items 后端日记数组，每条含 id/title/content/created_at/mood_score
 * @param {Object} options 可选参数
 * @param {number} options.plotWidth 地块宽度 (默认 16)
 * @param {number} options.plotDepth 地块深度 (默认 10)
 * @returns {Array} 植物数组
 */
export function createGardenPlants(items, options = {}) {
  if (!items || items.length === 0) return []

  const { plotWidth = 16, plotDepth = 10 } = options
  const margin = 2

  // 按创建时间从新到旧排序
  const sorted = [...items].sort((a, b) => {
    const dateA = new Date(a.created_at || a.createdAt || 0)
    const dateB = new Date(b.created_at || b.createdAt || 0)
    return dateB - dateA
  })

  const count = sorted.length
  // 计算网格列数，尽可能接近正方形布局
  const cols = Math.max(1, Math.ceil(Math.sqrt(count * (plotWidth / plotDepth))))
  const rows = Math.max(1, Math.ceil(count / cols))

  // 每个单元格的宽度和深度
  const cellW = (plotWidth - margin * 2) / Math.max(1, cols - 1 || 1)
  const cellD = (plotDepth - margin * 2) / Math.max(1, rows - 1 || 1)

  return sorted.map((item, index) => {
    const col = index % cols
    const row = Math.floor(index / cols)

    // 基础网格坐标；单行/单列时保持居中，避免少量植物挤在地块边缘。
    let baseX = cols === 1 ? plotWidth / 2 : margin + col * cellW
    let baseZ = rows === 1 ? plotDepth / 2 : margin + row * cellD

    // 基于 id 的确定性 jitter
    const idSeed = hashStringToSeed(String(item.id))
    const xJitter = jitter(idSeed, 0.4)
    const zJitter = jitter(idSeed + 666, 0.4)

    // 确保 jitter 后仍在边距内
    const xRaw = baseX + xJitter
    const zRaw = baseZ + zJitter
    const x = Math.round(Math.min(Math.max(xRaw, margin), plotWidth - margin) * 100) / 100
    const z = Math.round(Math.min(Math.max(zRaw, margin), plotDepth - margin) * 100) / 100

    // 基于 id 的旋转
    const rotationY = Math.round(seededRandom(idSeed + 333) * 360)

    // 植物配置
    const moodScore = item.mood_score ?? item.moodScore ?? 0
    const createdAt = item.created_at || item.createdAt || ''
    const profile = moodToPlantProfile(moodScore)
    const bedType = pickFromSeed(idSeed + 999, ['round', 'ribbon', 'patch', 'stone'])

    return {
      id: String(item.id),
      sourceType: 'diary',
      title: item.title || '',
      content: item.content || '',
      contentPreview: truncatePreview(item.content),
      createdAt,
      moodScore,
      x,
      z,
      rotationY,
      ...profile,
      bedType,
      swaySpeed: Math.round((profile.swaySpeed + jitter(idSeed + 222, 0.18)) * 100) / 100,
      pulseIntensity: Math.round((profile.pulseIntensity + seededRandom(idSeed + 444) * 0.08) * 100) / 100,
      focusScale: Math.round((profile.focusScale + seededRandom(idSeed + 555) * 0.04) * 100) / 100,
      growthStory: describePlantGrowth({
        modelType: profile.modelType,
        growthLevel: profile.growthLevel,
        moodLabel: profile.moodLabel,
        title: item.title || ''
      } /* partial - describePlantGrowth only reads these keys */)
    }
  })
}

/**
 * 构建花园概览对象
 */
export function buildGardenOverview(plants) {
  if (!plants || plants.length === 0) {
    return {
      totalCount: 0,
      avgScore: '0.0',
      statusText: '需要浇水',
      statusEmoji: '🌱'
    }
  }

  const totalCount = plants.length
  const totalScore = plants.reduce((sum, p) => sum + (p.moodScore || 0), 0)
  const avg = totalCount > 0 ? totalScore / totalCount : 0
  const avgScore = (Math.round(avg * 10) / 10).toFixed(1)

  let statusText, statusEmoji
  if (avg >= 75) {
    statusText = '繁花盛开'
    statusEmoji = '🌻'
  } else if (avg >= 60) {
    statusText = '鲜花绽放'
    statusEmoji = '🌸'
  } else if (avg >= 40) {
    statusText = '稳定生长'
    statusEmoji = '🌿'
  } else if (avg >= 25) {
    statusText = '静谧生长'
    statusEmoji = '🍂'
  } else {
    statusText = '需要浇水'
    statusEmoji = '🌵'
  }

  return { totalCount, avgScore, statusText, statusEmoji }
}

/**
 * 生成植物成长说明文案（中文）
 */
export function describePlantGrowth(plant) {
  const label = plant.moodLabel || ''
  const type = plant.modelType || ''
  const level = plant.growthLevel || ''
  const title = plant.title || ''

  if (type === 'sunflower') {
    if (title) {
      return `这朵向日葵来自“${title}”，充满阳光与能量，正在盛放。`
    }
    return '这朵向日葵来自一篇高能量记录，正在盛放。'
  }
  if (type === 'leafBloom' || type === 'flower') {
    if (title) {
      return `这朵花来自“${title}”，温暖绽放，充满生机。`
    }
    return '这朵花来自一篇温暖的记录，正在绽放。'
  }
  if (type === 'sprout') {
    if (title) {
      return `这株新芽来自“${title}”，静静生长，孕育着希望。`
    }
    return '这株新芽来自一篇平静的记录，正在生长。'
  }
  if (type === 'duskLeaf') {
    if (title) {
      return `这片暮叶来自“${title}”，在静谧中积蓄力量。`
    }
    return '这片暮叶来自一篇沉思的记录，在静谧中积蓄力量。'
  }
  if (type === 'cactus') {
    if (title) {
      return `这株仙人掌来自“${title}”，坚韧不拔，顽强守护。`
    }
    return '这株仙人掌来自一篇低谷记录，坚韧不拔，顽强守护。'
  }

  return '这株植物正在生长。'
}
