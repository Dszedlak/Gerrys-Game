<template>
  <div class="login-form">
    <form @submit.prevent="onSubmit">
      <div class="form-group">
        <label class="form-label">
          <span class="label-icon">👤</span>
          Username
        </label>
        <input
          v-model="username"
          type="text"
          required
          maxlength="30"
          placeholder="Enter your username"
          class="form-input"
          autocomplete="username"
        />
      </div>
      
      <div class="form-group">
        <label class="form-label">
          <span class="label-icon">🔒</span>
          Password
        </label>
        <input
          v-model="password"
          type="password"
          required
          placeholder="Enter your password"
          class="form-input"
          autocomplete="current-password"
        />
      </div>
      
      <div v-if="error" class="error-message">
        <span class="error-icon">⚠️</span>
        {{ error }}
      </div>
      
      <button type="submit" :disabled="loading" class="submit-btn">
        <span v-if="loading" class="loading-spinner"></span>
        {{ loading ? 'Signing in...' : 'Sign In' }}
      </button>
    </form>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

export default {
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
.login-form {
  width: 100%;
}

.form-group {
  margin-bottom: 24px;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #94A3B8;
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 10px;
}

.label-icon {
  font-size: 1rem;
}

.form-input {
  width: 100%;
  padding: 14px 18px;
  background: #0B0F19;
  border: 2px solid #334155;
  border-radius: 12px;
  color: #F1F5F9;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.form-input::placeholder {
  color: #475569;
}

.form-input:hover {
  border-color: #475569;
}

.form-input:focus {
  outline: none;
  border-color: #EAB308;
  box-shadow: 0 0 0 4px rgba(234, 179, 8, 0.1);
}

.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #EF444422;
  border: 1px solid #EF444444;
  border-radius: 10px;
  color: #EF4444;
  font-size: 0.9rem;
  margin-bottom: 20px;
}

.error-icon {
  font-size: 1rem;
}

.submit-btn {
  width: 100%;
  padding: 16px 24px;
  background: linear-gradient(135deg, #EAB308 0%, #CA8A04 100%);
  border: none;
  border-radius: 12px;
  color: #0B0F19;
  font-size: 1.1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(234, 179, 8, 0.3);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(11, 15, 25, 0.3);
  border-top-color: #0B0F19;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
