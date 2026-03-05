<template>
  <div class="profile-page">
    <div class="profile-container">
      <div class="profile-card">
        <!-- Profile Header -->
        <div class="profile-header">
          <div class="avatar-section">
            <div class="avatar-wrapper">
              <img 
                :src="profilePic || defaultAvatar" 
                alt="Profile Picture"
                class="avatar-image"
                @error="handleImageError"
              />
              <button class="avatar-edit-btn" @click="showImageUrlModal = true" title="Change picture">
                📷
              </button>
            </div>
          </div>
          <div class="profile-info">
            <div class="username-row" v-if="!isEditingUsername">
              <h1 class="username">{{ username }}</h1>
              <button class="edit-btn" @click="startEditUsername" title="Edit username">✏️</button>
            </div>
            <div class="username-edit-row" v-else>
              <input 
                v-model="newUsername" 
                type="text" 
                class="username-input"
                placeholder="Enter new username"
                @keyup.enter="saveUsername"
                @keyup.escape="cancelEditUsername"
                ref="usernameInput"
              />
              <button class="save-btn" @click="saveUsername" :disabled="isSaving">✓</button>
              <button class="cancel-btn" @click="cancelEditUsername">✕</button>
            </div>
            <div class="stats">
              <div class="stat-item">
                <span class="stat-value">{{ score }}</span>
                <span class="stat-label">Total Score</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Messages -->
        <div v-if="successMessage" class="message success-message">
          {{ successMessage }}
        </div>
        <div v-if="errorMessage" class="message error-message">
          {{ errorMessage }}
        </div>

        <!-- Profile Actions -->
        <div class="profile-actions">
          <button class="action-btn primary" @click="$router.push({ name: 'Rooms' })">
            🎮 Play Game
          </button>
          <button class="action-btn secondary" @click="$router.push({ name: 'Home' })">
            🏆 Leaderboard
          </button>
        </div>
      </div>
    </div>

    <!-- Image URL Modal -->
    <div v-if="showImageUrlModal" class="modal-overlay" @click.self="closeImageModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Change Profile Picture</h3>
          <button class="modal-close" @click="closeImageModal">×</button>
        </div>
        <div class="modal-body">
          <!-- Tab Buttons -->
          <div class="upload-tabs">
            <button 
              class="upload-tab" 
              :class="{ active: uploadMode === 'file' }"
              @click="uploadMode = 'file'"
            >
              📁 Upload File
            </button>
            <button 
              class="upload-tab" 
              :class="{ active: uploadMode === 'url' }"
              @click="uploadMode = 'url'"
            >
              🔗 Image URL
            </button>
          </div>

          <!-- File Upload Tab -->
          <div v-if="uploadMode === 'file'" class="upload-section">
            <div class="preview-section" v-if="filePreview">
              <img :src="filePreview" class="preview-image" />
            </div>
            <div class="file-input-wrapper">
              <input 
                type="file" 
                ref="fileInput"
                accept=".png,.jpg,.jpeg,image/png,image/jpeg"
                @change="handleFileSelect"
                class="file-input-hidden"
              />
              <button class="file-select-btn" @click="$refs.fileInput.click()">
                {{ selectedFile ? 'Change File' : 'Choose Image' }}
              </button>
              <span class="file-name" v-if="selectedFile">{{ selectedFile.name }}</span>
            </div>
            <small class="form-hint">PNG or JPEG only, max 5MB</small>
            <p v-if="fileError" class="file-error">{{ fileError }}</p>
          </div>

          <!-- URL Tab -->
          <div v-else class="url-section">
            <div class="preview-section" v-if="newProfilePicUrl">
              <img 
                :src="newProfilePicUrl" 
                class="preview-image"
                @error="previewError = true"
              />
              <p v-if="previewError" class="preview-error">Unable to load image</p>
            </div>
            <div class="form-group">
              <label>Image URL</label>
              <input 
                v-model="newProfilePicUrl" 
                type="url" 
                class="form-input"
                placeholder="https://example.com/image.jpg"
                @input="previewError = false"
              />
              <small class="form-hint">Enter a direct link to an image (JPG, PNG)</small>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeImageModal">Cancel</button>
          <button 
            v-if="uploadMode === 'file'"
            class="btn-save" 
            @click="uploadFile" 
            :disabled="isSaving || !selectedFile || fileError"
          >
            {{ isSaving ? 'Uploading...' : 'Upload' }}
          </button>
          <button 
            v-else
            class="btn-save" 
            @click="saveProfilePic" 
            :disabled="isSaving || !newProfilePicUrl || previewError"
          >
            {{ isSaving ? 'Saving...' : 'Save' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import ApiService from '@/services/ApiService';

export default {
  name: 'ProfileView',
  data() {
    return {
      username: '',
      score: 0,
      profilePic: '',
      newUsername: '',
      newProfilePicUrl: '',
      isEditingUsername: false,
      showImageUrlModal: false,
      isSaving: false,
      successMessage: '',
      errorMessage: '',
      previewError: false,
      defaultAvatar: 'https://ui-avatars.com/api/?name=User&background=1A1F2E&color=EAB308',
      // File upload
      uploadMode: 'file',
      selectedFile: null,
      filePreview: null,
      fileError: ''
    }
  },
  methods: {
    async fetchProfile() {
      try {
        const response = await ApiService.get('auth/me');
        const data = response.data;
        this.username = data.username;
        this.score = data.score;
        this.profilePic = data.profilePic;
      } catch (e) {
        console.error('Failed to fetch profile:', e);
        this.errorMessage = 'Failed to load profile';
      }
    },
    startEditUsername() {
      this.newUsername = this.username;
      this.isEditingUsername = true;
      this.$nextTick(() => {
        this.$refs.usernameInput?.focus();
      });
    },
    cancelEditUsername() {
      this.isEditingUsername = false;
      this.newUsername = '';
    },
    async saveUsername() {
      if (!this.newUsername.trim() || this.newUsername === this.username) {
        this.cancelEditUsername();
        return;
      }
      
      this.isSaving = true;
      this.clearMessages();
      
      try {
        const response = await ApiService.put('auth/profile', { 
          username: this.newUsername.trim() 
        });
        this.username = response.data.username;
        this.$store.commit('auth/setUsername', response.data.username);
        this.isEditingUsername = false;
        this.showSuccess('Username updated successfully!');
      } catch (e) {
        this.errorMessage = e.response?.data?.errors || 'Failed to update username';
      } finally {
        this.isSaving = false;
      }
    },
    async saveProfilePic() {
      if (!this.newProfilePicUrl.trim()) return;
      
      this.isSaving = true;
      this.clearMessages();
      
      try {
        const response = await ApiService.put('auth/profile', { 
          profilePic: this.newProfilePicUrl.trim() 
        });
        this.profilePic = response.data.profilePic;
        this.showImageUrlModal = false;
        this.newProfilePicUrl = '';
        this.showSuccess('Profile picture updated!');
      } catch (e) {
        this.errorMessage = e.response?.data?.errors || 'Failed to update profile picture';
      } finally {
        this.isSaving = false;
      }
    },
    handleImageError(event) {
      event.target.src = this.defaultAvatar;
    },
    showSuccess(message) {
      this.successMessage = message;
      setTimeout(() => {
        this.successMessage = '';
      }, 3000);
    },
    clearMessages() {
      this.successMessage = '';
      this.errorMessage = '';
    },
    handleFileSelect(event) {
      const file = event.target.files[0];
      this.fileError = '';
      this.filePreview = null;
      this.selectedFile = null;
      
      if (!file) return;
      
      // Validate file type
      const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg'];
      if (!allowedTypes.includes(file.type)) {
        this.fileError = 'Only PNG and JPEG files are allowed';
        return;
      }
      
      // Validate file size (5MB max)
      if (file.size > 5 * 1024 * 1024) {
        this.fileError = 'File size must be less than 5MB';
        return;
      }
      
      this.selectedFile = file;
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        this.filePreview = e.target.result;
      };
      reader.readAsDataURL(file);
    },
    async uploadFile() {
      if (!this.selectedFile) return;
      
      this.isSaving = true;
      this.clearMessages();
      
      try {
        const formData = new FormData();
        formData.append('file', this.selectedFile);
        
        const response = await ApiService.post('auth/upload-avatar', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        
        this.profilePic = response.data.profilePic;
        this.closeImageModal();
        this.showSuccess('Profile picture uploaded!');
      } catch (e) {
        this.errorMessage = e.response?.data?.errors || 'Failed to upload image';
      } finally {
        this.isSaving = false;
      }
    },
    closeImageModal() {
      this.showImageUrlModal = false;
      this.selectedFile = null;
      this.filePreview = null;
      this.fileError = '';
      this.newProfilePicUrl = '';
      this.previewError = false;
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = '';
      }
    }
  },
  mounted() {
    this.fetchProfile();
  }
}
</script>

<style scoped>
.profile-page {
  background: #0B0F19;
  min-height: 100vh;
  padding: 40px 20px;
}

.profile-container {
  max-width: 600px;
  margin: 0 auto;
}

.profile-card {
  background: #1A1F2E;
  border-radius: 20px;
  padding: 40px;
  border: 1px solid #22D3EE33;
}

/* Profile Header */
.profile-header {
  display: flex;
  gap: 30px;
  align-items: flex-start;
  margin-bottom: 30px;
}

.avatar-section {
  flex-shrink: 0;
}

.avatar-wrapper {
  position: relative;
  width: 120px;
  height: 120px;
}

.avatar-image {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  border: 4px solid #EAB308;
  box-shadow: 0 0 30px rgba(234, 179, 8, 0.3);
}

.avatar-edit-btn {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #EAB308;
  border: 3px solid #1A1F2E;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1em;
  transition: transform 0.2s;
}

.avatar-edit-btn:hover {
  transform: scale(1.1);
}

.profile-info {
  flex-grow: 1;
}

.username-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.username {
  font-size: 2em;
  font-weight: 700;
  color: #F1F5F9;
  margin: 0;
}

.edit-btn {
  background: none;
  border: none;
  font-size: 1em;
  cursor: pointer;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.edit-btn:hover {
  opacity: 1;
}

.username-edit-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.username-input {
  flex-grow: 1;
  padding: 12px 16px;
  background: #0B0F19;
  border: 2px solid #EAB308;
  border-radius: 10px;
  color: #F1F5F9;
  font-size: 1.2em;
  font-weight: 600;
}

.username-input:focus {
  outline: none;
}

.save-btn,
.cancel-btn {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-size: 1.2em;
  transition: transform 0.2s;
}

.save-btn {
  background: #22C55E;
  color: white;
}

.cancel-btn {
  background: #EF4444;
  color: white;
}

.save-btn:hover,
.cancel-btn:hover {
  transform: scale(1.05);
}

.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Stats */
.stats {
  display: flex;
  gap: 24px;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 1.8em;
  font-weight: 700;
  color: #22D3EE;
}

.stat-label {
  font-size: 0.85em;
  color: #64748B;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Messages */
.message {
  padding: 12px 16px;
  border-radius: 10px;
  margin-bottom: 20px;
  font-weight: 500;
}

.success-message {
  background: #22C55E22;
  color: #22C55E;
  border: 1px solid #22C55E44;
}

.error-message {
  background: #EF444422;
  color: #EF4444;
  border: 1px solid #EF444444;
}

/* Profile Actions */
.profile-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.action-btn {
  flex: 1;
  padding: 16px 24px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 1em;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.action-btn.primary {
  background: linear-gradient(135deg, #EAB308 0%, #CA8A04 100%);
  color: #0B0F19;
}

.action-btn.secondary {
  background: transparent;
  border: 2px solid #22D3EE;
  color: #22D3EE;
}

.action-btn:hover {
  transform: translateY(-2px);
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: #1A1F2E;
  border-radius: 16px;
  width: 100%;
  max-width: 450px;
  border: 1px solid #22D3EE33;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: #0B0F19;
  border-bottom: 1px solid #22D3EE22;
}

.modal-header h3 {
  margin: 0;
  color: #EAB308;
  font-size: 1.3em;
}

.modal-close {
  background: none;
  border: none;
  color: #64748B;
  font-size: 1.8em;
  cursor: pointer;
  line-height: 1;
}

.modal-close:hover {
  color: #F1F5F9;
}

.modal-body {
  padding: 24px;
}

.preview-section {
  text-align: center;
  margin-bottom: 20px;
}

.preview-image {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #EAB308;
}

.preview-error {
  color: #EF4444;
  font-size: 0.85em;
  margin-top: 8px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  color: #94A3B8;
  font-size: 0.9em;
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 14px 16px;
  background: #0B0F19;
  border: 1px solid #22D3EE44;
  border-radius: 10px;
  color: #F1F5F9;
  font-size: 1em;
}

.form-input:focus {
  outline: none;
  border-color: #EAB308;
}

.form-hint {
  display: block;
  margin-top: 6px;
  color: #64748B;
  font-size: 0.8em;
}

.modal-footer {
  display: flex;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid #22D3EE22;
  justify-content: flex-end;
}

.btn-cancel,
.btn-save {
  padding: 12px 24px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background: transparent;
  border: 1px solid #64748B;
  color: #94A3B8;
}

.btn-cancel:hover {
  border-color: #F1F5F9;
  color: #F1F5F9;
}

.btn-save {
  background: linear-gradient(135deg, #EAB308 0%, #CA8A04 100%);
  border: none;
  color: #0B0F19;
}

.btn-save:hover {
  transform: translateY(-2px);
}

.btn-save:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* Responsive */
@media (max-width: 500px) {
  .profile-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  
  .username-row {
    justify-content: center;
  }
  
  .stats {
    justify-content: center;
  }
  
  .profile-actions {
    flex-direction: column;
  }
}

/* Upload Tabs */
.upload-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.upload-tab {
  flex: 1;
  padding: 12px 16px;
  background: #0B0F19;
  border: 1px solid #22D3EE33;
  border-radius: 8px;
  color: #94A3B8;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-tab:hover {
  border-color: #22D3EE66;
  color: #F1F5F9;
}

.upload-tab.active {
  background: #22D3EE22;
  border-color: #22D3EE;
  color: #22D3EE;
}

/* File Upload Section */
.upload-section,
.url-section {
  min-height: 150px;
}

.file-input-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.file-input-hidden {
  display: none;
}

.file-select-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #22D3EE 0%, #0891B2 100%);
  border: none;
  border-radius: 10px;
  color: #0B0F19;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.file-select-btn:hover {
  transform: translateY(-2px);
}

.file-name {
  color: #94A3B8;
  font-size: 0.9em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

.file-error {
  color: #EF4444;
  font-size: 0.85em;
  margin-top: 8px;
  margin-bottom: 0;
}
</style>













