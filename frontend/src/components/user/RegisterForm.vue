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
    onSubmit () {
      var credentials = { 
        username: this.username, 
        password: this.password, 
        confirmPassword: this.confirmPassword 
      };
      this.$store.dispatch("register", credentials)
      .then(() => {
        this.$router.push("/me")
      })
    }
  },
  computed: {
    errors () {
      return this.$store.state.auth.errors
    }
  }
}
</script>
