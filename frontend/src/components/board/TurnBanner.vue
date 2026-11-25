<template>
  <!-- Whenever the turn passes on: the screen darkens and says whose turn it is -->
  <transition name="banner">
    <div v-if="shown" class="banner" :class="{ 'is-mine': shown.mine }" role="status" @click="hide">
      <div class="banner__inner" :style="{ '--pawn': shown.color }">
        <div class="banner__round">Round {{ shown.round }}</div>
        <div class="banner__name">
          <span class="banner__dot" />
          <template v-if="shown.mine">Your turn!</template>
          <template v-else>{{ shown.name }}'s turn</template>
        </div>
        <div v-if="shown.mine" class="banner__sub">Collect your income, then roll the die</div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, watch, onBeforeUnmount } from 'vue'

const props = defineProps({
  state: { type: Object, default: null },
  phase: { type: String, default: 'loading' },
  playersById: { type: Object, default: () => ({}) },
  myUserId: { type: [Number, String], default: null }
})

const SHOW_MS = 2200

const shown = ref(null)
let timer = null
let seen = undefined // the turn we last knew about (undefined: none yet)

function hide() {
  clearTimeout(timer)
  shown.value = null
}

// Only a turn passing on while you watch: not on joining, and not the very first
// turn (the first-turn pop-up already says who starts).
watch(() => [props.phase, props.state?.turn_seq, props.state?.turn?.user_id], ([phase, seq, uid]) => {
  if (phase !== 'playing' || seq == null) {
    seen = phase === 'initiative' ? null : seen
    return
  }
  const key = `${seq}:${uid}`
  const first = seen === undefined || seen === null
  if (key === seen) return
  seen = key
  if (first || uid == null) return
  const p = props.playersById[uid]
  shown.value = {
    name: p?.username || 'Someone',
    color: p?.color || '#EAB308',
    mine: uid === props.myUserId,
    round: props.state?.round
  }
  clearTimeout(timer)
  timer = setTimeout(hide, SHOW_MS)
}, { immediate: true })

onBeforeUnmount(() => clearTimeout(timer))
</script>

<style scoped>
.banner {
  position: fixed;
  inset: 0;
  z-index: 1030;
  display: grid;
  place-items: center;
  background: rgba(3, 6, 12, 0.72);
  cursor: pointer;
}

.banner__inner {
  --pawn: #EAB308;
  padding: 26px 56px 30px;
  text-align: center;
  border-top: 2px solid var(--pawn);
  border-bottom: 2px solid var(--pawn);
  background: linear-gradient(90deg, transparent, rgba(15, 23, 42, 0.92) 18%, rgba(15, 23, 42, 0.92) 82%, transparent);
  width: 100%;
}

.banner__round {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1rem;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: #94A3B8;
}

.banner__name {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: clamp(2.4rem, 7vw, 4.6rem);
  font-weight: 800;
  letter-spacing: 0.02em;
  line-height: 1.1;
  color: #F8FAFC;
  text-shadow: 0 4px 24px rgba(0, 0, 0, 0.6);
}

.banner.is-mine .banner__name { color: #FDE68A; }

.banner__dot {
  width: 0.45em;
  height: 0.45em;
  border-radius: 50%;
  background: var(--pawn);
  box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.12), 0 0 22px var(--pawn);
}

.banner__sub {
  margin-top: 6px;
  font-size: 1rem;
  color: #CBD5E1;
}

.banner-enter-active { transition: opacity 0.25s ease; }
.banner-leave-active { transition: opacity 0.45s ease; }
.banner-enter-active .banner__inner { animation: banner-in 0.5s cubic-bezier(0.2, 0.9, 0.3, 1.2); }
.banner-enter-from, .banner-leave-to { opacity: 0; }

@keyframes banner-in {
  from { transform: scaleY(0.2); opacity: 0; letter-spacing: 0.3em; }
}
</style>
