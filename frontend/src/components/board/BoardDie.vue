<template>
  <div
    class="board-die"
    :class="[`board-die--${variant}`, { 'is-tumbling': tumbling }]"
    :style="{ '--die-size': size }"
  >
    <div class="board-die__tilt">
      <div class="board-die__cube" :style="{ transform: cubeTransform }">
        <div
          v-for="face in FACES"
          :key="face.value"
          class="board-die__face"
          :style="{ transform: `${face.place} translateZ(calc(var(--die-size) / 2))` }"
        >
          <span
            v-for="cell in 9"
            :key="cell"
            class="board-die__pip"
            :class="{ 'is-on': PIPS[face.value].includes(cell) }"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  value: { type: Number, default: 1 },
  // Tumble in on mount. The parent re-keys the die for every new roll, so
  // rolling the same number twice still animates; it passes false on first
  // load so joining a game mid-way doesn't replay the last roll.
  animate: { type: Boolean, default: false },
  variant: { type: String, default: 'black' }, // black | bone | toxic
  // Any CSS length (not a percentage: the faces are pushed out with translateZ)
  size: { type: String, default: '48px' }
})

// Where each face sits on the cube, and the rotation that brings it to the front
const FACES = [
  { value: 1, place: 'rotateY(0deg)', show: { x: 0, y: 0 } },
  { value: 6, place: 'rotateY(180deg)', show: { x: 0, y: 180 } },
  { value: 2, place: 'rotateY(90deg)', show: { x: 0, y: -90 } },
  { value: 5, place: 'rotateY(-90deg)', show: { x: 0, y: 90 } },
  { value: 3, place: 'rotateX(90deg)', show: { x: -90, y: 0 } },
  { value: 4, place: 'rotateX(-90deg)', show: { x: 90, y: 0 } }
]

// Pip cells on a 3×3 grid, numbered 1-9 left to right, top to bottom
const PIPS = {
  1: [5],
  2: [1, 9],
  3: [1, 5, 9],
  4: [1, 3, 7, 9],
  5: [1, 3, 5, 7, 9],
  6: [1, 3, 4, 6, 7, 9]
}

// Before an animated roll lands, the die sits on a neutral face; once
// mounted it turns to the real value and the CSS transition does the tumble.
const landed = ref(!props.animate)
const tumbling = ref(false)
let tumbleTimer = null
let frame = null

onMounted(() => {
  if (!props.animate) return
  // Two frames so the neutral pose is painted before we change it
  frame = requestAnimationFrame(() => {
    frame = requestAnimationFrame(() => {
      landed.value = true
      tumbling.value = true
      tumbleTimer = setTimeout(() => { tumbling.value = false }, 1100)
    })
  })
})

onBeforeUnmount(() => {
  clearTimeout(tumbleTimer)
  cancelAnimationFrame(frame)
})

// A different spin direction per die, so a pair doesn't move in lockstep
const spinDir = Math.random() < 0.5 ? 1 : -1

const cubeTransform = computed(() => {
  if (!landed.value) return 'rotateX(0deg) rotateY(0deg)'
  const face = FACES.find(f => f.value === props.value) || FACES[0]
  // Whole extra turns don't change which face ends up in front, but they
  // make the transition tumble.
  const turns = props.animate ? 2 : 0
  return `rotateX(${face.show.x + 360 * turns * spinDir}deg) rotateY(${face.show.y + 360 * turns}deg)`
})
</script>

<style scoped>
.board-die {
  width: var(--die-size);
  height: var(--die-size);
  perspective: 600px;
}

.board-die.is-tumbling {
  animation: die-bounce 1.1s cubic-bezier(.3, .6, .3, 1);
}

.board-die__tilt {
  width: 100%;
  height: 100%;
  transform-style: preserve-3d;
  transform: rotateX(-22deg) rotateY(-28deg);
}

.board-die__cube {
  position: relative;
  width: 100%;
  height: 100%;
  transform-style: preserve-3d;
  transition: transform 1.05s cubic-bezier(.15, .75, .25, 1);
}

.board-die__face {
  position: absolute;
  inset: 0;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(3, 1fr);
  padding: 14%;
  border-radius: 18%;
  background: var(--die-face);
  box-shadow: inset 0 0 0 1px var(--die-edge), inset 0 -6px 12px rgba(0, 0, 0, 0.35);
  backface-visibility: hidden;
}

.board-die__pip {
  place-self: center;
  width: 64%;
  aspect-ratio: 1;
  border-radius: 50%;
}

.board-die__pip.is-on {
  background: var(--die-pip);
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.5);
}

/* Variants */
.board-die--black {
  --die-face: radial-gradient(circle at 30% 25%, #3a3f4b, #0d1016 75%);
  --die-edge: rgba(255, 255, 255, 0.12);
  --die-pip: #F8FAFC;
}

.board-die--bone {
  --die-face: radial-gradient(circle at 30% 25%, #fbf7ec, #d9cfb4 80%);
  --die-edge: rgba(0, 0, 0, 0.18);
  --die-pip: #7f1d1d;
}

.board-die--toxic {
  --die-face: radial-gradient(circle at 30% 25%, #bef264, #3f6212 85%);
  --die-edge: rgba(0, 0, 0, 0.2);
  --die-pip: #1a2e05;
}

@keyframes die-bounce {
  0%   { transform: translateY(0) scale(1); }
  20%  { transform: translateY(-38%) scale(1.08); }
  45%  { transform: translateY(0) scale(0.96); }
  62%  { transform: translateY(-12%) scale(1.02); }
  80%  { transform: translateY(0) scale(1); }
  100% { transform: translateY(0) scale(1); }
}

</style>
