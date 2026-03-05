import { ref } from 'vue'

/**
 * useDictatorBidding composable
 * Manages Dictator auction bidding state and logic
 */
export function useDictatorBidding() {
  // Bidding state
  const biddingActive = ref(false)
  const bidTimeMinutes = ref(0)
  const currentUserBid = ref(null)
  const biddingTally = ref({}) // { userId: true/false indicating if they've bid }
  const dictatorWinner = ref(null)

  // Modal refs
  const dictatorBiddingModal = ref(null)
  const dictatorBiddingWinnerModal = ref(null)

  /**
   * Initialize bidding state
   */
  function initiateBidding(participants) {
    biddingActive.value = true
    biddingTally.value = {}
    currentUserBid.value = null
    bidTimeMinutes.value = 0

    // Initialize tally with all participants
    participants.forEach(p => {
      biddingTally.value[p.user_id] = false
    })
  }

  /**
   * Place a bid in the auction
   */
  function placeBid() {
    if (bidTimeMinutes.value <= 0) {
      console.warn('[Bidding] Invalid bid amount - must be greater than 0')
      return false
    }

    currentUserBid.value = bidTimeMinutes.value
    return true
  }

  /**
   * Conclude bidding after all participants have bid
   */
  function concludeBidding(participants) {
    const allBiddersCount = Object.values(biddingTally.value).filter(v => v === true).length
    const totalParticipants = participants.length

    if (allBiddersCount !== totalParticipants) {
      console.warn(`[Bidding] Not all participants have bid (${allBiddersCount}/${totalParticipants})`)
      return false
    }

    return true
  }

  /**
   * Handle bidding completion with winner announcement
   */
  function announceBiddingWinner(winnerName) {
    biddingActive.value = false
    dictatorWinner.value = winnerName
    dictatorBiddingModal.value?.hide?.()

    // Show winner modal with slight delay
    setTimeout(() => {
      dictatorBiddingWinnerModal.value?.show?.()
    }, 100)
  }

  /**
   * Reset bidding state
   */
  function resetBidding() {
    biddingActive.value = false
    bidTimeMinutes.value = 0
    currentUserBid.value = null
    biddingTally.value = {}
    dictatorWinner.value = null
  }

  return {
    // State
    biddingActive,
    bidTimeMinutes,
    currentUserBid,
    biddingTally,
    dictatorWinner,
    dictatorBiddingModal,
    dictatorBiddingWinnerModal,

    // Methods
    initiateBidding,
    placeBid,
    concludeBidding,
    announceBiddingWinner,
    resetBidding
  }
}
