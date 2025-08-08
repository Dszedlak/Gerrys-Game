<template>
  <BRow align-h="center">
    <BCol cols="8">
      <BTabs content-class="mt-3">
        <BTab title="Login">
          <LoginForm />
        </BTab>
        <BTab title="Register">
          <RegisterForm />
        </BTab>
      </BTabs>
    </BCol>
  </BRow>
</template>

<script>
import { BRow, BCol, BTabs, BTab } from 'bootstrap-vue-next'
import LoginForm from '@/components/user/LoginForm.vue'
import RegisterForm from '@/components/user/RegisterForm.vue'

export default {
  name: 'authComponent',
  components: {
    BRow,
    BCol,
    BTabs,
    BTab,
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