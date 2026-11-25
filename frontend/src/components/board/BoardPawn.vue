<template>
  <svg class="board-pawn" viewBox="0 0 40 54" :style="{ '--pawn': color }" :aria-label="label" role="img">
    <!-- A player's piece on the board: pawn, rook, knight, bishop, queen or king,
         shaded so it reads as a solid piece. Colour comes in as a hex. -->
    <defs>
      <radialGradient :id="`${uid}-shine`" cx="35%" cy="30%" r="75%">
        <stop offset="0%" stop-color="#fff" stop-opacity="0.75" />
        <stop offset="35%" stop-color="#fff" stop-opacity="0.12" />
        <stop offset="100%" stop-color="#000" stop-opacity="0.38" />
      </radialGradient>
    </defs>
    <ellipse cx="20" cy="50.5" rx="15" ry="3" class="board-pawn__shadow" />
    <g class="board-pawn__piece">
      <component :is="s.tag" v-for="(s, i) in shapes" :key="`p${i}`" v-bind="s.attrs">{{ s.text }}</component>
    </g>
    <g :fill="`url(#${uid}-shine)`">
      <component :is="s.tag" v-for="(s, i) in shapes" :key="`s${i}`" v-bind="s.attrs">{{ s.text }}</component>
    </g>
  </svg>
</template>

<script setup>
import { computed } from 'vue'
import { PIECE_SHAPES, PIECE_LABELS } from '@/components/board/pieces'

const props = defineProps({
  color: { type: String, default: '#94A3B8' },
  // see PIECES in pieces.js (pawn, rook, ... top hat, car, rocket, duck ...)
  piece: { type: String, default: 'pawn' }
})

// Gradient ids must be unique per instance in the document
const uid = `pawn-${Math.random().toString(36).slice(2, 10)}`

const shapes = computed(() => PIECE_SHAPES[props.piece] || PIECE_SHAPES.pawn)
const label = computed(() => PIECE_LABELS[props.piece] || 'Pawn')
</script>

<style scoped>
.board-pawn {
  display: block;
  width: 100%;
  height: auto;
  overflow: visible;
}

.board-pawn__piece {
  fill: var(--pawn);
  stroke: rgba(0, 0, 0, 0.45);
  stroke-width: 0.8;
}

.board-pawn__shadow {
  fill: rgba(0, 0, 0, 0.45);
}
</style>
