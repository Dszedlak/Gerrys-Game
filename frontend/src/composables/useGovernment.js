/**
 * useGovernment composable
 * Handles government roles, icons, and role assignment logic
 */
export function useGovernment() {
  /**
   * Normalize government payload from backend into role-based sets
   * Handles multiple payload formats from different backend versions
   */
  function normalizeGovernment(g) {
    const out = {
      type: g?.type ? String(g.type) : null,
      dictator: null,
      head_of_state: null,
      advisors: new Set(),
      politburo: new Set(),
      members: new Set()
    }
    if (!g) return out

    // Common flat fields
    out.dictator = g.leader_id ?? g.leaderId ?? g.dictator_id ?? g.dictatorId ?? null
    out.head_of_state = g.head_of_state_id ?? g.headOfStateId ?? null

    // Generic member ids
    const mIds = g.member_ids ?? g.memberUserIds
    if (Array.isArray(mIds)) mIds.forEach(id => out.members.add(Number(id)))

    // roles map object variants
    const rolesMap = g.roles ?? g.roleMap ?? g.membersByRole
    if (rolesMap) {
      if (rolesMap.dictator != null) out.dictator = Number(rolesMap.dictator)
      const hs = rolesMap.head_of_state ?? rolesMap.headOfState
      if (hs != null) out.head_of_state = Number(hs)
      const adv = rolesMap.advisors ?? rolesMap.advisor ?? []
      ;(Array.isArray(adv) ? adv : [adv]).forEach(id => out.advisors.add(Number(id)))
      const pb = rolesMap.politburo ?? []
      ;(Array.isArray(pb) ? pb : [pb]).forEach(id => out.politburo.add(Number(id)))
    }

    // members array of objects/numbers
    if (Array.isArray(g.members)) {
      for (const m of g.members) {
        if (m && typeof m === 'object') {
          const uid = Number(m.user_id ?? m.userId ?? m.id)
          const role = String(m.role ?? '').toLowerCase()
          if (!Number.isNaN(uid)) {
            out.members.add(uid)
            if (role === 'dictator') out.dictator = uid
            else if (role === 'head_of_state' || role === 'headofstate') out.head_of_state = uid
            else if (role === 'advisor') out.advisors.add(uid)
            else if (role === 'politburo') out.politburo.add(uid)
          }
        } else if (typeof m === 'number' || typeof m === 'string') {
          out.members.add(Number(m))
        }
      }
    }

    return out
  }

  /**
   * Return the correct icon for a participant based on government type + role
   */
  function getGovernmentIconForParticipant(participant, government) {
    const g = normalizeGovernment(government)
    if (!g.type) return null

    const type = g.type.toLowerCase()
    const uid = Number(participant.user_id ?? participant.userId ?? participant.id)

    if (type === 'dictatorship') {
      // Only the dictator gets an icon
      return g.dictator === uid ? '/dictator.png' : null
    }

    if (type === 'republic') {
      // Head of state has its own icon; advisors use republic.png
      if (g.head_of_state === uid) return '/headOfState.png'
      if (g.advisors.has(uid)) return '/republic.png'
      // Fallback: if no roles provided but member flagged, show republic icon
      if (g.members.has(uid)) return '/republic.png'
      return null
    }

    if (type === 'communism') {
      // Politburo members get icon
      if (g.politburo.has(uid)) return '/communism.png'
      // Fallback: if only generic members are provided, treat as politburo for icon
      if (g.members.has(uid) && g.politburo.size === 0) return '/communism.png'
      return null
    }

    // No icons for Democracy/Anarchy/unknown
    return null
  }

  /**
   * Get perk icon URL for a participant
   */
  function getPerkIconForParticipant(participant) {
    const perk = participant.perk
    if (!perk) return null

    if (perk === 'Manager') return '/manager.png'
    if (perk === 'Senior') return '/senior.png'
    if (perk === 'Executive') return '/executive.png'

    return null
  }

  return {
    normalizeGovernment,
    getGovernmentIconForParticipant,
    getPerkIconForParticipant
  }
}
