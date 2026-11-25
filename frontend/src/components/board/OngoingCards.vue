<template>
  <!-- Scenario cards that stay in play: debts, Income Tax, the Bounty Board -->
  <section v-if="hasAny" class="ongoing" aria-label="Ongoing cards">
    <header class="ongoing__head">🃏 Ongoing cards</header>

    <div v-if="bounty" class="ongoing__item">
      <div class="ongoing__title">📜 {{ bounty.title }} <span class="ongoing__tag">{{ bounty.left }} left</span></div>
      <p class="ongoing__text">
        Complete an assignment against anyone with a title: double reward, and they are demoted.
      </p>
    </div>

    <div v-if="tax" class="ongoing__item">
      <div class="ongoing__title">💷 {{ tax.title }} <span class="ongoing__tag">{{ fmt(tax.donated) }} / {{ fmt(tax.goal) }}</span></div>
      <div class="ongoing__bar"><span :style="{ width: `${Math.min(100, (tax.donated / tax.goal) * 100)}%` }" /></div>
      <p class="ongoing__text">
        Landing on Collectables &amp; Promotions costs no job 30m, Tier 1/2 1h, Tier 3 1.5h, a title 2h.
        Donating 24 hours in all lifts it.
      </p>
      <div v-if="started" class="ongoing__row">
        <span class="ongoing__label">Donate:</span>
        <button v-for="m in [30, 60, 120]" :key="m" type="button" class="ongoing__btn" @click="donate(m)">{{ fmt(m) }}</button>
      </div>
    </div>

    <div v-for="d in debts" :key="d.user_id" class="ongoing__item" :class="{ 'is-mine': d.user_id === myUserId }">
      <div class="ongoing__title">
        🛟 {{ d.title }} · {{ d.user_id === myUserId ? 'You owe' : `${nameOf(d.user_id)} owes` }}
        <span class="ongoing__tag ongoing__tag--bad">{{ fmt(d.minutes) }}</span>
      </div>
      <p class="ongoing__text">
        {{ fmt(Math.min(d.plan || 60, d.minutes)) }} a turn is repaid when {{ d.user_id === myUserId ? 'you collect' : 'they collect' }}
        income; 30 minutes interest is added at the end of each turn.
      </p>
      <div v-if="d.user_id === myUserId" class="ongoing__row">
        <span class="ongoing__label">Repay each turn:</span>
        <button
          v-for="m in [60, 120, 180]"
          :key="m"
          type="button"
          class="ongoing__btn ongoing__btn--plan"
          :class="{ 'is-on': (d.plan || 60) === m }"
          :aria-pressed="(d.plan || 60) === m"
          @click="board.setDebtPlan(m)"
        >{{ fmt(m) }}</button>
      </div>
      <div v-if="d.user_id === myUserId && isMyTurn" class="ongoing__row">
        <span v-if="d.paid_seq === turnSeq" class="ongoing__ok">✓ Repaid this turn</span>
        <span v-else class="ongoing__label">Due this turn: it's taken when you collect income.</span>
      </div>
    </div>
  </section>
</template>

<script setup>
import { askConfirm } from '@/composables/useConfirm'
import { computed } from 'vue'

const props = defineProps({
  board: { type: Object, required: true },
  state: { type: Object, default: null },
  playersById: { type: Object, default: () => ({}) },
  myUserId: { type: [Number, String], default: null }
})

const bounty = computed(() => props.state?.bounty || null)
const tax = computed(() => props.state?.income_tax || null)
const debts = computed(() =>
  Object.entries(props.state?.debts || {}).map(([uid, d]) => ({ ...d, user_id: Number(uid) }))
)
const hasAny = computed(() => Boolean(bounty.value || tax.value || debts.value.length))
const started = computed(() => Boolean(props.state?.started))
const turnSeq = computed(() => props.state?.turn_seq)
const isMyTurn = computed(() => started.value && props.state?.turn?.user_id === props.myUserId)
const nameOf = (uid) => props.playersById[uid]?.username || 'Someone'

function payOptions(owed) {
  if (owed < 60) return [owed]
  return [60, 120, 180].filter(m => m <= owed).concat(owed > 60 && owed < 180 && owed % 60 ? [owed] : [])
}

async function donate(minutes) {
  if (await askConfirm(`Donate ${fmt(minutes)} of your time to the state, towards lifting Income Tax?`)) {
    props.board.donateTax(minutes)
  }
}

function fmt(minutes) {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return h && m ? `${h}h ${m}m` : h ? `${h}h` : `${m}m`
}
</script>

<style scoped>
.ongoing {
  padding: 10px 12px 12px;
  border-radius: 12px;
  background: linear-gradient(180deg, #1E1B2E, #141226);
  border: 1px solid rgba(139, 92, 246, 0.4);
  color: #E2E8F0;
  font-size: 0.86rem;
}

.ongoing__head {
  margin-bottom: 6px;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 0.85rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #C4B5FD;
}

.ongoing__item {
  padding: 8px 0;
  border-top: 1px solid rgba(148, 163, 184, 0.12);
}

.ongoing__item.is-mine .ongoing__title { color: #FDE68A; }

.ongoing__title { font-weight: 700; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }

.ongoing__tag {
  padding: 1px 8px;
  border-radius: 999px;
  background: rgba(139, 92, 246, 0.2);
  color: #DDD6FE;
  font-size: 0.76rem;
}

.ongoing__tag--bad { background: rgba(248, 113, 113, 0.18); color: #FECACA; }

.ongoing__text { margin: 4px 0 0; color: #94A3B8; font-size: 0.8rem; line-height: 1.4; }

.ongoing__bar {
  height: 6px;
  margin-top: 6px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.15);
  overflow: hidden;
}

.ongoing__bar span { display: block; height: 100%; background: linear-gradient(90deg, #8B5CF6, #22D3EE); }

.ongoing__row { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-top: 6px; }
.ongoing__label { color: #94A3B8; font-size: 0.78rem; }
.ongoing__ok { color: #86EFAC; font-size: 0.8rem; }

.ongoing__btn {
  padding: 3px 10px;
  border-radius: 999px;
  border: 1px solid rgba(167, 139, 250, 0.5);
  background: rgba(139, 92, 246, 0.12);
  color: #DDD6FE;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
}

.ongoing__btn:hover { background: rgba(139, 92, 246, 0.25); }
.ongoing__btn--plan.is-on { border-color: #EAB308; background: rgba(234, 179, 8, 0.22); color: #FDE68A; }

.ongoing__btn--pay { border-color: rgba(234, 179, 8, 0.6); background: rgba(234, 179, 8, 0.12); color: #FDE68A; }
</style>
