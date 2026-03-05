<template>
  <b-modal
    ref="modal"
    id="govAssignModal"
    title="Assign Government Roles"
  >
    <div v-if="govForm.type === 'Dictatorship'">
      <label for="dictatorSelect" class="mr-2">Select the Dictator:</label>
      <select id="dictatorSelect" v-model="govForm.dictator" class="form-control">
        <option :value="null">Choose a user</option>
        <option v-for="opt in participantOptions" :key="opt.value" :value="opt.value">
          {{ opt.text }}
        </option>
      </select>
    </div>

    <div v-else-if="govForm.type === 'Republic'">
      <div class="mb-3">
        <label for="headSelect" class="mr-2">Head of State:</label>
        <select id="headSelect" v-model="govForm.head_of_state" class="form-control">
          <option :value="null">Choose a user</option>
          <option v-for="opt in participantOptions" :key="opt.value" :value="opt.value">
            {{ opt.text }}
          </option>
        </select>
      </div>
      <div>
        <label for="advisorSelect" class="mr-2">Advisors (2):</label>
        <select
          id="advisorSelect"
          v-model="govForm.advisors"
          class="form-control"
          multiple
          size="5"
        >
          <option v-for="opt in participantOptions" :key="opt.value" :value="opt.value">
            {{ opt.text }}
          </option>
        </select>
        <small class="text-muted">Hold Ctrl (Cmd on Mac) to select two advisors.</small>
      </div>
    </div>

    <div v-else-if="govForm.type === 'Communism'">
      <label for="politburoSelect" class="mr-2">Politburo members (2):</label>
      <select
        id="politburoSelect"
        v-model="govForm.politburo"
        class="form-control"
        multiple
        size="6"
      >
        <option v-for="opt in participantOptions" :key="opt.value" :value="opt.value">
          {{ opt.text }}
        </option>
      </select>
      <small class="text-muted">Hold Ctrl (Cmd on Mac) to select two members.</small>
    </div>

    <div v-else>
      <p class="text-muted">No roles required for {{ govForm.type }}.</p>
    </div>

    <div class="text-danger mt-2" v-if="error">{{ error }}</div>

    <div class="d-flex justify-content-end mt-3">
      <b-button size="sm" variant="secondary" :disabled="isSubmitting" @click="hide">
        Cancel
      </b-button>
      <b-button size="sm" class="ml-2" variant="primary" :disabled="isSubmitting" @click="submit">
        {{ isSubmitting ? 'Saving…' : 'Save' }}
      </b-button>
    </div>
    <template #footer></template>
  </b-modal>
</template>

<script setup>
import { ref, computed } from 'vue'

const modal = ref(null)
const isSubmitting = ref(false)
const error = ref('')
const govForm = ref({
  type: null,
  dictator: null,
  head_of_state: null,
  advisors: [],
  politburo: []
})

const props = defineProps({
  participants: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['submit'])

const participantOptions = computed(() =>
  (props.participants || []).map(p => ({
    value: p.user_id ?? p.userId ?? p.id,
    text: p.username || `User ${p.user_id || p.id}`
  }))
)

const show = (governmentType) => {
  govForm.value = {
    type: governmentType,
    dictator: null,
    head_of_state: null,
    advisors: [],
    politburo: []
  }
  error.value = ''
  modal.value?.show()
}

const hide = () => modal.value?.hide()

const submit = () => {
  error.value = ''
  const t = govForm.value.type
  let payload = { type: t }

  if (t === 'Dictatorship') {
    if (!govForm.value.dictator) {
      error.value = 'Please select a dictator.'
      return
    }
    payload.dictator = Number(govForm.value.dictator)
  } else if (t === 'Republic') {
    if (!govForm.value.head_of_state || (govForm.value.advisors || []).length !== 2) {
      error.value = 'Select a head of state and exactly 2 advisors.'
      return
    }
    payload.head_of_state = Number(govForm.value.head_of_state)
    payload.advisors = govForm.value.advisors.slice(0, 2).map(Number)
    const all = [payload.head_of_state, ...payload.advisors]
    if (new Set(all).size !== 3) {
      error.value = 'Head of state and advisors must be different people.'
      return
    }
  } else if (t === 'Communism') {
    if ((govForm.value.politburo || []).length !== 2) {
      error.value = 'Select exactly 2 politburo members.'
      return
    }
    payload.politburo = govForm.value.politburo.slice(0, 2).map(Number)
    if (new Set(payload.politburo).size !== 2) {
      error.value = 'Politburo members must be different people.'
      return
    }
  }

  isSubmitting.value = true
  try {
    emit('submit', payload)
  } finally {
    isSubmitting.value = false
  }
}

defineExpose({
  show,
  hide
})
</script>

<style>
/* Hide default modal footer for RoomGovernmentModal */
#govAssignModal .modal-footer {
  display: none !important;
}
</style>

<style scoped>
select.form-control {
  color: #F1F5F9;
  background-color: #1e293b;
  border: 1px solid #475569;
}

select.form-control:focus {
  color: #F1F5F9;
  background-color: #1e293b;
  border-color: #60a5fa;
  outline: none;
}

select.form-control option {
  color: #F1F5F9;
  background-color: #1e293b;
}
</style>
