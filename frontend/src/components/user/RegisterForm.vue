<template>
  <div class="form-container">
    <BForm @submit.prevent="onSubmit">
      <BFormGroup
        label="Username:"
        description="Enter your desired username"
        label-class="font-weight-bold pt-0">
        <BFormInput
          v-model="username"
          placeholder="username"
          required
          class="form-input"
        />
      </BFormGroup>
      <BFormGroup
        label="Password:"
        description="Enter your desired password"
        label-class="font-weight-bold pt-0">
        <BFormInput
          v-model="password"
          type="password"
          placeholder="password"
          required
          class="form-input"
        />
      </BFormGroup>
      <BFormGroup
        label="Confirm password:"
        description="Enter the same password again"
        label-class="font-weight-bold pt-0">
        <BFormInput
          v-model="confirmPassword"
          type="password"
          placeholder="password"
          required
          class="form-input"
        />
      </BFormGroup>
      <div class="form-group">
        <small v-if="errors" class="text-danger error-message">{{ errors }}</small>
      </div>
      <BButton type="submit" variant="success" class="submit-btn">Register</BButton>
    </BForm>
  </div>
</template>

<script>
import { BForm, BFormGroup, BFormInput, BButton } from 'bootstrap-vue-next'

export default {
  components: {
    BForm,
    BFormGroup,
    BFormInput,
    BButton
  },
  data () {
    return {
      username: "",
      password: "",
      confirmPassword: ""
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
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%) !important;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
  margin-top: 10px;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(40, 167, 69, 0.5);
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