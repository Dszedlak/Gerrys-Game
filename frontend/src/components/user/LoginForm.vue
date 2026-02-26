<template>
  <div class="form-container">
    <BForm @submit.prevent="onSubmit">
      <BFormGroup label="Username" label-for="username-input">
        <BFormInput
          id="username-input"
          v-model="username"
          required
          placeholder="Enter username"
          class="form-input"
        />
      </BFormGroup>
      <BFormGroup label="Password" label-for="password-input">
        <BFormInput
          id="password-input"
          v-model="password"
          type="password"
          required
          placeholder="Enter password"
          class="form-input"
        />
      </BFormGroup>
      <div class="mb-3">
        <small v-if="error" class="text-danger error-message">{{ error }}</small>
      </div>
      <BButton type="submit" variant="primary" :disabled="loading" class="submit-btn">
        {{ loading ? 'Logging in...' : 'Login' }}
      </BButton>
    </BForm>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { BForm, BFormGroup, BFormInput, BButton } from 'bootstrap-vue-next'

export default {
  components: { BForm, BFormGroup, BFormInput, BButton },
  setup() {
    const store = useStore()
    const router = useRouter()
    const username = ref('')
    const password = ref('')
    const error = ref('')
    const loading = ref(false)

    const onSubmit = () => {
      error.value = ''
      loading.value = true
      store.dispatch('auth/login', { username: username.value, password: password.value })
        .then(() => {
          router.push({ name: 'Home' })
        })
        .catch(() => {
          error.value = store.state.auth.errors || 'Login failed'
        })
        .finally(() => {
          loading.value = false
        })
    }

    return { username, password, error, loading, onSubmit }
  }
}
</script>
<style scoped>
.form-container {
  background: #0f1535;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 0 20px rgba(0, 255, 65, 0.2), inset 0 0 15px rgba(0, 255, 65, 0.05);
  border: 1px solid rgba(0, 255, 65, 0.2);
}

.form-input {
  border-radius: 8px;
  border: 2px solid rgba(0, 255, 65, 0.3);
  padding: 10px 12px;
  transition: all 0.3s ease;
  background: #0a0e27;
  color: #00ff41;
}

.form-input::placeholder {
  color: rgba(0, 255, 65, 0.5);
}

.form-input:focus {
  border-color: #00ff41;
  box-shadow: 0 0 15px rgba(0, 255, 65, 0.3), inset 0 0 10px rgba(0, 255, 65, 0.05);
  background: #0a0e27;
  color: #00ff41;
}

.submit-btn {
  width: 100%;
  background: #0f1535;
  border: 2px solid #00ff41;
  border-radius: 8px;
  padding: 12px 24px;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 0 15px rgba(0, 255, 65, 0.3);
  margin-top: 10px;
  color: #00ff41;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 0 30px rgba(0, 255, 65, 0.6);
  text-shadow: 0 0 8px rgba(0, 255, 65, 0.6);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.error-message {
  display: block;
  margin-bottom: 10px;
  font-weight: 500;
  color: #ff4444;
}
</style>