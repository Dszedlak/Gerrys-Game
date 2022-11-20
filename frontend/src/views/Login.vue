<template>
  <b-row align-h="center">
    <b-col cols="8">
      <b-tabs content-class="mt-3">
        <b-tab title="Login">
          <LoginForm></LoginForm>
        </b-tab>
        <b-tab title="Register">
          <RegisterForm></RegisterForm>
        </b-tab>
      </b-tabs>
    </b-col>
  </b-row>
</template>

<script>
import LoginForm from '@/components/user/LoginForm.vue'
import RegisterForm from '@/components/user/RegisterForm.vue'
export default {
  name: 'authComponent',
  components: {
    LoginForm,
    RegisterForm
  },
  data () {
    return {
      newComponent: false
    }
  },
  methods: {
    changeComponent: function () {
      this.newComponent = !this.newComponent
    }
  }
}
</script>