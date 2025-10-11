<template>
  <BForm @submit.prevent="onSubmit">
    <BFormGroup
      label="Username:"
      description="Enter your desired username"
      label-class="font-weight-bold pt-0">
      <BFormInput
        v-model="username"
        placeholder="username"
        required
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
      />
    </BFormGroup>
    <div class="form-group">
      <small v-if="errors" class="text-danger">{{ errors }}</small>
    </div>
    <BButton type="submit" variant="success">Register</BButton>
  </BForm>
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
