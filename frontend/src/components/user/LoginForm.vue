<template>
    <b-form @submit="onSubmit">
      <b-form-group
        label="Username:"
        description="Enter your username"
        placeholder="username"
        label-class="font-weight-bold pt-0">
        <b-form-input
          v-model="username"
          required>
          </b-form-input>
      </b-form-group>
      <b-form-group
        label="Password:"
        description="Enter your password"
        placeholder="password"
        label-class="font-weight-bold pt-0">
        <b-form-input
          v-model="password"
          type="password"
          required>
          </b-form-input>
      </b-form-group>
      <b-button type="submit" class="btn btn-success">Login</b-button>
    </b-form>
</template>

<script>
export default {
  data () {
    return {
      username: "",
      password: "",
    }
  },
  methods: {
    onSubmit () {
      var credentials = {
        username: this.username,
        password: this.password
      }
      this.$store.dispatch("login", credentials)
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
