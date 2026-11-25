/**
 * Component tests for the board's live pop-ups: the big dice roll every
 * player sees, and the card reveal that waits for the pawn to finish moving.
 */
import { describe, it, expect, jest, beforeEach, afterEach } from '@jest/globals'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import GameBoard from '@/components/board/GameBoard.vue'
import CardReveal from '@/components/board/CardReveal.vue'
import { DIE_SETTLE_MS, STEP_MS } from '@/components/board/boardLayout'

const TILES = Array.from({ length: 20 }, (_, index) => ({ index, kind: index === 3 ? 'scenario' : 'collectables', label: `Tile ${index}`, sub: '' }))
const players = [
  { user_id: 1, username: 'Ann', color: '#EF4444', alive: true, jailed: false },
  { user_id: 2, username: 'Bob', color: '#3B82F6', alive: true, jailed: false }
]

function boardState(extra = {}) {
  return {
    started: true,
    tiles: TILES,
    round: 1,
    turn: { user_id: 1, rolled: false },
    positions: { 1: 0, 2: 0 },
    reaper: { counter: 0 },
    last_roll: null,
    ...extra
  }
}

beforeEach(() => {
  try {
    window.localStorage.setItem('gg.collapsed.assignments.v2', '0')
    window.localStorage.setItem('gg.collapsed.oppressions.v2', '0')
  } catch (e) { /* ignore */ }
  jest.useFakeTimers()
  window.matchMedia = window.matchMedia || (() => ({ matches: false, addListener () {}, removeListener () {} }))
  window.requestAnimationFrame = (fn) => setTimeout(fn, 0)
  window.cancelAnimationFrame = (id) => clearTimeout(id)
})
afterEach(() => { jest.useRealTimers() })

describe('GameBoard big roll', () => {
  it('shows a new roll to everyone, then clears', async () => {
    const wrapper = mount(GameBoard, { props: { state: boardState(), players, myUserId: 2 } })
    expect(wrapper.find('.dice-stage').exists()).toBe(false)

    const roll = { id: 1, kind: 'move', user_id: 1, values: [3], path: [1, 2, 3], from: 0, to: 3, jumped_from: null }
    await wrapper.setProps({ state: boardState({ last_roll: roll, positions: { 1: 3, 2: 0 }, turn: { user_id: 1, rolled: true } }) })
    await nextTick()
    const stage = wrapper.find('.dice-stage')
    expect(stage.exists()).toBe(true)
    expect(stage.text()).toContain('Ann rolls')
    expect(stage.text()).toContain('3 → Tile 3')

    jest.advanceTimersByTime(DIE_SETTLE_MS + 1200)
    await nextTick()
    expect(wrapper.find('.dice-stage').exists()).toBe(false)
  })

  it('does not replay the last roll when you join mid-game', async () => {
    const roll = { id: 4, kind: 'move', user_id: 1, values: [2], path: [1, 2], from: 0, to: 2 }
    const wrapper = mount(GameBoard, { props: { state: boardState({ last_roll: roll }), players, myUserId: 2 } })
    await nextTick()
    expect(wrapper.find('.dice-stage').exists()).toBe(false)
  })

  it('lets the current player click the die to roll', async () => {
    const wrapper = mount(GameBoard, { props: { state: boardState(), players, myUserId: 1, canRoll: true } })
    await wrapper.find('.dice-tray').trigger('click')
    expect(wrapper.emitted('roll')).toHaveLength(1)
  })
})

describe('CardReveal', () => {
  const board = { chooseCardTarget: jest.fn(), replaceAssignment: jest.fn() }
  const byId = { 1: { ...players[0] }, 2: { ...players[1] } }
  const card = { deck: 'scenario', title: 'Tax Audit', text: 'Everyone loses 30 minutes.' }

  it('waits for the pawn to finish moving before showing a card drawn by a roll', async () => {
    const lastRoll = { id: 9, kind: 'move', user_id: 1, values: [3], path: [1, 2, 3], to: 3 }
    const wrapper = mount(CardReveal, { props: { reveal: null, lastRoll, playersById: byId, myUserId: 2, board } })
    await wrapper.setProps({ reveal: { id: 1, deck: 'scenario', action: 'drawn', user_id: 1, card, lines: ['Ann −30m'], after_roll: 9 } })

    jest.advanceTimersByTime(DIE_SETTLE_MS + 3 * STEP_MS)
    await nextTick()
    expect(wrapper.find('.reveal').exists()).toBe(false)

    jest.advanceTimersByTime(300)
    await nextTick()
    expect(wrapper.find('.reveal').exists()).toBe(true)
    expect(wrapper.text()).toContain('Ann drew a Scenario card')
    expect(wrapper.text()).toContain('Tax Audit')
    expect(wrapper.text()).toContain('Ann −30m')
  })

  it('asks only the drawer to choose a target', async () => {
    const pending = { kind: 'choose_target', deck: 'scenario', user_id: 1 }
    const reveal = { id: 2, deck: 'scenario', action: 'drawn', user_id: 1, card, pending: true, lines: [] }

    const drawer = mount(CardReveal, { props: { reveal: null, pending, playersById: byId, myUserId: 1, board } })
    await drawer.setProps({ reveal })
    jest.advanceTimersByTime(10)
    await nextTick()
    const choice = drawer.findAll('.reveal__choice')
    expect(choice.map(b => b.text())).toEqual(['Bob'])
    await choice[0].trigger('click')
    expect(board.chooseCardTarget).toHaveBeenCalledWith(2)

    const watcher = mount(CardReveal, { props: { reveal: null, pending, playersById: byId, myUserId: 2, board } })
    await watcher.setProps({ reveal })
    jest.advanceTimersByTime(10)
    await nextTick()
    expect(watcher.findAll('.reveal__choice')).toHaveLength(0)
    expect(watcher.text()).toContain('Waiting for Ann')
  })
})

describe('SpinWheel synced spin', () => {
  it('plays the server spin and lands on the server winner', async () => {
    const SpinWheel = (await import('@/components/SpinWheel.vue')).default
    const entries = [{ user_id: 1, username: 'Ann' }, { user_id: 2, username: 'Bob' }, { user_id: 3, username: 'Cat' }]
    const wrapper = mount(SpinWheel, {
      props: { participants: entries, inline: true, synced: true, showSpinButton: false },
      global: { stubs: { 'b-button': true, 'b-modal': true } }
    })
    const done = wrapper.vm.playSpin({ entries, winner_index: 1, rotation: 2000, duration_ms: 5000, by: 'Ann' })
    await jest.advanceTimersByTimeAsync(50)
    await done
    await nextTick()
    expect(wrapper.find('svg').attributes('style')).toContain('rotate(2000deg)')
    expect(wrapper.text()).not.toContain('Winner')
    await jest.advanceTimersByTimeAsync(5000)
    await nextTick()
    expect(wrapper.text()).toContain('Winner: Bob')
  })
})

describe('DiscardPile', () => {
  const discards = {
    collectable: [{ uid: 'k#1', deck: 'collectable', title: 'Knife', text: '' }, { uid: 'c#1', deck: 'collectable', title: 'Coffee', text: '' }],
    scenario: [{ uid: 's#1', deck: 'scenario', title: 'Tax Audit', text: '' }],
    assignment: []
  }

  async function mountPile(props) {
    const DiscardPile = (await import('@/components/board/DiscardPile.vue')).default
    const board = { takeFromDiscard: jest.fn(), purchase: jest.fn() }
    const wrapper = mount(DiscardPile, { props: { open: true, board, discards, players: [{ user_id: 2, username: 'Bob' }], ...props } })
    return { wrapper, board }
  }

  it('lets a player with a pick take any card', async () => {
    const { wrapper, board } = await mountPile({ myPicks: 1 })
    expect(wrapper.text()).toContain('You may take 1 card')
    const take = wrapper.findAll('button').filter(b => b.text() === 'Take')
    expect(take).toHaveLength(2)
    await take[1].trigger('click')
    expect(board.takeFromDiscard).toHaveBeenCalledWith('c#1')
  })

  it('sells any used card at the Black Market', async () => {
    const { wrapper, board } = await mountPile({ canBuy: true })
    const buy = wrapper.findAll('button').filter(b => b.text().startsWith('Buy'))
    await buy[0].trigger('click')
    expect(board.purchase).toHaveBeenCalledWith('black_market', 'k#1')
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('shows other discard piles read-only, and lets the admin hand cards out', async () => {
    const { wrapper, board } = await mountPile({ isAdmin: true })
    expect(wrapper.findAll('button').some(b => b.text() === 'Take' || b.text().startsWith('Buy'))).toBe(false)
    await wrapper.find('select').setValue(2)
    await wrapper.findAll('button').find(b => b.text() === 'Give').trigger('click')
    expect(board.takeFromDiscard).toHaveBeenCalledWith('k#1', 2)
    await wrapper.findAll('[role="tab"]')[1].trigger('click')
    expect(wrapper.text()).toContain('Tax Audit')
    expect(wrapper.find('select').exists()).toBe(false)
  })
})

describe('BoardLobby', () => {
  const players = [{ user_id: 1, username: 'Ann', color: '#f00' }, { user_id: 2, username: 'Bob', color: '#00f' }]

  async function mountLobby(props) {
    const BoardLobby = (await import('@/components/board/BoardLobby.vue')).default
    const board = { setReady: jest.fn(), start: jest.fn() }
    const wrapper = mount(BoardLobby, { props: { board, players, myUserId: 1, hostId: 1, ...props } })
    return { wrapper, board }
  }

  it('lets you ready up and shows who is ready', async () => {
    const { wrapper, board } = await mountLobby({ state: { ready: { 2: true } } })
    expect(wrapper.text()).toContain('1 of 2 ready')
    await wrapper.findAll('button').find(b => b.text().includes("I'm ready")).trigger('click')
    expect(board.setReady).toHaveBeenCalledWith(true)
  })

  it('only lets the host start once everyone is ready, or force start', async () => {
    window.confirm = jest.fn(() => true)
    const notReady = await mountLobby({ isAdmin: true, state: { ready: { 1: true } } })
    const start = notReady.wrapper.findAll('button').find(b => b.text().includes('Start game'))
    expect(start.attributes('disabled')).toBeDefined()
    await notReady.wrapper.findAll('button').find(b => b.text().includes('Force start')).trigger('click')
    expect(window.confirm.mock.calls[0][0]).toContain('Bob')
    expect(notReady.board.start).toHaveBeenCalledWith(true)

    const allReady = await mountLobby({ isAdmin: true, state: { ready: { 1: true, 2: true } } })
    expect(allReady.wrapper.text()).toContain("Everyone's ready")
    await allReady.wrapper.findAll('button').find(b => b.text().includes('Start game')).trigger('click')
    expect(allReady.board.start).toHaveBeenCalledWith()
    expect(allReady.wrapper.findAll('button').some(b => b.text().includes('Force start'))).toBe(false)
  })

  it('has no start buttons for other players', async () => {
    const { wrapper } = await mountLobby({ isAdmin: false, myUserId: 2, state: { ready: {} } })
    expect(wrapper.findAll('.lobby__actions button').map(b => b.text())).toEqual(["✓ I'm ready"])
  })
})

describe('HandLimitModal', () => {
  const card = (uid, deck = 'collectable') => ({ uid, deck, title: uid, text: '' })

  async function mountModal(hand, handLimit) {
    const HandLimitModal = (await import('@/components/board/HandLimitModal.vue')).default
    const board = { discardCard: jest.fn(), giveCard: jest.fn(), endTurn: jest.fn() }
    const wrapper = mount(HandLimitModal, {
      props: { open: true, board, hand, handLimit, others: [{ user_id: 2, username: 'Bob' }] }
    })
    return { wrapper, board }
  }

  it('asks for the extra cards and blocks ending the turn until you are at the limit', async () => {
    const hand = [card('a'), card('b'), card('c'), card('bandage#1', 'hospital')]
    const { wrapper, board } = await mountModal(hand, 3)
    expect(wrapper.text()).toContain('give away 1 more card')
    expect(wrapper.text()).toContain('4/3')
    expect(wrapper.text()).toContain('bandage#1') // every card in the hand counts, hospital items too
    const end = wrapper.findAll('button').find(b => b.text().includes('more to go'))
    expect(end.attributes('disabled')).toBeDefined()

    await wrapper.findAll('button').filter(b => b.text() === 'Discard')[0].trigger('click')
    expect(board.discardCard).toHaveBeenCalledWith('a')
    await wrapper.findAll('select')[1].setValue(2)
    await wrapper.findAll('button').filter(b => b.text() === 'Give')[1].trigger('click')
    expect(board.giveCard).toHaveBeenCalledWith('b', 2)

    // The server sends back the smaller hand
    await wrapper.setProps({ hand: [card('b'), card('c'), card('bandage#1', 'hospital')] })
    const ready = wrapper.findAll('button').find(b => b.text().includes('End turn'))
    expect(ready.attributes('disabled')).toBeUndefined()
    await ready.trigger('click')
    expect(board.endTurn).toHaveBeenCalled()
    expect(wrapper.emitted('close')).toBeTruthy()
  })
})

describe('OppressionBoard', () => {
  const playersById = {
    1: { user_id: 1, username: 'Ann', alive: true, color: '#f00' },
    2: { user_id: 2, username: 'Bob', alive: true, color: '#0f0' },
    3: { user_id: 3, username: 'Cat', alive: true, color: '#00f' }
  }
  const opp = (id, extra = {}) => ({ id, card: { title: `Opp ${id}`, text: 'Steal 20 minutes.' }, new: false, ...extra })

  async function mountBoard(props) {
    const OppressionBoard = (await import('@/components/board/OppressionBoard.vue')).default
    const board = { useOppression: jest.fn(), removeOppression: jest.fn() }
    const wrapper = mount(OppressionBoard, { props: { board, playersById, myUserId: 1, turnSeq: 5, ...props } })
    return { wrapper, board }
  }

  it('says there are none under Democracy', async () => {
    const { wrapper } = await mountBoard({ governmentType: 'Democracy' })
    expect(wrapper.text()).toContain('No government oppressions under Democracy')
  })

  it('lets the dictator use an oppression on their turn, but not a new or used one', async () => {
    const { wrapper, board } = await mountBoard({
      governmentType: 'Dictatorship',
      leaders: { dictator: 1 },
      isMyTurn: true,
      oppressions: [opp(1), opp(2, { new: true }), opp(3)],
      uses: { turn_seq: 5, by: { 1: 1 }, cards: [3], pairs: [] }
    })
    expect(wrapper.text()).toContain('As Dictator you can use 3 oppressions a turn · 2 left this turn')
    const useButtons = wrapper.findAll('button').filter(b => b.text() === 'Use…')
    expect(useButtons).toHaveLength(1)     // #2 is new, #3 already used
    await useButtons[0].trigger('click')
    await wrapper.findAll('button').find(b => b.text().includes('Cat')).trigger('click')
    expect(board.useOppression).toHaveBeenCalledWith(1, 3)
  })

  it('only offers enemies of the state under the Republic, and nothing to non-leaders', async () => {
    const { wrapper } = await mountBoard({
      governmentType: 'Republic', leaders: { head_of_state: 1 }, isMyTurn: true,
      oppressions: [opp(1)], stateEnemies: [{ user_id: 2, username: 'Bob' }]
    })
    await wrapper.findAll('button').find(b => b.text() === 'Use…').trigger('click')
    const names = wrapper.findAll('.opp__picker button').map(b => b.text())
    expect(names).toEqual(['Bob'])

    const peasant = await mountBoard({ governmentType: 'Dictatorship', leaders: { dictator: 2 }, isMyTurn: true, oppressions: [opp(1)] })
    expect(peasant.wrapper.findAll('button').some(b => b.text() === 'Use…')).toBe(false)
  })
})

describe('InitiativeModal', () => {
  const playersById = {
    1: { user_id: 1, username: 'Ann', color: '#f00' },
    2: { user_id: 2, username: 'Bob', color: '#0f0' },
    3: { user_id: 3, username: 'Cat', color: '#00f' }
  }
  const initiative = (extra = {}) => ({
    round: 1, order: [2, 1, 3], current: 1, rolls: { 2: 4 }, first_rolls: { 2: 4 }, history: [], done: false, ...extra
  })

  async function mountModal(props) {
    const InitiativeModal = (await import('@/components/board/InitiativeModal.vue')).default
    const board = { initiativeRoll: jest.fn(), initiativeRollCurrent: jest.fn() }
    const wrapper = mount(InitiativeModal, { props: { board, playersById, phase: 'initiative', ...props } })
    return { wrapper, board }
  }

  it('gives the current roller the Roll button and tells everyone else whose turn it is', async () => {
    const me = await mountModal({ myUserId: 1, state: { initiative: initiative() } })
    const roll = me.wrapper.findAll('button').find(b => b.text().includes('Your turn: roll'))
    await roll.trigger('click')
    expect(me.board.initiativeRoll).toHaveBeenCalled()

    const other = await mountModal({ myUserId: 3, isAdmin: true, state: { initiative: initiative() } })
    expect(other.wrapper.text()).toContain("Ann's turn to roll")
    expect(other.wrapper.findAll('button').some(b => b.text().includes('Your turn'))).toBe(false)
    await other.wrapper.findAll('button').find(b => b.text() === 'Roll for Ann').trigger('click')
    expect(other.board.initiativeRollCurrent).toHaveBeenCalled()
  })

  it('turns a tie for the top into a roll battle', async () => {
    const { wrapper } = await mountModal({
      myUserId: 3,
      state: { initiative: initiative({
        round: 2, order: [3, 1], current: 0, rolls: {}, first_rolls: { 1: 6, 2: 2, 3: 6 },
        history: [{ round: 1, order: [2, 1, 3], rolls: { 1: 6, 2: 2, 3: 6 } }]
      }) }
    })
    expect(wrapper.text()).toContain('Roll battle!')
    expect(wrapper.text()).toContain('Cat and Ann tied on 6')
    expect(wrapper.text()).toContain('Your turn: roll!')
  })

  it('announces who starts once the roll is over', async () => {
    const { wrapper } = await mountModal({ myUserId: 3, state: { initiative: initiative() } })
    await wrapper.setProps({
      phase: 'playing',
      state: { initiative: initiative({ done: true, winner: 1, winning_roll: 6 }), turn_order: [1, 3, 2] }
    })
    jest.advanceTimersByTime(3000)
    await nextTick()
    expect(wrapper.text()).toContain('Ann starts!')
    expect(wrapper.text()).toContain('Highest roll: 6')
    jest.advanceTimersByTime(7000)
    await nextTick()
    expect(wrapper.find('.init-modal').exists()).toBe(false)
  })

  it('does not pop up for someone joining after the game started', async () => {
    const { wrapper } = await mountModal({ myUserId: 3, phase: 'playing', state: { initiative: initiative({ done: true, winner: 1 }) } })
    expect(wrapper.find('.init-modal').exists()).toBe(false)
  })
})

describe('TileAction (step 3 pop-up)', () => {
  const playersById = { 1: { user_id: 1, username: 'Ann', alive: true }, 2: { user_id: 2, username: 'Bob', alive: true } }
  async function mountTile(kind, turn = {}) {
    const TileAction = (await import('@/components/board/TileAction.vue')).default
    const board = { purchase: jest.fn(), drawScenario: jest.fn(), redrawScenario: jest.fn() }
    const tiles = [{ index: 0, kind, label: 'The tile' }]
    const state = { tiles, positions: { 1: 0 }, turn: { user_id: 1, rolled: true, purchases: {}, ...turn }, decks: {} }
    const wrapper = mount(TileAction, { props: { board, state, playersById, myUserId: 1 } })
    return { wrapper, board }
  }

  it('buys as many collectables as you like in one go', async () => {
    const { wrapper, board } = await mountTile('collectables', { purchases: { collectable: 7 } })
    const plus = wrapper.find('[aria-label="One more"]')
    for (let i = 0; i < 7; i++) await plus.trigger('click')
    expect(wrapper.find('.shop__qty-n').text()).toBe('8') // already bought 7: no limit
    expect(plus.attributes('disabled')).toBeUndefined()
    const buy = wrapper.findAll('.shop__buy')[0]
    expect(buy.text()).toBe('Buy 8 · 8h')
    await buy.trigger('click')
    expect(board.purchase).toHaveBeenCalledWith('collectable', null, 8)
  })

  it('buys several hospital items too', async () => {
    const { wrapper, board } = await mountTile('hospital')
    await wrapper.find('[aria-label="One more"]').trigger('click')
    await wrapper.find('.shop__buy').trigger('click')
    expect(board.purchase).toHaveBeenCalledWith('hospital', null, 2)
  })

  it('lets you discard the scenario card you landed on and draw another', async () => {
    const { wrapper, board } = await mountTile('scenario', { scenario: 'sc#1' })
    window.confirm = jest.fn(() => true)
    await wrapper.findAll('button').find(b => b.text().includes('draw another')).trigger('click')
    expect(board.redrawScenario).toHaveBeenCalled()
  })
})

describe('ActionPopup', () => {
  async function mountPopup(turn = {}, extra = {}) {
    const ActionPopup = (await import('@/components/board/ActionPopup.vue')).default
    const state = { tiles: [{ index: 0, kind: 'scenario', label: 'Scenario' }], positions: { 1: 0 }, turn: { user_id: 1, rolled: true, ...turn } }
    return mount(ActionPopup, { props: { open: true, board: {}, state, myUserId: 1, ...extra } })
  }

  it('has no End turn button; its tab says what is still to do', async () => {
    const wrapper = await mountPopup({}, {
      minimised: true,
      state: {
        tiles: [{ index: 0, kind: 'scenario', label: 'Scenario' }], positions: { 1: 0 },
        turn: { user_id: 1, rolled: true, scenario: 'x#1' }, pending: { user_id: 1, kind: 'choose_target' }
      }
    })
    expect(wrapper.find('.action-tab').text()).toContain('Your card needs a decision')
    await wrapper.setProps({ minimised: false })
    expect(wrapper.findAll('button').some(b => b.text().includes('End turn'))).toBe(false)
  })

  it('minimises to a tab that brings it back', async () => {
    const wrapper = await mountPopup({ scenario: 'x#1' })
    await wrapper.findAll('button').find(b => b.text() === 'Minimise').trigger('click')
    expect(wrapper.emitted('minimise')).toHaveLength(1)
    await wrapper.setProps({ minimised: true })
    expect(wrapper.find('.action__panel').exists()).toBe(false)
    await wrapper.find('.action-tab').trigger('click')
    expect(wrapper.emitted('restore')).toHaveLength(1)
  })
})

describe('TurnBanner', () => {
  const playersById = { 1: { user_id: 1, username: 'Ann', color: '#f00' }, 2: { user_id: 2, username: 'Bob', color: '#0f0' } }
  it("darkens the screen with whose turn it is when the turn passes on, not on joining", async () => {
    const TurnBanner = (await import('@/components/board/TurnBanner.vue')).default
    const wrapper = mount(TurnBanner, {
      props: { phase: 'playing', playersById, myUserId: 2, state: { round: 1, turn_seq: 1, turn: { user_id: 1 } } }
    })
    expect(wrapper.find('.banner').exists()).toBe(false)
    await wrapper.setProps({ state: { round: 1, turn_seq: 2, turn: { user_id: 2 } } })
    expect(wrapper.find('.banner').text()).toContain('Your turn!')
    jest.advanceTimersByTime(2300); await nextTick()
    expect(wrapper.find('.banner').exists()).toBe(false)
    await wrapper.setProps({ state: { round: 2, turn_seq: 3, turn: { user_id: 1 } } })
    expect(wrapper.find('.banner').text()).toContain("Ann's turn")
  })
})

describe('GameBoard piles', () => {
  it('both piles open their menus (not the last card played)', async () => {
    const wrapper = mount(GameBoard, {
      props: { state: boardState({ turn: { user_id: 1, rolled: true } }), players, myUserId: 1, canBuyCollectable: true }
    })
    await wrapper.find('.deck--scenario').trigger('click')
    await wrapper.find('.deck--collectable').trigger('click')
    expect(wrapper.emitted('open-scenario-deck')).toHaveLength(1)
    expect(wrapper.emitted('open-collectable-deck')).toHaveLength(1)
    expect(wrapper.emitted('open-card')).toBeUndefined()
    expect(wrapper.find('.deck--collectable').text()).toContain('Buy')
  })
})

describe('DeckMenu', () => {
  const playersById = { 1: { user_id: 1, username: 'Ann' }, 2: { user_id: 2, username: 'Bob' } }
  const state = (extra = {}) => ({
    started: true,
    turn: { user_id: 1 },
    decks: { scenario: { draw: 20, discard: 3 }, collectable: { draw: 40, discard: 2 } },
    ...extra
  })
  async function mountMenu(props) {
    const DeckMenu = (await import('@/components/board/DeckMenu.vue')).default
    const board = { drawScenario: jest.fn(), shuffleDeck: jest.fn(), purchase: jest.fn() }
    const wrapper = mount(DeckMenu, { props: { open: true, board, playersById, ...props } })
    const btn = (text) => wrapper.findAll('button').find(b => b.text().includes(text))
    return { wrapper, board, btn }
  }

  it('scenario: the current player can draw & play, shuffle, and see the played cards', async () => {
    window.confirm = jest.fn(() => true)
    const { wrapper, board, btn } = await mountMenu({ deck: 'scenario', myUserId: 1, state: state() })
    expect(wrapper.text()).toContain('20 in the deck · 3 played')
    await btn('Draw & play').trigger('click')
    expect(board.drawScenario).toHaveBeenCalled()
    await btn('Shuffle').trigger('click')
    expect(board.shuffleDeck).toHaveBeenCalledWith('scenario')
    await btn('See the played').trigger('click')
    expect(wrapper.emitted('show-discards')).toHaveLength(1)
  })

  it('scenario: no drawing on another turn or mid-card (the admin can draw)', async () => {
    const other = await mountMenu({ deck: 'scenario', myUserId: 2, state: state() })
    expect(other.btn('Draw & play').attributes('disabled')).toBeDefined()
    expect(other.btn('Shuffle').attributes('disabled')).toBeDefined()
    expect(other.wrapper.text()).toContain('Only Ann can draw')
    const admin = await mountMenu({ deck: 'scenario', myUserId: 2, isAdmin: true, state: state() })
    expect(admin.btn('Draw & play').attributes('disabled')).toBeUndefined()
    const busy = await mountMenu({ deck: 'scenario', myUserId: 1, state: state({ event: { title: 'Mafia', done: false } }) })
    expect(busy.btn('Draw & play').attributes('disabled')).toBeDefined()
    await busy.btn('Show “Mafia”').trigger('click')
    expect(busy.wrapper.emitted('show-event')).toHaveLength(1)
  })

  it('collectables: buy any number, shuffle, and the Black Market pile', async () => {
    window.confirm = jest.fn(() => true)
    const { wrapper, board, btn } = await mountMenu({ deck: 'collectable', myUserId: 1, state: state(), canBuy: true, unitMinutes: 120 })
    const plus = wrapper.find('[aria-label="One more"]')
    for (let i = 0; i < 6; i++) await plus.trigger('click')
    await btn('Buy 7').trigger('click')
    expect(board.purchase).toHaveBeenCalledWith('collectable', null, 7)
    expect(wrapper.emitted('close')).toBeTruthy()
    await btn('Shuffle').trigger('click')
    expect(board.shuffleDeck).toHaveBeenCalledWith('collectable')
    await btn('See the discard pile').trigger('click')
    expect(wrapper.emitted('show-discards')).toHaveLength(1)

    const away = await mountMenu({ deck: 'collectable', myUserId: 1, state: state(), canBuy: false })
    expect(away.wrapper.text()).toContain('Land on a Collectables tile')
  })
})

describe('ScenarioEvent (a card in play for everyone)', () => {
  const playersById = {
    1: { user_id: 1, username: 'Ann', color: '#f00' },
    2: { user_id: 2, username: 'Bob', color: '#0f0' },
    3: { user_id: 3, username: 'Cat', color: '#00f' }
  }
  const event = (prompt, extra = {}) => ({
    id: 5,
    title: 'Secret Police',
    drawer: 1,
    done: false,
    lines: [{ text: 'Ann rolled 4 — failed', tone: 'bad' }],
    card: { uid: 'x#1', title: 'Secret Police', text: 'Roll 5+', deck: 'scenario' },
    roll: null,
    prompt,
    ...extra
  })
  async function mountEvent(props) {
    const ScenarioEvent = (await import('@/components/board/ScenarioEvent.vue')).default
    const board = { eventAnswer: jest.fn(), eventSkip: jest.fn(), redrawScenario: jest.fn() }
    const wrapper = mount(ScenarioEvent, { props: { board, playersById, ...props } })
    jest.advanceTimersByTime(10)
    await nextTick()
    const btn = (text) => wrapper.findAll('button').find(b => b.text().includes(text))
    return { wrapper, board, btn }
  }
  const rollFor = (uid) => ({ id: 9, kind: 'roll', user_id: uid, label: 'Secret Police', hint: 'needs 4+ · 1 charm: −1' })

  it('shows everyone the card; only the roller gets the Roll button', async () => {
    const roller = await mountEvent({ myUserId: 2, event: event(rollFor(2)) })
    expect(roller.wrapper.text()).toContain('Ann rolled 4')
    expect(roller.wrapper.text()).toContain('needs 4+')
    await roller.btn('Roll the die').trigger('click')
    expect(roller.board.eventAnswer).toHaveBeenCalledWith(9, true)

    const watcher = await mountEvent({ myUserId: 3, event: event(rollFor(2)) })
    expect(watcher.btn('Roll the die')).toBeUndefined()
    expect(watcher.wrapper.text()).toContain('Waiting for Bob to roll')

    const admin = await mountEvent({ myUserId: 3, isAdmin: true, event: event(rollFor(2)) })
    await admin.btn('Roll for Bob').trigger('click')
    expect(admin.board.eventAnswer).toHaveBeenCalledWith(9, true)
  })

  it('minimises to a tab, and pops back up when it is your go', async () => {
    const { wrapper, btn } = await mountEvent({ myUserId: 3, event: event(rollFor(2)) })
    await btn('Minimise').trigger('click')
    expect(wrapper.find('.sev__panel').exists()).toBe(false)
    expect(wrapper.find('.sev-tab').text()).toContain('waiting for Bob')
    await wrapper.setProps({ event: event({ ...rollFor(3), id: 10 }) })
    await nextTick()
    expect(wrapper.find('.sev__panel').exists()).toBe(true)
  })

  it('votes are cast by each voter; picks need confirming', async () => {
    const vote = {
      id: 11, kind: 'vote', voters: [1, 2, 3], voted: [1], exclude_self: true, anonymous: true, question: 'Who loses time?',
      options: [{ key: '1', label: 'Ann' }, { key: '2', label: 'Bob' }, { key: '3', label: 'Cat' }]
    }
    const bob = await mountEvent({ myUserId: 2, event: event(vote) })
    expect(bob.btn('Bob')).toBeUndefined() // no voting for yourself
    await bob.btn('Cat').trigger('click')
    expect(bob.board.eventAnswer).toHaveBeenCalledWith(11, '3')
    expect(bob.wrapper.text()).toContain('1 of 3 voted')

    const pick = {
      id: 12, kind: 'pick', user_id: 2, question: 'Who to search?', min: 0, max: 2,
      options: [{ key: '1', label: 'Ann' }, { key: '3', label: 'Cat' }]
    }
    const judge = await mountEvent({ myUserId: 2, event: event(pick) })
    await judge.btn('Ann').trigger('click')
    await judge.btn('Cat').trigger('click')
    await judge.btn('Confirm (2)').trigger('click')
    expect(judge.board.eventAnswer).toHaveBeenCalledWith(12, ['1', '3'])
  })

  it('choose cards from your own hand', async () => {
    const prompt = { id: 13, kind: 'cards', user_id: 2, count: 2, candidates: ['a#1', 'b#1', 'c#1'], question: 'Discard two' }
    const hand = [{ uid: 'a#1', title: 'Knife' }, { uid: 'b#1', title: 'Snitch' }, { uid: 'c#1', title: 'Advance' }]
    const { btn, board } = await mountEvent({ myUserId: 2, event: event(prompt), hand })
    await btn('Knife').trigger('click')
    await btn('Advance').trigger('click')
    await btn('Confirm').trigger('click')
    expect(board.eventAnswer).toHaveBeenCalledWith(13, ['a#1', 'c#1'])
  })
})

describe('OngoingCards', () => {
  it('shows your RNLI bill as due this turn, and lets anyone donate towards Income Tax', async () => {
    const OngoingCards = (await import('@/components/board/OngoingCards.vue')).default
    window.confirm = jest.fn(() => true)
    const board = { payDebt: jest.fn(), donateTax: jest.fn() }
    const state = {
      started: true,
      turn_seq: 4,
      turn: { user_id: 2 },
      debts: { 2: { title: 'RNLI', minutes: 450, paid_seq: 3 } },
      income_tax: { title: 'Income Tax', donated: 120, goal: 1440 },
      bounty: { title: 'Bounty Board', left: 2 }
    }
    const wrapper = mount(OngoingCards, { props: { board, state, myUserId: 2, playersById: { 2: { username: 'Bob' } } } })
    expect(wrapper.text()).toContain('You owe')
    expect(wrapper.text()).toContain('Bounty Board')
    expect(wrapper.text()).toContain('Due this turn')
    await wrapper.findAll('.ongoing__btn:not(.ongoing__btn--plan)').find(b => b.text() === '1h').trigger('click')
    expect(board.donateTax).toHaveBeenCalledWith(60)
  })
})

describe('InitiativeModal die', () => {
  const playersById = { 1: { user_id: 1, username: 'Ann', color: '#f00' }, 2: { user_id: 2, username: 'Bob', color: '#0f0' } }
  const initiative = { round: 1, order: [1, 2], current: 1, rolls: {}, first_rolls: {}, history: [], done: false }
  async function mountModal(state) {
    const InitiativeModal = (await import('@/components/board/InitiativeModal.vue')).default
    const BoardDie = (await import('@/components/board/BoardDie.vue')).default
    const wrapper = mount(InitiativeModal, {
      props: { board: { initiativeRoll: jest.fn() }, playersById, phase: 'initiative', myUserId: 2, state }
    })
    return { wrapper, die: () => wrapper.findComponent(BoardDie) }
  }

  it('animates the very first roll (the player who goes first)', async () => {
    const { wrapper, die } = await mountModal({ initiative })
    await wrapper.setProps({
      state: { initiative: { ...initiative, rolls: { 1: 5 } }, last_roll: { id: 1, kind: 'initiative', user_id: 1, values: [5] } }
    })
    await nextTick()
    expect(die().props('animate')).toBe(true)
  })

  it("doesn't replay a roll already made when you join late", async () => {
    const { die } = await mountModal({
      initiative,
      server_now: '2026-11-23T10:00:30Z',
      last_roll: { id: 3, kind: 'initiative', user_id: 1, values: [4], at: '2026-11-23T10:00:00Z' }
    })
    expect(die().props('animate')).toBe(false)
  })

  it('animates a roll that has only just been made, even if this screen sees it first (the roller)', async () => {
    const { wrapper, die } = await mountModal(null)
    await wrapper.setProps({
      state: {
        initiative: { ...initiative, rolls: { 2: 2 } },
        server_now: '2026-11-23T10:00:00.300Z',
        last_roll: { id: 7, kind: 'initiative', user_id: 2, values: [2], at: '2026-11-23T10:00:00.250Z' }
      }
    })
    await nextTick()
    expect(die().props('animate')).toBe(true)
  })
})

describe('Time Virus in the action pop-up', () => {
  it('says Roll, and tells the board a die was rolled', async () => {
    const TileAction = (await import('@/components/board/TileAction.vue')).default
    const board = { timeVirus: jest.fn() }
    const playersById = { 1: { user_id: 1, username: 'Ann', alive: true }, 2: { user_id: 2, username: 'Bob', alive: true } }
    const state = { tiles: [{ index: 0, kind: 'time_virus', label: 'Time Virus' }], positions: { 1: 0 }, turn: { user_id: 1, rolled: true } }
    const wrapper = mount(TileAction, { props: { board, state, playersById, myUserId: 1 } })
    const roll = () => wrapper.find('.virus__roll')
    expect(roll().attributes('disabled')).toBeDefined() // pick a victim first
    await wrapper.findAll('.virus__target').find(b => b.text().includes('Bob')).trigger('click')
    expect(roll().text()).toBe('🎲 Roll the virus on Bob')
    expect(wrapper.text()).not.toContain('Release')
    await roll().trigger('click')
    expect(board.timeVirus).toHaveBeenCalledWith(2)
    expect(wrapper.emitted('rolled')[0]).toEqual(['time_virus'])
  })
})

describe('JobPickModal', () => {
  const jobs = [
    { id: 13, name: 'Data Analyst', tier: 1, type: 'Finance' },
    { id: 20, name: 'Phone Scammer', tier: 1, type: 'Illicit' },
    { id: 30, name: 'Teacher', tier: 1, type: 'Public Service' },
    { id: 14, name: 'Accountant', tier: 2, type: 'Finance' }
  ]
  const playersById = { 1: { user_id: 1, username: 'Ann', color: '#f00' }, 2: { user_id: 2, username: 'Bob', color: '#0f0' } }
  async function mountPick(props) {
    const JobPickModal = (await import('@/components/board/JobPickModal.vue')).default
    const board = { pickJob: jest.fn() }
    const wrapper = mount(JobPickModal, { props: { board, jobs, playersById, phase: 'jobs', ...props } })
    return { wrapper, board }
  }
  const state = (picked = {}) => ({ phase: 'jobs', job_pick: { order: [1, 2], picked } })

  it('offers only Tier 1 jobs and shows who has chosen', async () => {
    const { wrapper, board } = await mountPick({ myUserId: 1, state: state({ 2: 30 }) })
    const names = wrapper.findAll('.jobpick__job').map(b => b.find('.jobpick__name').text())
    expect(names).toEqual(['Data Analyst', 'Phone Scammer', 'Teacher'])
    expect(wrapper.text()).toContain('✓ Teacher')
    await wrapper.findAll('.jobpick__job')[1].trigger('click')
    expect(board.pickJob).toHaveBeenCalledWith(20)
  })

  it('lets the admin pick for a player, or deal random jobs', async () => {
    const { wrapper, board } = await mountPick({ myUserId: 1, isAdmin: true, state: state({ 1: 13 }) })
    await wrapper.find('.jobpick__admin').setValue('30')
    expect(board.pickJob).toHaveBeenCalledWith(30, 2)
    await wrapper.find('.jobpick__random').trigger('click')
    expect(board.pickJob).toHaveBeenCalledWith(null, null, true)
  })

  it('is hidden outside the job-choosing step', async () => {
    const { wrapper } = await mountPick({ myUserId: 1, phase: 'playing', state: { phase: 'playing' } })
    expect(wrapper.find('.jobpick').exists()).toBe(false)
  })
})

describe('Senate tile actions', () => {
  async function mountSenate({ govRole = null, governmentName = 'Dictatorship', turn = {}, kind = 'senate' } = {}) {
    const TileAction = (await import('@/components/board/TileAction.vue')).default
    const board = { senateVote: jest.fn(), introduceOppression: jest.fn() }
    const playersById = {
      1: { user_id: 1, username: 'Ann', alive: true, govRole, approval: null },
      2: { user_id: 2, username: 'Bob', alive: true, approval: 'approve' }
    }
    const state = {
      tiles: [{ index: 0, kind, label: 'Senate' }],
      positions: { 1: 0 },
      turn: { user_id: 1, rolled: true, ...turn },
      oppressions: []
    }
    const wrapper = mount(TileAction, { props: { board, state, playersById, myUserId: 1, governmentName } })
    return { wrapper, board }
  }

  it("changes another player's vote for 1 hour (on every Senate tile)", async () => {
    window.confirm = jest.fn(() => true)
    for (const kind of ['senate', 'senate_virus']) {
      const { wrapper, board } = await mountSenate({ kind })
      expect(wrapper.text()).toContain("Change another player's vote · 1h")
      const bob = wrapper.findAll('.senate-votes__row').find(r => r.text().includes('Bob'))
      expect(bob.find('.senate-votes__now').text()).toBe('✓ approves')
      const [approve, reject] = bob.findAll('.senate-votes__btn')
      expect(approve.attributes('disabled')).toBeDefined() // Bob already approves
      await reject.trigger('click')
      expect(board.senateVote).toHaveBeenCalledWith(2, 'reject')
    }
  })

  it('only government members can introduce an oppression; one Senate action per visit', async () => {
    const peasant = await mountSenate()
    expect(peasant.wrapper.text()).not.toContain('Government oppression')
    const dictator = await mountSenate({ govRole: 'Dictator' })
    expect(dictator.wrapper.text()).toContain('Government oppression')
    const used = await mountSenate({ govRole: 'Dictator', turn: { senate_used: true } })
    expect(used.wrapper.text()).toContain("you've taken your Senate action")
    expect(used.wrapper.findAll('.senate-votes__btn').every(b => b.attributes('disabled') !== undefined)).toBe(true)
    const democracy = await mountSenate({ govRole: 'Dictator', governmentName: 'Democracy' })
    expect(democracy.wrapper.text()).not.toContain('Government oppression')
  })
})

describe('AssignmentBoard targets', () => {
  it('shows each slip\'s target prominently, and warns when it is you', async () => {
    const AssignmentBoard = (await import('@/components/board/AssignmentBoard.vue')).default
    const playersById = { 1: { user_id: 1, username: 'Ann', color: '#f00', alive: true }, 2: { user_id: 2, username: 'Bob', color: '#0f0', alive: true } }
    const assignments = [
      { id: 1, target: 2, card: { title: 'Steal a car', text: 'Do it' } },
      { id: 2, target: 1, card: { title: 'Frame them', text: 'Do it' } }
    ]
    const wrapper = mount(AssignmentBoard, { props: { board: {}, assignments, playersById, myUserId: 1, started: true } })
    const items = wrapper.findAll('.assign__item')
    expect(items[0].find('.assign__target').text()).toContain('Target')
    expect(items[0].find('.assign__target-name').text()).toBe('Bob')
    expect(items[1].classes()).toContain('is-mine')
    expect(items[1].find('.assign__target-name').text()).toBe("You're the target!")
    expect(items[1].find('.assign__claim').exists()).toBe(false)
  })
})

describe('GameBoard card moves', () => {
  it('hops a pawn moved by a card (Advance, Shortcut) without rolling the die', async () => {
    const wrapper = mount(GameBoard, { props: { state: boardState(), players, myUserId: 2 } })
    const move = { id: 9, kind: 'card_move', user_id: 1, values: [], path: [1, 2, 3, 4, 5], from: 0, to: 5, jumped_from: null }
    await wrapper.setProps({ state: boardState({ last_roll: move, positions: { 1: 5, 2: 0 } }) })
    await nextTick()
    expect(wrapper.find('.dice-stage').exists()).toBe(false) // no big die
    jest.advanceTimersByTime(150 + 5 * STEP_MS + 50)
    await nextTick()
    expect(wrapper.find('.dice-caption').text()).not.toContain('rolled')
  })
})

describe('HandPanel card hints', () => {
  async function mountHand(state, hand) {
    const HandPanel = (await import('@/components/board/HandPanel.vue')).default
    const playersById = {
      15: { user_id: 15, username: 'egg', alive: true, jailed: false },
      5: { user_id: 5, username: 'Szedlburg', alive: true, jailed: false }
    }
    return mount(HandPanel, { props: { board: { playCard: jest.fn() }, hand, playersById, myUserId: 15, started: true, state } })
  }
  const advance = { uid: 'col-advance#3', title: 'Advance', deck: 'collectable', text: 'Advance to another player' }

  it('greys out Advance with the reason when nobody is ahead before the Black Market', async () => {
    const wrapper = await mountHand({ started: true, turn: { user_id: 15 }, positions: { 15: 13, 5: 9 } }, [advance])
    const use = wrapper.findAll('button').find(b => b.text() === 'Use')
    expect(use.attributes('disabled')).toBeDefined()
    expect(wrapper.find('.hand__why').text()).toBe('Nobody is ahead of you before the Black Market')
  })

  it('allows Advance when someone is ahead, and says when it is not your turn', async () => {
    const ok = await mountHand({ started: true, turn: { user_id: 15 }, positions: { 15: 3, 5: 9 } }, [advance])
    expect(ok.findAll('button').find(b => b.text() === 'Use').attributes('disabled')).toBeUndefined()
    expect(ok.find('.hand__why').exists()).toBe(false)
    const notMine = await mountHand({ started: true, turn: { user_id: 5 }, positions: { 15: 3, 5: 9 } }, [advance])
    expect(notMine.find('.hand__why').text()).toBe('Use this on your turn')
  })
})

describe('Collapsible assignments and oppressions', () => {
  beforeEach(() => { try { window.localStorage.clear() } catch (e) { /* ignore */ } })

  it('assignments start collapsed (still warning when you are targeted) and remember being opened', async () => {
    const AssignmentBoard = (await import('@/components/board/AssignmentBoard.vue')).default
    const playersById = { 1: { user_id: 1, username: 'Ann', alive: true }, 2: { user_id: 2, username: 'Bob', alive: true } }
    const assignments = [{ id: 1, target: 1, card: { title: 'Frame them', text: 'x' } }]
    const mine = mount(AssignmentBoard, { props: { board: {}, assignments, playersById, myUserId: 1, started: true } })
    expect(mine.find('.assign__list').exists()).toBe(false)
    expect(mine.find('.assign__alert').text()).toContain('1 on you')
    await mine.find('.assign__head').trigger('click')
    expect(mine.find('.assign__list').exists()).toBe(true)
    expect(window.localStorage.getItem('gg.collapsed.assignments.v2')).toBe('0')

    const again = mount(AssignmentBoard, { props: { board: {}, assignments, playersById, myUserId: 2, started: true } })
    expect(again.find('.assign__claim').text()).toBe('Claim reward') // remembered as open
  })

  it('oppressions start collapsed too', async () => {
    const OppressionBoard = (await import('@/components/board/OppressionBoard.vue')).default
    const wrapper = mount(OppressionBoard, { props: { board: {}, oppressions: [], governmentType: 'Democracy' } })
    expect(wrapper.text()).not.toContain('No government oppressions')
    await wrapper.find('.opp__head').trigger('click')
    expect(wrapper.text()).toContain('No government oppressions under Democracy')
  })
})

describe('ScenarioEvent: a card that can\'t be used', () => {
  it('offers the drawer a Discard button (and no "draw another")', async () => {
    const ScenarioEvent = (await import('@/components/board/ScenarioEvent.vue')).default
    const board = { eventAnswer: jest.fn(), eventSkip: jest.fn(), redrawScenario: jest.fn() }
    const playersById = { 1: { user_id: 1, username: 'Ann' }, 2: { user_id: 2, username: 'Bob' } }
    const event = {
      id: 8, title: 'Jury Corruption', drawer: 1, done: false, roll: null,
      lines: [{ text: "🚫 No Judge is in play, so this card can't be used.", tone: '' }],
      card: { uid: 'j#1', title: 'Jury Corruption', text: '...', deck: 'scenario' },
      prompt: { id: 4, kind: 'choice', user_id: 1, unusable: true, question: "Can't be used", options: [{ key: 'discard', label: '🗑️ Discard this card' }] }
    }
    const drawer = mount(ScenarioEvent, { props: { board, playersById, myUserId: 1, event } })
    jest.advanceTimersByTime(10); await nextTick()
    const discard = drawer.findAll('button').find(b => b.text().includes('Discard this card'))
    expect(discard.classes()).toContain('sev__btn--discard')
    expect(drawer.findAll('button').some(b => b.text().includes('draw another'))).toBe(false)
    await discard.trigger('click')
    expect(board.eventAnswer).toHaveBeenCalledWith(4, 'discard')

    const other = mount(ScenarioEvent, { props: { board, playersById, myUserId: 2, event } })
    jest.advanceTimersByTime(10); await nextTick()
    expect(other.text()).toContain('is to discard it')
    expect(other.findAll('button').some(b => b.text().includes('Discard this card'))).toBe(false)
  })
})

describe('ScenarioEvent closes itself when the card is done', () => {
  const playersById = { 1: { user_id: 1, username: 'Ann' } }
  const event = (extra) => ({
    id: 21, title: 'Murder', drawer: 1, done: false, roll: null, lines: [{ text: 'x', tone: '' }],
    card: { uid: 'm#1', title: 'Murder', text: '...', deck: 'scenario' },
    prompt: { id: 1, kind: 'roll', user_id: 1, label: 'Murder', hint: '' }, ...extra
  })
  async function mountIt(ev) {
    const ScenarioEvent = (await import('@/components/board/ScenarioEvent.vue')).default
    const wrapper = mount(ScenarioEvent, { props: { board: { eventAnswer: jest.fn() }, playersById, myUserId: 1, event: ev } })
    jest.advanceTimersByTime(10); await nextTick()
    return wrapper
  }

  it('closes soon after the last action', async () => {
    const wrapper = await mountIt(event())
    expect(wrapper.find('.sev__panel').exists()).toBe(true)
    await wrapper.setProps({ event: event({ done: true, prompt: null }) })
    jest.advanceTimersByTime(2600); await nextTick()
    expect(wrapper.find('.sev__panel').exists()).toBe(false)
    expect(wrapper.find('.sev-tab').exists()).toBe(false)
  })

  it('a card that needed no choices stays up long enough to read', async () => {
    const wrapper = await mountIt(event())
    await wrapper.setProps({ event: event({ id: 22, done: true, prompt: null }) })
    jest.advanceTimersByTime(300); await nextTick()
    jest.advanceTimersByTime(5000); await nextTick()
    expect(wrapper.find('.sev__panel').exists()).toBe(true)
    jest.advanceTimersByTime(4500); await nextTick()
    expect(wrapper.find('.sev__panel').exists()).toBe(false)
  })
})

describe('RNLI debt in the player bar and income', () => {
  it('flags the debt next to the player', async () => {
    const PlayerLedger = (await import('@/components/board/PlayerLedger.vue')).default
    const players = [{
      user_id: 1, username: 'Ann', color: '#f00', alive: true, incomeNet: -50, incomeLines: [], bleed: 0, heat: 0, heatMax: 3,
      handCount: 2, jobName: 'Teacher', debt: { title: 'RNLI', minutes: 450, repay: 60 }
    }]
    const wrapper = mount(PlayerLedger, { props: { players } })
    expect(wrapper.find('.ledger__debt').text()).toBe('🛟 7h 30m')
    expect(wrapper.find('.ledger__debt').attributes('title')).toContain('Repaying 1h a turn')
  })

  it('lets you choose the repayment, which is taken when you collect income', async () => {
    const OngoingCards = (await import('@/components/board/OngoingCards.vue')).default
    const board = { setDebtPlan: jest.fn() }
    const state = { started: true, turn_seq: 4, turn: { user_id: 2 }, debts: { 2: { title: 'RNLI', minutes: 450, plan: 60, paid_seq: 3 } } }
    const wrapper = mount(OngoingCards, { props: { board, state, myUserId: 2, playersById: {} } })
    expect(wrapper.text()).toContain("taken when you collect income")
    await wrapper.findAll('.ongoing__btn--plan').find(b => b.text() === '2h').trigger('click')
    expect(board.setDebtPlan).toHaveBeenCalledWith(120)
  })
})

describe('Turn panel steps and dealt cards', () => {
  async function mountPanel(turn, tileKind = 'collectables') {
    const TurnPanel = (await import('@/components/board/TurnPanel.vue')).default
    const board = { collectIncome: jest.fn(), roll: jest.fn(), endTurn: jest.fn() }
    const playersById = { 1: { user_id: 1, username: 'Ann', alive: true, jailed: false, color: '#f00' } }
    const state = {
      phase: 'playing', started: true, round: 2, turn: { user_id: 1, ...turn }, turn_order: [1], turn_index: 0,
      positions: { 1: 0 }, tiles: [{ index: 0, kind: tileKind, label: tileKind === 'collectables' ? 'Collectables' : 'Job Centre' }],
      last_roll: { kind: 'move', user_id: 1, values: [2] }
    }
    const wrapper = mount(TurnPanel, { props: { board, state, playersById, myUserId: 1, incomeNet: 10 } })
    return { wrapper, board }
  }

  it('one row per step, the current one highlighted', async () => {
    const { wrapper, board } = await mountPanel({ paid: false, rolled: false })
    const steps = wrapper.findAll('.step')
    expect(steps).toHaveLength(3)
    expect(steps[0].classes()).toContain('is-current')
    expect(steps[0].text()).toContain('+10m this turn')
    await steps[0].find('.step__action').trigger('click')
    expect(board.collectIncome).toHaveBeenCalled()
    await steps[1].find('.step__action').trigger('click')
    expect(board.roll).toHaveBeenCalled()
  })

  it('says what the tile dealt into your hand', async () => {
    const { wrapper } = await mountPanel({ paid: true, rolled: true, dealt: ['Collectable'] })
    const steps = wrapper.findAll('.step')
    expect(steps[0].classes()).toContain('is-done')
    expect(steps[1].find('.step__pip').text()).toBe('2')
    expect(steps[2].text()).toContain('1 Collectable added to your hand')

    const both = await mountPanel({ paid: true, rolled: true, dealt: ['Promotion card', 'Job Opportunity'] }, 'job_centre')
    expect(both.wrapper.text()).toContain('1 Promotion card + 1 Job Opportunity added to your hand')
  })
})

describe('Waiting for the pawn, and end turn any time', () => {
  it('the board reports when a pawn has landed', async () => {
    const wrapper = mount(GameBoard, { props: { state: boardState(), players, myUserId: 2 } })
    const roll = { id: 3, kind: 'move', user_id: 1, values: [2], path: [1, 2], from: 0, to: 2, jumped_from: null }
    await wrapper.setProps({ state: boardState({ last_roll: roll, positions: { 1: 2, 2: 0 } }) })
    await nextTick()
    expect((wrapper.emitted('landed') || []).some(([id]) => id === 3)).toBe(false)
    // The pawn hops one step at a time: let each step's timer run in turn
    for (let i = 0; i < 12; i++) {
      jest.advanceTimersByTime(STEP_MS)
      await Promise.resolve(); await Promise.resolve()
    }
    await nextTick()
    expect(wrapper.emitted('landed').some(([id]) => id === 3)).toBe(true)
  })

  it('the scenario panel waits while a pawn is moving; the first roll in it animates', async () => {
    const ScenarioEvent = (await import('@/components/board/ScenarioEvent.vue')).default
    const BoardDie = (await import('@/components/board/BoardDie.vue')).default
    const ev = (roll) => ({
      id: 30, title: 'Murder', drawer: 1, done: false, lines: [], roll,
      card: { uid: 'm#1', title: 'Murder', text: '...', deck: 'scenario' },
      prompt: { id: 2, kind: 'roll', user_id: 1, label: 'Murder', hint: '' }
    })
    const wrapper = mount(ScenarioEvent, { props: { board: {}, playersById: { 1: { user_id: 1, username: 'Ann' } }, myUserId: 1, event: ev(null), moving: true } })
    jest.advanceTimersByTime(10); await nextTick()
    expect(wrapper.find('.sev__panel').exists()).toBe(false)
    await wrapper.setProps({ moving: false })
    expect(wrapper.find('.sev__panel').exists()).toBe(true)
    await wrapper.setProps({ event: ev({ id: 77, user_id: 1, values: [4], bonus: 0, total: 4, need: 5, ok: false, label: 'Murder' }) })
    await nextTick()
    expect(wrapper.findComponent(BoardDie).props('animate')).toBe(true)
  })

  it('End turn works before collecting income or rolling; the admin can set whose turn it is', async () => {
    const TurnPanel = (await import('@/components/board/TurnPanel.vue')).default
    const board = { endTurn: jest.fn(), setTurn: jest.fn() }
    const playersById = { 1: { user_id: 1, username: 'Ann', alive: true }, 2: { user_id: 2, username: 'Bob', alive: true } }
    const state = { phase: 'playing', started: true, round: 1, turn: { user_id: 1 }, turn_order: [1, 2], turn_index: 0, positions: { 1: 0, 2: 0 }, tiles: [{ index: 0, kind: 'start', label: 'Start' }] }
    const wrapper = mount(TurnPanel, { props: { board, state, playersById, myUserId: 1, isAdmin: true } })
    const end = wrapper.find('.turn__btn--end')
    expect(end.attributes('disabled')).toBeUndefined()
    await end.trigger('click')
    expect(board.endTurn).toHaveBeenCalled()
    window.confirm = jest.fn(() => true)
    await wrapper.find('select[aria-label="Whose turn"]').setValue(2)
    await wrapper.findAll('button').find(b => b.text() === 'Make it their turn').trigger('click')
    expect(board.setTurn).toHaveBeenCalledWith(2)
  })
})

describe('Choosing your piece in the lobby', () => {
  const players = [
    { user_id: 1, username: 'Ann', color: '#EF4444', colorName: 'red', piece: 'pawn' },
    { user_id: 2, username: 'Bob', color: '#3B82F6', colorName: 'blue', piece: 'knight' }
  ]
  async function mountLobby() {
    const BoardLobby = (await import('@/components/board/BoardLobby.vue')).default
    const board = { setLook: jest.fn(), setReady: jest.fn(), start: jest.fn() }
    const wrapper = mount(BoardLobby, { props: { board, state: { phase: 'lobby', ready: {} }, players, myUserId: 1 } })
    return { wrapper, board }
  }

  it("lets you pick a colour nobody else has (everyone plays a pawn)", async () => {
    const { wrapper, board } = await mountLobby()
    const blue = wrapper.find('[aria-label="blue (taken by Bob)"]')
    expect(blue.attributes('disabled')).toBeDefined()
    expect(wrapper.find('[aria-label="red"]').attributes('aria-checked')).toBe('true')
    await wrapper.find('[aria-label="green"]').trigger('click')
    expect(board.setLook).toHaveBeenCalledWith({ color: 'green' })
    expect(wrapper.findAll('.lobby__piece-btn')).toHaveLength(0) // no piece choice
  })

  it('draws the pawn', async () => {
    const BoardPawn = (await import('@/components/board/BoardPawn.vue')).default
    const { PIECES } = await import('@/components/board/pieces')
    for (const piece of PIECES) {
      const w = mount(BoardPawn, { props: { color: '#f00', piece } })
      expect(w.find('.board-pawn__piece').element.children.length).toBeGreaterThan(1)
      expect(w.attributes('aria-label')).toBeTruthy()
    }
  })
})

describe('Jobs, titles and abilities', () => {
  const reference = [
    { name: 'Teacher', faction: 'Public Service', tier: 1, pay: 10, ability: '' },
    { name: 'Assassin', faction: 'Illicit', tier: 3, pay: 30, ability: 'Inflict bleeding.' },
    { name: 'Judge', faction: 'Public Service', tier: 3, pay: 30, ability: 'Decide court cases.', automatic: 'Automatic: court cases come to you to decide.' }
  ]
  const jobs = [{ id: 7, name: 'Teacher', tier: 1, type: 'Public Service' }, { id: 22, name: 'Assassin', tier: 3, type: 'Illicit' }, { id: 25, name: 'Judge', tier: 3, type: 'Public Service' }]
  const players = [
    { user_id: 1, username: 'Ann', jobName: 'Teacher', alive: true },
    { user_id: 2, username: 'Bob', jobName: 'Assassin', alive: true }
  ]

  it('the job browser shows every job with its ability, and who holds the Tier 3 ones', async () => {
    const JobsModal = (await import('@/components/board/JobsModal.vue')).default
    window.confirm = jest.fn(() => true)
    const wrapper = mount(JobsModal, { props: { open: true, reference, jobs, players, myUserId: 1 } })
    expect(wrapper.text()).toContain('Inflict bleeding.')
    const cards = wrapper.findAll('.job')
    const assassin = cards.find(c => c.text().includes('Assassin'))
    expect(assassin.text()).toContain('Taken · Bob')
    expect(assassin.attributes('disabled')).toBeDefined()
    expect(cards.find(c => c.text().includes('Teacher')).text()).toContain('Your job')
    await cards.find(c => c.text().includes('Judge')).trigger('click')
    expect(wrapper.emitted('choose')[0]).toEqual([25])
  })

  it('an Executive picks a second Tier 3 ability', async () => {
    const JobsModal = (await import('@/components/board/JobsModal.vue')).default
    window.confirm = jest.fn(() => true)
    const wrapper = mount(JobsModal, { props: { open: true, secondary: true, reference, jobs, players, myUserId: 1 } })
    expect(wrapper.text()).not.toContain('Teacher') // Tier 3 only
    await wrapper.findAll('.job').find(c => c.text().includes('Judge')).trigger('click')
    expect(wrapper.emitted('choose-secondary')[0]).toEqual(['Judge'])
  })

  it('titles show what they need, and the next one can be taken on your turn', async () => {
    const TitlesModal = (await import('@/components/board/TitlesModal.vue')).default
    window.confirm = jest.fn(() => true)
    const board = { applyTitle: jest.fn() }
    const titles = [
      { name: 'Manager', pay: 40, quantity: 6, left: 6, abilities: '+1 against War', isNext: true, ready: true, mine: false,
        checks: [{ ok: true, text: 'Hold a Tier 3 job' }, { ok: true, text: 'A completed assignment slip (traded in)' }] },
      { name: 'Senior', pay: 50, quantity: 4, left: 4, abilities: '+2 heat threshold', isNext: false, ready: false, mine: false,
        checks: [{ ok: false, text: 'A Promotion card in your hand (used)' }] }
    ]
    const wrapper = mount(TitlesModal, { props: { open: true, alert: true, titles, isMyTurn: true, board } })
    expect(wrapper.text()).toContain('You can become a Manager!')
    expect(wrapper.text()).toContain('A completed assignment slip (traded in)')
    await wrapper.find('.title-card__apply').trigger('click')
    expect(board.applyTitle).toHaveBeenCalled()
  })

  it('the turn panel offers my job abilities (automatic ones need no button)', async () => {
    const TurnPanel = (await import('@/components/board/TurnPanel.vue')).default
    const board = { useAbility: jest.fn() }
    const state = { phase: 'playing', started: true, round: 1, turn: { user_id: 1, abilities_used: { secondary: true } }, turn_order: [1], turn_index: 0, positions: { 1: 0 }, tiles: [{ index: 0, kind: 'start', label: 'Start' }] }
    const abilities = [
      { slot: 'primary', job: 'Assassin', text: 'Inflict bleeding.', automatic: null, used: false },
      { slot: 'secondary', job: 'Time Keeper', text: 'Siphon.', automatic: null, used: true }
    ]
    const wrapper = mount(TurnPanel, { props: { board, state, playersById: { 1: { user_id: 1, alive: true } }, myUserId: 1, abilities } })
    const rows = wrapper.findAll('.ability')
    expect(rows).toHaveLength(2)
    await rows[0].find('.ability__use').trigger('click')
    expect(board.useAbility).toHaveBeenCalledWith('primary')
    expect(rows[1].find('.ability__use').attributes('disabled')).toBeDefined()
    expect(rows[1].text()).toContain('Used this turn')
  })
})

describe('In-game confirmations and the job list for cards', () => {
  it('askConfirm shows the in-game dialog (title from the question, red for destructive actions)', async () => {
    const ConfirmHost = (await import('@/components/ConfirmHost.vue')).default
    const { askConfirm } = await import('@/composables/useConfirm')
    const host = mount(ConfirmHost, { attachTo: document.body })
    const answer = askConfirm('Discard “Knife”? It goes to the Black Market.')
    await nextTick(); await nextTick()
    expect(host.find('.confirm__title').text()).toBe('Discard “Knife”?')
    expect(host.find('.confirm__detail').text()).toBe('It goes to the Black Market.')
    expect(host.find('.confirm__panel').classes()).toContain('is-danger')
    await host.find('.confirm__btn--ok').trigger('click')
    await expect(answer).resolves.toBe(true)

    const second = askConfirm('Become a Pimp?')
    await nextTick(); await nextTick()
    expect(host.find('.confirm__panel').classes()).not.toContain('is-danger')
    await host.find('.confirm__btn--cancel').trigger('click')
    await expect(second).resolves.toBe(false)
    host.unmount()
  })

  it('a card asking for a job offers only its jobs, and can keep yours', async () => {
    const JobsModal = (await import('@/components/board/JobsModal.vue')).default
    const reference = [
      { name: 'Teacher', faction: 'Public Service', tier: 1, pay: 10, ability: '' },
      { name: 'Data Analyst', faction: 'Finance', tier: 1, pay: 10, ability: '' },
      { name: 'Judge', faction: 'Public Service', tier: 3, pay: 30, ability: 'Decide court cases.' }
    ]
    const jobs = [{ id: 7, name: 'Teacher', tier: 1 }, { id: 13, name: 'Data Analyst', tier: 1 }, { id: 25, name: 'Judge', tier: 3 }]
    const wrapper = mount(JobsModal, {
      props: { open: true, reference, jobs, players: [{ user_id: 1, username: 'Ann', jobName: 'Teacher' }], myUserId: 1,
        allowed: ['13'], keepable: true, cardName: 'Job Opportunity', cardQuestion: 'Job Opportunity: choose a Tier 1 job' }
    })
    expect(wrapper.text()).toContain('Choose your new job')
    const judge = wrapper.findAll('.job').find(c => c.text().includes('Judge'))
    expect(judge.text()).toContain('Not offered by this card')
    expect(judge.attributes('disabled')).toBeDefined()
    await wrapper.find('.jobs__keep').trigger('click')
    expect(wrapper.emitted('keep')).toHaveLength(1)
  })

  it('the live card panel hands a job question to the jobs list', async () => {
    const ScenarioEvent = (await import('@/components/board/ScenarioEvent.vue')).default
    const prompt = { id: 40, kind: 'job', user_id: 1, question: 'Careers Advisor: choose any available job', options: [{ key: '13', label: 'Data Analyst' }], keep: true, card: 'Careers Advisor' }
    const event = { id: 50, title: 'Careers Advisor', deck: 'collectable', played: true, drawer: 1, done: false, lines: [], roll: null, card: { title: 'Careers Advisor', text: '' }, prompt }
    const wrapper = mount(ScenarioEvent, { props: { board: {}, playersById: { 1: { user_id: 1, username: 'Ann' } }, myUserId: 1, event } })
    jest.advanceTimersByTime(10); await nextTick()
    await wrapper.findAll('button').find(b => b.text().includes('Choose from the jobs list')).trigger('click')
    expect(wrapper.emitted('pick-job')[0][0].id).toBe(40)
  })
})
