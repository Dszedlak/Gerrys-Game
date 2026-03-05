import { nextTick } from 'vue'

/**
 * useRoomSockets composable
 * Manages all WebSocket event handlers for the room
 * Organizes socket listeners by feature area
 */
export function useRoomSockets(socket) {
  /**
   * Setup all socket event listeners
   */
  function setupSocketListeners(state) {
    // ============= CLOCK EVENTS =============
    socket.on('updateClock', async (data) => {
      let newClock
      if (typeof data.data === 'string') {
        try {
          newClock = String(JSON.parse(data.data))
        } catch {
          newClock = data.data
        }
      } else {
        newClock = String(data.data)
      }

      state.clock.value = newClock

      // Update clock in participants array for current user
      const currentUserIndex = state.participants.value.findIndex(
        p => p.user_id === state.currentUserId.value
      )
      if (currentUserIndex !== -1) {
        const updated = [...state.participants.value]
        updated[currentUserIndex] = {
          ...updated[currentUserIndex],
          clock: newClock
        }
        state.participants.value = updated
        await nextTick()
      }
    })

    socket.on('updateAllClocks', (data) => {
      const clocks = data.clocks
      if (clocks && clocks[state.currentUserId.value]) {
        state.clock.value = clocks[state.currentUserId.value]

        const currentUserIndex = state.participants.value.findIndex(
          p => p.user_id === state.currentUserId.value
        )
        if (currentUserIndex !== -1) {
          state.participants.value[currentUserIndex].clock = clocks[state.currentUserId.value]
        }
      }

      // Update all other participants
      state.participants.value.forEach((p, index) => {
        if (clocks[p.user_id]) {
          state.participants.value[index].clock = clocks[p.user_id]
        }
      })
    })

    socket.on('userClockUpdate', (data) => {
      const participantIndex = state.participants.value.findIndex(
        p => p.user_id === data.user_id
      )
      if (participantIndex !== -1) {
        state.participants.value[participantIndex] = {
          ...state.participants.value[participantIndex],
          clock: data.clock
        }
        state.participants.value = [...state.participants.value]
      }

      if (data.user_id === state.currentUserId.value) {
        state.clock.value = data.clock
      }
    })

    // ============= JOB & PERK UPDATES =============
    socket.on('userJobUpdate', (data) => {
      const participantIndex = state.participants.value.findIndex(
        p => p.user_id === data.user_id
      )
      if (participantIndex !== -1) {
        state.participants.value[participantIndex] = {
          ...state.participants.value[participantIndex],
          job_name: data.job_name,
          job_tier: data.job_tier
        }
        state.participants.value = [...state.participants.value]
      }
    })

    socket.on('userPerkUpdate', (data) => {
      const participantIndex = state.participants.value.findIndex(
        p => p.user_id === data.user_id
      )
      if (participantIndex !== -1) {
        state.participants.value[participantIndex] = {
          ...state.participants.value[participantIndex],
          perk: data.perk
        }
        state.participants.value = [...state.participants.value]
      }
    })

    // ============= COLLECTIONS/DATA UPDATES =============
    socket.on('updateCollectionData', (payload) => {
      try {
        const raw = payload?.data ?? payload
        const data = typeof raw === 'string' ? JSON.parse(raw) : raw
        const govs = Array.isArray(data?.governments) ? data.governments : []
        const jbs = Array.isArray(data?.jobs) ? data.jobs : []

        if (govs.length) {
          state.governments.value = govs.map((g, idx) => ({
            id: g.id ?? g.value ?? idx + 1,
            name: state.govLabel(g)
          }))
        }
        state.jobs.value = jbs
      } catch (e) {
        console.error('[Socket] updateCollectionData parse error', e)
      }
    })

    socket.on('updateRoomId', (data) => {
      state.updateRoomId(data.data)
    })

    socket.on('setUserId', (data) => {
      state.setUserId(data.data)
    })

    socket.on('UpdateUserStatus', (data) => {
      const room = JSON.parse(data.data)
      state.participants.value = Array.isArray(room.participants)
        ? room.participants.map(p => ({
            user_id: p.user_id,
            username: p.username ?? 'Unknown',
            job_name: p.job_name ?? '-',
            job_tier: p.job_tier ?? '-',
            clock: p.clock ?? '00•00•00',
            bleed: p.bleed ?? 0,
            heat: p.heat ?? 0,
            perk: p.perk ?? null
          }))
        : []
    })

    // ============= ROOM STATE =============
    socket.on('room_state', (payload) => {
      const room = typeof payload === 'string' ? JSON.parse(payload) : payload
      state.roomname.value = room?.name || state.roomname.value

      // Capture room owner
      state.roomOwnerId.value =
        room?.owner_id ?? room?.creator_id ?? room?.created_by ?? room?.createdBy ?? null

      state.participants.value = Array.isArray(room?.participants)
        ? room.participants.map(p => ({
            user_id: p.user_id,
            username: p.username ?? 'Unknown',
            job_name: p.job_name ?? 'Unemployed',
            job_tier: p.job_tier ?? '-',
            clock: p.clock ?? '00•00•00',
            bleed: p.bleed ?? 0,
            heat: p.heat ?? 0,
            perk: p.perk ?? null
          }))
        : []

      state.roomGovernment.value = room?.government || null

      // Sync dropdown if we have government data
      const syncId = state.findGovernmentIdByName(state.roomGovernment.value?.type)
      if (syncId !== undefined) state.selectedGovernmentId.value = syncId

      // Sync current user's display data
      const currentUser = state.participants.value.find(
        p => p.user_id === state.currentUserId.value
      )
      if (currentUser) {
        state.selectedPerk.value = currentUser.perk
        state.clock.value = currentUser.clock
      }
    })

    // ============= SENATE/APPROVAL VOTES =============
    socket.on('approvalStatusUpdated', (data) => {
      const participant = state.participants.value.find(p => p.user_id === data.user_id)
      if (participant) {
        participant.approval_status = data.status
      }
    })

    socket.on('voteRecorded', (data) => {
      const participant = state.participants.value.find(p => p.user_id === data.user_id)
      if (participant) {
        participant.gov_vote = data.vote
      }
    })

    // ============= DICTATOR BIDDING =============
    socket.on('startDictatorBidding', (data) => {
      state.initiateBidding()
      state.dictatorBiddingModal.value?.show?.()
    })

    socket.on('biddingTallyUpdate', (data) => {
      state.biddingTally.value = data.tally || {}
    })

    socket.on('dictatorWinner', (data) => {
      state.announceBiddingWinner(data.winner_name)
    })
  }

  /**
   * Remove all socket listeners (cleanup)
   */
  function removeSocketListeners() {
    socket.offAny()
  }

  return {
    setupSocketListeners,
    removeSocketListeners
  }
}
