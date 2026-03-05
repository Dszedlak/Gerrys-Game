import { ref, computed } from 'vue'

/**
 * usePolitburoWheel composable
 * Manages Politburo selection using the wheel spinner
 */
export function usePolitburoWheel() {
  // Politburo selection state
  const politburoMembers = ref([])
  const isSpinningPolitburo = ref(false)
  const balanceBooksOnSave = ref(false)
  const currentWheelWinner = ref(null)
  const showWheelResult = ref(false)
  const govError = ref('')

  // Modal refs
  const politburoWheelModal = ref(null)
  const politburoWheelRef = ref(null)

  /**
   * Get available candidates (exclude already selected)
   */
  function getAvailableCandidates(participants) {
    return participants.filter(p => !politburoMembers.value.includes(p.user_id))
  }

  /**
   * Check if selection is complete
   */
  const isSelectionComplete = computed(() => {
    return politburoMembers.value.length === 2
  })

  /**
   * Add member to politburo selection
   */
  function addMember(memberId, memberName) {
    if (!memberId) {
      console.error('[Politburo] Invalid member ID')
      return false
    }

    if (politburoMembers.value.includes(memberId)) {
      console.warn('[Politburo] Member already selected:', memberName)
      return false
    }

    if (politburoMembers.value.length >= 2) {
      console.warn('[Politburo] Already have 2 members selected')
      return false
    }

    politburoMembers.value.push(memberId)
    console.log('[Politburo] Added member:', memberName, 'ID:', memberId)
    return true
  }

  /**
   * Remove member from selection
   */
  function removeMember(memberId) {
    const idx = politburoMembers.value.indexOf(memberId)
    if (idx > -1) {
      politburoMembers.value.splice(idx, 1)
      return true
    }
    return false
  }

  /**
   * Start spinning for next member
   */
  function spinForNextMember() {
    if (politburoMembers.value.length >= 2 || isSpinningPolitburo.value) {
      console.warn('[Politburo] Cannot spin: already have 2 members or spinning in progress')
      return false
    }

    if (!politburoWheelRef.value) {
      console.error('[Politburo] Wheel ref not available')
      return false
    }

    isSpinningPolitburo.value = true

    // Open wheel modal and trigger spin
    try {
      politburoWheelRef.value.open()

      // Small delay to ensure modal is visible before spinning
      setTimeout(() => {
        politburoWheelRef.value.spinWheel()
        isSpinningPolitburo.value = false
      }, 100)

      return true
    } catch (e) {
      console.error('[Politburo] Spin failed:', e)
      isSpinningPolitburo.value = false
      return false
    }
  }

  /**
   * Spin again (close modal and re-spin)
   */
  function spinAgain() {
    try {
      politburoWheelRef.value?.wheelModal?.hide?.()

      setTimeout(() => {
        spinForNextMember()
      }, 300)

      return true
    } catch (e) {
      console.error('[Politburo] Spin again failed:', e)
      return false
    }
  }

  /**
   * Reset politburo selection
   */
  function resetSelection() {
    politburoMembers.value = []
    balanceBooksOnSave.value = false
    govError.value = ''
    showWheelResult.value = false
    currentWheelWinner.value = null
  }

  /**
   * Cancel selection and close modal
   */
  function cancelSelection() {
    resetSelection()
    try {
      politburoWheelModal.value?.hide?.()
    } catch (e) {
      console.error('[Politburo] Cancel failed:', e)
    }
  }

  /**
   * Validate selection is complete
   */
  function validateSelection() {
    govError.value = ''

    if (politburoMembers.value.length !== 2) {
      govError.value = 'Must select exactly 2 politburo members'
      return false
    }

    // Check for duplicates
    if (new Set(politburoMembers.value).size !== 2) {
      govError.value = 'Politburo members must be different people'
      return false
    }

    return true
  }

  return {
    // State
    politburoMembers,
    isSpinningPolitburo,
    balanceBooksOnSave,
    currentWheelWinner,
    showWheelResult,
    govError,
    politburoWheelModal,
    politburoWheelRef,

    // Computed
    isSelectionComplete,

    // Methods
    getAvailableCandidates,
    addMember,
    removeMember,
    spinForNextMember,
    spinAgain,
    resetSelection,
    cancelSelection,
    validateSelection
  }
}
