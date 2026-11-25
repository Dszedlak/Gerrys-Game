<template>
  <!-- Ending your turn over the hand limit: discard or give cards away first -->
  <transition name="limit">
    <div v-if="open" class="limit" role="dialog" aria-label="Too many cards" @click.self="$emit('close')">
      <section class="limit__panel">
        <header class="limit__head">
          <div>
            <h3 class="limit__title">Too many cards to end your turn</h3>
            <p class="limit__sub">
              You can keep {{ handLimit }} in your hand. Discard or give away
              <strong>{{ over }}</strong> more card{{ over === 1 ? '' : 's' }}.
            </p>
          </div>
          <span class="limit__count" :class="{ 'is-ok': over === 0 }">{{ counted.length }}/{{ handLimit }}</span>
        </header>

        <div class="limit__grid">
          <div v-for="c in counted" :key="c.uid" class="limit__slot">
            <CardFace :card="c" size="sm" />
            <div class="limit__actions">
              <button type="button" class="limit__btn limit__btn--bad" :disabled="over === 0" @click="board.discardCard(c.uid)">
                Discard
              </button>
              <select v-model="giveTo[c.uid]" class="limit__select" :disabled="over === 0" aria-label="Give to">
                <option :value="undefined" disabled>Give to…</option>
                <option v-for="p in others" :key="p.user_id" :value="p.user_id">{{ p.username }}</option>
              </select>
              <button
                type="button"
                class="limit__btn"
                :disabled="over === 0 || giveTo[c.uid] === undefined"
                @click="board.giveCard(c.uid, giveTo[c.uid])"
              >Give</button>
            </div>
          </div>
        </div>

        <footer class="limit__foot">
          <button type="button" class="limit__btn" @click="$emit('close')">Back</button>
          <button
            type="button"
            class="limit__btn limit__btn--end"
            :disabled="over > 0"
            @click="endTurn"
          >{{ over > 0 ? `${over} more to go` : 'End turn ⏭' }}</button>
        </footer>
      </section>
    </div>
  </transition>
</template>

<script setup>
import { reactive, computed } from 'vue'
import CardFace from '@/components/board/CardFace.vue'
import { HAND_LIMIT_DECKS } from '@/components/board/boardLayout'

const props = defineProps({
  open: { type: Boolean, default: false },
  board: { type: Object, required: true },
  hand: { type: Array, default: () => [] },
  handLimit: { type: Number, default: 5 },
  // Ledger entries of everyone else, to give cards to
  others: { type: Array, default: () => [] }
})

const emit = defineEmits(['close'])

const giveTo = reactive({})
// Every card in your hand counts towards the limit
const counted = computed(() => props.hand.filter(c => HAND_LIMIT_DECKS.includes(c.deck || 'collectable')))
const over = computed(() => Math.max(0, counted.value.length - props.handLimit))

function endTurn() {
  props.board.endTurn()
  emit('close')
}
</script>

<style scoped>
.limit {
  position: fixed;
  inset: 0;
  z-index: 1050;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(11, 15, 25, 0.75);
  backdrop-filter: blur(3px);
}

.limit__panel {
  width: min(900px, 100%);
  max-height: min(760px, 100%);
  display: flex;
  flex-direction: column;
  border-radius: 14px;
  background: linear-gradient(180deg, #1A1F2E, #121726);
  border: 1px solid rgba(249, 115, 22, 0.5);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
  font-family: 'Barlow Condensed', 'Segoe UI', sans-serif;
  color: #E2E8F0;
  overflow: hidden;
}

.limit__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.15);
}

.limit__title {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 800;
  color: #FDBA74;
}

.limit__sub {
  margin: 4px 0 0;
  font-family: 'Segoe UI', system-ui, sans-serif;
  font-size: 0.9rem;
  color: #CBD5E1;
}

.limit__count {
  padding: 4px 12px;
  border-radius: 999px;
  background: rgba(249, 115, 22, 0.18);
  color: #FDBA74;
  font-size: 1.3rem;
  font-weight: 800;
}

.limit__count.is-ok { background: rgba(74, 222, 128, 0.16); color: #86EFAC; }

.limit__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 12px;
  padding: 14px 18px;
  overflow-y: auto;
}

.limit__slot { display: flex; flex-direction: column; gap: 6px; }
.limit__slot :deep(.card-face) { flex: 1; }

.limit__actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
}

.limit__actions .limit__btn--bad { grid-column: 1 / -1; }

.limit__select {
  min-width: 0;
  padding: 2px 4px;
  border-radius: 6px;
  font-size: 0.8rem;
}

.limit__btn {
  padding: 5px 10px;
  border-radius: 7px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: #0f1420;
  color: #CBD5E1;
  font-family: inherit;
  font-size: 0.92rem;
  font-weight: 700;
  cursor: pointer;
}

.limit__btn:disabled { opacity: 0.4; cursor: not-allowed; }
.limit__btn:hover:not(:disabled) { border-color: #EAB308; color: #FDE68A; }
.limit__btn--bad { border-color: rgba(248, 113, 113, 0.5); color: #FCA5A5; }

.limit__foot {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 12px 18px;
  border-top: 1px solid rgba(148, 163, 184, 0.15);
}

.limit__btn--end {
  min-width: 160px;
  border-color: rgba(34, 211, 238, 0.55);
  background: rgba(34, 211, 238, 0.12);
  color: #A5F3FC;
  font-size: 1.05rem;
}

.limit-enter-active,
.limit-leave-active { transition: opacity 0.2s ease; }
.limit-enter-from,
.limit-leave-to { opacity: 0; }
</style>
