<template>
  <!-- The last player standing wins: everyone sees it; the admin can end the game from here -->
  <transition name="winner">
    <div v-if="open" class="winner" role="dialog" aria-label="Game over">
      <section class="winner__panel" :style="{ '--pawn': player?.color || '#EAB308' }">
        <div class="winner__trophy">🏆</div>
        <div class="winner__eyebrow">Game over</div>
        <h2 class="winner__title">{{ isMe ? 'You won!' : `${player?.username || 'Someone'} wins!` }}</h2>
        <p class="winner__sub">
          {{ isMe ? "You're the last player standing: everyone else's time has run out." :
            `${player?.username || 'They'} is the last player standing: everyone else's time has run out.` }}
        </p>
        <div class="winner__btns">
          <button v-if="isAdmin" type="button" class="winner__btn winner__btn--go" @click="$emit('end-game')">
            End the game &amp; see the history
          </button>
          <button type="button" class="winner__btn" @click="$emit('close')">Close</button>
        </div>
      </section>
    </div>
  </transition>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  // Ledger entry of the winner
  player: { type: Object, default: null },
  myUserId: { type: [Number, String], default: null },
  isAdmin: { type: Boolean, default: false }
})

defineEmits(['close', 'end-game'])

const isMe = computed(() => props.player && props.player.user_id === props.myUserId)
</script>

<style scoped>
.winner {
  position: fixed;
  inset: 0;
  z-index: 1060;
  display: grid;
  place-items: center;
  padding: 16px;
  background: radial-gradient(circle at 50% 40%, rgba(234, 179, 8, 0.25), rgba(3, 6, 12, 0.85) 65%);
  backdrop-filter: blur(3px);
}

.winner__panel {
  width: min(440px, 100%);
  padding: 26px 24px 20px;
  border-radius: 20px;
  text-align: center;
  background: linear-gradient(180deg, #1F1A0C, #121726);
  border: 2px solid #EAB308;
  box-shadow: 0 0 0 6px color-mix(in srgb, var(--pawn) 35%, transparent), 0 30px 70px rgba(0, 0, 0, 0.6);
  color: #E2E8F0;
}

.winner__trophy { font-size: 4rem; line-height: 1; animation: winner-bounce 1.4s ease-in-out infinite; }

.winner__eyebrow {
  margin-top: 8px;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 0.9rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #22D3EE;
}

.winner__title {
  margin: 2px 0 6px;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 2.4rem;
  font-weight: 800;
  color: #FDE68A;
}

.winner__sub { margin: 0; font-size: 0.92rem; color: #CBD5E1; }

.winner__btns { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin-top: 18px; }

.winner__btn {
  padding: 9px 16px;
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.45);
  background: rgba(148, 163, 184, 0.1);
  color: #E2E8F0;
  font-weight: 700;
  cursor: pointer;
}

.winner__btn--go { border-color: #EAB308; background: rgba(234, 179, 8, 0.2); color: #FDE68A; }

@keyframes winner-bounce {
  0%, 100% { transform: translateY(0) rotate(-4deg); }
  50% { transform: translateY(-8px) rotate(4deg); }
}

@media (prefers-reduced-motion: reduce) {
  .winner__trophy { animation: none; }
}

.winner-enter-active, .winner-leave-active { transition: opacity 0.25s ease; }
.winner-enter-from, .winner-leave-to { opacity: 0; }
</style>
