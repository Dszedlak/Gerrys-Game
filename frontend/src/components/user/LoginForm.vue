<template>
  <form @submit.prevent="onSubmit">
    <div class="mb-3">
      <label for="username" class="form-label">Username</label>
      <input id="username" v-model="username" type="text" class="form-control" required />
    </div>
    <div class="mb-3">
      <label for="password" class="form-label">Password</label>
      <input id="password" v-model="password" type="password" class="form-control" required />
    </div>
    <div class="form-group">
      <small v-if="errors" class="text-danger">{{errors}}</small>
    </div>
    <button type="submit" class="btn btn-primary">Login</button>
  </form>
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
        this.$router.push("/home")
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
