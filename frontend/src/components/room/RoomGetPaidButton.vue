<template>
  <b-row class="room-get-paid__row">
    <b-col>
      <div class="room-get-paid__container">
        <b-button
          class="room-get-paid__button"
          variant="warning"
          :disabled="isLoading"
          @click="$emit('get-paid')"
          title="Request pay based on your current job"
        >
          {{ isLoading ? 'Getting Paid…' : 'Get Paid' }}
        </b-button>
      </div>
    </b-col>
  </b-row>
</template>

<script setup>
defineProps({
  isLoading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['get-paid'])
</script>

<style scoped>
.room-get-paid__row {
  margin-top: 20px;
  margin-bottom: 20px;
}

.room-get-paid__container {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
}

.room-get-paid__button {
  background: #1A1F2E !important;
  border: 2px solid #EAB308 !important;
  color: #EAB308 !important;
  font-weight: 600 !important;
  border-radius: 8px !important;
  padding: 8px 20px !important;
  transition: all 0.2s ease !important;
  font-size: 0.9em !important;
  min-width: 150px;
}

.room-get-paid__button:hover:not(:disabled) {
  border-color: #F1F5F9 !important;
  color: #F1F5F9 !important;
  transform: translateY(-2px) !important;
}

.room-get-paid__button:disabled {
  opacity: 0.6 !important;
  cursor: not-allowed !important;
}
</style>
