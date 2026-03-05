import { ref, computed } from 'vue'

/**
 * useRoomState composable
 * Manages core room state: participants, clock, jobs, governments, etc.
 */
export function useRoomState() {
  // Core room data
  const roomname = ref('test')
  const roomOwnerId = ref(null)
  const clock = ref('')
  const participants = ref([])
  const roomGovernment = ref(null)

  // Collections
  const jobs = ref([])
  const governments = ref([])
  const defaultGovernments = [
    { id: 1, name: 'Democracy' },
    { id: 2, name: 'Republic' },
    { id: 3, name: 'Dictatorship' },
    { id: 4, name: 'Communism' },
    { id: 5, name: 'Anarchy' }
  ]

  // Filter active players (those not out of time)
  const activePlayers = computed(() => {
    const active = participants.value.filter(p => {
      if (!p || !p.clock) return true
      const isDead = String(p.clock).trim() === '00•00•00'
      return !isDead
    })

    // Sort: current user at top
    return active.sort((a, b) => {
      // Will be filled by parent with currentUserId
      return 0
    })
  })

  // Filter dropped players (those out of time)
  const droppedPlayers = computed(() => {
    const dropped = participants.value.filter(p => {
      if (!p || !p.clock) return false
      const isDead = String(p.clock).trim() === '00•00•00'
      return isDead
    })

    return dropped.sort((a, b) => {
      return 0
    })
  })

  // Normalize government label
  function govLabel(g) {
    return String(g?.name ?? g?.type ?? g?.label ?? '').trim()
  }

  // Display governments with consistent naming
  const displayGovernments = computed(() => {
    const list = governments.value?.length ? governments.value : defaultGovernments
    return list.map((g, idx) => ({
      id: g.id ?? g.value ?? idx + 1,
      name: govLabel(g) || 'Unnamed'
    }))
  })

  // Find government ID by name or type
  function findGovernmentIdByName(name) {
    if (!name) return null
    const target = String(name).toLowerCase()
    const g = governments.value.find(x => {
      const a = x?.name ? String(x.name).toLowerCase() : ''
      const b = x?.type ? String(x.type).toLowerCase() : ''
      return a === target || b === target
    })
    return g ? g.id ?? null : null
  }

  // Check if government is communist
  const isCommunist = computed(() => {
    const govType = roomGovernment.value?.type
    return govType && String(govType).toLowerCase() === 'communism'
  })

  return {
    // State
    roomname,
    roomOwnerId,
    clock,
    participants,
    roomGovernment,
    jobs,
    governments,
    defaultGovernments,

    // Computed
    activePlayers,
    droppedPlayers,
    displayGovernments,
    isCommunist,

    // Methods
    govLabel,
    findGovernmentIdByName
  }
}
