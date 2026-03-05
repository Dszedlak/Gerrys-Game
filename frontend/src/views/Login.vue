<template>
  <div class="auth-page">
    <div class="auth-container">
      <!-- Logo/Branding -->
      <div class="auth-header">
        <div class="auth-logo">🎲</div>
        <h1 class="auth-title">Gerry's Game</h1>
      </div>
      
      <!-- Auth Card -->
      <div class="auth-card">
        <!-- Tab Buttons -->
        <div class="auth-tabs">
          <button 
            class="auth-tab" 
            :class="{ active: activeTab === 'login' }"
            @click="activeTab = 'login'"
          >
            Sign In
          </button>
          <button 
            class="auth-tab" 
            :class="{ active: activeTab === 'register' }"
            @click="activeTab = 'register'"
          >
            Create Account
          </button>
        </div>
        
        <!-- Form Content -->
        <div class="auth-form-container">
          <LoginForm v-if="activeTab === 'login'" />
          <RegisterForm v-else />
        </div>
      </div>
      
      <!-- Footer -->
      <p class="auth-footer">
        I am going to fucking kill myself if I have to write one more line of css.
      </p>
    </div>
  </div>
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
      activeTab: 'login'
    }
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0B0F19 0%, #1A1F2E 50%, #0B0F19 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  position: relative;
  overflow: hidden;
}

/* Decorative background elements */
.auth-page::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle at 30% 20%, rgba(234, 179, 8, 0.05) 0%, transparent 50%),
              radial-gradient(circle at 70% 80%, rgba(34, 211, 238, 0.05) 0%, transparent 50%);
  animation: float 20s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  50% { transform: translate(-2%, -2%) rotate(1deg); }
}

.auth-container {
  width: 100%;
  max-width: 440px;
  position: relative;
  z-index: 1;
}

/* Header/Branding */
.auth-header {
  text-align: center;
  margin-bottom: 32px;
}

.auth-logo {
  font-size: 4rem;
  margin-bottom: 16px;
  filter: drop-shadow(0 0 20px rgba(234, 179, 8, 0.4));
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.auth-title {
  font-size: 2.5rem;
  font-weight: 800;
  background: linear-gradient(135deg, #EAB308 0%, #FCD34D 50%, #EAB308 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 8px 0;
  letter-spacing: -0.5px;
}

.auth-subtitle {
  color: #64748B;
  font-size: 1rem;
  margin: 0;
}

/* Auth Card */
.auth-card {
  background: #1A1F2E;
  border-radius: 20px;
  border: 1px solid #22D3EE33;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4),
              0 0 40px rgba(34, 211, 238, 0.1);
}

/* Tab Buttons */
.auth-tabs {
  display: flex;
  background: #0B0F19;
  border-bottom: 1px solid #22D3EE22;
}

.auth-tab {
  flex: 1;
  padding: 18px 24px;
  background: none;
  border: none;
  color: #64748B;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.auth-tab::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 3px;
  background: linear-gradient(90deg, #EAB308, #22D3EE);
  border-radius: 3px 3px 0 0;
  transition: width 0.3s ease;
}

.auth-tab:hover {
  color: #F1F5F9;
}

.auth-tab.active {
  color: #EAB308;
}

.auth-tab.active::after {
  width: 60%;
}

/* Form Container */
.auth-form-container {
  padding: 32px;
}

/* Footer */
.auth-footer {
  text-align: center;
  color: #475569;
  font-size: 0.85rem;
  margin-top: 24px;
}
</style>









