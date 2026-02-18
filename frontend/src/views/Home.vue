<template>
    <div>
      <h2>Leaderboard</h2>
      <table class="leaderboard-table">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Profile Picture</th>
            <th>Username</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(user, index) in sortedUsers" :key="user.username">
            <td>{{ index + 1 }}</td>
            <td>
              <img :src="user.profilePic" alt="Profile Pic" class="profile-pic">
            </td>
            <td>{{ user.username }}</td>
            <td>{{ user.score }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </template>
<script>
import LeaderboardService from '@/services/LeaderboardService';

export default {
  data() {
    return {
      users: [], // Initialize it as an empty array
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
          console.log(e);
        });
    },
  },
  computed: {
    // Create a computed property to sort users by score
    sortedUsers() {
      return this.users.slice().sort((a, b) => b.score - a.score);
    },
  },
  mounted() {
    this.retrieveLeaderboard();
  },
};
</script>
<style scoped>
/* Container styling */
div {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
  padding: 40px 20px;
  margin: -8px -8px 0 -8px;
}

h2 {
  color: #333;
  font-weight: 700;
  text-align: center;
  margin-bottom: 30px;
  font-size: 2em;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Style the leaderboard table */
.leaderboard-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  border: none;
}

.leaderboard-table thead {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.leaderboard-table th {
  padding: 15px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border: none;
}

.leaderboard-table td {
  padding: 15px;
  text-align: center;
  border: 1px solid #e8e8e8;
}

.leaderboard-table tbody tr {
  transition: background-color 0.2s ease;
}

.leaderboard-table tbody tr:hover {
  background-color: #f8f9fa;
}

.leaderboard-table tbody tr:last-child td {
  border-bottom: none;
}

/* Rank styling - add medal emojis for top 3 */
.leaderboard-table tbody tr:nth-child(1) td:first-child::before {
  content: '🥇 ';
}

.leaderboard-table tbody tr:nth-child(2) td:first-child::before {
  content: '🥈 ';
}

.leaderboard-table tbody tr:nth-child(3) td:first-child::before {
  content: '🥉 ';
}

/* Style the profile picture */
.profile-pic {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
  transition: transform 0.2s ease;
}

.leaderboard-table tbody tr:hover .profile-pic {
  transform: scale(1.1);
}
</style>