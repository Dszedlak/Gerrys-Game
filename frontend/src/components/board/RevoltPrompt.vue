<template>
  <!-- Peasant's Revolt: you (a peasant) share a tile with a government leader.
       Works on anyone's turn, once per leader per turn. -->
  <transition name="revolt">
    <div v-if="targets.length" class="revolt" role="region" aria-label="Peasant's Revolt">
      <div class="revolt__head">
        <span class="revolt__icon">✊</span>
        <div>
          <strong>Peasant's Revolt!</strong>
          <small>You're on the same tile as {{ names }}. Steal 1 hour and throw a free Throwing Knife.</small>
        </div>
      </div>
      <div class="revolt__btns">
        <button
          v-for="t in targets"
          :key="t.user_id"
          type="button"
          class="revolt__btn"
          :style="{ '--pawn': t.color }"
          @click="revolt(t)"
        >✊ Revolt against {{ t.username }} <span>({{ t.govRole }})</span></button>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { computed } from 'vue'
import { askConfirm } from '@/composables/useConfirm'

const props = defineProps({
  board: { type: Object, required: true },
  // Ledger entries of the leaders you can revolt against
  targets: { type: Array, default: () => [] }
})

const names = computed(() => props.targets.map(t => `${t.username} (${t.govRole})`).join(' and '))

async function revolt(t) {
  if (await askConfirm(`Start a Peasant's Revolt against ${t.username}? You steal 1 hour from them and they take 20 minutes of bleeding.`, { confirmText: 'Revolt!' })) {
    props.board.peasantRevolt(t.user_id)
  }
}
</script>

<style scoped>
.revolt {
  position: fixed;
  left: 50%;
  bottom: 18px;
  transform: translateX(-50%);
  z-index: 1030;
  width: min(520px, calc(100vw - 32px));
  padding: 12px 14px;
  border-radius: 14px;
  background: linear-gradient(180deg, #3B1212, #1F0A0A);
  border: 1px solid rgba(248, 113, 113, 0.7);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.55), 0 0 0 3px rgba(239, 68, 68, 0.18);
  color: #FEE2E2;
}

.revolt__head { display: flex; gap: 10px; align-items: flex-start; }
.revolt__icon { font-size: 1.6rem; line-height: 1; }
.revolt__head strong { display: block; font-family: 'Barlow Condensed', sans-serif; font-size: 1.25rem; letter-spacing: 0.03em; color: #FCA5A5; }
.revolt__head small { display: block; font-size: 0.82rem; color: #FECACA; }

.revolt__btns { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }

.revolt__btn {
  flex: 1 1 auto;
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid #F87171;
  border-left: 5px solid var(--pawn, #F87171);
  background: rgba(239, 68, 68, 0.22);
  color: #FFF1F2;
  font-weight: 800;
  cursor: pointer;
}

.revolt__btn:hover { background: rgba(239, 68, 68, 0.38); }
.revolt__btn span { font-weight: 600; color: #FECACA; }

.revolt-enter-active, .revolt-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.revolt-enter-from, .revolt-leave-to { opacity: 0; transform: translate(-50%, 12px); }
</style>
