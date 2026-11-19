<template>
  <div class="premium">
    <button type="button" class="premium__buy" @click="open">
      💎 BUY PREMIUM GERRY'S GAME MEMBERSHIP 💎
    </button>

    <Teleport to="body">
      <div
        v-if="isOpen"
        class="premium__overlay"
        role="dialog"
        aria-modal="true"
        aria-label="Premium membership"
        @keydown.esc="close"
      >
        <div class="premium__stars" aria-hidden="true">
          <span
            v-for="star in stars"
            :key="star.id"
            class="premium__star"
            :style="star.style"
          >✡️</span>
        </div>

        <div class="premium__marquee" aria-hidden="true">
          <span>
            🚨 LIMITED TIME OFFER 🚨 ACT NOW 🚨 NOT A SCAM 🚨 GERRY APPROVED 🚨
            100% LEGIT 🚨 LIMITED TIME OFFER 🚨 ACT NOW 🚨 NOT A SCAM 🚨
          </span>
        </div>

        <div class="premium__card">
          <h2 class="premium__title">⚠️ PLZ ENTER BANK ACCOUNT DETAILS ⚠️</h2>

          <p class="premium__price">
            FOR JUST <span class="premium__price-amount">£50</span> A MONTH!!!
          </p>

          <p class="premium__lead">you get EXCLUSIVE access to:</p>

          <ul class="premium__perks">
            <li v-for="perk in perks" :key="perk.text">
              <span class="premium__perk-icon">{{ perk.icon }}</span>
              {{ perk.text }}
            </li>
          </ul>

          <!-- Real inputs, but every character typed is replaced with a star
               on the spot. What was typed is never kept, and there is no
               form, name or submit, so nothing can be sent anywhere. -->
          <div class="premium__fake-form">
            <label
              v-for="field in fields"
              :key="field.key"
              class="premium__fake-field"
            >
              <span>{{ field.label }}</span>
              <input
                type="text"
                class="premium__fake-box"
                :value="starred[field.key]"
                autocomplete="off"
                autocorrect="off"
                autocapitalize="off"
                spellcheck="false"
                @input="starify(field.key, $event)"
              />
            </label>
          </div>

          <p class="premium__countdown">
            ⏰ OFFER ENDS IN 00:00:0{{ countdown }} ⏰
          </p>

          <div class="premium__actions">
            <button
              type="button"
              class="premium__subscribe"
              :style="{ transform: `translate(${dodge.x}px, ${dodge.y}px)` }"
              @mouseenter="runAway"
              @click="subscribe"
            >
              {{ subscribed ? '✅ PAUL HAS BEEN HACKED ✅' : '💸 SUBSCRIBE NOW 💸' }}
            </button>
          </div>

          <button ref="closeBtn" type="button" class="premium__close" @click="close">
            no thanks, I hate fun
          </button>
        </div>

        <!-- Full-screen reveal, shown 5s after subscribing -->
        <div v-if="revealing" class="premium__reveal" @click="close">
          <img :src="REVEAL_IMAGE" alt="" class="premium__reveal-img" />
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, nextTick, onBeforeUnmount } from 'vue'

const perks = [
  { icon: '⏱️', text: "Removing time from people's clocks whenever you want" },
  { icon: '💻', text: "Hacking Paul's PC" },
  { icon: '🏆', text: 'Winning the game' },
  { icon: '🏡', text: 'A holiday home in the West Bank' }
]

// Served from frontend/public
const MUSIC_URL = `${process.env.BASE_URL}premium-music.mp3`
// Image shown full screen 5s after subscribing, served from frontend/public
const REVEAL_IMAGE = `${process.env.BASE_URL}premium-reveal.jpg`
const REVEAL_DELAY_MS = 5000

// Stars drift across the screen on random paths, speeds and spins
const rand = (min, max) => min + Math.random() * (max - min)
const stars = Array.from({ length: 150 }, (_, id) => ({
  id,
  style: {
    left: `${rand(0, 100)}vw`,
    top: `${rand(0, 100)}vh`,
    fontSize: `${rand(1.6, 4)}rem`,
    animationDuration: `${rand(1, 2.5)}s`,
    animationDelay: `${-rand(0, 2.5)}s`,
    '--dx': `${rand(-60, 60)}vw`,
    '--dy': `${rand(-60, 60)}vh`,
    '--spin': `${rand(-720, 720)}deg`
  }
}))

const fields = [
  { key: 'sortCode', label: 'Sort code' },
  { key: 'account', label: 'Account no.' },
  { key: 'maiden', label: "Mother's maiden name" }
]

const STAR = '✡' // ✡ — one code point, so lengths count cleanly
const starred = ref({ sortCode: '', account: '', maiden: '' })

// Keep only the character count; the typed text itself is discarded
function starify(key, e) {
  const count = Array.from(e.target.value).length
  const masked = STAR.repeat(count)
  starred.value[key] = masked
  e.target.value = masked
}

const isOpen = ref(false)
const subscribed = ref(false)
const countdown = ref(9)
const dodge = ref({ x: 0, y: 0 })
const revealing = ref(false)
const closeBtn = ref(null)
let timer = null
let revealTimer = null
let dodges = 0
let music = null

// The offer is always about to end, and never does
function tick() {
  countdown.value = countdown.value <= 1 ? 9 : countdown.value - 1
}

async function open() {
  isOpen.value = true
  subscribed.value = false
  countdown.value = 9
  dodge.value = { x: 0, y: 0 }
  dodges = 0
  revealing.value = false
  starred.value = { sortCode: '', account: '', maiden: '' }
  timer = setInterval(tick, 1000)

  // Started from the click, so the browser allows it to play with sound
  music = music || new Audio(MUSIC_URL)
  music.loop = true
  music.currentTime = 0
  music.play().catch(() => {})
  await nextTick()
  closeBtn.value?.focus()
}

function close() {
  isOpen.value = false
  revealing.value = false
  clearInterval(timer)
  clearTimeout(revealTimer)
  timer = null
  revealTimer = null
  music?.pause()
}

// The subscribe button dodges the mouse a few times before giving up
function runAway() {
  if (subscribed.value || dodges >= 5) return
  dodges++
  const rx = () => (Math.random() - 0.5) * 320
  const ry = () => (Math.random() - 0.5) * 120
  dodge.value = { x: rx(), y: ry() }
}

function subscribe() {
  subscribed.value = true
  dodge.value = { x: 0, y: 0 }
  dodges = 0

  if (REVEAL_IMAGE && !revealTimer) {
    revealTimer = setTimeout(() => { revealing.value = true }, REVEAL_DELAY_MS)
  }
}

onBeforeUnmount(close)
</script>

<style scoped>
.premium {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

.premium__buy {
  padding: 12px 26px;
  border: 3px solid #fff200;
  border-radius: 999px;
  background: linear-gradient(90deg, #ff00cc, #ffcc00, #00ffcc, #ff00cc);
  background-size: 300% 100%;
  color: #1a0033;
  font-family: 'Comic Sans MS', 'Comic Sans', cursive;
  font-size: 1.05rem;
  font-weight: 900;
  letter-spacing: 0.04em;
  cursor: pointer;
  box-shadow: 0 0 18px rgba(255, 0, 204, 0.6);
  animation: premium-slide 3s linear infinite, premium-pulse 1.2s ease-in-out infinite;
}

.premium__buy:hover {
  transform: scale(1.06) rotate(-1deg);
}

/* ---------- The obnoxious screen ---------- */
.premium__overlay {
  position: fixed;
  inset: 0;
  z-index: 5000;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 16px;
  overflow-y: auto;
  font-family: 'Comic Sans MS', 'Comic Sans', cursive;
  /* 5 colour swaps a second = 2.5 flashes/s, just under the 3 flashes/s
     seizure limit (WCAG 2.3.1). Don't make this any faster. */
  animation: premium-flash 0.8s steps(1) infinite;
}

.premium__marquee {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  overflow: hidden;
  white-space: nowrap;
  background: #000;
  color: #fff200;
  font-weight: 900;
  padding: 6px 0;
}

.premium__marquee span {
  display: inline-block;
  padding-left: 100%;
  animation: premium-marquee 5s linear infinite;
}

.premium__card {
  max-width: 640px;
  width: 100%;
  margin-top: 40px;
  padding: 24px 28px;
  background: #fff;
  border: 8px dashed #ff0000;
  border-radius: 18px;
  box-shadow: 0 0 0 8px #fff200, 0 0 60px rgba(0, 0, 0, 0.6);
  color: #1a0033;
  text-align: center;
}

.premium__title {
  margin: 0 0 10px;
  color: #ff0000;
  font-size: 1.9rem;
  font-weight: 900;
  text-shadow: 3px 3px 0 #fff200;
  /* Small elements like this may strobe fast; only the full-screen
     background is held under the 3 flashes/s limit. */
  animation: premium-shake 0.35s linear infinite,
             premium-text-strobe 0.15s steps(1) infinite;
}

.premium__price {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 900;
}

.premium__price-amount {
  display: inline-block;
  color: #00a000;
  font-size: 2.6rem;
  animation: premium-pulse 0.8s ease-in-out infinite,
             premium-money-strobe 0.12s steps(1) infinite;
}

.premium__lead {
  margin: 8px 0 6px;
  font-size: 1.1rem;
  font-style: italic;
}

.premium__perks {
  list-style: none;
  margin: 0 0 14px;
  padding: 0;
  text-align: left;
}

.premium__perks li {
  margin: 6px 0;
  padding: 8px 12px;
  background: #fff7b3;
  border: 2px solid #ff00cc;
  border-radius: 10px;
  font-size: 1.05rem;
  font-weight: 700;
}

.premium__perk-icon {
  margin-right: 6px;
}

.premium__fake-form {
  display: grid;
  gap: 6px;
  margin-bottom: 12px;
}

.premium__fake-field {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  font-weight: 700;
}

/* Explicit, so global label styles can't recolour it */
.premium__fake-field > span {
  color: #000;
}

.premium__fake-box {
  flex: 0 1 220px;
  min-width: 0;
  padding: 4px 10px;
  background: #fff;
  border: 2px inset #999;
  color: #0038b8;
  font-family: inherit;
  font-size: 1.1rem;
  letter-spacing: 0.1em;
}

.premium__fake-box:focus {
  outline: 3px solid #ff00cc;
}

.premium__countdown {
  margin: 0 0 12px;
  color: #ff0000;
  font-size: 1.2rem;
  font-weight: 900;
  animation: premium-text-strobe 0.2s steps(1) infinite;
}

.premium__actions {
  display: flex;
  justify-content: center;
  min-height: 60px;
}

.premium__subscribe {
  padding: 14px 30px;
  border: 4px solid #000;
  border-radius: 12px;
  background: #00e000;
  color: #000;
  font-family: inherit;
  font-size: 1.3rem;
  font-weight: 900;
  cursor: pointer;
  animation: premium-border-strobe 0.15s steps(1) infinite;
  transition: transform 0.15s ease-out;
}

.premium__close {
  margin-top: 14px;
  background: none;
  border: none;
  color: #888;
  font-size: 0.75rem;
  text-decoration: underline;
  cursor: pointer;
}

/* ---------- Flying stars, behind the card ---------- */
.premium__stars {
  position: fixed;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.premium__star {
  position: absolute;
  line-height: 1;
  animation-name: premium-fly;
  animation-timing-function: linear;
  animation-iteration-count: infinite;
  animation-direction: alternate;
}

.premium__card,
.premium__marquee {
  position: relative;
  z-index: 1;
}

.premium__marquee {
  position: absolute;
}

/* ---------- Reveal ---------- */
.premium__reveal {
  position: fixed;
  inset: 0;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
  cursor: pointer;
}

/* Whole image visible, as large as the screen allows */
.premium__reveal-img {
  width: 100vw;
  height: 100vh;
  object-fit: contain;
}

/* ---------- Animations ---------- */
@keyframes premium-fly {
  from { transform: translate(0, 0) rotate(0deg); }
  to   { transform: translate(var(--dx), var(--dy)) rotate(var(--spin)); }
}

@keyframes premium-flash {
  0%   { background: #ff00cc; }
  25%  { background: #fff200; }
  50%  { background: #00e5ff; }
  75%  { background: #39ff14; }
}

@keyframes premium-text-strobe {
  0%  { color: #ff0000; }
  50% { color: #0000ff; }
}

@keyframes premium-money-strobe {
  0%  { color: #00a000; }
  50% { color: #ff00cc; }
}

@keyframes premium-border-strobe {
  0%  { border-color: #000;    background: #00e000; }
  50% { border-color: #ff0000; background: #fff200; }
}

@keyframes premium-slide {
  from { background-position: 0% 0; }
  to   { background-position: 300% 0; }
}

@keyframes premium-pulse {
  0%, 100% { transform: scale(1); }
  50%      { transform: scale(1.08); }
}

@keyframes premium-shake {
  0%, 100% { transform: translate(0, 0); }
  25%      { transform: translate(-2px, 1px); }
  75%      { transform: translate(2px, -1px); }
}

@keyframes premium-marquee {
  from { transform: translateX(0); }
  to   { transform: translateX(-100%); }
}

@media (max-width: 600px) {
  .premium__buy {
    font-size: 0.85rem;
    padding: 10px 16px;
  }

  .premium__title {
    font-size: 1.35rem;
  }

  .premium__card {
    padding: 18px 14px;
  }
}
</style>
