<template>
  <!-- The assignment board: up to 6 slips, each with its black-bag target -->
  <section class="assign" aria-label="Assignment board">
    <button type="button" class="assign__head" :aria-expanded="!collapsed" @click="toggle">
      <span class="assign__chevron" :class="{ 'is-open': !collapsed }">▸</span>
      <span class="assign__eyebrow">📜 Assignments</span>
      <span v-if="collapsed && targetingMe" class="assign__alert">🎯 {{ targetingMe }} on you</span>
      <span class="assign__count">{{ assignments.length }}/{{ max }}</span>
    </button>

    <template v-if="!collapsed">
    <p v-if="bounty" class="assign__bounty">
      🎯 Bounty Board: {{ bounty.left }} left — complete one against anyone with a title for double the reward (they're demoted).
    </p>

    <p v-if="!assignments.length" class="assign__empty">
      No assignments yet. Land on an Assignment Slip tile to draw one.
    </p>

    <ul v-else class="assign__list">
      <li
        v-for="a in assignments"
        :key="a.id"
        class="assign__item"
        :class="{ 'is-mine': a.target === myUserId }"
        :style="{ '--pawn': playersById[a.target]?.color || '#94A3B8' }"
      >
        <!-- The target, front and centre, in their pawn colour -->
        <div class="assign__target" :title="`Target: ${playersById[a.target]?.username || 'someone'}`">
          <span class="assign__aim">🎯 Target</span>
          <span class="assign__who">
            <span class="assign__dot" />
            <span class="assign__target-name">
              {{ a.target === myUserId ? "You're the target!" : playersById[a.target]?.username || 'Unknown' }}
            </span>
          </span>
        </div>
        <div class="assign__body">
          <div class="assign__title">
            {{ a.card?.title || 'Assignment' }}
            <span v-if="a.card?.example" class="assign__example">example</span>
          </div>
          <div class="assign__text">{{ a.card?.text }}</div>
        </div>
        <button
          v-if="(a.target !== myUserId || bountyTargets(a).length) && canClaim"
          type="button"
          class="assign__claim"
          :disabled="claimedThisTurn"
          :title="claimedThisTurn ? 'You can only complete one assignment per turn' : 'You completed it: claim the reward and keep the slip'"
          @click="claim(a)"
        >Claim reward</button>
        <TargetSelect
          v-if="picking?.id === a.id"
          :label="picking.step === 'against' ? 'Completed against:' : 'Reward on:'"
          :players="picking.step === 'against' ? bountyTargets(a, true) : others"
          @pick="(uid) => finish(a, uid)"
          @cancel="picking = null"
        />
      </li>
    </ul>
    </template>
  </section>
</template>

<script setup>
import { askConfirm } from '@/composables/useConfirm'
import { ref, computed, h } from 'vue'
import { useCollapsed } from '@/composables/useCollapsed'

const props = defineProps({
  board: { type: Object, required: true },
  assignments: { type: Array, default: () => [] },
  max: { type: Number, default: 6 },
  playersById: { type: Object, default: () => ({}) },
  myUserId: { type: [Number, String], default: null },
  started: { type: Boolean, default: false },
  claimedThisTurn: { type: Boolean, default: false },
  // Bounty Board in play: { left } (see OngoingCards)
  bounty: { type: Object, default: null }
})

const picking = ref(null)
const { collapsed, toggle } = useCollapsed('assignments.v2', true)
const targetingMe = computed(() => props.assignments.filter(a => a.target === props.myUserId).length)
const canClaim = computed(() => props.started && Boolean(props.playersById[props.myUserId]?.alive))
const others = computed(() => Object.values(props.playersById).filter(p => p.alive && p.user_id !== props.myUserId))

// Bounty Board: anyone with a title (other than me) is fair game, as well as the slip's own target
function bountyTargets(a, withOwn = false) {
  if (!props.bounty) return []
  const titled = Object.values(props.playersById).filter(p => p.perk && p.alive && p.user_id !== props.myUserId)
  const own = withOwn && a.target !== props.myUserId ? [props.playersById[a.target]].filter(Boolean) : []
  return [...own, ...titled.filter(p => p.user_id !== a.target)]
}

async function claim(a) {
  if (bountyTargets(a).length) {
    picking.value = { id: a.id, step: 'against', against: null }
    return
  }
  const target = props.playersById[a.target]?.username || 'your target'
  if (!await askConfirm(`Claim “${a.card?.title}” against ${target}? Only claim it if you really completed it — it's written to the log.`)) return
  if (a.card?.needs_target) picking.value = { id: a.id, step: 'reward', against: null }
  else props.board.claimAssignment(a.id)
}

async function finish(a, uid) {
  const p = picking.value
  picking.value = null
  if (p?.step === 'against') {
    const name = props.playersById[uid]?.username || 'them'
    if (!await askConfirm(`Claim “${a.card?.title}” against ${name}? Only claim it if you really completed it — it's written to the log.`)) return
    const against = uid === a.target ? null : uid
    if (a.card?.needs_target) picking.value = { id: a.id, step: 'reward', against }
    else props.board.claimAssignment(a.id, null, against)
    return
  }
  props.board.claimAssignment(a.id, uid, p?.against ?? null)
}

const TargetSelect = (p, { emit }) =>
  h('div', { class: 'assign__picker' }, [
    h('span', p.label || 'Reward on:'),
    ...p.players.map(pl => h('button', { type: 'button', onClick: () => emit('pick', pl.user_id) }, pl.username)),
    h('button', { type: 'button', onClick: () => emit('cancel') }, 'Cancel')
  ])
TargetSelect.props = ['players', 'label']
TargetSelect.emits = ['pick', 'cancel']
</script>

<style scoped>
.assign__bounty {
  margin: 0 0 8px;
  padding: 6px 10px;
  border-radius: 8px;
  background: rgba(234, 179, 8, 0.12);
  border: 1px solid rgba(234, 179, 8, 0.5);
  color: #FDE68A;
  font-size: 0.88rem;
}

.assign {
  padding: 10px 12px 12px;
  border-radius: 12px;
  background: linear-gradient(180deg, #1A1F2E, #121726);
  border: 1px solid rgba(249, 115, 22, 0.3);
  font-family: 'Barlow Condensed', 'Segoe UI', sans-serif;
  color: #E2E8F0;
}

.assign__head {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  margin: 0;
  padding: 0;
  border: 0;
  background: none;
  font: inherit;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.assign__head + * { margin-top: 8px; }

.assign__chevron {
  display: inline-block;
  width: 12px;
  color: #FDBA74;
  transition: transform 0.15s ease;
}

.assign__chevron.is-open { transform: rotate(90deg); }

.assign__alert {
  padding: 0 7px;
  border-radius: 999px;
  background: rgba(239, 68, 68, 0.25);
  color: #FECACA;
  font-size: 0.78rem;
  font-weight: 700;
}

.assign__head .assign__count { margin-left: auto; }

.assign__eyebrow {
  font-size: 0.85rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #FDBA74;
}

.assign__count { font-size: 0.85rem; color: #94A3B8; }

.assign__empty {
  margin: 0;
  font-family: 'Segoe UI', system-ui, sans-serif;
  font-size: 0.8rem;
  color: #64748B;
}

.assign__list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(165px, 1fr));
  align-items: start;
  gap: 6px;
}

.assign__item {
  --pawn: #94A3B8;
  display: flex;
  flex-direction: column;
  border-radius: 9px;
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid color-mix(in srgb, var(--pawn) 65%, transparent);
  overflow: hidden;
}

/* Top strip: who the slip is aimed at (label above, name on its own line), centred */
.assign__target {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 1px;
  min-width: 0;
  padding: 5px 10px 6px;
  background: linear-gradient(90deg, color-mix(in srgb, var(--pawn) 45%, transparent), color-mix(in srgb, var(--pawn) 12%, transparent));
}

.assign__aim {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.8);
}

.assign__who {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  max-width: 100%;
  min-width: 0;
}

.assign__target-name {
  min-width: 0;
  overflow-wrap: anywhere;
  font-size: 1.15rem;
  font-weight: 800;
  line-height: 1.1;
  color: #fff;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.6);
}

.assign__dot {
  flex: 0 0 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--pawn);
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.85), 0 0 8px var(--pawn);
}

/* Aimed at me: red alert */
.assign__item.is-mine { border-color: #EF4444; box-shadow: 0 0 12px rgba(239, 68, 68, 0.35); }
.assign__item.is-mine .assign__target { background: linear-gradient(90deg, rgba(239, 68, 68, 0.6), rgba(239, 68, 68, 0.15)); }
.assign__item.is-mine .assign__target-name { color: #FEE2E2; }

.assign__body { flex: 1; min-width: 0; padding: 5px 10px 7px; }

.assign__title {
  font-size: 1rem;
  font-weight: 700;
  line-height: 1.1;
}

.assign__example {
  margin-left: 4px;
  padding: 0 4px;
  border-radius: 3px;
  background: #EAB308;
  color: #1c1917;
  font-size: 0.65rem;
  text-transform: uppercase;
  vertical-align: middle;
}

.assign__text {
  font-family: 'Segoe UI', system-ui, sans-serif;
  font-size: 0.76rem;
  line-height: 1.3;
  color: #94A3B8;
}

.assign__claim {
  margin: 0 8px 8px;
  padding: 4px 10px;
  border-radius: 6px;
  border: 1px solid rgba(249, 115, 22, 0.6);
  background: rgba(249, 115, 22, 0.12);
  color: #FDBA74;
  font-family: inherit;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
}

.assign__claim:hover:not(:disabled) { background: rgba(249, 115, 22, 0.25); }
.assign__claim:disabled { opacity: 0.4; cursor: not-allowed; }

:deep(.assign__picker) {
  padding: 0 10px 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  font-size: 0.85rem;
}

:deep(.assign__picker button) {
  padding: 1px 8px;
  border-radius: 6px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: #1A1F2E;
  color: #F1F5F9;
  font-family: inherit;
  cursor: pointer;
}
</style>
