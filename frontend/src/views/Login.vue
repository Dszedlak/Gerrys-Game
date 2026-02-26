<template>
  <div class="login-container">
    <BRow align-h="center" class="w-100">
      <BCol cols="12" sm="10" md="8" lg="6" xl="6">
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
  background: #0a0e27;
  min-height: 50vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  margin: -8px -8px 0 -8px;
}

.w-100 {
  width: 100% !important;
}

.tabs-wrapper {
  background: #0f1535;
  border-radius: 12px;
  box-shadow: 0 0 25px rgba(0, 255, 65, 0.2), inset 0 0 15px rgba(0, 255, 65, 0.05);
  overflow: hidden;
  width: 100%;
  border: 1px solid rgba(0, 255, 65, 0.2);
  padding: 20px;
}

/* Style for tabs navigation */
:deep(.tabs-nav) {
  border-bottom: 2px solid rgba(0, 255, 65, 0.2) !important;
  margin-bottom: 20px;
}

:deep(.nav-link) {
  color: rgba(0, 255, 65, 0.6) !important;
  border: none !important;
  font-weight: 600;
  transition: all 0.3s ease;
}

:deep(.nav-link:hover) {
  color: #00ff41 !important;
  text-shadow: 0 0 8px rgba(0, 255, 65, 0.4);
  border: none !important;
}

:deep(.nav-link.active) {
  color: #00ff41 !important;
  border-bottom: 2px solid #00ff41 !important;
  background: transparent !important;
  text-shadow: 0 0 8px rgba(0, 255, 65, 0.5);
}
</style>