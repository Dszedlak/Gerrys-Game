/**
 * Pure layout and presentation helpers for the board view.
 *
 * The rules (movement, turn order, purchases) live on the server in
 * backend/app/websocket/board_rules.py. This file only decides where things
 * are drawn and how they are described.
 *
 * The track is 20 tiles around a 6×6 grid, clockwise from Start in the
 * bottom-left corner:
 *
 *    5  6  7  8  9 10        Job Centre ......... Senate
 *    4              11
 *    3              12
 *    2              13
 *    1              14
 *    0 19 18 17 16 15        Start ............. Hospital
 */

export const BOARD_SIZE = 20
export const JAIL = -1

/**
 * Relative sizes of the grid's six columns (and rows). The outer ring is a
 * little deeper than it is wide so tile labels have room to breathe.
 * Both the CSS grid and the pawn coordinates are derived from this.
 */
export const TRACK = [1.3, 1, 1, 1, 1, 1.3]
const TRACK_TOTAL = TRACK.reduce((a, b) => a + b, 0)
const TRACK_EDGES = TRACK.reduce((edges, w) => [...edges, edges[edges.length - 1] + w], [0])

export const GRID_TEMPLATE = TRACK.map(f => `${f}fr`).join(' ')

/** Inset of the centre panel, as a percentage of the board. */
export const CENTER_INSET = (TRACK[0] / TRACK_TOTAL) * 100

function wrap(index) {
  return ((index % BOARD_SIZE) + BOARD_SIZE) % BOARD_SIZE
}

/** Grid cell for a tile: { row, col }, both 0-5. */
export function tileGridPosition(index) {
  const i = wrap(index)
  if (i <= 5) return { row: 5 - i, col: 0 }
  if (i <= 10) return { row: 0, col: i - 5 }
  if (i <= 15) return { row: i - 10, col: 5 }
  return { row: 5, col: 5 - (i - 15) }
}

/** Which side of the board a tile sits on. */
export function tileSide(index) {
  const i = wrap(index)
  if (i % 5 === 0) return 'corner'
  if (i < 5) return 'left'
  if (i < 10) return 'top'
  if (i < 15) return 'right'
  return 'bottom'
}

/** Centre of a tile as { x, y } percentages of the board. */
export function tileCenter(index) {
  const { row, col } = tileGridPosition(index)
  return {
    x: ((TRACK_EDGES[col] + TRACK_EDGES[col + 1]) / 2 / TRACK_TOTAL) * 100,
    y: ((TRACK_EDGES[row] + TRACK_EDGES[row + 1]) / 2 / TRACK_TOTAL) * 100
  }
}

/**
 * Offsets, in board percent, for `count` pawns sharing one tile so they
 * cluster in a tidy grid instead of stacking on top of each other.
 */
export function pawnOffsets(count, spacing = 3.1) {
  if (count <= 0) return []
  const cols = Math.ceil(Math.sqrt(count))
  const rows = Math.ceil(count / cols)
  const out = []
  for (let i = 0; i < count; i++) {
    const r = Math.floor(i / cols)
    // Centre a short last row
    const inRow = r === rows - 1 ? count - r * cols : cols
    const c = i - r * cols
    out.push({
      dx: (c - (inRow - 1) / 2) * spacing,
      dy: (r - (rows - 1) / 2) * spacing * 0.9
    })
  }
  return out
}

export const PAWN_COLORS = {
  red: '#EF4444',
  blue: '#3B82F6',
  green: '#22C55E',
  yellow: '#FACC15',
  purple: '#A855F7',
  orange: '#F97316',
  teal: '#14B8A6',
  pink: '#EC4899',
  white: '#E5E7EB',
  black: '#4B5563'
}

export function pawnColor(name) {
  return PAWN_COLORS[name] || '#94A3B8'
}

// ---------------------------------------------------------------------------
// The Reaper's counter
// ---------------------------------------------------------------------------

export const HORSEMEN = [
  { name: 'Pestilence', upper: 25, color: '#84CC16' },
  { name: 'War', upper: 50, color: '#EF4444' },
  { name: 'Famine', upper: 75, color: '#F59E0B' },
  { name: 'Death', upper: 100, color: '#A78BFA' }
]

export function horsemanFor(counter) {
  if (!counter || counter <= 0) return null
  return HORSEMEN.find(h => counter <= h.upper) || HORSEMEN[HORSEMEN.length - 1]
}

// ---------------------------------------------------------------------------
// Tiles
// ---------------------------------------------------------------------------

/** Icon and colour family per tile kind. */
export const TILE_THEME = {
  start: { icon: '🏁', tone: 'start' },
  collectables: { icon: '🎴', tone: 'collectables' },
  assignment: { icon: '📜', tone: 'assignment' },
  scenario: { icon: '🃏', tone: 'scenario' },
  promotion: { icon: '⬆️', tone: 'job' },
  job_centre: { icon: '💼', tone: 'job' },
  time_virus: { icon: '🦠', tone: 'virus' },
  senate: { icon: '🏛️', tone: 'senate' },
  senate_virus: { icon: '🦠', tone: 'senate' },
  hospital: { icon: '🏥', tone: 'hospital' },
  go_to_job_centre: { icon: '↪️', tone: 'jump' },
  black_market: { icon: '🕶️', tone: 'market' }
}

export function tileTheme(kind) {
  return TILE_THEME[kind] || { icon: '▫️', tone: 'plain' }
}

/** What happens when you land on a tile, in plain words. */
export function tileDescription(tile, { doctorInPlay = false } = {}) {
  if (!tile) return ''
  const hospitalCost = doctorInPlay ? '60 minutes (doubled: a Doctor is in play)' : '30 minutes'
  switch (tile.kind) {
    case 'start':
      return 'Landing on or passing Start removes 1 heat. This is applied automatically.'
    case 'collectables':
      return 'A free collectable is dealt straight into your hand. Buy as many more as you like for 1 hour each (you might buy some for other players), plus one Promotion card for 2 hours. By the end of your turn you must be back within your hand limit.'
    case 'assignment':
      return 'An Assignment Slip is drawn onto the assignment board and its target is pulled from the black bag, for everyone to see.'
    case 'scenario':
      return 'The top Scenario card is drawn for everyone to see, and the game carries out what it says. You can discard it and draw another.'
    case 'promotion':
      return 'A Promotion card and a Job Opportunity are dealt straight into your hand.'
    case 'job_centre':
      return 'A Job Opportunity is dealt straight into your hand: take an available Tier 1 job (resign first if you are employed).'
    case 'time_virus':
      return 'Nominate any alive player. Roll the die: they lose 30 minutes per pip (1 = 30 min … 6 = 3 hours).'
    case 'senate':
      return 'Receive a Shortcut card. Change your own vote for free, and take one Senate action per visit: change another player\'s vote (1 hour), or — if you\'re in a government that uses oppressions — introduce a government oppression (2 hours).'
    case 'senate_virus':
      return 'Senate tile: receive a Shortcut card and take one Senate action. You also get to release the Time Virus on a player of your choice.'
    case 'hospital':
      return `A free hospital item (bandage) is dealt straight into your hand. You can buy up to 5 more for ${hospitalCost} each.`
    case 'go_to_job_centre':
      return 'Jump straight to the Job Centre. You have passed Start (−1 heat).'
    case 'black_market':
      return 'Spend 2.5 hours to buy any one used collectable of your choice from the discard pile.'
    default:
      return ''
  }
}

/** The sub-label shown on the tile itself, adjusted for live rules. */
export function tileSubLabel(tile, { doctorInPlay = false } = {}) {
  if (!tile) return ''
  if (tile.kind === 'hospital' && tile.sub) {
    return doctorInPlay ? '60 min per item' : tile.sub
  }
  return tile.sub || ''
}

// ---------------------------------------------------------------------------
// Governments
// ---------------------------------------------------------------------------

/** The government card shown beside the board. Mirrors Help.vue / the rules. */
export const GOVERNMENT_CARDS = {
  Democracy: {
    icon: '🗳️',
    summary: 'The starting government. There are no leaders. Every alive player holds an approval vote, changed at the Senate; when most reject, a vote on a new government follows.'
  },
  Republic: {
    image: '/republic.png',
    summary: 'The Head of State is elected by popular vote and chooses two advisors. Oppressions may only target enemies of the state (agreed by the Head of State and at least one advisor), one per state enemy per turn. Any title promotion needs an extra completed assignment slip.'
  },
  Dictatorship: {
    image: '/dictator.png',
    summary: 'The dictator is chosen by a one-vote blind auction and makes every decision, with up to three oppressions per turn. The dictator earns +10 minutes per turn. Jail costs 12 hours.'
  },
  Communism: {
    image: '/communism.png',
    summary: 'Two politburo members are chosen at random. Each earns +10 minutes per turn, and every peasant pays 20 minutes per turn to the state.'
  },
  Anarchy: {
    icon: '🏴',
    summary: 'No leaders and no government income effects.'
  }
}

export function governmentCard(type) {
  return GOVERNMENT_CARDS[type] || { icon: '🏛️', summary: '' }
}

/** Jail fee in hours: 8, or 12 under a Dictatorship (matches getOutOfJail). */
export function jailFeeHours(governmentType) {
  return governmentType === 'Dictatorship' ? 12 : 8
}

/** Jail at 3 heat, or 4 for a Senior or Executive. Mirrors board_rules.heat_threshold. */
export function heatThreshold(perk) {
  return perk === 'Senior' || perk === 'Executive' ? 4 : 3
}

// ---------------------------------------------------------------------------
// Formatting
// ---------------------------------------------------------------------------

/** "1h 30m", "45m", "2h". */
export function formatDuration(minutes) {
  const m = Math.abs(Math.round(minutes))
  const h = Math.floor(m / 60)
  const rest = m % 60
  if (h && rest) return `${h}h ${rest}m`
  if (h) return `${h}h`
  return `${rest}m`
}

/** H:MM:SS countdown. */
export function formatCountdown(ms) {
  const total = Math.max(0, Math.floor(ms / 1000))
  const h = Math.floor(total / 3600)
  const m = Math.floor((total % 3600) / 60)
  const s = total % 60
  return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

/** Parse a DD•HH•MM clock into minutes. */
export function clockToMinutes(clock) {
  const digits = String(clock || '').replace(/[^0-9]/g, '')
  if (digits.length < 6) return 0
  return Number(digits.slice(0, 2)) * 1440 + Number(digits.slice(2, 4)) * 60 + Number(digits.slice(4, 6))
}

/** Log entries newer than `lastSeq` that should be shouted to the room. */
export function newAnnouncements(log, lastSeq) {
  if (lastSeq === null || lastSeq === undefined) return []
  return (log || []).filter(e => e.seq > lastSeq && e.announce)
}

// ---------------------------------------------------------------------------
// Cards and timing
// ---------------------------------------------------------------------------

export const DECK_META = {
  scenario: { icon: '🃏', label: 'Scenario', color: '#8B5CF6' },
  assignment: { icon: '📜', label: 'Assignment Slip', color: '#F97316' },
  collectable: { icon: '🎴', label: 'Collectable', color: '#14B8A6' },
  job: { icon: '💼', label: 'Job Opportunity', color: '#EC4899' },
  promotion: { icon: '⬆️', label: 'Promotion', color: '#3B82F6' },
  hospital: { icon: '🩹', label: 'Hospital item', color: '#EAB308' },
  shortcut: { icon: '↪️', label: 'Shortcut', color: '#6366F1' },
  oppression: { icon: '⛓️', label: 'Government oppression', color: '#DC2626' }
}

// The Democracy card: "All purchases are double in price."
export function purchaseMultiplier(governmentType) {
  return String(governmentType || '').toLowerCase() === 'democracy' ? 2 : 1
}

/** 90 -> "1.5h", 60 -> "1h", 30 -> "30m" */
export function formatPrice(minutes) {
  if (minutes < 60) return `${minutes}m`
  const h = minutes / 60
  return `${Number.isInteger(h) ? h : h.toFixed(1).replace(/\.0$/, '')}h`
}

/** What landing on the tile dealt into your hand, in words ('' if nothing). */
export function dealtSummary(turn) {
  const items = turn?.dealt || []
  if (!items.length) return ''
  return `${items.map(i => `1 ${i}`).join(' + ')} added to your hand`
}

// Up to 5 collectables (or 5 hospital items) bought per visit
export const PURCHASE_LIMIT = 5

// Tiles with something to do once you're on them: these open the action pop-up
export const ACTION_TILE_KINDS = ['collectables', 'hospital', 'senate', 'senate_virus', 'black_market', 'time_virus', 'scenario']

// Hand cards that count towards the hand limit ("5 collectables in hand")
export const HAND_LIMIT_DECKS = ['collectable', 'job', 'promotion']

// How long the die tumbles, and each hop of the pawn after it.
export const DIE_SETTLE_MS = 1050
export const STEP_MS = 270
const JUMP_MS = 850

/** How long a roll takes to play out on the board, so a card can wait for the pawn. */
export function moveDurationMs(roll, { settle = DIE_SETTLE_MS, step = STEP_MS } = {}) {
  if (!roll) return 0
  if (roll.kind === 'card_move') return 150 + (roll.path?.length || 0) * step
  if (roll.kind !== 'move') return settle
  const jump = roll.jumped_from !== null && roll.jumped_from !== undefined ? JUMP_MS : 0
  return settle + (roll.path?.length || 0) * step + jump
}
