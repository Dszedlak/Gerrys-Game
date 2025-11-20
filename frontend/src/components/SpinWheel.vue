<template>
  <b-modal id="wheelSpinnerModal" ref="wheelModal" title="Spin the Wheel" size="xl" hide-footer @shown="onModalShown" @hidden="onModalHidden">
    <div class="wheel-container">
      <div v-if="!participants || participants.length === 0" class="no-participants">
        <p>No participants available to spin!</p>
      </div>
      <div v-else class="wheel-content">
        <div class="wheel-wrapper">
          <div class="wheel-pointer">▼</div>
          <svg ref="wheelSvg" class="wheel-svg" :class="{ spinning: isSpinning }" :style="{ transform: `rotate(${currentRotation}deg)` }" viewBox="0 0 500 500" @transitionend="onSpinEnd">
            <g v-for="(item, index) in wheelItems" :key="index">
              <path :d="getSlicePath(index)" :fill="item.color" :stroke="'#fff'" :stroke-width="2" />
              <text :x="getTextX(index)" :y="getTextY(index)" :transform="getTextTransform(index)" text-anchor="middle" class="wheel-text" :fill="'#ffffff'">{{ item.text }}</text>
            </g>
          </svg>
        </div>
        <div class="spin-controls mt-4">
          <b-button variant="primary" size="lg" :disabled="isSpinning" @click="spinWheel" class="spin-button">{{ isSpinning ? 'Spinning...' : 'SPIN!' }}</b-button>
        </div>
        <div v-if="winner" class="winner-result mt-4">
          <h3>🎉 Winner: <span class="winner-name">{{ winner }}</span> 🎉</h3>
        </div>
      </div>
    </div>
  </b-modal>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  participants: { type: Array, required: true, default: () => [] }
})

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

function spinWheel() {
  if (isSpinning.value || wheelItems.value.length === 0) return
  isSpinning.value = true
  winner.value = null
  const winnerIndex = Math.floor(Math.random() * wheelItems.value.length)
  const spins = 5 + Math.random() * 3
  const baseRotation = spins * 360
  const winnerSliceMiddle = winnerIndex * sliceAngle.value + sliceAngle.value / 2
  const targetRotation = baseRotation + (360 - winnerSliceMiddle)
  currentRotation.value = targetRotation
  setTimeout(() => {
    winner.value = wheelItems.value[winnerIndex].text
    isSpinning.value = false
  }, 5000)
}

function onSpinEnd() {}

defineExpose({ open })
</script>

<style scoped>
.wheel-container { padding: 20px; min-height: 400px; }
.no-participants { text-align: center; padding: 60px 20px; font-size: 1.2em; color: #999; }
.wheel-content { display: flex; flex-direction: column; align-items: center; }
.wheel-wrapper { position: relative; width: 500px; height: 500px; margin: 0 auto; }
.wheel-pointer { position: absolute; top: -20px; left: 50%; transform: translateX(-50%); font-size: 40px; color: #e74c3c; z-index: 10; text-shadow: 0 2px 4px rgba(0,0,0,0.3); }
.wheel-svg { width: 100%; height: 100%; border-radius: 50%; box-shadow: 0 8px 16px rgba(0,0,0,0.3); transition: none; }
.wheel-svg.spinning { transition: transform 5s cubic-bezier(0.25, 0.1, 0.25, 1); }
.wheel-text { font-size: 16px; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.5); pointer-events: none; }
.spin-controls { text-align: center; }
.spin-button { min-width: 200px; font-size: 1.5em; font-weight: bold; padding: 12px 40px; border-radius: 50px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); transition: all 0.3s ease; }
.spin-button:hover:not(:disabled) { transform: scale(1.05); box-shadow: 0 6px 12px rgba(0,0,0,0.3); }
.spin-button:disabled { opacity: 0.6; cursor: not-allowed; }
.winner-result { text-align: center; animation: fadeIn 0.5s ease-in; }
.winner-result h3 { font-size: 2em; color: #2ecc71; margin: 0; }
.winner-name { color: #f39c12; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.2); }
@keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
@media (max-width: 768px) {
  .wheel-wrapper { width: 350px; height: 350px; }
  .wheel-text { font-size: 12px; }
  .spin-button { font-size: 1.2em; padding: 10px 30px; }
  .winner-result h3 { font-size: 1.5em; }
}
</style>
