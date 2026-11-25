<template>
  <!-- Your tile's actions, in the middle of the board. Minimise it to see the board
       (and click the piles); it comes back from the tab at the bottom. -->
  <transition name="action">
    <div v-if="open && !minimised" class="action" role="dialog" :aria-label="`${tileLabel}: your actions`" @click.self="$emit('minimise')">
      <div class="action__panel">
        <div class="action__eyebrow">
          <span>Your turn · step 3</span>
          <button type="button" class="action__min" title="Minimise (see the board)" aria-label="Minimise" @click="$emit('minimise')">–</button>
        </div>

        <TileAction
          :board="board"
          :state="state"
          :playersById="playersById"
          :myUserId="myUserId"
          :doctorInPlay="doctorInPlay"
          :priceMultiplier="priceMultiplier"
          :governmentName="governmentName"
          @open-card="$emit('open-card')"
          @open-discard="$emit('open-discard')"
          @set-approval="(s) => $emit('set-approval', s)"
          @rolled="(kind) => $emit('rolled', kind)"
        />

        <!-- No End turn here: that's in the turn panel, once you're done -->
        <div class="action__foot">
          <button type="button" class="action__btn" @click="$emit('minimise')">Minimise</button>
        </div>
      </div>
    </div>
  </transition>

  <transition name="action-tab">
    <button
      v-if="open && minimised"
      type="button"
      class="action-tab"
      :class="{ 'is-urgent': Boolean(blocker) }"
      @click="$emit('restore')"
    >
      <span class="action-tab__arrow">▲</span>
      <span><strong>{{ tileLabel }}</strong> · {{ blocker ? blocker : 'your actions' }}</span>
    </button>
  </transition>
</template>

<script setup>
import { computed } from 'vue'
import TileAction from '@/components/board/TileAction.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  minimised: { type: Boolean, default: false },
  board: { type: Object, required: true },
  state: { type: Object, default: null },
  playersById: { type: Object, default: () => ({}) },
  myUserId: { type: [Number, String], default: null },
  doctorInPlay: { type: Boolean, default: false },
  priceMultiplier: { type: Number, default: 1 },
  governmentName: { type: String, default: 'Democracy' }
})

defineEmits(['minimise', 'restore', 'rolled', 'open-card', 'open-discard', 'set-approval'])

const tileLabel = computed(() => {
  const pos = props.state?.positions?.[String(props.myUserId)]
  return props.state?.tiles?.[pos]?.label || 'Your tile'
})

// What still has to happen before the turn can end
const blocker = computed(() => {
  const s = props.state
  if (s?.event && !s.event.done) return `Finish “${s.event.title}” first`
  if (s?.pending && s.pending.user_id === props.myUserId) return 'Your card needs a decision'
  const debt = s?.debts?.[String(props.myUserId)]
  if (debt && debt.paid_seq !== s?.turn_seq) return `Pay 1–3 hours off your ${debt.title} bill first`
  return ''
})
</script>

<style scoped>
.action {
  position: absolute;
  inset: 0;
  z-index: 35;
  display: grid;
  place-items: center;
  padding: 16px;
  background: rgba(11, 15, 25, 0.45);
}

.action__panel {
  width: min(440px, 100%);
  max-height: 100%;
  overflow-y: auto;
  padding: 14px 18px 16px;
  border-radius: 16px;
  background: linear-gradient(180deg, #1A1F2E, #121726);
  border: 1px solid rgba(234, 179, 8, 0.55);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.55), 0 0 30px rgba(234, 179, 8, 0.12);
}

.action__eyebrow {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 0.82rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #FDE68A;
}

.action__min {
  width: 30px;
  height: 26px;
  padding: 0;
  border-radius: 7px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: transparent;
  color: #CBD5E1;
  font-size: 1.2rem;
  font-weight: 700;
  line-height: 1;
  cursor: pointer;
}

.action__min:hover { border-color: #EAB308; color: #fff; }

.action__blocker {
  margin: 12px 0 0;
  font-size: 0.82rem;
  color: #FDBA74;
  text-align: center;
}

.action__foot {
  display: flex;
  gap: 8px;
  margin-top: 14px;
}

.action__btn {
  flex: 1;
  padding: 9px 12px;
  border-radius: 9px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: rgba(148, 163, 184, 0.08);
  color: #E2E8F0;
  font-weight: 700;
  font-size: 0.92rem;
  cursor: pointer;
}

.action__btn:hover:not(:disabled) { border-color: #EAB308; }
.action__btn:disabled { opacity: 0.45; cursor: not-allowed; }

.action__btn--end {
  flex: 1.4;
  border-color: rgba(34, 211, 238, 0.55);
  background: rgba(34, 211, 238, 0.12);
  color: #A5F3FC;
}

/* The minimised tab */
.action-tab {
  position: absolute;
  left: 50%;
  bottom: 12px;
  z-index: 35;
  display: flex;
  align-items: center;
  gap: 8px;
  max-width: calc(100% - 32px);
  padding: 8px 16px;
  border-radius: 999px;
  border: 1px solid rgba(234, 179, 8, 0.7);
  background: rgba(18, 23, 38, 0.94);
  color: #FDE68A;
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
  transform: translateX(-50%);
  cursor: pointer;
}

.action-tab:hover { background: #1F2937; }
.action-tab.is-urgent { border-color: #A78BFA; color: #DDD6FE; animation: tab-pulse 1.6s ease-in-out infinite; }
.action-tab__arrow { font-size: 0.7rem; }

@keyframes tab-pulse { 50% { box-shadow: 0 0 20px rgba(167, 139, 250, 0.55); } }

.action-enter-active, .action-leave-active { transition: opacity 0.2s ease; }
.action-enter-active .action__panel, .action-leave-active .action__panel { transition: transform 0.22s ease; }
.action-enter-from, .action-leave-to { opacity: 0; }
.action-enter-from .action__panel, .action-leave-to .action__panel { transform: scale(0.94) translateY(20px); }

.action-tab-enter-active, .action-tab-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.action-tab-enter-from, .action-tab-leave-to { opacity: 0; transform: translate(-50%, 12px); }
</style>
