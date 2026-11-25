<template>
  <section class="board-log" :class="{ 'is-collapsed': collapsed }">
    <button
      type="button"
      class="board-log__head"
      :aria-expanded="!collapsed"
      :title="collapsed ? 'Show the game log' : 'Minimise the game log'"
      @click="toggle"
    >
      <span class="board-log__chevron">{{ collapsed ? '▸' : '▾' }}</span>
      <span>Game log</span>
      <span class="board-log__count">{{ entries.length }}</span>
    </button>
    <!-- Minimised: just the latest line -->
    <div v-if="collapsed && latest" class="board-log__latest" :style="{ '--who': colorFor(latest.user_id) }">
      {{ latest.text }}
    </div>
    <ol v-show="!collapsed" ref="listRef" class="board-log__list" @scroll="onScroll">
      <li v-if="!entries.length" class="board-log__empty">Nothing has happened yet.</li>
      <li
        v-for="e in entries"
        :key="e.seq"
        class="board-log__entry"
        :class="`board-log__entry--${e.kind}`"
        :style="{ '--who': colorFor(e.user_id) }"
      >
        <span class="board-log__text">{{ e.text }}</span>
        <time v-if="e.ts" class="board-log__time" :datetime="e.ts">{{ timeOf(e.ts) }}</time>
      </li>
    </ol>
  </section>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps({
  log: { type: Array, default: () => [] },
  playersById: { type: Object, default: () => ({}) }
})

const entries = computed(() => props.log || [])
const latest = computed(() => entries.value[entries.value.length - 1] || null)
const listRef = ref(null)

const STORAGE_KEY = 'gg.logCollapsed'
function readCollapsed() {
  try { return localStorage.getItem(STORAGE_KEY) === '1' } catch { return false }
}
const collapsed = ref(readCollapsed())

async function toggle() {
  collapsed.value = !collapsed.value
  try { localStorage.setItem(STORAGE_KEY, collapsed.value ? '1' : '0') } catch { /* private mode */ }
  if (!collapsed.value) {
    pinnedToBottom = true
    await nextTick()
    const el = listRef.value
    if (el) el.scrollTop = el.scrollHeight
  }
}
// Follow new entries unless the reader has scrolled up to look at history
let pinnedToBottom = true

function onScroll() {
  const el = listRef.value
  if (!el) return
  pinnedToBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 24
}

watch(() => entries.value.length && entries.value[entries.value.length - 1].seq, async () => {
  if (!pinnedToBottom) return
  await nextTick()
  const el = listRef.value
  if (el) el.scrollTop = el.scrollHeight
}, { immediate: true })

function colorFor(uid) {
  return (uid != null && props.playersById[uid]?.color) || 'rgba(148, 163, 184, 0.35)'
}

function timeOf(iso) {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.board-log__chevron { width: 12px; color: #EAB308; }

.board-log__latest {
  padding: 6px 12px 8px;
  border-left: 3px solid var(--who);
  font-size: 0.85rem;
  color: #CBD5E1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.board-log {
  display: flex;
  flex-direction: column;
  min-height: 0;
  border-radius: 12px;
  background: linear-gradient(180deg, #141a28, #0f1420);
  border: 1px solid rgba(148, 163, 184, 0.14);
  overflow: hidden;
  text-align: left;
}

.board-log.is-collapsed {
  flex: 0 0 auto;
  min-height: 0;
}

.board-log__head {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 12px;
  border: 0;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 0.85rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #94A3B8;
}

.board-log__count {
  margin-left: auto;
  padding: 0 7px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.14);
  font-size: 0.75rem;
  letter-spacing: 0;
}

.board-log__list {
  flex: 1;
  min-height: 0;
  margin: 0;
  padding: 6px 8px 8px;
  list-style: none;
  overflow-y: auto;
  scrollbar-width: thin;
}

.board-log__empty {
  padding: 10px 6px;
  color: #475569;
  font-size: 0.85rem;
}

.board-log__entry {
  display: flex;
  gap: 8px;
  align-items: baseline;
  padding: 5px 8px;
  margin-bottom: 3px;
  border-left: 3px solid var(--who);
  border-radius: 0 6px 6px 0;
  background: rgba(148, 163, 184, 0.04);
  font-size: 0.83rem;
  line-height: 1.35;
  color: #CBD5E1;
  animation: log-in 0.3s ease-out;
}

.board-log__text { flex: 1; }

.board-log__time {
  flex: 0 0 auto;
  font-size: 0.7rem;
  color: #475569;
}

.board-log__entry--turn { color: #F8FAFC; font-weight: 600; background: rgba(234, 179, 8, 0.06); }
.board-log__entry--round {
  border-left-color: #EAB308;
  color: #FDE68A;
  font-weight: 700;
  background: rgba(234, 179, 8, 0.1);
}
.board-log__entry--attack { background: rgba(163, 230, 53, 0.08); color: #D9F99D; }
.board-log__entry--jail { background: rgba(239, 68, 68, 0.1); color: #FECACA; }
.board-log__entry--reaper,
.board-log__entry--horseman { border-left-color: #A78BFA; background: rgba(167, 139, 250, 0.1); color: #DDD6FE; }
.board-log__entry--horseman { font-weight: 700; }
.board-log__entry--money { color: #BBF7D0; }
.board-log__entry--manual,
.board-log__entry--admin { color: #94A3B8; font-style: italic; }

@keyframes log-in {
  from { opacity: 0; transform: translateX(-6px); }
  to   { opacity: 1; transform: none; }
}

@media (prefers-reduced-motion: reduce) {
  .board-log__entry { animation: none; }
}
</style>
