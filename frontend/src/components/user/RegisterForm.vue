<template>
  <div class="register-form">
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
          placeholder="Choose a username"
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
          placeholder="Create a password"
          class="form-input"
          autocomplete="new-password"
        />
      </div>
      
      <div class="form-group">
        <label class="form-label">
          <span class="label-icon">🔐</span>
          Confirm Password
        </label>
        <input
          v-model="confirmPassword"
          type="password"
          required
          placeholder="Confirm your password"
          class="form-input"
          autocomplete="new-password"
        />
      </div>
      
      <div v-if="errors" class="error-message">
        <span class="error-icon">⚠️</span>
        {{ errors }}
      </div>
      
      <button type="submit" :disabled="loading" class="submit-btn">
        <span v-if="loading" class="loading-spinner"></span>
        {{ loading ? 'Creating account...' : 'Create Account' }}
      </button>
    </form>
  </div>
</template>

<script>
export default {
  data () {
    return {
      username: "",
      password: "",
      confirmPassword: "",
      loading: false
    }
  },
  methods: {
    async onSubmit () {
      var credentials = { 
        username: this.username, 
        password: this.password, 
        confirmPassword: this.confirmPassword 
      };
      console.log('[Register] Submitting registration for:', this.username)
      this.loading = true
      try {
        await this.$store.dispatch('auth/register', credentials)
        console.log('[Register] Registration successful, now logging in...')
        // If registration didn't return a token, automatically login
        await this.$store.dispatch('auth/login', {
          username: this.username,
          password: this.password
        })
        console.log('[Register] Auto-login successful, navigating to rooms')
        this.$router.push('/rooms')
      } catch (err) {
        console.error('[Register] Failed:', err)
        // If registration succeeded but login failed, still show success
        if (err === 'Registration succeeded, please login') {
          try {
            await this.$store.dispatch('auth/login', {
              username: this.username,
              password: this.password
            })
            console.log('[Register] Auto-login successful after registration')
            this.$router.push('/rooms')
          } catch (loginErr) {
            console.error('[Register] Auto-login failed:', loginErr)
            this.error = 'Registration succeeded, please login manually'
          }
        } else {
          this.error = this.$store.state.auth.errors || 'Registration failed'
        }
      } finally {
        this.loading = false
      }
    }
  },
  computed: {
    errors () {
      return this.$store.state.auth.errors
    }
  }
}
</script>

<style scoped>
.register-form {
  width: 100%;
}

.form-group {
  margin-bottom: 20px;
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
  border-color: #22D3EE;
  box-shadow: 0 0 0 4px rgba(34, 211, 238, 0.1);
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
  background: linear-gradient(135deg, #22D3EE 0%, #0891B2 100%);
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
  box-shadow: 0 8px 20px rgba(34, 211, 238, 0.3);
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
