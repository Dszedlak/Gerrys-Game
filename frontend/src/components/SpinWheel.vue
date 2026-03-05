<template>
  <!-- Modal mode (default) -->
  <b-modal v-if="!inline" id="wheelSpinnerModal" ref="wheelModal" title="Spin the Wheel" size="xl" @shown="onModalShown" @hidden="onModalHidden">
    <div class="wheel-container">
      <div v-if="!participants || participants.length === 0" class="no-participants">
        <p>No participants available to spin!</p>
      </div>
      <div v-else class="wheel-content">
        <div class="wheel-wrapper">
          <div class="wheel-pointer">▼</div>
          <svg ref="wheelSvg" class="wheel-svg" :class="{ spinning: isSpinning }" :style="{ transform: `rotate(${currentRotation}deg)` }" viewBox="0 0 500 500" @transitionend="onSpinEnd">
            <g v-for="(item, index) in wheelItems" :key="index">
              <path :d="getSlicePath(index)" :fill="item.color" :stroke="'#ffffff'" :stroke-width="2" style="opacity: 1;" />
              <text :x="getTextX(index)" :y="getTextY(index)" :transform="getTextTransform(index)" text-anchor="middle" class="wheel-text" fill="#000000" style="font-size: 14px; font-weight: bold; pointer-events: none;">{{ item.text }}</text>
            </g>
          </svg>
        </div>
        <div class="spin-controls mt-4">
          <b-button variant="primary" size="lg" :disabled="isSpinning" @click="spinWheel" class="spin-button">{{ isSpinning ? 'Spinning...' : 'SPIN!' }}</b-button>
        </div>
        <div v-if="winner" class="winner-result mt-4">
          <h3>🎉 Winner: <span class="winner-name">{{ winner.text || winner }}</span> 🎉</h3>
          <div v-if="showCustomActions" class="custom-actions mt-3">
            <slot name="winner-actions" :winner="winner"></slot>
          </div>
        </div>
      </div>
    </div>
    <template #footer></template>
  </b-modal>

  <!-- Inline mode (no modal wrapper) -->
  <div v-else class="wheel-container-inline">
    <div v-if="!participants || participants.length === 0" class="no-participants">
      <p>No participants available to spin!</p>
    </div>
    <div v-else class="wheel-content">
      <div class="wheel-wrapper-inline">
        <div class="wheel-pointer">▼</div>
        <svg ref="wheelSvg" class="wheel-svg" :class="{ spinning: isSpinning }" :style="{ transform: `rotate(${currentRotation}deg)` }" viewBox="0 0 500 500" @transitionend="onSpinEnd">
          <g v-for="(item, index) in wheelItems" :key="index">
            <path :d="getSlicePath(index)" :fill="item.color" :stroke="'#ffffff'" :stroke-width="2" style="opacity: 1;" />
            <text :x="getTextX(index)" :y="getTextY(index)" :transform="getTextTransform(index)" text-anchor="middle" class="wheel-text-inline" fill="#000000">{{ item.text }}</text>
          </g>
        </svg>
      </div>
      
      <!-- Show spin button for admin when not spinning and no winner yet -->
      <div v-if="isAdmin && !winner && showSpinButton" class="spin-controls-inline mt-3">
        <b-button variant="warning" size="lg" :disabled="isSpinning" @click="handleSpinClick" class="spin-button-inline">
          {{ isSpinning ? 'Spinning...' : '🎲 Spin The Wheel' }}
        </b-button>
      </div>
      
      <!-- Winner result with admin actions -->
      <div v-if="winner" class="winner-result-inline mt-3">
        <div class="winner-banner-inline">
          🎉 Winner: <span class="winner-name">{{ winner.text || winner }}</span>
        </div>
        <div v-if="showCustomActions && isAdmin" class="custom-actions-inline mt-2">
          <slot name="winner-actions" :winner="winner"></slot>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  participants: { type: Array, required: true, default: () => [] },
  showCustomActions: { type: Boolean, default: false },
  inline: { type: Boolean, default: false },
  isAdmin: { type: Boolean, default: false },
  showSpinButton: { type: Boolean, default: true }
})

const emit = defineEmits(['spin-request'])

function handleSpinClick() {
  // Emit event for parent to handle broadcasting, then spin
  emit('spin-request')
}

const wheelModal = ref(null)
const wheelSvg = ref(null)
const isSpinning = ref(false)
const currentRotation = ref(0)
const winner = ref(null)

const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B739', '#52B788', '#E74C3C', '#3498DB', '#9B59B6', '#1ABC9C', '#F39C12']

const wheelItems = computed(() => {
  if (!props.participants || props.participants.length === 0) return []
  return props.participants.map((p, index) => ({
    text: p.username || `User ${p.user_id}`,
    value: p.user_id || p.userId || p.id,
    color: colors[index % colors.length]
  }))
})

const sliceAngle = computed(() => wheelItems.value.length > 0 ? 360 / wheelItems.value.length : 0)

function getSlicePath(index) {
  const angle = sliceAngle.value
  const startAngle = index * angle - 90
  const endAngle = startAngle + angle
  const centerX = 250, centerY = 250, radius = 240
  const startRad = (startAngle * Math.PI) / 180
  const endRad = (endAngle * Math.PI) / 180
  const x1 = centerX + radius * Math.cos(startRad)
  const y1 = centerY + radius * Math.sin(startRad)
  const x2 = centerX + radius * Math.cos(endRad)
  const y2 = centerY + radius * Math.sin(endRad)
  const largeArc = angle > 180 ? 1 : 0
  return `M ${centerX} ${centerY} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`
}

function getTextX(index) {
  const angle = sliceAngle.value
  const midAngle = (index * angle + angle / 2 - 90) * Math.PI / 180
  const radius = 160
  return 250 + radius * Math.cos(midAngle)
}

function getTextY(index) {
  const angle = sliceAngle.value
  const midAngle = (index * angle + angle / 2 - 90) * Math.PI / 180
  const radius = 160
  return 250 + radius * Math.sin(midAngle)
}

function getTextTransform(index) {
  const angle = sliceAngle.value
  const rotation = index * angle + angle / 2
  return `rotate(${rotation} ${getTextX(index)} ${getTextY(index)})`
}

function open() {
  winner.value = null
  wheelModal.value?.show()
}

function onModalShown() {
  winner.value = null
}

function onModalHidden() {
  isSpinning.value = false
}

// Generate spin data (rotation and winner) without executing - for synced spins
function generateSpinData() {
  if (wheelItems.value.length === 0) return null
  
  const numSlices = wheelItems.value.length
  const sliceSize = 360 / numSlices
  const spins = 5 + Math.random() * 3
  const extraRotation = Math.random() * sliceSize
  const totalRotation = spins * 360 + extraRotation
  
  // Calculate winner from rotation
  const normalizedRotation = totalRotation % 360
  const pointerSliceAngle = (360 - normalizedRotation) % 360
  let winnerIndex = Math.floor(pointerSliceAngle / sliceSize)
  if (winnerIndex >= numSlices) winnerIndex = 0
  if (winnerIndex < 0) winnerIndex = numSlices - 1
  
  return {
    rotation: totalRotation,
    winnerIndex,
    winner: wheelItems.value[winnerIndex]
  }
}

// Spin to a specific rotation (used for synchronized spins)
function spinToRotation(targetRotation, spinDuration = 5000) {
  if (isSpinning.value || wheelItems.value.length === 0) return
  isSpinning.value = true
  winner.value = null
  
  const numSlices = wheelItems.value.length
  const sliceSize = 360 / numSlices
  
  currentRotation.value = targetRotation
  
  setTimeout(() => {
    const normalizedRotation = targetRotation % 360
    const pointerSliceAngle = (360 - normalizedRotation) % 360
    let winnerIndex = Math.floor(pointerSliceAngle / sliceSize)
    if (winnerIndex >= numSlices) winnerIndex = 0
    if (winnerIndex < 0) winnerIndex = numSlices - 1
    
    winner.value = {
      text: wheelItems.value[winnerIndex].text,
      value: wheelItems.value[winnerIndex].value
    }
    isSpinning.value = false
  }, spinDuration)
}

function spinWheel() {
  // Local spin - generates and executes immediately
  const spinData = generateSpinData()
  if (!spinData) return
  spinToRotation(spinData.rotation)
}

function clearWinner() {
  winner.value = null
  currentRotation.value = 0
  isSpinning.value = false
}

function onSpinEnd() {}

defineExpose({ open, winner, spinWheel, spinToRotation, generateSpinData, clearWinner, wheelModal })
</script>

<style scoped>
.wheel-container { padding: 20px; min-height: 400px; }
.wheel-container-inline { padding: 10px; text-align: center; }
.no-participants { text-align: center; padding: 40px 20px; font-size: 1.1em; color: #EAB308; }
.wheel-content { display: flex; flex-direction: column; align-items: center; }
.wheel-wrapper { position: relative; width: 500px; height: 500px; margin: 0 auto; }
.wheel-wrapper-inline { position: relative; width: 300px; height: 300px; margin: 0 auto; }
.wheel-text-inline { font-size: 16px; font-weight: bold; pointer-events: none; }
.wheel-pointer { position: absolute; top: -15px; left: 50%; transform: translateX(-50%); font-size: 32px; color: #EAB308; z-index: 10; }
.wheel-svg { width: 100%; height: 100%; border-radius: 50%;; transition: none; border: 2px solid rgba(145, 70, 255, 0.3); }
.wheel-svg.spinning { transition: transform 5s cubic-bezier(0.25, 0.1, 0.25, 1); }
.wheel-text { font-size: 16px; font-weight: bold;; pointer-events: none; }
.spin-controls { text-align: center; }
.spin-controls-inline { text-align: center; }
.spin-button { min-width: 200px; font-size: 1.5em; font-weight: bold; padding: 12px 40px; border-radius: 50px; transition: all 0.3s ease; background: #1A1F2E !important; border: 2px solid #EAB308 !important; color: #EAB308 !important; }
.spin-button-inline { min-width: 180px; font-size: 1.1em; font-weight: bold; padding: 10px 24px; border-radius: 50px; transition: all 0.3s ease; }
.spin-button:hover:not(:disabled) { transform: scale(1.05);;; }
.spin-button:disabled { opacity: 0.6; cursor: not-allowed; }
.winner-result { text-align: center; animation: fadeIn 0.5s ease-in; }
.winner-result h3 { font-size: 2em; color: #EAB308; margin: 0;; }
.winner-result-inline { text-align: center; animation: fadeIn 0.5s ease-in; }
.winner-banner-inline { font-size: 1.1em; color: #EAB308; font-weight: bold; padding: 6px 12px; background: #1e293b; border-radius: 6px; display: inline-block; }
.custom-actions-inline { display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; margin-top: 8px; }
.winner-name { color: #ffcc00; font-weight: bold;; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
@media (max-width: 768px) {
  .wheel-wrapper { width: 350px; height: 350px; }
  .wheel-wrapper-inline { width: 260px; height: 260px; }
  .wheel-text { font-size: 12px; }
  .wheel-text-inline { font-size: 12px; }
  .spin-button { font-size: 1.2em; padding: 10px 30px; }
  .winner-result h3 { font-size: 1.5em; }
}
</style>

<style>
/* Hide default modal footer for wheel spinner modal */
#wheelSpinnerModal .modal-footer {
  display: none !important;
}
</style>













