<template>
    <div class="profile-container">
      <div class="profile-card">
        <h1>User Profile</h1>
        <div class="profile-content">
          <p class="placeholder-text">Your profile information will appear here</p>
        </div>
      </div>
	</div>
</template>

<script>
export default {
  name: 'ProfileView',
}
</script>

<style scoped>
.profile-container {
  background: #0a0e27;
  min-height: 100vh;
  padding: 40px 20px;
  margin: -8px -8px 0 -8px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.profile-card {
  background: #0f1535;
  border-radius: 12px;
  box-shadow: 0 0 20px rgba(0, 255, 65, 0.2), inset 0 0 15px rgba(0, 255, 65, 0.05);
  padding: 40px;
  max-width: 600px;
  width: 100%;
  border: 1px solid rgba(0, 255, 65, 0.2);
}

h1 {
  color: #00ff41;
  font-weight: 700;
  margin-bottom: 30px;
  text-align: center;
  font-size: 2.5em;
  text-shadow: 0 0 15px rgba(0, 255, 65, 0.5);
}

.profile-content {
  padding: 20px;
  background: rgba(0, 255, 65, 0.05);
  border-radius: 8px;
  border-left: 4px solid #00ff41;
}

.placeholder-text {
  color: rgba(0, 255, 65, 0.6);
  text-align: center;
  font-style: italic;
  margin: 0;
}
</style>