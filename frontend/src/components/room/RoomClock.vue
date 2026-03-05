<template>
  <div>
    <!-- Clock Display Row with Jail, Clock, and Get Paid buttons -->
    <b-row class="room-clock__display-row">
      <b-col cols="12" class="room-clock__display-container">
        <!-- Jail Button (Left) -->
        <div class="room-clock__action-section room-clock__action-section--left">
          <b-button 
            class="room-clock__jail-btn"
            :disabled="isLoadingJail"
            @click="$emit('get-out-of-jail')"
            title="Pay jail fee (8 hours, 12 during dictatorship)"
          >
            <span v-if="!isLoadingJail" class="room-clock__jail-icon">JAIL</span>
            <span v-else>Paying…</span>
            <!-- Top-left suit symbol -->
            <span class="room-clock__suit-symbol room-clock__suit-symbol--diamonds room-clock__suit-symbol-Diamonds--top-left">♦</span>
            <!-- Bottom-right suit symbol -->
            <span class="room-clock__suit-symbol room-clock__suit-symbol--diamonds room-clock__suit-symbol-Diamonds--bottom-right">♦</span>
          </b-button>
        </div>

        <!-- Clock Display (Center) -->
        <div class="room-clock__value">{{ clock }}</div>

        <!-- Get Paid Button (Right) -->
        <div class="room-clock__action-section room-clock__action-section--right">
          <b-button 
            class="room-clock__get-paid-btn"
            :disabled="isLoadingPay"
            @click="$emit('get-paid')"
            title="Get paid based on your job"
          >
            <span v-if="!isLoadingPay">GET PAID</span>
            <span v-else>Paying…</span>
            <!-- Top-left suit symbol -->
            <span class="room-clock__suit-symbol room-clock__suit-symbol--spades room-clock__suit-symbol-Spades--top-left">♠</span>
            <!-- Bottom-right suit symbol -->
            <span class="room-clock__suit-symbol room-clock__suit-symbol--spades room-clock__suit-symbol-Spades--bottom-right">♠</span>
          </b-button>
        </div>
      </b-col>
    </b-row>

    <!-- Clock Controls Row -->
    <b-row class="room-clock__controls-row">
      <b-col cols="12">
        <div class="room-clock__controls">
          <b-button-group class="room-clock__button-group room-clock__button-group--negative">
            <b-button 
              class="room-clock__control-button"
              @click="onAdjustClock(-60)"
            >
              -1h
            </b-button>
            <b-button 
              class="room-clock__control-button"
              @click="onAdjustClock(-30)"
            >
              -30
            </b-button>
            <b-button 
              class="room-clock__control-button"
              @click="onAdjustClock(-20)"
            >
              -20
            </b-button>
            <b-button 
              class="room-clock__control-button"
              @click="onAdjustClock(-10)"
            >
              -10
            </b-button>
          </b-button-group>
          <b-button-group class="room-clock__button-group room-clock__button-group--positive">
            <b-button 
              class="room-clock__control-button"
              @click="onAdjustClock(10)"
            >
              +10
            </b-button>
            <b-button 
              class="room-clock__control-button"
              @click="onAdjustClock(20)"
            >
              +20
            </b-button>
            <b-button 
              class="room-clock__control-button"
              @click="onAdjustClock(30)"
            >
              +30
            </b-button>
            <b-button 
              class="room-clock__control-button"
              @click="onAdjustClock(60)"
            >
              +1h
            </b-button>
          </b-button-group>
        </div>
      </b-col>
    </b-row>
  </div>
</template>

<script setup>
import { defineProps, defineEmits, computed } from 'vue'

const props = defineProps({
  clock: {
    type: String,
    required: true
  },
  maxCollectables: {
    type: Number,
    default: 5
  },
  isLoadingPay: {
    type: Boolean,
    default: false
  },
  isLoadingJail: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['adjust-clock', 'get-paid', 'get-out-of-jail'])

const onAdjustClock = (delta) => {
  emit('adjust-clock', delta)
}
</script>

<style scoped>
.room-clock__display-row {
  height: auto;
  text-align: center;
  padding: 15px 10px;
  margin-bottom: 3px;
  background: transparent;
  border-radius: 0;
  box-shadow: none;
}

.room-clock__display-container {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
}

.room-clock__action-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.room-clock__action-section--left {
  order: -1;
}

.room-clock__action-section--right {
  order: 1;
}

.room-clock__collectables-label {
  font-size: 0.75em;
  font-weight: 600;
  color: #F1F5F9;
  text-align: center;
  margin-top: 4px;
}

.room-clock__value {
  font-size: 4em;
  font-weight: bold;
  color: #00ff00;
  font-family: 'Barlow Condensed', monospace;
  background: radial-gradient(ellipse at center, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.9) 100%);
  border: 3px solid #000;
  border-radius: 15px;
  padding: 26px 44px;
  letter-spacing: 8px;
  display: inline-block;
}

/* JAIL BUTTON - 3 OF DIAMONDS CARD */
.room-clock__jail-btn {
  width: 70px !important;
  height: 112px !important;
  padding: 0 !important;
  background: linear-gradient(135deg, #f5f5f5 0%, #ffffff 100%) !important;
  border: 2px solid #000 !important;
  border-radius: 8px !important;
  position: relative !important;
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3) !important;
  transition: all 0.2s ease !important;
  color: #000 !important;
  font-weight: 700 !important;
}

/* Top-left corner: "3" and "♦" */
.room-clock__jail-btn::before {
  content: '3';
  position: absolute;
  top: 4px;
  left: 4px;
  font-size: 0.7em;
  line-height: 0.8;
  color: #e74c3c;
  font-weight: 900;
}

/* Bottom-right corner: upside down "3" */
.room-clock__jail-btn::after {
  content: '3';
  position: absolute;
  bottom: 4px;
  right: 4px;
  font-size: 0.7em;
  line-height: 0.8;
  color: #e74c3c;
  font-weight: 900;
  transform: rotate(180deg);
}

/* Center diamond symbol */
.room-clock__jail-btn .room-clock__jail-icon {
  font-size: 1.2em;
  color: #e74c3c;
  font-weight: 900;
}

/* Suit symbols on cards */
.room-clock__suit-symbol {
  position: absolute;
  font-size: 0.85em;
  font-weight: 900;
  line-height: 1;
}

/* Top-left position */
.room-clock__suit-symbol-Diamonds--top-left {
  top: 12px;
  left: 3px;
}

/* Top-left position */
.room-clock__suit-symbol-Spades--top-left {
  top: 12px;
  left: 4px;
}


/* Bottom-right position */
.room-clock__suit-symbol-Diamonds--bottom-right {
  bottom: 12px;
  right: 3px;
  transform: rotate(180deg);
}

/* Bottom-right position */
.room-clock__suit-symbol-Spades--bottom-right {
  bottom: 12px;
  right: 4px;
  transform: rotate(180deg);
}

.room-clock__suit-symbol--diamonds {
  color: #e74c3c;
}

.room-clock__suit-symbol--spades {
  color: #000000;
}

.room-clock__jail-btn:not(:disabled):hover {
  border-color: #e74c3c !important;
  transform: translateY(-3px) !important;
  box-shadow: 0 6px 16px rgba(231, 76, 60, 0.4) !important;
}

.room-clock__jail-btn:disabled {
  opacity: 0.5 !important;
  cursor: not-allowed !important;
  background: linear-gradient(135deg, #ccc 0%, #aaa 100%) !important;
  border: 2px solid #666 !important;
}

.room-clock__jail-icon {
  font-weight: 700;
  font-size: 1.2em;
  color: #e74c3c;
}

/* GET PAID BUTTON - ACE OF SPADES CARD */
.room-clock__get-paid-btn {
  width: 70px !important;
  height: 112px !important;
  padding: 0 !important;
  background: linear-gradient(135deg, #ffffff 0%, #bebebe 100%) !important;
  border: 2px solid #8b8b8b !important;
  border-radius: 8px !important;
  position: relative !important;
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
  transition: all 0.2s ease !important;
  color: #000000 !important;
  font-weight: 700 !important;
}

/* Top-left corner: "A" */
.room-clock__get-paid-btn::before {
  content: 'A';
  position: absolute;
  top: 4px;
  left: 4px;
  font-size: 0.7em;
  line-height: 0.8;
  color: #000000;
  font-weight: 900;
}

/* Bottom-right corner: upside down "A" */
.room-clock__get-paid-btn::after {
  content: 'A';
  position: absolute;
  bottom: 4px;
  right: 4px;
  font-size: 0.7em;
  line-height: 0.8;
  color: #000000;
  font-weight: 900;
  transform: rotate(180deg);
}

/* Show the text on the button */
.room-clock__get-paid-btn span {
  font-size: 0.8em;
  display: inline-block;
  color: #000000;
  font-weight: 700;
  text-align: center;
  line-height: 1.2;
}

.room-clock__get-paid-btn:not(:disabled):hover {
  border-color: #FFF !important;
  transform: translateY(-3px) !important;
  box-shadow: 0 6px 16px rgba(255, 215, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.15) !important;
}

.room-clock__get-paid-btn:disabled {
  opacity: 0.5 !important;
  cursor: not-allowed !important;
  background: linear-gradient(135deg, #333 0%, #222 100%) !important;
  border-color: #666 !important;
}

.room-clock__controls-row {
  justify-content: center;
}

.room-clock__controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
  margin-bottom: 16px;
  margin-left: 15px;
}

.room-clock__button-group {
  display: flex;
  gap: 0;
}

.room-clock__button-group--negative {
  /* placeholder for grouping negative adjustments */
}

.room-clock__button-group--positive {
  /* placeholder for grouping positive adjustments */
}

.room-clock__control-button {
  width: auto;
  padding: 1px 18px !important;
  height: 45px;
  text-align: center;
  margin-right: 0;
  background: #1A1F2E !important;
  border: 2px solid #22D3EE !important;
  color: #F1F5F9 !important;
  font-weight: 700 !important;
  border-radius: 8px !important;
  transition: all 0.2s ease !important;
  font-size: 1.05em !important;
}

.room-clock__control-button:hover {
  transform: translateY(-2px) !important;
  border-color: #EAB308 !important;
  color: #EAB308 !important;
}

.room-clock__control-button:active {
  transform: translateY(0) !important;
}
</style>
