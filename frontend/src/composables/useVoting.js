import { ref, computed } from 'vue'

/**
 * useVoting composable
 * Manages government voting state and logic with secret ballots
 * Votes are hidden until admin concludes the vote
 */
export function useVoting() {
  // Voting state
  const votingActive = ref(false)
  const voteTally = ref({}) // { userId: true/false indicating if they've voted }
  const currentUserVote = ref(null) // The current user's vote (only they can see this)
  const voteResults = ref(null) // { userId: { vote, username }, ... } - revealed after conclusion
  const votingConcluded = ref(false)
  
  // Question being voted on (optional)
  const voteQuestion = ref('Cast your vote on the current matter')

  // Modal refs
  const voteModal = ref(null)
  const voteResultsModal = ref(null)

  /**
   * Initialize voting state
   */
  function initiateVoting(participants, question = null) {
    votingActive.value = true
    votingConcluded.value = false
    voteTally.value = {}
    currentUserVote.value = null
    voteResults.value = null
    
    if (question) {
      voteQuestion.value = question
    }

    // Initialize tally with all participants
    participants.forEach(p => {
      voteTally.value[p.user_id] = false
    })
  }

  /**
   * Cast a vote
   */
  function castVote(choice) {
    if (!['yes', 'no', 'abstain'].includes(choice)) {
      console.warn('[Voting] Invalid vote choice')
      return false
    }

    currentUserVote.value = choice
    return true
  }

  /**
   * Update tally when another participant votes
   */
  function updateTally(userId) {
    voteTally.value[userId] = true
  }

  /**
   * Count how many have voted
   */
  const votedCount = computed(() => {
    return Object.values(voteTally.value).filter(v => v === true).length
  })

  /**
   * Count total participants
   */
  const totalParticipants = computed(() => {
    return Object.keys(voteTally.value).length
  })

  /**
   * Check if all participants have voted
   */
  const allVoted = computed(() => {
    return totalParticipants.value > 0 && votedCount.value === totalParticipants.value
  })

  /**
   * Handle voting conclusion with results reveal
   */
  function concludeVoting(results) {
    votingConcluded.value = true
    votingActive.value = false
    voteResults.value = results
    
    // Close the voting modal and show results
    voteModal.value?.hide?.()

    // Show results modal with slight delay
    setTimeout(() => {
      voteResultsModal.value?.show?.()
    }, 100)
  }

  /**
   * Reset voting state
   */
  function resetVoting() {
    votingActive.value = false
    votingConcluded.value = false
    voteTally.value = {}
    currentUserVote.value = null
    voteResults.value = null
    voteQuestion.value = 'Cast your vote on the current matter'
  }

  /**
   * Get aggregated results summary
   */
  const resultsSummary = computed(() => {
    if (!voteResults.value) return null

    const summary = {
      yes: 0,
      no: 0,
      abstain: 0,
      total: 0,
      votes: []
    }

    for (const [userId, data] of Object.entries(voteResults.value)) {
      summary.total++
      if (data.vote === 'yes') summary.yes++
      else if (data.vote === 'no') summary.no++
      else if (data.vote === 'abstain') summary.abstain++
      
      summary.votes.push({
        userId: parseInt(userId),
        username: data.username,
        vote: data.vote
      })
    }

    // Determine outcome
    if (summary.yes > summary.no) {
      summary.outcome = 'PASSED'
    } else if (summary.no > summary.yes) {
      summary.outcome = 'REJECTED'
    } else {
      summary.outcome = 'TIE'
    }

    return summary
  })

  return {
    // State
    votingActive,
    voteTally,
    currentUserVote,
    voteResults,
    votingConcluded,
    voteQuestion,
    voteModal,
    voteResultsModal,

    // Computed
    votedCount,
    totalParticipants,
    allVoted,
    resultsSummary,

    // Methods
    initiateVoting,
    castVote,
    updateTally,
    concludeVoting,
    resetVoting
  }
}
