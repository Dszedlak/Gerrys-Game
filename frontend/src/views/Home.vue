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
  background: #0a0e27;
  min-height: 100vh;
  padding: 40px 20px;
  margin: -8px -8px 0 -8px;
}

h2 {
  color: #00ff41;
  font-weight: 700;
  text-align: center;
  margin-bottom: 30px;
  font-size: 2em;
  text-shadow: 0 0 15px rgba(0, 255, 65, 0.5);
}

/* Style the leaderboard table */
.leaderboard-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
  background: #0f1535;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 0 20px rgba(0, 255, 65, 0.2), inset 0 0 15px rgba(0, 255, 65, 0.05);
  border: 1px solid rgba(0, 255, 65, 0.2);
}

.leaderboard-table thead {
  background: #0a0e27;
  color: #00ff41;
  border-bottom: 2px solid rgba(0, 255, 65, 0.3);
}

.leaderboard-table th {
  padding: 15px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border: none;
  color: #00ff41;
  text-shadow: 0 0 8px rgba(0, 255, 65, 0.3);
}

.leaderboard-table td {
  padding: 15px;
  text-align: center;
  border: 1px solid rgba(0, 255, 65, 0.1);
  color: #00ff41;
}

.leaderboard-table tbody tr {
  transition: background-color 0.2s ease;
}

.leaderboard-table tbody tr:hover {
  background-color: rgba(0, 255, 65, 0.05);
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
  border: 3px solid #00ff41;
  box-shadow: 0 0 15px rgba(0, 255, 65, 0.4);
  transition: transform 0.2s ease;
}

.leaderboard-table tbody tr:hover .profile-pic {
  transform: scale(1.1);
}
</style>