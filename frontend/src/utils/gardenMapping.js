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

function parseDate(value) {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

function dayKey(value) {
  const date = parseDate(value)
  if (!date) return ''
  return date.toISOString().slice(0, 10)
}

function daysBetween(later, earlier) {
  if (!later || !earlier) return 0
  const diff = later.getTime() - earlier.getTime()
  return Math.max(0, Math.round(diff / 86400000))
}

function scoreAverage(items) {
  if (!items.length) return 0
  return items.reduce((sum, item) => sum + Number(item.moodScore ?? item.mood_score ?? 0), 0) / items.length
}

function scoreVolatility(items, avg = scoreAverage(items)) {
  if (items.length <= 1) return 0
  const variance = items.reduce((sum, item) => {
    const score = Number(item.moodScore ?? item.mood_score ?? 0)
    return sum + ((score - avg) ** 2)
  }, 0) / items.length
  return Math.sqrt(variance)
}

const THEME_RULES = [
  {
    key: 'work',
    label: '工作压力',
    icon: '💼',
    color: '#7d93a5',
    groundType: 'stone',
    keywords: ['工作', '项目', '会议', '压力', '加班', '任务', '同事', '客户', '汇报', '考试', '学习']
  },
  {
    key: 'relationship',
    label: '亲密关系',
    icon: '💌',
    color: '#e89bab',
    groundType: 'flowerbed',
    keywords: ['朋友', '家人', '妈妈', '爸爸', '喜欢', '关系', '恋人', '爱', '陪伴', '聊天', '同学']
  },
  {
    key: 'growth',
    label: '自我成长',
    icon: '🌿',
    color: '#8fbf78',
    groundType: 'path',
    keywords: ['成长', '坚持', '目标', '计划', '练习', '完成', '进步', '反思', '勇气', '改变']
  },
  {
    key: 'rest',
    label: '休息修复',
    icon: '☁️',
    color: '#a9c8d8',
    groundType: 'pond',
    keywords: ['休息', '睡觉', '疲惫', '累', '放松', '治愈', '安静', '散步', '冥想', '恢复']
  },
  {
    key: 'travel',
    label: '远方见闻',
    icon: '🚪',
    color: '#e7c36f',
    groundType: 'gate',
    keywords: ['旅行', '出门', '城市', '风景', '公园', '路上', '远方', '车站', '海', '山']
  },
  {
    key: 'daily',
    label: '日常微光',
    icon: '✦',
    color: '#d9c88f',
    groundType: 'meadow',
    keywords: []
  }
]

const THEME_BY_KEY = THEME_RULES.reduce((map, item) => {
  map[item.key] = item
  return map
}, {})

function normalizeTags(tags) {
  if (!tags) return ''
  if (Array.isArray(tags)) return tags.join(' ')
  return String(tags)
}

function itemText(item) {
  return [
    item.title,
    item.content,
    item.ai_analysis,
    item.mood_label,
    normalizeTags(item.tags)
  ].filter(Boolean).join(' ')
}

function extractTheme(item) {
  const text = itemText(item)
  const matched = THEME_RULES.find(rule => rule.key !== 'daily' && rule.keywords.some(keyword => text.includes(keyword)))
  return matched || THEME_BY_KEY.daily
}

function timeLayerForAge(ageDays) {
  if (ageDays <= 7) {
    return {
      key: 'fresh',
      label: '新鲜记忆',
      description: '最近一周的记录仍像刚冒出的叶片。'
    }
  }
  if (ageDays <= 30) {
    return {
      key: 'settled',
      label: '沉淀记忆',
      description: '一个月内的记录开始变成稳定花丛。'
    }
  }
  return {
    key: 'archived',
    label: '旧日地貌',
    description: '更早的记录沉积成石碑、老树和小径。'
  }
}

function contentWeight(content) {
  const length = String(content || '').length
  if (length >= 180) return 0.9
  if (length >= 90) return 0.55
  if (length >= 40) return 0.28
  return 0.12
}

function moodWeight(score) {
  const distanceFromCenter = Math.abs(Number(score || 0) - 50)
  return Math.min(0.9, distanceFromCenter / 55)
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
  const anchorDate = sorted
    .map(item => parseDate(item.created_at || item.createdAt))
    .filter(Boolean)
    .sort((a, b) => b - a)[0] || null

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
    const createdDate = parseDate(createdAt)
    const ageDays = anchorDate && createdDate ? daysBetween(anchorDate, createdDate) : index
    const theme = extractTheme(item)
    const timeLayer = timeLayerForAge(ageDays)
    const profile = moodToPlantProfile(moodScore)
    const bedType = pickFromSeed(idSeed + 999, ['round', 'ribbon', 'patch', 'stone'])

    return {
      id: String(item.id),
      sourceType: 'diary',
      title: item.title || '',
      content: item.content || '',
      contentPreview: truncatePreview(item.content),
      createdAt,
      sourceMoodLabel: item.mood_label || item.moodLabel || '',
      moodScore,
      x,
      z,
      rotationY,
      ...profile,
      bedType,
      swaySpeed: Math.round((profile.swaySpeed + jitter(idSeed + 222, 0.18)) * 100) / 100,
      pulseIntensity: Math.round((profile.pulseIntensity + seededRandom(idSeed + 444) * 0.08) * 100) / 100,
      focusScale: Math.round((profile.focusScale + seededRandom(idSeed + 555) * 0.04) * 100) / 100,
      themeKey: theme.key,
      themeLabel: theme.label,
      themeIcon: theme.icon,
      themeColor: theme.color,
      groundType: theme.groundType,
      ageDays,
      timeLayer: timeLayer.key,
      timeLayerLabel: timeLayer.label,
      memoryWeight: Math.round((1 + Math.min(2.2, contentWeight(item.content || '') + moodWeight(moodScore))) * 100) / 100,
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
      statusEmoji: '🌱',
      volatility: '0.0',
      activeDays: 0,
      firstDate: '',
      lastDate: ''
    }
  }

  const totalCount = plants.length
  const totalScore = plants.reduce((sum, p) => sum + (p.moodScore || 0), 0)
  const avg = totalCount > 0 ? totalScore / totalCount : 0
  const avgScore = (Math.round(avg * 10) / 10).toFixed(1)
  const volatility = (Math.round(scoreVolatility(plants, avg) * 10) / 10).toFixed(1)
  const dateKeys = plants.map(p => dayKey(p.createdAt)).filter(Boolean).sort()
  const activeDays = new Set(dateKeys).size
  const firstDate = dateKeys[0] || ''
  const lastDate = dateKeys[dateKeys.length - 1] || ''

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

  return { totalCount, avgScore, statusText, statusEmoji, volatility, activeDays, firstDate, lastDate }
}

export function buildGardenClimate(plants, overview = buildGardenOverview(plants)) {
  const avg = Number(overview.avgScore || 0)
  const volatility = Number(overview.volatility || 0)
  const windSpeed = Math.round((0.45 + Math.min(1.45, volatility / 26)) * 100) / 100
  const cloudSpeed = Math.round((0.2 + Math.min(1.15, volatility / 34)) * 100) / 100
  const moodStability = Math.max(0, Math.round((100 - volatility * 2) * 10) / 10)

  if (avg >= 75) {
    return {
      type: 'sunny',
      icon: '☀️',
      label: '晴光盛放',
      summary: '阳光充足，记忆向上生长。',
      skyColor: '#bfe6f2',
      horizonColor: '#fff2bd',
      groundTint: '#d9efae',
      lightColor: '#fff0b8',
      sunlightIntensity: 3.2,
      fogColor: '#fff8ec',
      fogNear: 20,
      fogFar: 58,
      windSpeed,
      cloudSpeed,
      rainIntensity: 0,
      mistIntensity: 0.05,
      puddleIntensity: 0.15,
      leafDrift: 0.85,
      moodStability
    }
  }

  if (avg >= 60) {
    return {
      type: 'breezy',
      icon: '🌤️',
      label: '微风晴间多云',
      summary: '适合回顾与整理，情绪趋于平稳。',
      skyColor: '#c9e6ef',
      horizonColor: '#fff0c8',
      groundTint: '#cfe6a2',
      lightColor: '#ffe9b6',
      sunlightIntensity: 2.75,
      fogColor: '#fff8ec',
      fogNear: 18,
      fogFar: 54,
      windSpeed,
      cloudSpeed,
      rainIntensity: 0,
      mistIntensity: 0.12,
      puddleIntensity: 0.22,
      leafDrift: 0.62,
      moodStability
    }
  }

  if (avg >= 40) {
    return {
      type: 'cloudy',
      icon: '☁️',
      label: '薄云平稳',
      summary: '光线变柔，花园正在安静沉淀。',
      skyColor: '#d7e3e5',
      horizonColor: '#f8e8cf',
      groundTint: '#c8d89a',
      lightColor: '#f2dfc0',
      sunlightIntensity: 2.25,
      fogColor: '#f7f0df',
      fogNear: 15,
      fogFar: 46,
      windSpeed,
      cloudSpeed,
      rainIntensity: 0.08,
      mistIntensity: 0.28,
      puddleIntensity: 0.36,
      leafDrift: 0.42,
      moodStability
    }
  }

  if (avg >= 25) {
    return {
      type: 'mist',
      icon: '🌫️',
      label: '细雾修复',
      summary: '花园放慢速度，把低落安放成可以照看的角落。',
      skyColor: '#d5dde1',
      horizonColor: '#efe2d2',
      groundTint: '#bac991',
      lightColor: '#decdbf',
      sunlightIntensity: 1.85,
      fogColor: '#eee4d9',
      fogNear: 11,
      fogFar: 38,
      windSpeed,
      cloudSpeed,
      rainIntensity: 0.18,
      mistIntensity: 0.45,
      puddleIntensity: 0.55,
      leafDrift: 0.25,
      moodStability
    }
  }

  return {
    type: 'rainy',
    icon: '🌧️',
    label: '雨后守护',
    summary: '雨水不是惩罚，它在替这段记忆保留位置。',
    skyColor: '#c6d3dc',
    horizonColor: '#e4dbd5',
    groundTint: '#a9bf93',
    lightColor: '#d6c7bb',
    sunlightIntensity: 1.55,
    fogColor: '#e7ded8',
    fogNear: 9,
    fogFar: 34,
    windSpeed,
    cloudSpeed,
    rainIntensity: 0.34,
    mistIntensity: 0.62,
    puddleIntensity: 0.78,
    leafDrift: 0.18,
    moodStability
  }
}

export function buildGardenZones(plants, options = {}) {
  if (!plants || plants.length === 0) return []
  const { plotWidth = 16, plotDepth = 10 } = options
  const groups = new Map()

  plants.forEach((plant) => {
    const key = plant.themeKey || 'daily'
    const theme = THEME_BY_KEY[key] || THEME_BY_KEY.daily
    const current = groups.get(key) || {
      key,
      label: theme.label,
      icon: theme.icon,
      color: theme.color,
      groundType: theme.groundType,
      count: 0,
      scoreTotal: 0,
      recentDate: ''
    }
    current.count += 1
    current.scoreTotal += Number(plant.moodScore || 0)
    if (!current.recentDate || String(plant.createdAt || '') > current.recentDate) {
      current.recentDate = plant.createdAt || ''
    }
    groups.set(key, current)
  })

  const positions = [
    [plotWidth * 0.26, plotDepth * 0.64],
    [plotWidth * 0.72, plotDepth * 0.35],
    [plotWidth * 0.5, plotDepth * 0.78],
    [plotWidth * 0.18, plotDepth * 0.28],
    [plotWidth * 0.82, plotDepth * 0.72],
    [plotWidth * 0.52, plotDepth * 0.32]
  ]

  return [...groups.values()]
    .sort((a, b) => b.count - a.count || a.key.localeCompare(b.key))
    .slice(0, 6)
    .map((zone, index) => {
      const seed = hashStringToSeed(`${zone.key}:${zone.count}:${zone.recentDate}`)
      const [baseX, baseZ] = positions[index] || positions[positions.length - 1]
      return {
        ...zone,
        seed,
        avgScore: (Math.round((zone.scoreTotal / zone.count) * 10) / 10).toFixed(1),
        x: Math.round((baseX + jitter(seed, 0.35)) * 100) / 100,
        z: Math.round((baseZ + jitter(seed + 11, 0.3)) * 100) / 100,
        radius: Math.round((1.15 + Math.min(1.25, zone.count * 0.18)) * 100) / 100
      }
    })
}

export function buildGardenTimeLayers(plants) {
  const layers = {
    fresh: { key: 'fresh', label: '新鲜记忆', count: 0, description: '最近一周仍在发芽。' },
    settled: { key: 'settled', label: '沉淀记忆', count: 0, description: '一个月内逐渐变成花丛。' },
    archived: { key: 'archived', label: '旧日地貌', count: 0, description: '更早的记录沉入小径与石碑。' }
  }

  ;(plants || []).forEach((plant) => {
    const key = plant.timeLayer || 'fresh'
    if (layers[key]) layers[key].count += 1
  })

  return Object.values(layers)
}

export function buildGardenLandmarks(plants) {
  return (plants || [])
    .filter((plant) => {
      return plant.ageDays >= 30 || plant.memoryWeight >= 2.05 || plant.moodScore >= 82 || plant.moodScore <= 28
    })
    .slice(0, 8)
    .map((plant, index) => {
      let type = 'journal_bench'
      if (plant.ageDays >= 30) type = 'memory_stone'
      if (plant.moodScore >= 82) type = 'glowing_tree'
      if (plant.moodScore <= 28) type = 'quiet_pond'
      const seed = hashStringToSeed(`${plant.id}:${type}:${index}`)
      return {
        id: `${plant.id}-${type}`,
        type,
        sourceId: plant.id,
        title: plant.title,
        date: plant.createdAt,
        theme: plant.themeKey,
        moodScore: plant.moodScore,
        seed,
        x: Math.round((plant.x + jitter(seed, 0.65)) * 100) / 100,
        z: Math.round((plant.z + jitter(seed + 13, 0.55)) * 100) / 100
      }
    })
}

function buildGardenNarration(overview, climate, zones) {
  if (!overview.totalCount) return '第一粒种子落下后，这里会开始长出你的私人立体绘本。'
  const mainZone = zones[0]
  if (mainZone) {
    return `${climate.label}，${mainZone.label}正在成为花园里最清晰的一片地貌。`
  }
  return `${climate.label}，${overview.totalCount} 段记忆正在花园里慢慢安放。`
}

export function buildGardenWorld(items, options = {}) {
  const plants = createGardenPlants(items, options)
  const overview = buildGardenOverview(plants)
  const climate = buildGardenClimate(plants, overview)
  const zones = buildGardenZones(plants, options)
  const timeLayers = buildGardenTimeLayers(plants)
  const landmarks = buildGardenLandmarks(plants)

  return {
    plants,
    overview,
    climate,
    zones,
    timeLayers,
    landmarks,
    narration: buildGardenNarration(overview, climate, zones),
    anchorDate: overview.lastDate
  }
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
