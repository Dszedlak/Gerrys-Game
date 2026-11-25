<template>
  <!-- Everything about me that I can change, always visible -->
  <section class="me" aria-label="You" :style="{ '--pawn': player?.color || '#22D3EE' }">
    <header class="me__head">
      <span class="me__eyebrow"><span class="me__dot" /> You</span>
      <span class="me__meta" :title="incomeTitle">
        Income <strong :class="(player?.incomeNet || 0) >= 0 ? 'is-good' : 'is-bad'">{{ formatSigned(player?.incomeNet || 0) }}</strong>/turn
      </span>
    </header>

    <div class="me__clock">{{ clock || '00•00•00' }}</div>
    <div class="me__adjust">
      <button
        v-for="n in [-60, -30, -10, 10, 30, 60]"
        :key="n"
        type="button"
        class="me__adj"
        :class="n < 0 ? 'me__adj--minus' : 'me__adj--plus'"
        @click="$emit('adjust-clock', n)"
      >{{ n < 0 ? '−' : '+' }}{{ Math.abs(n) === 60 ? '1h' : Math.abs(n) }}</button>
    </div>

    <div class="me__grid">
      <div class="me__field me__field--wide">
        <span class="me__label">💼 Job</span>
        <div class="me__value-row">
          <span class="me__value">
            {{ player?.jobName || 'Unemployed' }}
            <small v-if="player?.jobTier">Tier {{ player.jobTier }}</small>
          </span>
          <button type="button" class="me__browse" @click="$emit('open-jobs')">All jobs</button>
        </div>
        <span v-if="secondaryJob" class="me__extra">💎 Executive ability: {{ secondaryJob }}</span>
      </div>

      <div class="me__field">
        <span class="me__label">🎖️ Title</span>
        <div class="me__value-row">
          <span class="me__value">{{ player?.perk || 'None' }}</span>
          <button type="button" class="me__browse" :class="{ 'is-ready': titleReady }" @click="$emit('open-titles')">
            {{ titleReady ? '🎖️ New!' : 'Titles' }}
          </button>
        </div>
      </div>

      <div class="me__field">
        <span class="me__label">🗳️ Approval</span>
        <div class="me__seg" role="group" aria-label="Approval of the government">
          <button
            type="button"
            :class="{ 'is-on is-good': player?.approval === 'approve' }"
            @click="$emit('set-approval', 'approve')"
          >✓ Approve</button>
          <button
            type="button"
            :class="{ 'is-on is-bad': player?.approval === 'reject' }"
            @click="$emit('set-approval', 'reject')"
          >✗ Reject</button>
        </div>
      </div>

      <div class="me__field">
        <span class="me__label">🩸 Bleed</span>
        <div class="me__stepper">
          <button type="button" aria-label="Less bleed" :disabled="!player?.bleed" @click="$emit('bleed-changed', -1)">−</button>
          <span :class="{ 'is-bad': player?.bleed > 0 }">{{ player?.bleed ? `${player.bleed} · −${player.bleed * 10}m` : 'None' }}</span>
          <button type="button" aria-label="More bleed" @click="$emit('bleed-changed', 1)">+</button>
        </div>
      </div>

      <div class="me__field">
        <span class="me__label">🔥 Heat <small>(Jail at {{ player?.heatMax || 3 }})</small></span>
        <div class="me__stepper">
          <button type="button" aria-label="Less heat" :disabled="!player?.heat" @click="$emit('heat-changed', -1)">−</button>
          <span class="me__pips">
            <span v-for="n in Math.max(player?.heatMax || 3, player?.heat || 0)" :key="n" class="me__pip" :class="{ 'is-on': n <= (player?.heat || 0) }" />
          </span>
          <button type="button" aria-label="More heat" @click="$emit('heat-changed', 1)">+</button>
        </div>
      </div>
    </div>

    <div v-if="isDoctorInPlay" class="me__notice">🏥 A Doctor is in play: hospital items cost 60 minutes.</div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  // My ledger entry (see BoardView)
  player: { type: Object, default: null },
  // Every participant, to show which Tier 3 jobs are taken
  participants: { type: Array, default: () => [] },
  jobs: { type: Array, default: () => [] },
  clock: { type: String, default: '' },
  myUserId: { type: [Number, String], default: null },
  isDoctorInPlay: { type: Boolean, default: false },
  // An Executive's second Tier 3 ability, and whether the next title is ready to take
  secondaryJob: { type: String, default: null },
  titleReady: { type: Boolean, default: false }
})

const emit = defineEmits(['adjust-clock', 'update-job', 'update-perk', 'bleed-changed', 'heat-changed', 'set-approval',
  'open-jobs', 'open-titles'])

const TIER_LABELS = { 0: 'Unemployed', 1: 'Tier 1', 2: 'Tier 2', 3: 'Tier 3 — one player each' }

const isAlive = (p) => String(p?.clock || '').trim() !== '00•00•00'

// Same grouping as the table view: by tier, alphabetical, Tier 3 unique per game
const groupedJobs = computed(() => {
  const byTier = new Map()
  for (const j of props.jobs) {
    const tier = j.tier || 0
    let takenBy = null
    if (tier === 3) {
      const holder = props.participants.find(p => p.job_name === j.name && p.user_id !== props.myUserId && isAlive(p))
      if (holder) takenBy = holder.username
    }
    if (!byTier.has(tier)) byTier.set(tier, [])
    byTier.get(tier).push({ ...j, takenBy })
  }
  return [...byTier.keys()].sort((a, b) => a - b).map(tier => ({
    tier,
    label: TIER_LABELS[tier] || `Tier ${tier}`,
    jobs: byTier.get(tier).sort((a, b) => a.name.localeCompare(b.name))
  }))
})

const currentJobId = computed(() => {
  const name = props.player?.jobName
  const job = props.jobs.find(j => j.name === name) || props.jobs.find(j => (j.tier || 0) === 0)
  return job?.id ?? null
})

function onJob(e) {
  const id = Number(e.target.value)
  if (!Number.isNaN(id) && id !== currentJobId.value) emit('update-job', id)
}

function onPerk(e) {
  emit('update-perk', e.target.value || null)
}

function formatSigned(total) {
  const sign = total >= 0 ? '+' : '−'
  const abs = Math.abs(total)
  const h = Math.floor(abs / 60)
  const m = abs % 60
  if (h && !m) return `${sign}${h}h`
  return `${sign}${h ? `${h}h ` : ''}${m}m`
}

const incomeTitle = computed(() =>
  (props.player?.incomeLines || [])
    .map(l => `${l.label}: ${l.minutes >= 0 ? '+' : '−'}${Math.abs(l.minutes)}m`)
    .join('\n')
)
</script>

<style scoped>
.me {
  --pawn: #22D3EE;
  padding: 10px 12px 12px;
  border-radius: 12px;
  background: linear-gradient(180deg, #1A1F2E, #121726);
  border: 1px solid color-mix(in srgb, var(--pawn) 45%, transparent);
  box-shadow: inset 0 3px 0 var(--pawn);
  font-family: 'Barlow Condensed', 'Segoe UI', sans-serif;
  color: #E2E8F0;
}

.me__head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.me__eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.9rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #F1F5F9;
}

.me__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--pawn);
}

.me__meta {
  font-size: 0.95rem;
  color: #94A3B8;
  cursor: help;
}

@media (max-height: 980px) {
  .me__clock { font-size: 1.9rem !important; margin: 4px 0 !important; }
}

.me__clock {
  margin: 6px 0;
  padding: 2px 0;
  border-radius: 10px;
  background: radial-gradient(ellipse at center, rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.9));
  border: 2px solid #000;
  font-size: 2.4rem;
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: 6px;
  text-align: center;
  color: #00ff00;
  text-shadow: 0 0 12px rgba(0, 255, 0, 0.35);
}

.me__adjust {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 4px;
}

.me__adj {
  padding: 4px 0;
  border-radius: 7px;
  background: #0f1420;
  font-family: inherit;
  font-weight: 700;
  font-size: 0.95rem;
  cursor: pointer;
  transition: transform 0.12s;
}

.me__adj:hover { transform: translateY(-1px); }
.me__adj--minus { border: 1px solid rgba(248, 113, 113, 0.55); color: #FCA5A5; }
.me__adj--plus { border: 1px solid rgba(74, 222, 128, 0.55); color: #86EFAC; }

.me__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px 10px;
  margin-top: 10px;
}

.me__field {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.me__field--wide { grid-column: 1 / -1; }

.me__label {
  font-size: 0.82rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #94A3B8;
}

.me__label small { text-transform: none; letter-spacing: 0; color: #64748B; }

.me__select {
  width: 100%;
  padding: 5px 8px;
  border-radius: 7px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: #0f1420;
  color: #F1F5F9;
  font-family: inherit;
  font-size: 1.05rem;
  font-weight: 600;
  cursor: pointer;
}

.me__select:focus { outline: 2px solid #EAB308; outline-offset: 1px; }

.me__seg {
  display: flex;
  border-radius: 7px;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.35);
}

.me__seg button {
  flex: 1;
  padding: 5px 0;
  border: 0;
  background: #0f1420;
  color: #94A3B8;
  font-family: inherit;
  font-size: 0.98rem;
  font-weight: 700;
  cursor: pointer;
}

.me__seg button + button { border-left: 1px solid rgba(148, 163, 184, 0.35); }
.me__seg button.is-on.is-good { background: rgba(74, 222, 128, 0.18); color: #86EFAC; }
.me__seg button.is-on.is-bad { background: rgba(248, 113, 113, 0.18); color: #FCA5A5; }

.me__stepper {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 2px;
  border-radius: 7px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: #0f1420;
}

.me__stepper > span {
  flex: 1;
  text-align: center;
  font-size: 1rem;
  font-weight: 700;
  white-space: nowrap;
}

.me__stepper button {
  width: 30px;
  height: 28px;
  border-radius: 5px;
  border: 0;
  background: rgba(148, 163, 184, 0.14);
  color: #F1F5F9;
  font-size: 1.2rem;
  font-weight: 700;
  line-height: 1;
  cursor: pointer;
}

.me__stepper button:hover:not(:disabled) { background: rgba(234, 179, 8, 0.3); }
.me__stepper button:disabled { opacity: 0.35; cursor: not-allowed; }

.me__pips {
  display: inline-flex;
  justify-content: center;
  gap: 5px;
}

.me__pip {
  width: 11px;
  height: 11px;
  border-radius: 2px;
  transform: rotate(45deg);
  background: rgba(148, 163, 184, 0.2);
}

.me__pip.is-on {
  background: #FB923C;
  box-shadow: 0 0 6px rgba(251, 146, 60, 0.7);
}

.is-good { color: #4ADE80; }
.is-bad { color: #F87171; }

.me__notice {
  margin-top: 8px;
  padding: 5px 8px;
  border-radius: 7px;
  background: rgba(234, 179, 8, 0.12);
  color: #FDE68A;
  font-size: 0.85rem;
}

/* Job and title, with buttons to browse them */
.me__value-row { display: flex; align-items: center; gap: 8px; min-height: 36px; }

.me__value {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 1.2rem;
  font-weight: 700;
  color: #FDE68A;
}

.me__value small { margin-left: 4px; font-size: 0.78rem; font-weight: 600; color: #94A3B8; }

.me__browse {
  flex: 0 0 auto;
  padding: 5px 11px;
  border-radius: 8px;
  border: 1px solid rgba(34, 211, 238, 0.5);
  background: rgba(34, 211, 238, 0.1);
  color: #A5F3FC;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
}

.me__browse:hover { background: rgba(34, 211, 238, 0.2); }
.me__browse.is-ready { border-color: #22C55E; background: rgba(34, 197, 94, 0.2); color: #BBF7D0; animation: me-ready 1.4s ease-in-out infinite; }

@keyframes me-ready { 50% { box-shadow: 0 0 14px rgba(34, 197, 94, 0.5); } }

.me__extra { display: block; margin-top: 2px; font-size: 0.78rem; color: #A5B4FC; }
</style>
