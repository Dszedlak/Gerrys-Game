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
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
  padding: 40px 20px;
  margin: -8px -8px 0 -8px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.profile-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  padding: 40px;
  max-width: 600px;
  width: 100%;
}

h1 {
  color: #333;
  font-weight: 700;
  margin-bottom: 30px;
  text-align: center;
  font-size: 2.5em;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.profile-content {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.placeholder-text {
  color: #999;
  text-align: center;
  font-style: italic;
  margin: 0;
}
</style>