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
/* Add your component-specific styles here */

/* Style the leaderboard table */
.leaderboard-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

.leaderboard-table th, .leaderboard-table td {
  padding: 10px;
  text-align: center;
  border: 1px solid #ccc;
}

/* Style the profile picture */
.profile-pic {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  object-fit: cover;
}
</style>