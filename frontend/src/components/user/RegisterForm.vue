<template>
  <b-form @submit="onSubmit">
    <b-form-group
      label="Username:"
      description="Enter your desired username"
      placeholder="username"
      label-class="font-weight-bold pt-0">
      <b-form-input
        v-model="username"
        required>
        </b-form-input>
    </b-form-group>
    <b-form-group
      label="Password:"
      description="Enter your desired password"
      placeholder="password"
      label-class="font-weight-bold pt-0">
      <b-form-input
        v-model="password"
        type="password"
        required>
        </b-form-input>
    </b-form-group>
    <b-form-group
      label="Confirm password:"
      description="Enter the same password again"
      placeholder="password"
      label-class="font-weight-bold pt-0">
      <b-form-input
        v-model="confirmPassword"
        type="password"
        required>
        </b-form-input>
    </b-form-group>
    <div class="form-group">
      <small v-if="errors" class="text-danger">{{errors}}</small>
    </div>
    <b-button type="submit" class="btn btn-success">Register</b-button>
  </b-form>
</template>

<script>
export default {
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
