<template>
  <div class="login-container">
    <BRow align-h="center">
      <BCol cols="8">
        <div class="tabs-wrapper">
          <BTabs content-class="mt-3" nav-class="tabs-nav">
            <BTab title="Login">
              <LoginForm />
            </BTab>
            <BTab title="Register">
              <RegisterForm />
            </BTab>
          </BTabs>
        </div>
      </BCol>
    </BRow>
  </div>
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

<style scoped>
.login-container {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
  display: flex;
  align-items: center;
  padding: 40px 20px;
  margin: -8px -8px 0 -8px;
}

.tabs-wrapper {
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  width: 100%;
}
</style>