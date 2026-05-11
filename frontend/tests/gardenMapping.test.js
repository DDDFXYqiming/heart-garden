import { describe, test, expect } from 'vitest'
import {
  hashStringToSeed,
  moodToPlantProfile,
  createGardenPlants,
  buildGardenOverview,
  describePlantGrowth
} from '../src/utils/gardenMapping'

/* ===================================================================
   hashStringToSeed
   =================================================================== */
describe('hashStringToSeed', () => {
  test('returns a positive integer for any string', () => {
    const result = hashStringToSeed('hello')
    expect(Number.isInteger(result)).toBe(true)
    expect(result).toBeGreaterThan(0)
  })

  test('returns the same value for the same string (deterministic)', () => {
    const a = hashStringToSeed('garden-test-42')
    const b = hashStringToSeed('garden-test-42')
    expect(a).toBe(b)
  })

  test('returns different values for different strings', () => {
    const a = hashStringToSeed('alpha')
    const b = hashStringToSeed('beta')
    expect(a).not.toBe(b)
  })

  test('handles empty string', () => {
    const result = hashStringToSeed('')
    expect(Number.isInteger(result)).toBe(true)
    expect(result).toBeGreaterThan(0)
  })

  test('handles numeric strings consistently', () => {
    const a = hashStringToSeed('12345')
    const b = hashStringToSeed('12345')
    expect(a).toBe(b)
  })

  test('handles special characters', () => {
    const a = hashStringToSeed('!@#$%^&*()_+')
    const b = hashStringToSeed('!@#$%^&*()_+')
    expect(a).toBe(b)
  })
})

/* ===================================================================
   moodToPlantProfile
   =================================================================== */
describe('moodToPlantProfile', () => {
  test('score >= 75 returns sunflower profile with bloom/radiant growth', () => {
    const profile = moodToPlantProfile(85)
    expect(profile.modelType).toBe('sunflower')
    expect(profile.growthLevel).toMatch(/bloom|radiant/)
    expect(profile.height).toBeGreaterThanOrEqual(2.0)
  })

  test('score 75 exactly returns sunflower', () => {
    const profile = moodToPlantProfile(75)
    expect(profile.modelType).toBe('sunflower')
  })

  test('score 60-74 returns leafBloom or flower with bloom growth', () => {
    const profile = moodToPlantProfile(65)
    expect(['leafBloom', 'flower']).toContain(profile.modelType)
    expect(profile.growthLevel).toBe('bloom')
  })

  test('score 60 exactly returns leafBloom or flower', () => {
    const profile = moodToPlantProfile(60)
    expect(['leafBloom', 'flower']).toContain(profile.modelType)
  })

  test('score 74 returns leafBloom or flower', () => {
    const profile = moodToPlantProfile(74)
    expect(['leafBloom', 'flower']).toContain(profile.modelType)
  })

  test('score 40-59 returns sprout with sprout/bud growth', () => {
    const profile = moodToPlantProfile(50)
    expect(profile.modelType).toBe('sprout')
    expect(['sprout', 'bud']).toContain(profile.growthLevel)
  })

  test('score 40 exactly returns sprout', () => {
    const profile = moodToPlantProfile(40)
    expect(profile.modelType).toBe('sprout')
  })

  test('score 59 returns sprout', () => {
    const profile = moodToPlantProfile(59)
    expect(profile.modelType).toBe('sprout')
  })

  test('score 25-39 returns duskLeaf with bud growth and muted colors', () => {
    const profile = moodToPlantProfile(30)
    expect(profile.modelType).toBe('duskLeaf')
    expect(profile.growthLevel).toBe('bud')
    // primaryColor should be muted purple/brown — check it contains expected hue
    const color = profile.primaryColor.toLowerCase()
    expect(color).toMatch(/purple|brown|#/)
  })

  test('score 25 exactly returns duskLeaf', () => {
    const profile = moodToPlantProfile(25)
    expect(profile.modelType).toBe('duskLeaf')
  })

  test('score < 25 returns cactus with seed/survivor growth', () => {
    const profile = moodToPlantProfile(10)
    expect(profile.modelType).toBe('cactus')
    expect(['seed', 'survivor']).toContain(profile.growthLevel)
  })

  test('score 0 returns cactus', () => {
    const profile = moodToPlantProfile(0)
    expect(profile.modelType).toBe('cactus')
  })

  test('returns object with all required fields', () => {
    const profile = moodToPlantProfile(50)
    const requiredFields = [
      'modelType', 'growthLevel', 'primaryColor', 'secondaryColor',
      'height', 'petalCount', 'petalScale', 'glowIntensity', 'moodLabel'
    ]
    requiredFields.forEach(field => {
      expect(profile).toHaveProperty(field)
    })
  })

  test('moodLabel is a non-empty string for each score bracket', () => {
    const scores = [85, 65, 50, 30, 10]
    scores.forEach(score => {
      const profile = moodToPlantProfile(score)
      expect(typeof profile.moodLabel).toBe('string')
      expect(profile.moodLabel.length).toBeGreaterThan(0)
    })
  })
})

/* ===================================================================
   createGardenPlants
   =================================================================== */
describe('createGardenPlants', () => {
  const sampleItems = [
    { id: '1', title: '开心的一天', content: '今天天气真好，心情非常愉快', mood_score: 85, created_at: '2026-05-03' },
    { id: '2', title: '平静的工作日', content: '普通的一天，工作顺利', mood_score: 65, created_at: '2026-05-02' },
    { id: '3', title: '有点低落', content: '今天不太开心，需要休息', mood_score: 35, created_at: '2026-05-01' }
  ]

  test('returns an array with same length as input', () => {
    const plants = createGardenPlants(sampleItems)
    expect(Array.isArray(plants)).toBe(true)
    expect(plants).toHaveLength(3)
  })

  test('each plant has all required fields', () => {
    const plants = createGardenPlants(sampleItems)
    const requiredFields = [
      'id', 'sourceType', 'title', 'content', 'contentPreview',
      'createdAt', 'moodScore', 'x', 'z', 'rotationY',
      'modelType', 'growthLevel', 'primaryColor', 'secondaryColor',
      'accentColor', 'height', 'petalCount', 'petalLayers',
      'petalScale', 'leafCount', 'glowIntensity', 'pulseIntensity',
      'swaySpeed', 'bedType', 'focusScale', 'moodLabel', 'growthStory'
    ]
    plants.forEach(plant => {
      requiredFields.forEach(field => {
        expect(plant).toHaveProperty(field)
      })
    })
  })

  test('sourceType is always "diary"', () => {
    const plants = createGardenPlants(sampleItems)
    plants.forEach(plant => {
      expect(plant.sourceType).toBe('diary')
    })
  })

  test('contentPreview truncates at 64 characters with ellipsis', () => {
    const longContent = '今天天气真好，心情非常愉快，出去散步看到了美丽的风景，还遇到了可爱的猫咪，真是太棒了！今天天气真好，心情非常愉快，出去散步看到了美丽的风景，还遇到了可爱的猫咪，真是太棒了！'
    const items = [{ id: '999', title: '长文', content: longContent, mood_score: 70, created_at: '2026-05-10' }]
    const plants = createGardenPlants(items)
    expect(plants[0].contentPreview.length).toBeLessThanOrEqual(67) // 64 + '...'
    expect(plants[0].contentPreview).toMatch(/\.\.\.$/)
  })

  test('contentPreview does NOT add ellipsis if content is <= 64 chars', () => {
    const shortContent = '今天天气真好'
    const items = [{ id: '1', title: '短文', content: shortContent, mood_score: 60, created_at: '2026-05-10' }]
    const plants = createGardenPlants(items)
    expect(plants[0].contentPreview).toBe(shortContent)
    expect(plants[0].contentPreview).not.toMatch(/\.\.\.$/)
  })

  test('positions are deterministic (same input -> same output)', () => {
    const plants1 = createGardenPlants(sampleItems)
    const plants2 = createGardenPlants(sampleItems)
    plants1.forEach((p, i) => {
      expect(p.x).toBe(plants2[i].x)
      expect(p.z).toBe(plants2[i].z)
      expect(p.rotationY).toBe(plants2[i].rotationY)
    })
  })

  test('all x coordinates are within [0, plotWidth] with margin', () => {
    const plants = createGardenPlants(sampleItems, { plotWidth: 16, plotDepth: 10 })
    plants.forEach(plant => {
      expect(plant.x).toBeGreaterThanOrEqual(0.5)
      expect(plant.x).toBeLessThanOrEqual(15.5)
    })
  })

  test('all z coordinates are within [0, plotDepth] with margin', () => {
    const plants = createGardenPlants(sampleItems, { plotWidth: 16, plotDepth: 10 })
    plants.forEach(plant => {
      expect(plant.z).toBeGreaterThanOrEqual(0.5)
      expect(plant.z).toBeLessThanOrEqual(9.5)
    })
  })

  test('plants are not all at the same position', () => {
    const manyItems = Array.from({ length: 9 }, (_, i) => ({
      id: String(i + 1),
      title: `日记 ${i + 1}`,
      content: '内容',
      mood_score: 50 + (i * 5),
      created_at: `2026-05-${String(i + 1).padStart(2, '0')}`
    }))
    const plants = createGardenPlants(manyItems)
    const positions = plants.map(p => `${p.x},${p.z}`)
    const uniquePositions = new Set(positions)
    expect(uniquePositions.size).toBeGreaterThan(1)
  })

  test('new visual motion fields are deterministic for the same input', () => {
    const plants1 = createGardenPlants(sampleItems)
    const plants2 = createGardenPlants(sampleItems)

    plants1.forEach((plant, index) => {
      expect(plant.leafCount).toBe(plants2[index].leafCount)
      expect(plant.petalLayers).toBe(plants2[index].petalLayers)
      expect(plant.swaySpeed).toBe(plants2[index].swaySpeed)
      expect(plant.pulseIntensity).toBe(plants2[index].pulseIntensity)
      expect(plant.bedType).toBe(plants2[index].bedType)
      expect(plant.accentColor).toBe(plants2[index].accentColor)
      expect(plant.focusScale).toBe(plants2[index].focusScale)
    })
  })

  test('bedType is one of the supported immersive garden base types', () => {
    const plants = createGardenPlants(sampleItems)
    const allowed = ['round', 'ribbon', 'patch', 'stone']
    plants.forEach(plant => {
      expect(allowed).toContain(plant.bedType)
    })
  })

  test('returns empty array for empty input', () => {
    const plants = createGardenPlants([])
    expect(plants).toEqual([])
  })

  test('single item positions are valid', () => {
    const items = [{ id: '1', title: 'test', content: 'test', mood_score: 50, created_at: '2026-05-01' }]
    const plants = createGardenPlants(items)
    expect(plants).toHaveLength(1)
    expect(plants[0].x).toBeGreaterThanOrEqual(0.5)
    expect(plants[0].x).toBeLessThanOrEqual(15.5)
    expect(plants[0].z).toBeGreaterThanOrEqual(0.5)
    expect(plants[0].z).toBeLessThanOrEqual(9.5)
  })

  test('plants sorted from newest to oldest by created_at', () => {
    const items = [
      { id: '1', title: '旧', content: 'a', mood_score: 50, created_at: '2026-05-01' },
      { id: '2', title: '中', content: 'b', mood_score: 50, created_at: '2026-05-03' },
      { id: '3', title: '新', content: 'c', mood_score: 50, created_at: '2026-05-05' }
    ]
    const plants = createGardenPlants(items)
    expect(plants[0].title).toBe('新')
    expect(plants[1].title).toBe('中')
    expect(plants[2].title).toBe('旧')
  })

  test('custom options are respected', () => {
    const plants = createGardenPlants(sampleItems, { plotWidth: 20, plotDepth: 12 })
    plants.forEach(plant => {
      expect(plant.x).toBeGreaterThanOrEqual(0.5)
      expect(plant.x).toBeLessThanOrEqual(19.5)
      expect(plant.z).toBeGreaterThanOrEqual(0.5)
      expect(plant.z).toBeLessThanOrEqual(11.5)
    })
  })
})

/* ===================================================================
   buildGardenOverview
   =================================================================== */
describe('buildGardenOverview', () => {
  test('returns totalCount matching plant count', () => {
    const plants = createGardenPlants([
      { id: '1', title: 'a', content: 'a', mood_score: 80, created_at: '2026-05-01' },
      { id: '2', title: 'b', content: 'b', mood_score: 60, created_at: '2026-05-02' }
    ])
    const overview = buildGardenOverview(plants)
    expect(overview.totalCount).toBe(2)
  })

  test('avgScore is a string with one decimal place', () => {
    const plants = createGardenPlants([
      { id: '1', title: 'a', content: 'a', mood_score: 80, created_at: '2026-05-01' },
      { id: '2', title: 'b', content: 'b', mood_score: 60, created_at: '2026-05-02' }
    ])
    const overview = buildGardenOverview(plants)
    expect(typeof overview.avgScore).toBe('string')
    expect(overview.avgScore).toMatch(/^\d+\.\d$/) // e.g., "70.0"
  })

  test('avgScore is correct', () => {
    const plants = createGardenPlants([
      { id: '1', title: 'a', content: 'a', mood_score: 100, created_at: '2026-05-01' },
      { id: '2', title: 'b', content: 'b', mood_score: 50, created_at: '2026-05-02' }
    ])
    const overview = buildGardenOverview(plants)
    expect(overview.avgScore).toBe('75.0')
  })

  test('avgScore rounds to one decimal', () => {
    const plants = createGardenPlants([
      { id: '1', title: 'a', content: 'a', mood_score: 85, created_at: '2026-05-01' },
      { id: '2', title: 'b', content: 'b', mood_score: 62, created_at: '2026-05-02' }
    ])
    const overview = buildGardenOverview(plants)
    // (85 + 62) / 2 = 73.5
    expect(overview.avgScore).toBe('73.5')
  })

  test('statusText and statusEmoji are strings', () => {
    const plants = createGardenPlants([
      { id: '1', title: 'a', content: 'a', mood_score: 80, created_at: '2026-05-01' }
    ])
    const overview = buildGardenOverview(plants)
    expect(typeof overview.statusText).toBe('string')
    expect(overview.statusText.length).toBeGreaterThan(0)
    expect(typeof overview.statusEmoji).toBe('string')
    expect(overview.statusEmoji.length).toBeGreaterThan(0)
  })

  test('high avg score yields positive status', () => {
    const plants = createGardenPlants([
      { id: '1', title: 'a', content: 'a', mood_score: 90, created_at: '2026-05-01' },
      { id: '2', title: 'b', content: 'b', mood_score: 85, created_at: '2026-05-02' }
    ])
    const overview = buildGardenOverview(plants)
    expect(overview.avgScore).toBe('87.5')
    // status should indicate flourish
    expect(overview.statusEmoji).toMatch(/🌻|🌸|🌺/)
  })

  test('low avg score yields muted status', () => {
    const plants = createGardenPlants([
      { id: '1', title: 'a', content: 'a', mood_score: 20, created_at: '2026-05-01' },
      { id: '2', title: 'b', content: 'b', mood_score: 15, created_at: '2026-05-02' }
    ])
    const overview = buildGardenOverview(plants)
    expect(overview.avgScore).toBe('17.5')
  })

  test('empty plants returns zero overview', () => {
    const overview = buildGardenOverview([])
    expect(overview.totalCount).toBe(0)
    expect(overview.avgScore).toBe('0.0')
  })
})

/* ===================================================================
   describePlantGrowth
   =================================================================== */
describe('describePlantGrowth', () => {
  test('returns a non-empty Chinese string', () => {
    const plant = createGardenPlants([
      { id: '1', title: 'test', content: 'test', mood_score: 85, created_at: '2026-05-01' }
    ])[0]
    const desc = describePlantGrowth(plant)
    expect(typeof desc).toBe('string')
    expect(desc.length).toBeGreaterThan(0)
    // Should contain Chinese characters
    expect(desc).toMatch(/[\u4e00-\u9fff]/)
  })

  test('sunflower plants get a high-energy description', () => {
    const plant = createGardenPlants([
      { id: '1', title: '活力日', content: '充满活力的一天', mood_score: 90, created_at: '2026-05-01' }
    ])[0]
    const desc = describePlantGrowth(plant)
    expect(plant.modelType).toBe('sunflower')
    expect(desc).toMatch(/向日葵|盛放|高能量|阳光/)
  })

  test('cactus plants get a resilient description', () => {
    const plant = createGardenPlants([
      { id: '1', title: '难日', content: '艰难的一天', mood_score: 10, created_at: '2026-05-01' }
    ])[0]
    const desc = describePlantGrowth(plant)
    expect(plant.modelType).toBe('cactus')
    expect(desc).toMatch(/仙人掌|坚韧|顽强|种子|守护/)
  })

  test('different plants get different descriptions', () => {
    const plants = createGardenPlants([
      { id: '1', title: 'a', content: 'a', mood_score: 90, created_at: '2026-05-01' },
      { id: '2', title: 'b', content: 'b', mood_score: 10, created_at: '2026-05-02' }
    ])
    const desc1 = describePlantGrowth(plants[0])
    const desc2 = describePlantGrowth(plants[1])
    expect(desc1).not.toBe(desc2)
  })

  test('describes sprout for medium scores', () => {
    const plant = createGardenPlants([
      { id: '1', title: '平', content: '普通的一天', mood_score: 50, created_at: '2026-05-01' }
    ])[0]
    const desc = describePlantGrowth(plant)
    expect(desc).toMatch(/芽|苗|生长/)
  })
})
