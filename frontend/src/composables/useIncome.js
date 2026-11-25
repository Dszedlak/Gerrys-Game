import { useGovernment } from './useGovernment'

/**
 * useIncome composable
 * Single source of truth for per-turn income on the client.
 *
 * This mirrors the authoritative server calculation in
 * backend/app/websocket/sockets.py -> balanceChange().
 * Any rule added here must be added there too, or the displayed
 * income will drift from what "Get Paid" actually awards.
 */

const INCOME_PER_TIER = 10
const BLEED_PENALTY_PER_COUNTER = 10
const PERK_BONUS = { Manager: 10, Senior: 20, Executive: 30 }

const CHARITY_COMMISSIONER = 'Charity Commissioner'
const CHARITY_COMMISSIONER_PENALTY = -20

// Government cards (v4.27)
const COMMUNISM_POLITBURO_BONUS = 20
const COMMUNISM_PEASANT_PENALTY = -20
const DICTATOR_BONUS = 30
const HEAD_OF_STATE_BONUS = 20
const ADVISOR_BONUS = 10

/**
 * Resolve a participant's user id across the several shapes the
 * backend and the various socket events use.
 */
export function participantId(participant) {
  return Number(participant?.user_id ?? participant?.userId ?? participant?.id)
}

export function useIncome() {
  const { normalizeGovernment } = useGovernment()

  /**
   * Is any alive player holding the Charity Commissioner job?
   * Returns that player's id, or null.
   */
  function findCharityCommissioner(allPlayers = []) {
    const holder = allPlayers.find(p => p.job_name === CHARITY_COMMISSIONER)
    return holder ? participantId(holder) : null
  }

  /**
   * Build the full per-turn income breakdown for one player.
   *
   * @returns {{ lines: Array<{label: string, minutes: number}>, net: number }}
   */
  function computeIncomeBreakdown(player, { jobs = [], government = null, allPlayers = [] } = {}) {
    const lines = []
    if (!player) return { lines, net: 0 }

    const uid = participantId(player)

    // --- Job: tier * 10. Joined by name because that is what room_state carries.
    const job = jobs.find(j => j.name === player.job_name)
    const tier = job?.tier || 0
    const jobIncome = tier * INCOME_PER_TIER
    lines.push({
      label: `Job — ${player.job_name || 'Unemployed'}${tier ? ` (Tier ${tier})` : ''}`,
      minutes: jobIncome
    })

    // --- Title (stored as `perk`)
    const perkBonus = PERK_BONUS[player.perk] || 0
    if (perkBonus) {
      lines.push({ label: `Title — ${player.perk}`, minutes: perkBonus })
    }

    // --- Government
    const g = normalizeGovernment(government)
    const type = g.type ? g.type.toLowerCase() : null

    if (type === 'communism') {
      // Fall back to plain membership when roles are absent, matching
      // the same tolerance used for government icons.
      const isPolitburo = g.politburo.has(uid) || (g.politburo.size === 0 && g.members.has(uid))
      lines.push({
        label: `Government — Communism (${isPolitburo ? 'politburo' : 'peasant'})`,
        minutes: isPolitburo ? COMMUNISM_POLITBURO_BONUS : COMMUNISM_PEASANT_PENALTY
      })
    } else if (type === 'dictatorship' && g.dictator === uid) {
      lines.push({ label: 'Government — Dictatorship (dictator)', minutes: DICTATOR_BONUS })
    } else if (type === 'republic' && g.head_of_state === uid) {
      lines.push({ label: 'Government — Republic (head of state)', minutes: HEAD_OF_STATE_BONUS })
    } else if (type === 'republic' && g.advisors.has(uid)) {
      lines.push({ label: 'Government — Republic (advisor)', minutes: ADVISOR_BONUS })
    }

    // --- Charity Commissioner: -20 to every player except the Commissioner.
    const commissionerId = findCharityCommissioner(allPlayers)
    if (commissionerId !== null && commissionerId !== uid) {
      lines.push({
        label: `${CHARITY_COMMISSIONER} in game`,
        minutes: CHARITY_COMMISSIONER_PENALTY
      })
    }

    // --- Bleed
    const bleed = player.bleed || 0
    if (bleed) {
      lines.push({ label: `Bleed ×${bleed}`, minutes: -(bleed * BLEED_PENALTY_PER_COUNTER) })
    }

    const net = lines.reduce((sum, l) => sum + l.minutes, 0)
    return { lines, net }
  }

  /**
   * Format a signed minute total as +HH:MM / -HH:MM
   */
  function formatMinutes(total) {
    const sign = total >= 0 ? '+' : '-'
    const abs = Math.abs(total)
    const h = String(Math.floor(abs / 60)).padStart(2, '0')
    const m = String(abs % 60).padStart(2, '0')
    return `${sign}${h}:${m}`
  }

  /**
   * Compact signed form for a single breakdown row, e.g. "+30 min" / "-20 min"
   */
  function formatSignedMinutes(minutes) {
    return `${minutes >= 0 ? '+' : '-'}${Math.abs(minutes)} min`
  }

  return {
    computeIncomeBreakdown,
    findCharityCommissioner,
    formatMinutes,
    formatSignedMinutes
  }
}
