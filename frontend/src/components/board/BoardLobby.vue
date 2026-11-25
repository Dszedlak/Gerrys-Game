<template>
  <!-- Waiting lobby: everyone readies up, then the host starts the game -->
  <section class="lobby" aria-label="Waiting lobby">
    <header class="lobby__head">
      <div class="lobby__eyebrow">Waiting lobby</div>
      <h2 class="lobby__title">{{ roomName || "Gerry's Game" }}</h2>
      <div v-if="versionName" class="lobby__version">{{ versionName }}</div>
    </header>

    <div class="lobby__status" :class="{ 'is-ready': allReady }">
      <template v-if="allReady">Everyone's ready! {{ isAdmin ? 'Start the game when you like.' : 'Waiting for the host to start.' }}</template>
      <template v-else>{{ readyCount }} of {{ players.length }} ready</template>
    </div>

    <ul class="lobby__players">
      <li
        v-for="p in players"
        :key="p.user_id"
        class="lobby__player"
        :class="{ 'is-ready': isReady(p), 'is-me': p.user_id === myUserId }"
        :style="{ '--pawn': p.color }"
      >
        <span class="lobby__avatar">
          <img v-if="p.profilePic" :src="p.profilePic" alt="" />
          <span v-else>{{ initials(p.username) }}</span>
        </span>
        <span class="lobby__piece" :title="`${p.username}'s pawn`"><BoardPawn :color="p.color" /></span>
        <span class="lobby__name">
          {{ p.username }}
          <small v-if="p.user_id === hostId" class="lobby__tag">host</small>
          <small v-if="p.user_id === myUserId" class="lobby__tag lobby__tag--me">you</small>
        </span>
        <span class="lobby__ready">{{ isReady(p) ? '✓ Ready' : 'Not ready' }}</span>
      </li>
    </ul>

    <!-- Your pawn: a colour nobody else has -->
    <section v-if="me" class="lobby__look" aria-label="Your pawn">
      <div class="lobby__look-preview">
        <BoardPawn :color="me.color" />
      </div>
      <div class="lobby__look-pickers">
        <div class="lobby__look-label">Your pawn's colour</div>
        <div class="lobby__swatches" role="radiogroup" aria-label="Pawn colour">
          <button
            v-for="c in colorOptions"
            :key="c.name"
            type="button"
            role="radio"
            class="lobby__swatch"
            :class="{ 'is-mine': c.mine, 'is-taken': c.takenBy }"
            :style="{ '--swatch': c.hex }"
            :aria-checked="c.mine"
            :aria-label="c.takenBy ? `${c.name} (taken by ${c.takenBy})` : c.name"
            :title="c.takenBy ? `${c.name}: taken by ${c.takenBy}` : c.name"
            :disabled="Boolean(c.takenBy)"
            @click="board.setLook({ color: c.name })"
          ><span v-if="c.takenBy" class="lobby__swatch-x">✕</span></button>
        </div>
      </div>
    </section>

    <div class="lobby__actions">
      <button
        type="button"
        class="lobby__btn"
        :class="meReady ? 'lobby__btn--undo' : 'lobby__btn--ready'"
        @click="board.setReady(!meReady)"
      >{{ meReady ? 'Not ready after all' : "✓ I'm ready" }}</button>

      <template v-if="isAdmin">
        <button
          type="button"
          class="lobby__btn lobby__btn--start"
          :disabled="!allReady"
          :title="allReady ? 'Start the game' : 'Waiting for everyone to ready up'"
          @click="board.start()"
        >🎲 Start game</button>
        <button
          v-if="!allReady"
          type="button"
          class="lobby__btn lobby__btn--force"
          @click="forceStart"
        >⏩ Force start</button>
      </template>
    </div>

    <p class="lobby__how">
      When the game starts, everyone rolls the die. The highest roll takes the first turn
      (a tie at the top rolls again), and then the game begins.
    </p>
  </section>
</template>

<script setup>
import { askConfirm } from '@/composables/useConfirm'
import { computed } from 'vue'
import BoardPawn from '@/components/board/BoardPawn.vue'
import { PAWN_COLORS } from '@/components/board/boardLayout'

const props = defineProps({
  board: { type: Object, required: true },
  state: { type: Object, default: null },
  // Ledger entries from BoardView
  players: { type: Array, default: () => [] },
  myUserId: { type: [Number, String], default: null },
  hostId: { type: [Number, String], default: null },
  isAdmin: { type: Boolean, default: false },
  roomName: { type: String, default: '' },
  versionName: { type: String, default: '' }
})

const me = computed(() => props.players.find(p => p.user_id === props.myUserId) || null)

// Every colour, with who has it (a colour belongs to one player only)
const colorOptions = computed(() =>
  Object.entries(PAWN_COLORS).map(([name, hex]) => {
    const owner = props.players.find(p => p.colorName === name && p.user_id !== props.myUserId)
    return { name, hex, mine: me.value?.colorName === name, takenBy: owner?.username || null }
  })
)

const ready = computed(() => props.state?.ready || {})
const isReady = (p) => Boolean(ready.value[String(p.user_id)])
const meReady = computed(() => Boolean(ready.value[String(props.myUserId)]))
const readyCount = computed(() => props.players.filter(isReady).length)
const allReady = computed(() => props.players.length > 0 && readyCount.value === props.players.length)

function initials(name) {
  return String(name || '?').split(/[\s_]+/).filter(Boolean).slice(0, 2).map(w => w[0].toUpperCase()).join('') || '?'
}

async function forceStart() {
  const waiting = props.players.filter(p => !isReady(p)).map(p => p.username)
  if (await askConfirm(`Start without waiting for ${waiting.join(', ')}?`)) props.board.start(true)
}
</script>

<style scoped>
.lobby {
  width: min(720px, 100%);
  margin: 24px auto;
  padding: 24px 28px 28px;
  border-radius: 16px;
  background: linear-gradient(180deg, #1A1F2E, #121726);
  border: 1px solid rgba(234, 179, 8, 0.35);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.45);
  font-family: 'Barlow Condensed', 'Segoe UI', sans-serif;
  color: #E2E8F0;
  text-align: center;
}

.lobby__eyebrow {
  font-size: 0.9rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #22D3EE;
}

.lobby__title {
  margin: 2px 0 0;
  font-size: 2.4rem;
  font-weight: 800;
  color: #FDE68A;
}

.lobby__version { color: #64748B; font-size: 1rem; }

.lobby__status {
  display: inline-block;
  margin: 16px 0 14px;
  padding: 6px 16px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.12);
  color: #CBD5E1;
  font-size: 1.1rem;
  font-weight: 700;
}

.lobby__status.is-ready { background: rgba(74, 222, 128, 0.15); color: #86EFAC; }

.lobby__players {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
  text-align: left;
}

.lobby__player {
  --pawn: #94A3B8;
  display: grid;
  grid-template-columns: auto 1fr;
  grid-template-rows: auto auto;
  column-gap: 10px;
  align-items: center;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(148, 163, 184, 0.15);
  border-left: 4px solid var(--pawn);
  transition: border-color 0.2s ease, background 0.2s ease;
}

.lobby__player.is-ready {
  border-color: rgba(74, 222, 128, 0.5);
  border-left-color: var(--pawn);
  background: rgba(22, 101, 52, 0.18);
}

.lobby__avatar {
  grid-row: 1 / 3;
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  overflow: hidden;
  background: var(--pawn);
  color: #fff;
  font-size: 1.2rem;
  font-weight: 800;
}

.lobby__avatar img { width: 100%; height: 100%; object-fit: cover; }

.lobby__name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 1.15rem;
  font-weight: 700;
}

.lobby__tag {
  margin-left: 4px;
  padding: 0 5px;
  border-radius: 4px;
  background: rgba(234, 179, 8, 0.2);
  color: #FDE68A;
  font-size: 0.7rem;
  text-transform: uppercase;
}

.lobby__tag--me { background: rgba(34, 211, 238, 0.2); color: #A5F3FC; }

.lobby__ready { font-size: 0.95rem; color: #64748B; }
.lobby__player.is-ready .lobby__ready { color: #86EFAC; font-weight: 700; }

.lobby__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
  margin-top: 22px;
}

.lobby__btn {
  padding: 10px 22px;
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.4);
  background: #0f1420;
  color: #E2E8F0;
  font-family: inherit;
  font-size: 1.2rem;
  font-weight: 800;
  cursor: pointer;
  transition: transform 0.12s ease;
}

.lobby__btn:hover:not(:disabled) { transform: translateY(-1px); }
.lobby__btn:disabled { opacity: 0.45; cursor: not-allowed; }
.lobby__btn--ready { border-color: #22C55E; background: linear-gradient(180deg, #22C55E, #15803D); color: #fff; }
.lobby__btn--undo { color: #94A3B8; }
.lobby__btn--start { border-color: #EAB308; background: linear-gradient(180deg, #EAB308, #CA8A04); color: #1c1917; }
.lobby__btn--force { border-color: rgba(234, 179, 8, 0.6); color: #FDE68A; }

.lobby__how {
  margin: 18px auto 0;
  max-width: 480px;
  font-family: 'Segoe UI', system-ui, sans-serif;
  font-size: 0.88rem;
  color: #64748B;
}

/* Your piece */
.lobby__piece { width: 22px; flex: 0 0 22px; }

.lobby__look {
  display: grid;
  grid-template-columns: 86px minmax(0, 1fr);
  align-items: center;
  gap: 16px;
  margin: 14px 0;
  padding: 14px 16px;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(148, 163, 184, 0.18);
}

.lobby__look-preview {
  width: 70px;
  justify-self: center;
  filter: drop-shadow(0 6px 14px rgba(0, 0, 0, 0.5));
}

.lobby__look-pickers { display: grid; gap: 6px; min-width: 0; }

.lobby__look-label {
  font-size: 0.74rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #94A3B8;
}

.lobby__swatches { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 6px; }

.lobby__swatch {
  position: relative;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.25);
  background: var(--swatch);
  cursor: pointer;
  transition: transform 0.12s ease, box-shadow 0.15s ease;
}

.lobby__swatch:hover:not(:disabled) { transform: scale(1.1); }
.lobby__swatch.is-mine { border-color: #fff; box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.35), 0 0 14px var(--swatch); }
.lobby__swatch.is-taken { opacity: 0.35; cursor: not-allowed; }

.lobby__swatch-x {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: #0B0F19;
  font-weight: 900;
  font-size: 0.9rem;
}


@media (max-width: 560px) {
  .lobby__look { grid-template-columns: 1fr; }
}
</style>
