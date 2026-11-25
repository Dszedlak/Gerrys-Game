<template>
  <!-- One playing card: Scenario, Assignment slip or Collectable -->
  <article class="card-face" :class="[`card-face--${deck}`, `card-face--${size}`, { 'is-example': card?.example }]">
    <span v-if="card?.example" class="card-face__ribbon">Example</span>
    <header class="card-face__head">
      <span class="card-face__icon">{{ DECK_META[deck]?.icon }}</span>
      <span class="card-face__deck">{{ DECK_META[deck]?.label }}</span>
      <span v-if="card?.equip" class="card-face__tag" title="Can be equipped next to your name">Equip</span>
    </header>
    <h4 class="card-face__title" :class="{ 'is-contraband': card?.contraband }" :title="card?.contraband ? 'Contraband' : undefined">
      {{ card?.title || 'Unknown card' }}
    </h4>
    <p class="card-face__text">{{ card?.text }}</p>
    <slot />
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { DECK_META } from '@/components/board/boardLayout'

const props = defineProps({
  card: { type: Object, default: null },
  // 'lg' for the reveal, 'md' for the hand, 'sm' for chips
  size: { type: String, default: 'md' }
})

const deck = computed(() => props.card?.deck || 'collectable')
</script>

<style scoped>
.card-face {
  --tone: #2DD4BF;
  --ink: #0f172a;
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 14px 14px;
  border-radius: 12px;
  overflow: hidden;
  background:
    linear-gradient(160deg, color-mix(in srgb, var(--tone) 22%, #fdfbf5) 0%, #f8f5ec 40%, #efe9da 100%);
  color: var(--ink);
  border: 2px solid color-mix(in srgb, var(--tone) 70%, #000);
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.45), inset 0 0 0 3px rgba(255, 255, 255, 0.55);
  font-family: 'Barlow Condensed', 'Segoe UI', sans-serif;
  text-align: left;
}

.card-face--scenario { --tone: #8B5CF6; }
.card-face--assignment { --tone: #F97316; }
.card-face--collectable { --tone: #14B8A6; }
.card-face--shortcut { --tone: #6366F1; }
.card-face--oppression { --tone: #DC2626; }
.card-face--job { --tone: #EC4899; }
.card-face--promotion { --tone: #3B82F6; }
.card-face--hospital { --tone: #EAB308; }

.card-face__ribbon {
  position: absolute;
  top: 12px;
  right: -30px;
  width: 110px;
  padding: 2px 0;
  transform: rotate(35deg);
  background: #EAB308;
  color: #1c1917;
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-align: center;
  text-transform: uppercase;
}

.card-face__head {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-bottom: 6px;
  border-bottom: 2px solid color-mix(in srgb, var(--tone) 55%, transparent);
}

.card-face__icon { font-size: 1.1rem; }

.card-face__deck {
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: color-mix(in srgb, var(--tone) 75%, #000);
}

.card-face__tag {
  margin-left: auto;
  padding: 0 6px;
  border-radius: 4px;
  background: color-mix(in srgb, var(--tone) 25%, #fff);
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
}

.card-face__title {
  margin: 2px 0 0;
  font-size: 1.35rem;
  font-weight: 800;
  line-height: 1.05;
  color: var(--ink);
}

/* Contraband cards have red names, as on the physical cards */
.card-face__title.is-contraband { color: #DC2626; }

.card-face__text {
  margin: 0;
  white-space: pre-line;
  font-family: 'Segoe UI', system-ui, sans-serif;
  font-size: 0.86rem;
  line-height: 1.4;
  color: #292524;
}

/* Sizes */
.card-face--lg {
  width: min(340px, 86vw);
  min-height: 300px;
  padding: 18px 20px 20px;
}
.card-face--lg .card-face__title { font-size: 2rem; }
.card-face--lg .card-face__text { font-size: 1.02rem; }

.card-face--sm {
  padding: 8px 10px 10px;
  gap: 3px;
}
.card-face--sm .card-face__title { font-size: 1.05rem; }
.card-face--sm .card-face__text { font-size: 0.76rem; }
.card-face--sm .card-face__head { padding-bottom: 3px; }
/* Small collectables skip the deck name (it crowds the Equip tag); other card types keep it */
.card-face--sm.card-face--collectable .card-face__deck { display: none; }
.card-face--sm .card-face__deck { font-size: 0.66rem; }
</style>
