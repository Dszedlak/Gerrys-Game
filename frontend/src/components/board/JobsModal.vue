<template>
  <!-- Every job, by tier, with what it pays and what it can do. Click one to take it
       (or, as an Executive, to choose your executive ability). -->
  <transition name="jobs">
    <div v-if="open" class="jobs" role="dialog" :aria-label="secondary ? 'Choose your executive ability' : 'Jobs'" @click.self="$emit('close')">
      <section class="jobs__panel">
        <header class="jobs__head">
          <div>
            <div class="jobs__eyebrow">{{ cardName || (secondary ? 'Executive' : 'Jobs') }}</div>
            <h2 class="jobs__title">{{ secondary ? 'Choose your executive ability' : allowed ? 'Choose your new job' : 'Choose a job' }}</h2>
            <p class="jobs__sub">
              <template v-if="allowed">
                {{ cardQuestion || 'Pick one of the jobs this card offers.' }} The others are greyed out.
              </template>
              <template v-else-if="secondary">
                Pick another Tier 3 job: you get its ability as well as your own. It can't be changed, and it goes if you lose the Executive title.
              </template>
              <template v-else>
                What each job pays and can do. Tier 3 jobs are one per game. Click a job to take it.
              </template>
            </p>
          </div>
          <button type="button" class="jobs__close" aria-label="Close" @click="$emit('close')">×</button>
        </header>

        <div class="jobs__body">
          <section v-for="tier in tiers" :key="tier.tier" class="jobs__tier">
            <h3 class="jobs__tier-title">Tier {{ tier.tier }} <span>· {{ tier.tier * 10 }} minutes a turn</span></h3>
            <div class="jobs__grid">
              <button
                v-for="j in tier.jobs"
                :key="j.name"
                type="button"
                class="job"
                :class="[factionClass(j.faction), { 'is-mine': j.mine, 'is-taken': j.takenBy || j.notOffered, 'is-secondary': j.isMySecondary }]"
                :disabled="Boolean(j.takenBy) || j.mine || (secondary && j.tier !== 3) || j.notOffered"
                :title="j.takenBy ? `Taken by ${j.takenBy}` : j.mine ? 'Your job' : secondary ? `Take the ${j.name} ability` : `Become a ${j.name}`"
                @click="pick(j)"
              >
                <span class="job__top">
                  <span class="job__faction">{{ j.faction }}</span>
                  <span v-if="j.mine" class="job__badge job__badge--mine">Your job</span>
                  <span v-else-if="j.isMySecondary" class="job__badge job__badge--mine">Your executive ability</span>
                  <span v-else-if="j.takenBy" class="job__badge">Taken · {{ j.takenBy }}</span>
                  <span v-else-if="j.notOffered" class="job__badge">Not offered by this card</span>
                </span>
                <span class="job__name">{{ j.name }}</span>
                <span class="job__pay">+{{ j.pay }}m a turn</span>
                <span class="job__ability" :class="{ 'is-none': !j.ability }">
                  {{ j.ability || 'No special ability.' }}
                </span>
                <span v-if="j.automatic" class="job__auto">⚙️ {{ j.automatic }}</span>
              </button>
            </div>
          </section>
        </div>
        <footer v-if="allowed" class="jobs__foot">
          <button v-if="keepable" type="button" class="jobs__keep" @click="$emit('keep')">Keep my current job</button>
          <span class="jobs__foot-note">Close this to choose later: the card waits.</span>
        </footer>
      </section>
    </div>
  </transition>
</template>

<script setup>
import { askConfirm } from '@/composables/useConfirm'
import { computed } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  // true: an Executive choosing the ability of another Tier 3 job
  secondary: { type: Boolean, default: false },
  // state.reference.jobs: { name, faction, tier, pay, ability, automatic }
  reference: { type: Array, default: () => [] },
  // The room's jobs list (for ids)
  jobs: { type: Array, default: () => [] },
  // Ledger players: { user_id, username, jobName, alive }
  players: { type: Array, default: () => [] },
  myUserId: { type: [Number, String], default: null },
  // state.secondary_jobs: { uid: job name }
  secondaryJobs: { type: Object, default: () => ({}) },
  // A card asking for a job (Promotion, Careers Advisor, Job Opportunity): the job ids it offers
  allowed: { type: Array, default: null },
  keepable: { type: Boolean, default: false },
  cardName: { type: String, default: '' },
  cardQuestion: { type: String, default: '' }
})

const emit = defineEmits(['close', 'choose', 'choose-secondary', 'keep'])

const me = computed(() => props.players.find(p => p.user_id === props.myUserId) || null)

const tiers = computed(() => {
  const list = props.reference.length ? props.reference
    : props.jobs.filter(j => j.tier >= 1).map(j => ({ name: j.name, faction: j.type, tier: j.tier, pay: j.tier * 10, ability: '' }))
  const out = []
  for (const tier of [1, 2, 3]) {
    const jobs = list.filter(j => j.tier === tier).map(j => {
      const holder = tier === 3
        ? props.players.find(p => p.user_id !== props.myUserId && p.alive !== false &&
            (p.jobName === j.name || props.secondaryJobs?.[String(p.user_id)] === j.name))
        : null
      const id = props.jobs.find(x => x.name === j.name)?.id
      return {
        ...j,
        notOffered: Boolean(props.allowed) && !props.allowed.includes(String(id)),
        mine: me.value?.jobName === j.name,
        isMySecondary: props.secondaryJobs?.[String(props.myUserId)] === j.name,
        takenBy: holder?.username || null
      }
    })
    if (props.secondary && tier !== 3) continue
    if (jobs.length) out.push({ tier, jobs })
  }
  return out
})

async function pick(j) {
  if (props.secondary) {
    if (await askConfirm(`Take the ${j.name} ability as your executive ability? It can't be changed later.`)) {
      emit('choose-secondary', j.name)
    }
    return
  }
  const job = props.jobs.find(x => x.name === j.name)
  if (!job) return
  if (await askConfirm(`Become a ${j.name}?`)) emit('choose', job.id)
}

function factionClass(f) {
  const t = String(f || '').toLowerCase()
  if (t.includes('finance')) return 'is-finance'
  if (t.includes('illicit')) return 'is-illicit'
  return 'is-public'
}
</script>

<style scoped>
.jobs {
  position: fixed;
  inset: 0;
  z-index: 1045;
  display: grid;
  place-items: center;
  padding: 18px;
  background: rgba(3, 6, 12, 0.72);
  backdrop-filter: blur(3px);
}

.jobs__panel {
  width: min(1000px, 100%);
  max-height: calc(100vh - 36px);
  display: flex;
  flex-direction: column;
  border-radius: 18px;
  background: linear-gradient(180deg, #1A1F2E, #121726);
  border: 1px solid rgba(234, 179, 8, 0.55);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.6);
  color: #E2E8F0;
  overflow: hidden;
}

.jobs__head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 20px 12px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
}

.jobs__eyebrow {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 0.85rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #22D3EE;
}

.jobs__title {
  margin: 0;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1.8rem;
  font-weight: 800;
  color: #FDE68A;
}

.jobs__sub { margin: 2px 0 0; font-size: 0.88rem; color: #94A3B8; }

.jobs__close {
  align-self: flex-start;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: transparent;
  color: #CBD5E1;
  font-size: 1.2rem;
  cursor: pointer;
}

.jobs__body { padding: 14px 20px 20px; overflow-y: auto; }

.jobs__tier + .jobs__tier { margin-top: 18px; }

.jobs__tier-title {
  margin: 0 0 8px;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1.2rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: #F1F5F9;
}

.jobs__tier-title span { font-size: 0.9rem; font-weight: 600; color: #94A3B8; }

.jobs__grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 10px; }

.job {
  --tone: #3B82F6;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 12px 12px 14px;
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--tone) 35%, transparent);
  border-left: 4px solid var(--tone);
  background: color-mix(in srgb, var(--tone) 8%, #0F172A);
  color: #E2E8F0;
  text-align: left;
  cursor: pointer;
  transition: transform 0.12s ease, border-color 0.15s ease, box-shadow 0.15s ease;
}

.job.is-finance { --tone: #22C55E; }
.job.is-illicit { --tone: #EF4444; }
.job.is-public { --tone: #3B82F6; }

.job:hover:not(:disabled) { transform: translateY(-2px); border-color: var(--tone); box-shadow: 0 8px 20px rgba(0, 0, 0, 0.35); }
.job:disabled { cursor: default; }
.job.is-taken { opacity: 0.45; }
.job.is-mine, .job.is-secondary { box-shadow: 0 0 0 2px #EAB308; }

.job__top { display: flex; justify-content: space-between; align-items: center; gap: 6px; }

.job__faction {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: color-mix(in srgb, var(--tone) 70%, #fff);
}

.job__badge {
  padding: 1px 8px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.18);
  color: #CBD5E1;
  font-size: 0.7rem;
  font-weight: 700;
  white-space: nowrap;
}

.job__badge--mine { background: rgba(234, 179, 8, 0.25); color: #FDE68A; }

.job__name { font-family: 'Barlow Condensed', sans-serif; font-size: 1.3rem; font-weight: 800; color: #F8FAFC; }
.job__pay { font-size: 0.8rem; font-weight: 600; color: #86EFAC; }

.job__ability {
  margin-top: 2px;
  font-size: 0.82rem;
  line-height: 1.45;
  color: #CBD5E1;
  white-space: pre-line;
}

.job__ability.is-none { color: #64748B; font-style: italic; }
.job__auto { font-size: 0.75rem; color: #FDE68A; }

.jobs__foot {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px 16px;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
}

.jobs__keep {
  padding: 8px 16px;
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.45);
  background: rgba(148, 163, 184, 0.1);
  color: #E2E8F0;
  font-weight: 700;
  cursor: pointer;
}

.jobs__foot-note { font-size: 0.8rem; color: #94A3B8; }

.jobs-enter-active, .jobs-leave-active { transition: opacity 0.2s ease; }
.jobs-enter-from, .jobs-leave-to { opacity: 0; }
</style>
