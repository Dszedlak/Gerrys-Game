import { ref } from 'vue'
import { newAnnouncements } from '@/components/board/boardLayout'

/**
 * useBoard
 *
 * Client side of the board view. The server owns the board (dice, pawns,
 * turn order, the Reaper's counter) and pushes the whole thing as a
 * `boardState` event after every change; this just holds the latest copy
 * and wraps the actions. See backend/app/websocket/board.py.
 *
 * @param socket       the room's socket.io client
 * @param onAnnounce   called with each new log entry flagged `announce`
 *                     (Time Virus hits, horsemen, jailings, …)
 */
export function useBoard(socket, { onAnnounce } = {}) {
  const state = ref(null)
  // server clock minus local clock, for the Reaper's countdown
  const serverOffsetMs = ref(0)
  // My collectables. Hands are private, so the server sends each player
  // their own as `boardHand` rather than in the shared state.
  const hand = ref([])
  let lastSeq = null

  socket.on('boardHand', (payload) => {
    const next = typeof payload === 'string' ? JSON.parse(payload) : payload
    hand.value = Array.isArray(next?.hand) ? next.hand : []
  })

  socket.on('boardState', (payload) => {
    const next = typeof payload === 'string' ? JSON.parse(payload) : payload
    if (!next) return

    if (next.server_now) {
      const serverNow = Date.parse(next.server_now)
      if (!Number.isNaN(serverNow)) serverOffsetMs.value = serverNow - Date.now()
    }

    // Only announce what happened since we last looked - never replay the
    // backlog on first load or reconnect.
    if (onAnnounce) newAnnouncements(next.log, lastSeq).forEach(onAnnounce)
    lastSeq = next.seq ?? 0

    state.value = next
  })

  function send(event, data) {
    if (data === undefined) socket.emit(event)
    else socket.emit(event, JSON.stringify(data))
  }

  return {
    state,
    serverOffsetMs,
    hand,

    sync: () => send('boardSync'),
    // Lobby: ready up; the admin starts (force skips anyone not ready)
    setReady: (ready) => send('boardSetReady', { ready }),
    // In the lobby: your pawn's colour (e.g. 'red') and/or piece ('pawn', 'rook', 'knight'...)
    setLook: (look) => send('boardSetLook', look),
    start: (force = false) => send('boardStart', force ? { force: true } : {}),
    // Everyone rolls for the first turn; the admin can roll for anyone still to roll
    initiativeRoll: () => send('boardInitiativeRoll'),
    initiativeRollAll: () => send('boardInitiativeRollAll'),
    initiativeRollCurrent: () => send('boardInitiativeRollCurrent'),
    // Before the first turn: choose a Tier 1 job (the admin can choose for a player, or deal random ones)
    pickJob: (jobId, userId = null, random = false) =>
      send('boardPickJob', random ? { random: true } : { job_id: jobId, ...(userId != null ? { user_id: userId } : {}) }),
    // Discard this turn's scenario card and draw another (the drawer, or the admin)
    redrawScenario: () => send('boardRedrawScenario'),
    // Draw & play the top scenario card (from the deck on the board)
    drawScenario: () => send('boardDrawScenario'),
    reset: () => send('boardReset'),
    roll: () => send('boardRoll'),
    endTurn: () => send('boardEndTurn'),
    // Titles: take the next one up (on your turn); an Executive's second Tier 3 ability
    applyTitle: () => send('boardApplyTitle'),
    chooseSecondaryJob: (job) => send('boardChooseSecondaryJob', { job }),
    // Use your Tier 3 job's ability ('primary') or your executive ability ('secondary')
    useAbility: (slot = 'primary') => send('boardUseAbility', { slot }),
    // Admin: make it this player's turn, from the start
    setTurn: (userId) => send('boardSetTurn', { user_id: userId }),
    collectIncome: () => send('boardCollectIncome'),
    // `card` picks a specific used collectable at the Black Market
    purchase: (kind, card, count) => send('boardPurchase', {
      kind,
      ...(card ? { card } : {}),
      ...(count > 1 ? { count } : {})
    }),
    timeVirus: (targetUserId) => send('boardTimeVirus', { target_user_id: targetUserId }),
    goToJail: (userId) => send('boardGoToJail', userId == null ? {} : { user_id: userId }),
    moveToken: (userId, tile) => send('boardMoveToken', { user_id: userId, tile }),
    summonReaper: () => send('boardSummonReaper'),

    // Cards
    chooseCardTarget: (targetUserId) => send('boardResolveCard', { target_user_id: targetUserId }),
    replaceAssignment: (assignmentId) => send('boardResolveCard', { replace: assignmentId }),
    // `against`: Bounty Board - complete it against any player with a title
    claimAssignment: (assignmentId, targetUserId, against) =>
      send('boardClaimAssignment', {
        assignment_id: assignmentId,
        target_user_id: targetUserId ?? null,
        ...(against != null ? { against } : {})
      }),
    playCard: (card, targetUserId) => send('boardPlayCard', { card, target_user_id: targetUserId ?? null }),
    equipCard: (card) => send('boardEquipCard', { card }),
    unequipCard: (card) => send('boardUnequipCard', { card }),
    discardCard: (card) => send('boardDiscardCard', { card }),
    giveCard: (card, toUserId) => send('boardGiveCard', { card, to_user_id: toUserId }),
    // From the collectable discard pile: with a discard pick, or (admin) to any player
    takeFromDiscard: (card, toUserId) =>
      send('boardTakeFromDiscard', toUserId == null ? { card } : { card, to_user_id: toUserId }),
    // Admin: shuffle a deck's discards back in ('scenario', 'collectable', ... or 'all')
    shuffleDeck: (deck) => send('boardShuffleDeck', { deck }),

    // Government oppressions: introduce one at the Senate, leaders use them, admin removes
    introduceOppression: () => send('boardIntroduceOppression'),
    // At the Senate: change another player's approval for 1 hour
    senateVote: (targetUserId, status) => send('boardSenateVote', { target_user_id: targetUserId, status }),
    useOppression: (oppressionId, targetUserId) =>
      send('boardUseOppression', { oppression_id: oppressionId, target_user_id: targetUserId }),
    removeOppression: (oppressionId) => send('boardRemoveOppression', { oppression_id: oppressionId }),

    // Scenario cards in play: answer the question you're asked (roll, choose, vote...)
    eventAnswer: (promptId, answer) => send('boardEventAnswer', { prompt_id: promptId, answer }),
    // Admin: skip the current question, or stop the card
    eventSkip: (stop = false) => send('boardEventSkip', stop ? { stop: true } : {}),
    // Take back a card you played (while you're still choosing): it stays in your hand
    eventWithdraw: () => send('boardEventWithdraw', {}),
    // A peasant on the same tile as a government leader: steal 1h + a free Throwing Knife
    peasantRevolt: (targetUserId) => send('boardPeasantRevolt', { target_user_id: targetUserId }),
    // Ongoing cards: pay off a debt (RNLI), donate to lift Income Tax
    payDebt: (minutes) => send('boardPayDebt', { minutes }),
    // How much of the debt is repaid each turn when you collect income (60, 120 or 180)
    setDebtPlan: (minutes) => send('boardSetDebtPlan', { minutes }),
    donateTax: (minutes) => send('boardDonateTax', { minutes })
  }
}
