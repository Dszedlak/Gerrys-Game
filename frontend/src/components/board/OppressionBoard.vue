<template>
  <!-- Government oppressions in play (max 4). Leaders use them on their turn. -->
  <section class="opp" aria-label="Government oppressions">
    <button type="button" class="opp__head" :aria-expanded="!collapsed" @click="toggle">
      <span class="opp__chevron" :class="{ 'is-open': !collapsed }">▸</span>
      <span class="opp__eyebrow">⛓️ Oppressions</span>
      <span class="opp__count">{{ oppressions.length }}/{{ max }}</span>
    </button>

    <template v-if="!collapsed">
    <p v-if="!allowed" class="opp__empty">
      No government oppressions under {{ governmentType || 'Democracy' }}.
    </p>
    <p v-else-if="!oppressions.length" class="opp__empty">
      None in play. Government members at the Senate can introduce one for 2 hours.
    </p>

    <ul v-else class="opp__list">
      <li v-for="o in oppressions" :key="o.id" class="opp__item" :class="{ 'is-used': isUsed(o) }">
        <div class="opp__body">
          <div class="opp__title">
            {{ o.card?.title || 'Oppression' }}
            <span v-if="o.new" class="opp__tag">usable next turn</span>
            <span v-else-if="isUsed(o)" class="opp__tag opp__tag--used">used this turn</span>
          </div>
          <div class="opp__text">{{ o.card?.text }}</div>
        </div>
        <div class="opp__actions">
          <button
            v-if="canUse(o)"
            type="button"
            class="opp__use"
            :disabled="usesLeft <= 0"
            :title="usesLeft <= 0 ? 'No oppression uses left this turn' : 'Use this oppression on a player'"
            @click="picking = picking === o.id ? null : o.id"
          >Use…</button>
          <button
            v-if="isAdmin"
            type="button"
            class="opp__remove"
            title="Admin: remove this oppression (e.g. Chief Justice)"
            @click="remove(o)"
          >✕</button>
        </div>
        <div v-if="picking === o.id" class="opp__picker">
          <span>Use on:</span>
          <button
            v-for="p in targets"
            :key="p.user_id"
            type="button"
            :style="{ '--pawn': p.color }"
            @click="use(o, p)"
          ><span class="opp__dot" />{{ p.username }}</button>
          <span v-if="!targets.length" class="opp__none">{{ isRepublic ? 'No enemies of the state' : 'Nobody to target' }}</span>
        </div>
      </li>
    </ul>

    <p v-if="myRole && allowed" class="opp__role">
      As {{ myRole }} you can use {{ usesDescription }}<template v-if="isMyTurn"> · {{ usesLeftText }}</template>.
    </p>
    </template>
  </section>
</template>

<script setup>
import { askConfirm } from '@/composables/useConfirm'
import { ref, computed } from 'vue'
import { useCollapsed } from '@/composables/useCollapsed'

const { collapsed, toggle } = useCollapsed('oppressions.v2', true)

const props = defineProps({
  board: { type: Object, required: true },
  oppressions: { type: Array, default: () => [] },
  max: { type: Number, default: 4 },
  // state.oppression_uses: { turn_seq, by: {uid: n}, cards: [ids], pairs: [[leader, target]] }
  uses: { type: Object, default: null },
  turnSeq: { type: Number, default: null },
  governmentType: { type: String, default: 'Democracy' },
  // { dictator, politburo:Set, head_of_state } from useGovernment().normalizeGovernment
  leaders: { type: Object, default: () => ({}) },
  stateEnemies: { type: Array, default: () => [] },
  playersById: { type: Object, default: () => ({}) },
  myUserId: { type: [Number, String], default: null },
  isMyTurn: { type: Boolean, default: false },
  isAdmin: { type: Boolean, default: false }
})

// Uses per turn on the Government cards
const LIMITS = { communism: 2, dictatorship: 3, republic: 1 }

const picking = ref(null)
const type = computed(() => String(props.governmentType || '').toLowerCase())
const allowed = computed(() => type.value in LIMITS)
const isRepublic = computed(() => type.value === 'republic')

const myRole = computed(() => {
  const me = props.myUserId
  const g = props.leaders || {}
  if (type.value === 'dictatorship' && g.dictator === me) return 'Dictator'
  if (type.value === 'communism' && g.politburo?.has?.(me)) return 'a Politburo leader'
  if (type.value === 'republic' && g.head_of_state === me) return 'Head of State'
  return null
})

const currentUses = computed(() => (props.uses && props.uses.turn_seq === props.turnSeq ? props.uses : null))
const usedByMe = computed(() => currentUses.value?.by?.[String(props.myUserId)] || 0)
const usesLeft = computed(() => (isRepublic.value ? 1 : Math.max(0, (LIMITS[type.value] || 0) - usedByMe.value)))
const usesDescription = computed(() =>
  isRepublic.value ? 'one oppression per enemy of the state each turn' : `${LIMITS[type.value]} oppressions a turn`
)
const usesLeftText = computed(() => (isRepublic.value ? 'state enemies only' : `${usesLeft.value} left this turn`))

const isUsed = (o) => Boolean(currentUses.value?.cards?.includes(o.id))
const canUse = (o) => Boolean(myRole.value) && props.isMyTurn && !o.new && !isUsed(o)

const targets = computed(() => {
  const enemies = new Set(props.stateEnemies.map(e => Number(e.user_id ?? e)))
  const already = new Set((currentUses.value?.pairs || []).filter(p => p[0] === props.myUserId).map(p => p[1]))
  return Object.values(props.playersById).filter(p =>
    p.alive && p.user_id !== props.myUserId &&
    (!isRepublic.value || (enemies.has(p.user_id) && !already.has(p.user_id)))
  )
})

function use(o, p) {
  picking.value = null
  props.board.useOppression(o.id, p.user_id)
}

async function remove(o) {
  if (await askConfirm(`Remove “${o.card?.title}” from play?`)) props.board.removeOppression(o.id)
}
</script>

<style scoped>
.opp {
  padding: 10px 12px 12px;
  border-radius: 12px;
  background: linear-gradient(180deg, #1A1F2E, #121726);
  border: 1px solid rgba(220, 38, 38, 0.35);
  font-family: 'Barlow Condensed', 'Segoe UI', sans-serif;
  color: #E2E8F0;
}

.opp__head {
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

.opp__head + * { margin-top: 8px; }
.opp__head .opp__count { margin-left: auto; }

.opp__chevron {
  display: inline-block;
  width: 12px;
  color: #FCA5A5;
  transition: transform 0.15s ease;
}

.opp__chevron.is-open { transform: rotate(90deg); }

.opp__eyebrow {
  font-size: 0.85rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #FCA5A5;
}

.opp__count { font-size: 0.85rem; color: #94A3B8; }

.opp__empty {
  margin: 0;
  font-family: 'Segoe UI', system-ui, sans-serif;
  font-size: 0.8rem;
  color: #64748B;
}

.opp__list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(165px, 1fr));
  align-items: start;
  gap: 6px;
}

.opp__item {
  display: grid;
  grid-template-columns: 1fr;
  gap: 4px 8px;
  padding: 6px 8px;
  border-radius: 8px;
  background: rgba(127, 29, 29, 0.22);
  border-left: 4px solid #DC2626;
}

.opp__item.is-used { opacity: 0.6; }

.opp__title { font-size: 1rem; font-weight: 700; line-height: 1.15; }

.opp__tag {
  margin-left: 4px;
  padding: 0 5px;
  border-radius: 4px;
  background: rgba(148, 163, 184, 0.2);
  color: #CBD5E1;
  font-size: 0.68rem;
  text-transform: uppercase;
  vertical-align: middle;
}

.opp__tag--used { background: rgba(234, 179, 8, 0.2); color: #FDE68A; }

.opp__text {
  font-family: 'Segoe UI', system-ui, sans-serif;
  font-size: 0.76rem;
  line-height: 1.3;
  color: #94A3B8;
}

.opp__actions { display: flex; align-items: flex-start; gap: 4px; }

.opp__use,
.opp__remove,
.opp__picker button {
  padding: 2px 10px;
  border-radius: 6px;
  border: 1px solid rgba(220, 38, 38, 0.6);
  background: rgba(220, 38, 38, 0.15);
  color: #FCA5A5;
  font-family: inherit;
  font-size: 0.88rem;
  font-weight: 700;
  cursor: pointer;
}

.opp__use:disabled { opacity: 0.4; cursor: not-allowed; }
.opp__remove { padding: 2px 7px; border-color: rgba(148, 163, 184, 0.35); background: transparent; color: #94A3B8; }

.opp__picker {
  grid-column: 1 / -1;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  font-size: 0.85rem;
}

.opp__picker button {
  --pawn: #94A3B8;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border-color: rgba(148, 163, 184, 0.35);
  background: #1A1F2E;
  color: #F1F5F9;
}

.opp__dot { width: 8px; height: 8px; border-radius: 50%; background: var(--pawn); }
.opp__none { color: #64748B; }

.opp__role {
  margin: 8px 0 0;
  font-family: 'Segoe UI', system-ui, sans-serif;
  font-size: 0.78rem;
  color: #FCA5A5;
}
</style>
