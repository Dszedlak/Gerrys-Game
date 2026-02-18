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
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.form-input {
  border-radius: 8px;
  border: 2px solid #e8e8e8;
  padding: 10px 12px;
  transition: all 0.3s ease;
}

.form-input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.submit-btn {
  width: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
  margin-top: 10px;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.error-message {
  display: block;
  margin-bottom: 10px;
  font-weight: 500;
}
</style>