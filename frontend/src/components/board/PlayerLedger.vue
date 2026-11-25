<template>
  <!-- Civ 6-style player strip: one compact card per player, in turn order -->
  <section class="ledger" aria-label="Players">
    <div class="ledger__scroller">
      <article
        v-for="p in players"
        :key="p.user_id"
        class="ledger__card"
        :class="{
          'is-current': p.isCurrent,
          'is-me': p.isMe,
          'is-dead': !p.alive,
          'is-jailed': p.jailed
        }"
        :style="{ '--pawn': p.color }"
      >
        <div class="ledger__portrait">
          <img
            v-if="p.profilePic"
            v-show="!brokenPhotos[p.user_id]"
            :src="p.profilePic"
            alt=""
            class="ledger__photo"
            @error="brokenPhotos[p.user_id] = true"
          />
          <span v-if="!p.profilePic || brokenPhotos[p.user_id]" class="ledger__initials">{{ initials(p.username) }}</span>
          <span v-if="p.turnNo" class="ledger__badge ledger__badge--order" :title="`Turn order: ${p.turnNo}`">{{ p.turnNo }}</span>
          <img
            v-if="p.govIcon"
            :src="p.govIcon"
            :alt="p.govRole || 'Government'"
            :title="p.govRole || 'Government'"
            class="ledger__badge ledger__badge--gov"
          />
          <span v-if="!p.alive" class="ledger__badge ledger__badge--state" title="Out of time: servant of the Reaper">💀</span>
          <span v-else-if="p.jailed" class="ledger__badge ledger__badge--state" title="In Jail">🔒</span>
        </div>

        <div class="ledger__main">
          <div class="ledger__name-row">
            <span class="ledger__name" :title="p.username">{{ p.username }}</span>
            <span v-if="p.isCurrent" class="ledger__chip ledger__chip--turn">turn</span>
            <span v-else-if="p.isMe" class="ledger__chip">you</span>
            <span class="ledger__income" :class="p.incomeNet >= 0 ? 'is-good' : 'is-bad'" :title="incomeTitle(p)">
              {{ formatIncome(p.incomeNet) }}/turn
            </span>
          </div>


          <div class="ledger__stats">
            <span class="ledger__stat" :class="{ 'is-bad': p.bleed > 0 }" :title="p.bleed ? `Bleeding: −${p.bleed * 10}m a turn` : 'Not bleeding'">
              🩸{{ p.bleed || 0 }}
            </span>
            <span
              class="ledger__stat ledger__heat"
              :class="{ 'is-hot': p.heat > 0, 'is-max': p.heat >= p.heatMax }"
              :title="`Heat: ${p.heat || 0} of ${p.heatMax} (Jail at ${p.heatMax})`"
            >
              <span class="ledger__flame">🔥</span>{{ p.heat || 0 }}
              <span class="ledger__pips" :class="{ 'is-max': p.heat >= p.heatMax }">
                <span v-for="n in p.heatMax" :key="n" class="ledger__pip" :class="{ 'is-on': n <= p.heat }" />
              </span>
            </span>
            <span
              v-if="p.debt"
              class="ledger__stat ledger__debt"
              :title="`${p.debt.title} debt: ${fmtMinutes(p.debt.minutes)} left. Repaying ${fmtMinutes(p.debt.repay)} a turn (from income); +30m interest at the end of each turn.`"
            >🛟 {{ fmtMinutes(p.debt.minutes) }}</span>
            <span class="ledger__stat" title="Collectables in hand">🎴{{ p.handCount }}</span>
            <span
              v-if="p.targetedBy"
              class="ledger__stat ledger__targeted"
              :title="`${p.targetedBy} assignment slip${p.targetedBy === 1 ? '' : 's'} target ${p.isMe ? 'you' : p.username}`"
            >🎯{{ p.targetedBy }}</span>
            <span v-if="p.slipCount" class="ledger__stat" title="Completed assignment slips">📜{{ p.slipCount }}</span>
            <span class="ledger__approval" :class="approvalClass(p.approval)" :title="`Approval: ${p.approval || 'none'}`">
              {{ p.approval === 'approve' ? '✓' : p.approval === 'reject' ? '✗' : '·' }}
            </span>
          </div>

          <div class="ledger__job" :title="`${p.jobName}${p.perk ? ` · ${p.perk}` : ''}`">
            <span class="ledger__faction" :class="factionClass(p.jobFaction)" />
            <span class="ledger__job-name">{{ p.jobName }}</span>
            <span v-if="p.jobTier" class="ledger__tier">T{{ p.jobTier }}</span>
            <span v-if="p.perk" class="ledger__perk">{{ p.perk }}</span>
          </div>

          <div v-if="p.equipped?.length" class="ledger__equipped">
            <span
              v-for="c in p.equipped"
              :key="c.uid"
              class="ledger__equip"
              :title="`${c.title}: ${c.text}`"
            >🛡️ {{ c.title }}</span>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { reactive } from 'vue'

// Players' time is private (as at the table), so the strip shows no clocks:
// your own time is in the "You" panel.
defineProps({
  // Built in BoardView: see `ledgerPlayers` there for the shape
  players: { type: Array, default: () => [] }
})

const brokenPhotos = reactive({})

function initials(name) {
  return String(name || '?')
    .split(/[\s_]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map(w => w[0].toUpperCase())
    .join('') || '?'
}

function formatIncome(total) {
  const sign = total >= 0 ? '+' : '−'
  const abs = Math.abs(total)
  return `${sign}${Math.floor(abs / 60)}:${String(abs % 60).padStart(2, '0')}`
}

function fmtMinutes(minutes) {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return h && m ? `${h}h ${m}m` : h ? `${h}h` : `${m}m`
}

function incomeTitle(p) {
  const lines = (p.incomeLines || []).map(l => `${l.label}: ${l.minutes >= 0 ? '+' : '−'}${Math.abs(l.minutes)}m`)
  return ['Income per turn', ...lines].join('\n')
}

function factionClass(faction) {
  return {
    'is-finance': faction === 'Finance',
    'is-illicit': faction === 'Illicit',
    'is-public': faction === 'Public Service'
  }
}

function approvalClass(status) {
  return { 'is-good': status === 'approve', 'is-bad': status === 'reject' }
}
</script>

<style scoped>
.ledger {
  display: flex;
  gap: 8px;
  min-width: 0;
  padding: 6px;
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(26, 31, 46, 0.96), rgba(11, 15, 25, 0.96));
  border: 1px solid rgba(234, 179, 8, 0.28);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  font-family: 'Barlow Condensed', 'Segoe UI', sans-serif;
  color: #E2E8F0;
}

.ledger__scroller {
  display: flex;
  gap: 6px;
  flex: 1;
  min-width: 0;
  overflow-x: auto;
  scrollbar-width: thin;
}

.ledger__card {
  position: relative;
  flex: 1 0 210px;
  max-width: 300px;
  display: flex;
  gap: 9px;
  padding: 7px 9px 7px 7px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-top: 3px solid var(--pawn);
  transition: background 0.3s ease, box-shadow 0.3s ease;
}

.ledger__card.is-me { background: linear-gradient(180deg, rgba(34, 211, 238, 0.1), rgba(15, 23, 42, 0.6)); }

.ledger__card.is-current {
  background: linear-gradient(180deg, rgba(234, 179, 8, 0.2), rgba(15, 23, 42, 0.6));
  box-shadow: 0 0 0 1px rgba(234, 179, 8, 0.7), 0 0 18px rgba(234, 179, 8, 0.2);
}

.ledger__card.is-dead { opacity: 0.55; }
.ledger__card.is-dead .ledger__portrait { filter: grayscale(1); }

.ledger__portrait {
  position: relative;
  flex: 0 0 52px;
  height: 52px;
  border-radius: 50%;
  padding: 3px;
  background: conic-gradient(from 210deg, var(--pawn), color-mix(in srgb, var(--pawn) 45%, #0b0f19), var(--pawn));
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5);
}

.ledger__card.is-current .ledger__portrait { animation: portrait-glow 1.8s ease-in-out infinite; }

.ledger__photo,
.ledger__initials {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.ledger__initials {
  display: grid;
  place-items: center;
  background: radial-gradient(circle at 35% 30%, color-mix(in srgb, var(--pawn) 70%, #fff), color-mix(in srgb, var(--pawn) 55%, #0b0f19));
  color: #fff;
  font-size: 1.3rem;
  font-weight: 800;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.6);
}

.ledger__badge { position: absolute; display: grid; place-items: center; }

.ledger__badge--order {
  top: -3px;
  left: -4px;
  width: 19px;
  height: 19px;
  border-radius: 50%;
  background: #0B0F19;
  border: 1px solid rgba(234, 179, 8, 0.7);
  color: #FDE68A;
  font-size: 0.75rem;
  font-weight: 800;
}

.ledger__badge--gov {
  right: -6px;
  bottom: -4px;
  width: 24px;
  height: 24px;
  object-fit: contain;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.8));
}

.ledger__badge--state { top: -4px; right: -6px; font-size: 1rem; }

.ledger__main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.ledger__name-row {
  display: flex;
  align-items: center;
  gap: 5px;
  min-width: 0;
}

.ledger__name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 1.08rem;
  font-weight: 700;
  line-height: 1.1;
}

.ledger__chip {
  flex: 0 0 auto;
  padding: 0 5px;
  border-radius: 4px;
  background: rgba(34, 211, 238, 0.2);
  color: #A5F3FC;
  font-size: 0.7rem;
  text-transform: uppercase;
}

.ledger__chip--turn { background: #EAB308; color: #1c1917; font-weight: 800; }

.ledger__income {
  margin-left: auto;
  flex: 0 0 auto;
  font-size: 0.98rem;
  font-weight: 700;
  cursor: help;
}

.ledger__stats {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.92rem;
  font-weight: 600;
  color: #CBD5E1;
}

.ledger__approval { margin-left: auto; font-weight: 800; color: #475569; }

.ledger__heat {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 0 5px 0 2px;
  border-radius: 999px;
  color: #64748B;
}

.ledger__heat .ledger__pips { margin-left: 4px; }

/* No heat: a faded flame; some heat: orange; at the Jail limit: red and flickering */
.ledger__flame { filter: grayscale(1); opacity: 0.45; }
.ledger__heat.is-hot { color: #FDBA74; background: rgba(251, 146, 60, 0.12); }
.ledger__heat.is-hot .ledger__flame { filter: none; opacity: 1; }
.ledger__heat.is-max { color: #FCA5A5; background: rgba(239, 68, 68, 0.2); }
.ledger__heat.is-max .ledger__flame { animation: flicker 0.9s ease-in-out infinite; }

@keyframes flicker {
  50% { transform: scale(1.18) rotate(-6deg); filter: drop-shadow(0 0 4px #EF4444); }
}

.ledger__debt {
  padding: 0 6px;
  border-radius: 999px;
  background: rgba(239, 68, 68, 0.18);
  color: #FECACA;
  white-space: nowrap;
}

.ledger__targeted {
  padding: 0 6px;
  border-radius: 999px;
  background: rgba(249, 115, 22, 0.18);
  color: #FDBA74;
}

.ledger__pips { display: inline-flex; gap: 3px; }

.ledger__pip {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  transform: rotate(45deg);
  background: rgba(148, 163, 184, 0.2);
}

.ledger__pip.is-on { background: #FB923C; box-shadow: 0 0 5px rgba(251, 146, 60, 0.7); }
.ledger__pips.is-max .ledger__pip.is-on { background: #EF4444; }

.ledger__job {
  display: flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
  font-size: 0.9rem;
  color: #CBD5E1;
}

.ledger__faction {
  flex: 0 0 7px;
  height: 7px;
  border-radius: 50%;
  background: #475569;
}

.ledger__faction.is-finance { background: #EAB308; }
.ledger__faction.is-illicit { background: #EF4444; }
.ledger__faction.is-public  { background: #38BDF8; }

.ledger__job-name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ledger__tier,
.ledger__perk {
  flex: 0 0 auto;
  padding: 0 4px;
  border-radius: 4px;
  background: rgba(148, 163, 184, 0.16);
  font-size: 0.72rem;
}

.ledger__perk { background: rgba(234, 179, 8, 0.18); color: #FDE68A; }

.ledger__equipped {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
  margin-top: 2px;
}

.ledger__equip {
  max-width: 100%;
  padding: 0 5px;
  border-radius: 4px;
  background: rgba(20, 184, 166, 0.18);
  color: #5EEAD4;
  font-size: 0.75rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: help;
}

.is-good { color: #4ADE80; }
.is-bad { color: #F87171; }

@keyframes portrait-glow {
  0%, 100% { box-shadow: 0 0 0 0 rgba(234, 179, 8, 0), 0 4px 10px rgba(0, 0, 0, 0.5); }
  50%      { box-shadow: 0 0 0 4px rgba(234, 179, 8, 0.4), 0 4px 10px rgba(0, 0, 0, 0.5); }
}


@media (prefers-reduced-motion: reduce) {
  .ledger__card.is-current .ledger__portrait { animation: none; }
}
</style>
