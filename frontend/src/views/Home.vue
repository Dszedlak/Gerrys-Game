<template>
  <div class="leaderboard-page">
    <div class="leaderboard-container">
      <div class="leaderboard-header">
        <h1>Leaderboard</h1>
        <div class="leaderboard-tabs">
          <button 
            class="tab-btn" 
            :class="{ active: !showFriends }"
            @click="showFriends = false"
          >
            All Players
          </button>
          <button 
            class="tab-btn" 
            :class="{ active: showFriends }"
            @click="showFriends = true"
          >
            Friends
          </button>
        </div>
      </div>

      <!-- Top 3 Podium -->
      <div class="podium" v-if="sortedUsers.length >= 3">
        <div class="podium-place second">
          <div class="podium-avatar">
            <img 
              :src="sortedUsers[1]?.profilePic || 'https://ui-avatars.com/api/?name=' + sortedUsers[1]?.username" 
              @error="handleImageError"
            />
          </div>
          <div class="podium-rank">2</div>
          <div class="podium-name">{{ sortedUsers[1]?.username }}</div>
          <div class="podium-score">{{ sortedUsers[1]?.score }} pts</div>
          <div class="podium-bar"></div>
        </div>
        <div class="podium-place first">
          <div class="podium-crown">👑</div>
          <div class="podium-avatar gold">
            <img 
              :src="sortedUsers[0]?.profilePic || 'https://ui-avatars.com/api/?name=' + sortedUsers[0]?.username" 
              @error="handleImageError"
            />
          </div>
          <div class="podium-rank">1</div>
          <div class="podium-name">{{ sortedUsers[0]?.username }}</div>
          <div class="podium-score">{{ sortedUsers[0]?.score }} pts</div>
          <div class="podium-bar"></div>
        </div>
        <div class="podium-place third">
          <div class="podium-avatar">
            <img 
              :src="sortedUsers[2]?.profilePic || 'https://ui-avatars.com/api/?name=' + sortedUsers[2]?.username" 
              @error="handleImageError"
            />
          </div>
          <div class="podium-rank">3</div>
          <div class="podium-name">{{ sortedUsers[2]?.username }}</div>
          <div class="podium-score">{{ sortedUsers[2]?.score }} pts</div>
          <div class="podium-bar"></div>
        </div>
      </div>

      <!-- Rest of leaderboard -->
      <div class="leaderboard-list">
        <div 
          v-for="(user, index) in restOfUsers" 
          :key="user.username" 
          class="leaderboard-row"
        >
          <div class="row-rank">#{{ index + 4 }}</div>
          <div class="row-avatar">
            <img 
              :src="user.profilePic || 'https://ui-avatars.com/api/?name=' + user.username" 
              @error="handleImageError"
            />
          </div>
          <div class="row-name">{{ user.username }}</div>
          <div class="row-score">{{ user.score }} pts</div>
        </div>
        <div v-if="sortedUsers.length === 0" class="empty-state">
          <div class="empty-icon">🏆</div>
          <p>No players yet. Be the first!</p>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import LeaderboardService from '@/services/LeaderboardService';

export default {
  data() {
    return {
      users: [],
      friendsUsers: [],
      showFriends: false,
    };
  },
  methods: {
    retrieveLeaderboard() {
      LeaderboardService.getLeaderboard()
        .then(response => {
            this.users = response.data;
            console.log("leaderboard:", JSON.stringify(response.data));
        })
        .catch(e => {
          console.error("Error fetching leaderboard:", e);
        });
    },
    retrieveFriendsLeaderboard() {
      LeaderboardService.getFriendsLeaderboard()
        .then(response => {
            this.friendsUsers = response.data;
            console.log("friends leaderboard:", JSON.stringify(response.data));
        })
        .catch(e => {
          console.error("Error fetching friends leaderboard:", e);
        });
    },
    handleImageError(event) {
      event.target.src = 'https://ui-avatars.com/api/?name=User';
    }
  },
  computed: {
    sortedUsers() {
      const dataSource = this.showFriends ? this.friendsUsers : this.users;
      return dataSource.slice().sort((a, b) => b.score - a.score);
    },
    restOfUsers() {
      return this.sortedUsers.slice(3);
    }
  },
  watch: {
    showFriends(newVal) {
      if (newVal && this.friendsUsers.length === 0) {
        this.retrieveFriendsLeaderboard();
      }
    }
  },
  mounted() {
    this.retrieveLeaderboard();
  },
};
</script>
<style scoped>
.leaderboard-page {
  background: #0B0F19;
  min-height: 100vh;
  padding: 40px 20px;
}

.leaderboard-container {
  max-width: 800px;
  margin: 0 auto;
}

.leaderboard-header {
  text-align: center;
  margin-bottom: 40px;
}

.leaderboard-header h1 {
  font-size: 2.5em;
  font-weight: 700;
  color: #EAB308;
  margin: 0 0 24px 0;
}

.leaderboard-tabs {
  display: flex;
  justify-content: center;
  gap: 8px;
  background: #1A1F2E;
  padding: 6px;
  border-radius: 12px;
  display: inline-flex;
}

.tab-btn {
  padding: 12px 28px;
  background: transparent;
  border: none;
  color: #64748B;
  font-weight: 600;
  font-size: 0.95em;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-btn:hover {
  color: #F1F5F9;
}

.tab-btn.active {
  background: linear-gradient(135deg, #EAB308 0%, #CA8A04 100%);
  color: #0B0F19;
}

/* Podium Section */
.podium {
  display: flex;
  justify-content: center;
  align-items: flex-end;
  gap: 16px;
  margin-bottom: 32px;
  padding: 20px 0;
}

.podium-place {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}

.podium-crown {
  font-size: 2em;
  margin-bottom: 8px;
  animation: bounce 2s ease-in-out infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

.podium-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  overflow: hidden;
  border: 3px solid #64748B;
  margin-bottom: 12px;
  transition: transform 0.3s ease;
}

.podium-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.first .podium-avatar {
  width: 100px;
  height: 100px;
  border-color: #EAB308;
  box-shadow: 0 0 30px rgba(234, 179, 8, 0.4);
}

.second .podium-avatar {
  border-color: #94A3B8;
}

.third .podium-avatar {
  border-color: #CD7F32;
}

.podium-rank {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.9em;
  margin-bottom: 8px;
}

.first .podium-rank {
  background: linear-gradient(135deg, #EAB308 0%, #CA8A04 100%);
  color: #0B0F19;
}

.second .podium-rank {
  background: linear-gradient(135deg, #94A3B8 0%, #64748B 100%);
  color: #0B0F19;
}

.third .podium-rank {
  background: linear-gradient(135deg, #CD7F32 0%, #A0522D 100%);
  color: #FFF;
}

.podium-name {
  font-weight: 600;
  color: #F1F5F9;
  font-size: 1em;
  margin-bottom: 4px;
  max-width: 100px;
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
}

.podium-score {
  font-size: 0.85em;
  color: #22D3EE;
  font-weight: 500;
  margin-bottom: 12px;
}

.podium-bar {
  width: 100%;
  border-radius: 8px 8px 0 0;
}

.first .podium-bar {
  height: 120px;
  background: linear-gradient(180deg, #EAB308 0%, #CA8A04 100%);
  width: 110px;
}

.second .podium-bar {
  height: 90px;
  background: linear-gradient(180deg, #94A3B8 0%, #64748B 100%);
  width: 100px;
}

.third .podium-bar {
  height: 70px;
  background: linear-gradient(180deg, #CD7F32 0%, #A0522D 100%);
  width: 100px;
}

/* Leaderboard List */
.leaderboard-list {
  background: #1A1F2E;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid #22D3EE33;
}

.leaderboard-row {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #22D3EE11;
  transition: background 0.2s ease;
}

.leaderboard-row:last-child {
  border-bottom: none;
}

.leaderboard-row:hover {
  background: #22D3EE0A;
}

.row-rank {
  width: 50px;
  font-weight: 700;
  color: #64748B;
  font-size: 1em;
}

.row-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  overflow: hidden;
  margin-right: 16px;
  border: 2px solid #22D3EE44;
}

.row-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.row-name {
  flex-grow: 1;
  font-weight: 600;
  color: #F1F5F9;
  font-size: 1em;
}

.row-score {
  font-weight: 700;
  color: #22D3EE;
  font-size: 1em;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 3em;
  margin-bottom: 16px;
}

.empty-state p {
  color: #64748B;
  font-size: 1.1em;
  margin: 0;
}

/* Responsive */
@media (max-width: 600px) {
  .podium {
    gap: 8px;
  }
  
  .first .podium-avatar {
    width: 70px;
    height: 70px;
  }
  
  .podium-avatar {
    width: 55px;
    height: 55px;
  }
  
  .first .podium-bar {
    width: 80px;
    height: 80px;
  }
  
  .second .podium-bar,
  .third .podium-bar {
    width: 70px;
  }
  
  .podium-name {
    font-size: 0.85em;
    max-width: 70px;
  }
}
</style>













