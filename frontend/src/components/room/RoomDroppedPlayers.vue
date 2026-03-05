<template>
  <b-row v-if="droppedPlayers.length > 0" class="room-dropped-players__row">
    <b-col></b-col>
    <b-col cols="4">
      <h5 class="room-dropped-players__title">Dropped Players</h5>
      <table class="room-dropped-players__table">
        <thead>
          <tr>
            <th>Username</th>
            <th>Job Title</th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="p in droppedPlayers" 
            :key="p.user_id || p.userId || p.id"
            class="room-dropped-players__row-item"
          >
            <td>
              {{ p.username }}
              <img
                v-if="governmentIcon(p)"
                :src="governmentIcon(p)"
                class="room-dropped-players__gov-icon"
                alt=""
              />
            </td>
            <td>
              {{ p.job_name }}
              <img
                v-if="perkIcon(p)"
                :src="perkIcon(p)"
                class="room-dropped-players__perk-icon"
                :alt="p.perk"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </b-col>
    <b-col></b-col>
  </b-row>
</template>

<script setup>
import { defineProps } from 'vue'

defineProps({
  droppedPlayers: {
    type: Array,
    required: true
  },
  governmentIcon: {
    type: Function,
    required: true
  },
  perkIcon: {
    type: Function,
    required: true
  }
})
</script>

<style scoped>
.room-dropped-players__row {
  height: auto;
  padding-right: 0;
  padding-left: 0;
  margin-top: 30px;
  margin-bottom: 30px;
  position: relative;
  z-index: 1;
  clear: both;
}

.room-dropped-players__title {
  color: #888;
  font-weight: 600;
  margin-bottom: 12px;
}

.room-dropped-players__table {
  width: 100%;
  background: #1A1F2E !important;
  border: 1px solid rgba(241, 245, 249, 0.3) !important;
  border-radius: 8px;
  overflow: hidden;
  font-size: 0.85em;
}

.room-dropped-players__table thead {
  background: #0B0F19 !important;
  border-bottom: 1px solid #22D3EE !important;
}

.room-dropped-players__table thead th {
  vertical-align: middle;
  border: 1px solid #22D3EE !important;
  color: #EAB308 !important;
  font-weight: 700 !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-align: center !important;
  font-family: 'Barlow Condensed' !important;
  font-size: 0.95em !important;
  background: #1A1F2E !important;
  padding: 8px 10px !important;
  line-height: 1.4;
}

.room-dropped-players__table tbody {
  background: #1A1F2E !important;
}

.room-dropped-players__table tbody td {
  border-color: rgba(241, 245, 249, 0.15) !important;
  padding: 10px !important;
  vertical-align: middle;
  color: #666 !important;
  font-weight: 500;
  text-align: center !important;
  font-size: 0.9em !important;
  background: rgba(241, 245, 249, 0.05) !important;
}

.room-dropped-players__row-item {
  transition: background-color 0.2s ease;
  background: rgba(241, 245, 249, 0.05) !important;
  text-decoration: line-through;
  opacity: 0.6;
}

/* Icons */
.room-dropped-players__gov-icon {
  height: 20px;
  width: auto;
  margin-left: 4px;
  vertical-align: middle;
  display: inline-block;
}

.room-dropped-players__perk-icon {
  height: 20px;
  width: 20px;
  object-fit: contain;
  margin-left: 4px;
  vertical-align: middle;
  display: inline-block;
}
</style>
