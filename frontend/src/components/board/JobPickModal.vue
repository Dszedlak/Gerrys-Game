<template>
  <!-- After the roll for the first turn: everyone takes a Tier 1 job, then the game starts -->
  <transition name="jobpick">
    <div v-if="open" class="jobpick" role="dialog" aria-label="Choose your starting job">
      <section class="jobpick__panel">
        <div class="jobpick__eyebrow">Before the first turn</div>
        <h2 class="jobpick__title">Choose a Tier 1 job</h2>
        <p class="jobpick__sub">Everyone starts with a Tier 1 job. The game begins once everyone has chosen.</p>

        <div class="jobpick__jobs" role="radiogroup" aria-label="Tier 1 jobs">
          <button
            v-for="j in tier1"
            :key="j.id"
            type="button"
            role="radio"
            class="jobpick__job"
            :class="[factionClass(j.type), { 'is-mine': myPick === j.id }]"
            :aria-checked="myPick === j.id"
            :disabled="!canPick"
            @click="board.pickJob(j.id)"
          >
            <span class="jobpick__faction">{{ j.type }}</span>
            <span class="jobpick__name">{{ j.name }}</span>
            <span class="jobpick__pay">+{{ (j.tier || 1) * 10 }}m a turn</span>
            <span v-if="myPick === j.id" class="jobpick__check">✓ Your job</span>
          </button>
        </div>

        <ul class="jobpick__players">
          <li v-for="p in players" :key="p.user_id" :class="{ 'is-done': p.job, 'is-me': p.user_id === myUserId }">
            <span class="jobpick__dot" :style="{ background: p.color }" />
            <span class="jobpick__pname">{{ p.username }}<small v-if="p.user_id === myUserId"> (you)</small></span>
            <span class="jobpick__pjob">{{ p.job ? `✓ ${p.job}` : 'choosing…' }}</span>
            <select
              v-if="isAdmin && p.user_id !== myUserId && !p.job"
              class="jobpick__admin"
              :aria-label="`Choose a job for ${p.username}`"
              @change="(e) => { board.pickJob(Number(e.target.value), p.user_id); e.target.value = '' }"
            >
              <option value="">Pick for them…</option>
              <option v-for="j in tier1" :key="j.id" :value="j.id">{{ j.name }}</option>
            </select>
          </li>
        </ul>

        <p class="jobpick__status">
          <template v-if="!waiting.length">Everyone has a job: starting…</template>
          <template v-else-if="myPick">You can still change your mind. Waiting for {{ waiting.join(', ') }}…</template>
          <template v-else>Pick one of the jobs above.</template>
        </p>
        <button v-if="isAdmin && waiting.length" type="button" class="jobpick__random" @click="board.pickJob(null, null, true)">
          🎲 Random jobs for everyone still choosing
        </button>
      </section>
    </div>
  </transition>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  state: { type: Object, default: null },
  phase: { type: String, default: 'loading' },
  // Every job in the game (Room's jobs list): { id, name, tier, type }
  jobs: { type: Array, default: () => [] },
  playersById: { type: Object, default: () => ({}) },
  myUserId: { type: [Number, String], default: null },
  isAdmin: { type: Boolean, default: false },
  board: { type: Object, required: true }
})

const open = computed(() => props.phase === 'jobs' && Boolean(props.state?.job_pick))
const picked = computed(() => props.state?.job_pick?.picked || {})
const tier1 = computed(() => props.jobs.filter(j => Number(j.tier) === 1))
const jobName = (id) => props.jobs.find(j => j.id === id)?.name || null

const players = computed(() =>
  (props.state?.job_pick?.order || []).map(uid => {
    const p = props.playersById[uid] || { user_id: uid, username: 'Someone' }
    return { ...p, job: jobName(picked.value[String(uid)]) }
  })
)
const myPick = computed(() => picked.value[String(props.myUserId)] ?? null)
const canPick = computed(() => (props.state?.job_pick?.order || []).includes(props.myUserId))
const waiting = computed(() => players.value.filter(p => !p.job).map(p => (p.user_id === props.myUserId ? 'you' : p.username)))

function factionClass(type) {
  const t = String(type || '').toLowerCase()
  if (t.includes('finance')) return 'is-finance'
  if (t.includes('illicit')) return 'is-illicit'
  return 'is-public'
}
</script>

<style scoped>
.jobpick {
  position: fixed;
  inset: 0;
  z-index: 1035;
  display: grid;
  place-items: center;
  padding: 16px;
  background: rgba(3, 6, 12, 0.72);
  backdrop-filter: blur(3px);
}

.jobpick__panel {
  width: min(560px, 100%);
  max-height: calc(100vh - 32px);
  overflow-y: auto;
  padding: 20px 22px;
  border-radius: 18px;
  background: linear-gradient(180deg, #1A1F2E, #121726);
  border: 1px solid rgba(234, 179, 8, 0.55);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.6);
  color: #E2E8F0;
  text-align: center;
}

.jobpick__eyebrow {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 0.85rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #22D3EE;
}

.jobpick__title {
  margin: 2px 0 4px;
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 2rem;
  font-weight: 800;
  color: #FDE68A;
}

.jobpick__sub { margin: 0 0 14px; font-size: 0.9rem; color: #94A3B8; }

.jobpick__jobs {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 10px;
}

.jobpick__job {
  --tone: #2DD4BF;
  position: relative;
  display: grid;
  gap: 4px;
  padding: 14px 10px;
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--tone) 45%, transparent);
  background: color-mix(in srgb, var(--tone) 10%, #0F172A);
  color: #F8FAFC;
  cursor: pointer;
  transition: transform 0.12s ease, border-color 0.15s ease, box-shadow 0.15s ease;
}

.jobpick__job.is-finance { --tone: #22C55E; }
.jobpick__job.is-illicit { --tone: #EF4444; }
.jobpick__job.is-public { --tone: #3B82F6; }

.jobpick__job:hover:not(:disabled) { transform: translateY(-2px); border-color: var(--tone); }
.jobpick__job:disabled { opacity: 0.5; cursor: not-allowed; }

.jobpick__job.is-mine {
  border-color: var(--tone);
  box-shadow: 0 0 0 2px var(--tone), 0 0 22px color-mix(in srgb, var(--tone) 40%, transparent);
}

.jobpick__faction {
  font-size: 0.72rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: color-mix(in srgb, var(--tone) 70%, #fff);
}

.jobpick__name { font-family: 'Barlow Condensed', sans-serif; font-size: 1.35rem; font-weight: 800; }
.jobpick__pay { font-size: 0.8rem; color: #94A3B8; }
.jobpick__check { font-size: 0.8rem; font-weight: 700; color: #FDE68A; }

.jobpick__players {
  margin: 16px 0 8px;
  padding: 0;
  list-style: none;
  text-align: left;
}

.jobpick__players li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 4px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
}

.jobpick__players li.is-me .jobpick__pname { color: #A5F3FC; }
.jobpick__dot { width: 10px; height: 10px; border-radius: 50%; flex: 0 0 auto; }
.jobpick__pname { flex: 1; min-width: 0; font-weight: 600; }
.jobpick__pname small { color: #64748B; font-weight: 400; }
.jobpick__pjob { font-size: 0.85rem; color: #64748B; }
.jobpick__players li.is-done .jobpick__pjob { color: #86EFAC; font-weight: 600; }

.jobpick__admin {
  padding: 3px 6px;
  border-radius: 6px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: #0B0F19;
  color: #CBD5E1;
  font-size: 0.78rem;
}

.jobpick__status { margin: 8px 0 0; font-size: 0.85rem; color: #94A3B8; }

.jobpick__random {
  margin-top: 10px;
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: rgba(148, 163, 184, 0.08);
  color: #E2E8F0;
  font-size: 0.82rem;
  cursor: pointer;
}

.jobpick-enter-active, .jobpick-leave-active { transition: opacity 0.25s ease; }
.jobpick-enter-from, .jobpick-leave-to { opacity: 0; }
</style>
