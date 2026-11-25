/**
 * Tests for the board view's pure helpers (components/board/boardLayout.js)
 * and the useBoard composable's socket wiring.
 *
 * The rules themselves are tested server-side in
 * backend/tests/test_board_rules.py.
 */

import { describe, it, expect, jest } from '@jest/globals'
import {
  BOARD_SIZE,
  TRACK,
  CENTER_INSET,
  tileGridPosition,
  tileSide,
  tileCenter,
  pawnOffsets,
  horsemanFor,
  tileDescription,
  tileSubLabel,
  formatDuration,
  formatCountdown,
  clockToMinutes,
  newAnnouncements,
  jailFeeHours,
  heatThreshold,
  pawnColor,
  moveDurationMs,
  DIE_SETTLE_MS,
  STEP_MS
} from '@/components/board/boardLayout'
import { useBoard } from '@/composables/useBoard'

describe('board layout - the track', () => {
  it('walks the perimeter of a 6x6 grid without repeating a cell', () => {
    const cells = new Set()
    for (let i = 0; i < BOARD_SIZE; i++) {
      const { row, col } = tileGridPosition(i)
      expect(row === 0 || row === 5 || col === 0 || col === 5).toBe(true)
      cells.add(`${row},${col}`)
    }
    expect(cells.size).toBe(BOARD_SIZE)
  })

  it('puts the corners where the physical board has them', () => {
    expect(tileGridPosition(0)).toEqual({ row: 5, col: 0 }) // Start, bottom-left
    expect(tileGridPosition(5)).toEqual({ row: 0, col: 0 }) // Job Centre, top-left
    expect(tileGridPosition(10)).toEqual({ row: 0, col: 5 }) // Senate, top-right
    expect(tileGridPosition(15)).toEqual({ row: 5, col: 5 }) // Hospital, bottom-right
  })

  it('moves clockwise: each step is to an adjacent cell', () => {
    for (let i = 0; i < BOARD_SIZE; i++) {
      const a = tileGridPosition(i)
      const b = tileGridPosition(i + 1)
      expect(Math.abs(a.row - b.row) + Math.abs(a.col - b.col)).toBe(1)
    }
  })

  it('names sides', () => {
    expect(tileSide(0)).toBe('corner')
    expect(tileSide(3)).toBe('left')
    expect(tileSide(7)).toBe('top')
    expect(tileSide(12)).toBe('right')
    expect(tileSide(18)).toBe('bottom')
  })

  it('places tile centres inside the board and the outer ring', () => {
    for (let i = 0; i < BOARD_SIZE; i++) {
      const { x, y } = tileCenter(i)
      expect(x).toBeGreaterThan(0)
      expect(x).toBeLessThan(100)
      const onRing = x < CENTER_INSET || x > 100 - CENTER_INSET || y < CENTER_INSET || y > 100 - CENTER_INSET
      expect(onRing).toBe(true)
    }
    // Symmetry: Start and Hospital mirror each other
    expect(tileCenter(0).x + tileCenter(15).x).toBeCloseTo(100)
  })

  it('derives the centre inset from the track', () => {
    const total = TRACK.reduce((a, b) => a + b, 0)
    expect(CENTER_INSET).toBeCloseTo((TRACK[0] / total) * 100)
  })
})

describe('board layout - pawns', () => {
  it('gives each pawn on a tile its own spot', () => {
    for (let n = 1; n <= 10; n++) {
      const offsets = pawnOffsets(n)
      expect(offsets).toHaveLength(n)
      const keys = new Set(offsets.map(o => `${o.dx.toFixed(2)},${o.dy.toFixed(2)}`))
      expect(keys.size).toBe(n)
    }
    expect(pawnOffsets(1)).toEqual([{ dx: 0, dy: 0 }])
    expect(pawnOffsets(0)).toEqual([])
  })

  it('keeps a cluster centred on the tile', () => {
    const offsets = pawnOffsets(4)
    const meanX = offsets.reduce((a, o) => a + o.dx, 0) / offsets.length
    const meanY = offsets.reduce((a, o) => a + o.dy, 0) / offsets.length
    expect(meanX).toBeCloseTo(0)
    expect(meanY).toBeCloseTo(0)
  })

  it('falls back to a neutral colour', () => {
    expect(pawnColor('red')).toMatch(/^#/)
    expect(pawnColor('nope')).toBe('#94A3B8')
  })
})

describe('board layout - the Reaper', () => {
  it('maps the counter to the four horsemen', () => {
    expect(horsemanFor(0)).toBeNull()
    expect(horsemanFor(1).name).toBe('Pestilence')
    expect(horsemanFor(25).name).toBe('Pestilence')
    expect(horsemanFor(26).name).toBe('War')
    expect(horsemanFor(51).name).toBe('Famine')
    expect(horsemanFor(76).name).toBe('Death')
    expect(horsemanFor(140).name).toBe('Death')
  })
})

describe('board layout - text', () => {
  it('describes every tile kind', () => {
    const kinds = ['start', 'collectables', 'assignment', 'scenario', 'promotion', 'job_centre',
      'time_virus', 'senate', 'senate_virus', 'hospital', 'go_to_job_centre', 'black_market']
    kinds.forEach(kind => expect(tileDescription({ kind }).length).toBeGreaterThan(10))
  })

  it('doubles the hospital price when a Doctor is in play', () => {
    const hospital = { kind: 'hospital', sub: '30 min per item' }
    expect(tileSubLabel(hospital)).toBe('30 min per item')
    expect(tileSubLabel(hospital, { doctorInPlay: true })).toBe('60 min per item')
    expect(tileDescription(hospital, { doctorInPlay: true })).toContain('60 minutes')
  })

  it('formats durations and countdowns', () => {
    expect(formatDuration(90)).toBe('1h 30m')
    expect(formatDuration(120)).toBe('2h')
    expect(formatDuration(-45)).toBe('45m')
    expect(formatCountdown(2 * 3600 * 1000)).toBe('2:00:00')
    expect(formatCountdown(61 * 1000)).toBe('0:01:01')
    expect(formatCountdown(-5)).toBe('0:00:00')
  })

  it('reads DD•HH•MM clocks', () => {
    expect(clockToMinutes('01•00•00')).toBe(1440)
    expect(clockToMinutes('00•22•30')).toBe(1350)
    expect(clockToMinutes('')).toBe(0)
  })

  it('matches the server on jail fee and heat threshold', () => {
    expect(jailFeeHours('Democracy')).toBe(8)
    expect(jailFeeHours('Dictatorship')).toBe(12)
    expect(heatThreshold(null)).toBe(3)
    expect(heatThreshold('Manager')).toBe(3)
    expect(heatThreshold('Senior')).toBe(4)
    expect(heatThreshold('Executive')).toBe(4)
  })
})

describe('announcements', () => {
  const log = [
    { seq: 1, text: 'a', announce: true },
    { seq: 2, text: 'b', announce: false },
    { seq: 3, text: 'c', announce: true }
  ]

  it('never replays the backlog on first load', () => {
    expect(newAnnouncements(log, null)).toEqual([])
  })

  it('returns only new, announced entries', () => {
    expect(newAnnouncements(log, 1).map(e => e.text)).toEqual(['c'])
    expect(newAnnouncements(log, 3)).toEqual([])
  })
})

describe('useBoard', () => {
  function fakeSocket() {
    const handlers = {}
    return {
      handlers,
      on: jest.fn((event, fn) => { handlers[event] = fn }),
      emit: jest.fn()
    }
  }

  it('stores the latest board state and announces only new entries', () => {
    const socket = fakeSocket()
    const onAnnounce = jest.fn()
    const board = useBoard(socket, { onAnnounce })

    socket.handlers.boardState({ seq: 2, log: [{ seq: 2, text: 'old', announce: true }], server_now: new Date().toISOString() })
    expect(board.state.value.seq).toBe(2)
    expect(onAnnounce).not.toHaveBeenCalled()

    socket.handlers.boardState({
      seq: 4,
      log: [
        { seq: 2, text: 'old', announce: true },
        { seq: 3, text: 'quiet', announce: false },
        { seq: 4, text: 'virus!', announce: true }
      ]
    })
    expect(onAnnounce).toHaveBeenCalledTimes(1)
    expect(onAnnounce.mock.calls[0][0].text).toBe('virus!')
  })

  it('tracks the server clock offset', () => {
    const socket = fakeSocket()
    const board = useBoard(socket)
    const ahead = new Date(Date.now() + 60_000).toISOString()
    socket.handlers.boardState({ seq: 0, log: [], server_now: ahead })
    expect(board.serverOffsetMs.value).toBeGreaterThan(55_000)
  })

  it('sends actions as JSON payloads', () => {
    const socket = fakeSocket()
    const board = useBoard(socket)
    board.roll()
    expect(socket.emit).toHaveBeenLastCalledWith('boardRoll')
    board.purchase('hospital')
    expect(socket.emit).toHaveBeenLastCalledWith('boardPurchase', JSON.stringify({ kind: 'hospital' }))
    board.timeVirus(7)
    expect(socket.emit).toHaveBeenLastCalledWith('boardTimeVirus', JSON.stringify({ target_user_id: 7 }))
    board.moveToken(3, 12)
    expect(socket.emit).toHaveBeenLastCalledWith('boardMoveToken', JSON.stringify({ user_id: 3, tile: 12 }))
    board.goToJail()
    expect(socket.emit).toHaveBeenLastCalledWith('boardGoToJail', JSON.stringify({}))
  })

  it('keeps my private hand from boardHand', () => {
    const socket = fakeSocket()
    const board = useBoard(socket)
    expect(board.hand.value).toEqual([])
    socket.handlers.boardHand({ hand: [{ uid: 'a#1', title: 'Coffee' }] })
    expect(board.hand.value.map(c => c.title)).toEqual(['Coffee'])
    socket.handlers.boardHand({})
    expect(board.hand.value).toEqual([])
  })

  it('sends card actions', () => {
    const socket = fakeSocket()
    const board = useBoard(socket)
    board.playCard('a#1', 4)
    expect(socket.emit).toHaveBeenLastCalledWith('boardPlayCard', JSON.stringify({ card: 'a#1', target_user_id: 4 }))
    board.claimAssignment(9)
    expect(socket.emit).toHaveBeenLastCalledWith('boardClaimAssignment', JSON.stringify({ assignment_id: 9, target_user_id: null }))
    board.replaceAssignment(null)
    expect(socket.emit).toHaveBeenLastCalledWith('boardResolveCard', JSON.stringify({ replace: null }))
    board.chooseCardTarget(2)
    expect(socket.emit).toHaveBeenLastCalledWith('boardResolveCard', JSON.stringify({ target_user_id: 2 }))
  })
})

describe('card timing', () => {
  it('waits for the die and every hop before showing a card', () => {
    expect(moveDurationMs(null)).toBe(0)
    expect(moveDurationMs({ kind: 'virus' })).toBe(DIE_SETTLE_MS)
    expect(moveDurationMs({ kind: 'move', path: [1, 2, 3], jumped_from: null })).toBe(DIE_SETTLE_MS + 3 * STEP_MS)
    expect(moveDurationMs({ kind: 'move', path: [16, 17], jumped_from: 17 })).toBeGreaterThan(DIE_SETTLE_MS + 2 * STEP_MS)
  })
})

describe('purchase prices', () => {
  it('doubles under Democracy and formats as hours/minutes', async () => {
    const { purchaseMultiplier, formatPrice } = await import('@/components/board/boardLayout')
    expect(purchaseMultiplier('Democracy')).toBe(2)
    expect(purchaseMultiplier('Republic')).toBe(1)
    expect(formatPrice(60 * purchaseMultiplier('Democracy'))).toBe('2h')
    expect(formatPrice(150)).toBe('2.5h')
    expect(formatPrice(300)).toBe('5h')
    expect(formatPrice(30)).toBe('30m')
  })
})
