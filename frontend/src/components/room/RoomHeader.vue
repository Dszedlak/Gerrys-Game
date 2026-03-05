<template>
  <b-row class="room-header">
    <b-col>
      <div class="room-header__actions">
        <b-button-group class="room-header__button-group">
          <b-button 
            class="room-header__button"
            @click="$emit('leave-room')"
          >
            Leave Room?
          </b-button>
          <b-button 
            v-if="isAdmin"
            class="room-header__button room-header__button--info"
            variant="info"
            @click="$emit('open-admin-controls')"
          >
            Admin Controls
          </b-button>
        </b-button-group>
      </div>
    </b-col>
  </b-row>
</template>

<script setup>
const props = defineProps({
  isAdmin: {
    type: Boolean,
    required: true
  }
})
</script>

<style scoped>
.room-header {
  height: auto;
  text-align: center;
  padding: 15px 10px;
  margin-bottom: 3px;
  background: transparent;
  border-radius: 0;
  box-shadow: none;
}

.room-header__actions {
  display: flex;
  justify-content: center;
  margin-bottom: 0;
  margin-top: 0;
}

.room-header__button-group {
  gap: 10px;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  background: transparent;
  padding: 0;
  box-shadow: none;
}

.room-header__button {
  background: #1A1F2E !important;
  border: 2px solid #22D3EE !important;
  color: #F1F5F9 !important;
  font-weight: 600 !important;
  border-radius: 8px !important;
  padding: 8px 15px !important;
  transition: all 0.2s ease !important;
  height: auto !important;
}

.room-header__button:hover {
  transform: translateY(-2px) !important;
  border-color: #EAB308 !important;
  color: #EAB308 !important;
}

.room-header__button--danger {
  border-color: #ff4444 !important;
  color: #ff4444 !important;
}

.room-header__button--danger:hover {
  border-color: #EAB308 !important;
  color: #EAB308 !important;
}

.room-header__button--info {
  border-color: #F1F5F9 !important;
  color: #F1F5F9 !important;
}

.room-header__button--info:hover {
  border-color: #EAB308 !important;
  color: #EAB308 !important;
}
</style>
