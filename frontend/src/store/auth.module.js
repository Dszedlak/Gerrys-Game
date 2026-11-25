import ApiService from '@/services/ApiService'
import JwtService from '@/services/JwtService'
import AuthenticationService from '@/services/AuthenticationService'

const state = {
  token: localStorage.getItem('token') || '',
  username: localStorage.getItem('username') || '',
  errors: null,
  roomId: null, 
  userId: null,
  // Set when a saved sign-in turned out to be expired, for the login page
  sessionExpired: false
}

const getters = {
  currentUser(state) {
    return state.username;
  },
  isAuthenticated (state) {
    return !!state.token;
  },
  roomId (state) {
  return state.roomId;
  }
};

const actions = {
  login(context, credentials)  {
    return new Promise((resolve, reject) => {
      AuthenticationService.login(credentials)
        .then(({ data }) => {
          // Expecting { success, token, username }
          if (data && data.success && data.token && data.username) {
            context.commit('setUser', {
              username: data.username, 
              token: data.token
            });
            resolve(data);
          } else {
            context.commit("setError", "Invalid response from server");
            reject("Invalid response from server");
          }
        })
        .catch((error) => {
          // error.response may not exist
          const response = error.response || {};
          const errMsg = (response.data && (response.data.errors || response.data.message)) || "Login failed";
          context.commit("setError", errMsg);
          reject(errMsg);
        });
    });
  },
  logout(context) {
    context.commit("purgeAuth");
  },
  register(context, credentials) {
    return new Promise((resolve, reject) => {
      AuthenticationService.register(credentials)
      .then(({ data }) => {
        console.log('[Register] Response data:', data)
        // Check if backend returned token and username (like login does)
        if (data && data.token) {
          context.commit('setUser', {
            username: data.username || credentials.username,
            token: data.token
          });
          resolve(data);
        } else {
          // If no token returned, registration succeeded but need to login
          console.log('[Register] No token in response, registration succeeded but not logged in')
          context.commit("setError", "Registration succeeded, please login");
          reject("Registration succeeded, please login");
        }
      })
      .catch((error) => {
        console.error('[Register] Error:', error)
        const response = error.response || {};
        const errMsg = (response.data && (response.data.errors || response.data.message)) || "Registration failed";
        context.commit('setError', errMsg);
        reject(error);
      });
    });
  },
  /**
   * Check the saved sign-in with the server (on page load). Resolves true if
   * it's still good. If the server rejects it (expired, or the account is
   * gone) the stale sign-in is cleared and this resolves false. A network
   * error leaves it alone - the server may just be starting up.
   */
  async checkAuth(context) {
    const token = context.state.token || localStorage.getItem('token')
    if (!token) {
      context.commit('purgeAuth')
      return false
    }
    ApiService.setHeader(token)
    try {
      const { data } = await AuthenticationService.verifyToken()
      context.commit('setUser', { username: data.username, token })
      return true
    } catch (error) {
      const status = error?.response?.status
      if (status === 401 || status === 422 || status === 404) {
        context.commit('expireSession')
        return false
      }
      return true
    }
  }
};

const mutations = {
  setError(state, error) {
    state.errors = error;
  },
  setUser(state, { username, token }) {
    state.sessionExpired = false;
    state.isAuthenticated = true;
    state.username = username;
    state.token = token;
    state.errors = "";
    localStorage.setItem('token', token);
    localStorage.setItem('username', username);
    JwtService.saveToken(token);
    ApiService.setHeader(token); // Set the token in ApiService
  },
  purgeAuth(state) {
    state.isAuthenticated = false;
    state.username = null;
    state.token = '';
    state.errors = "";
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    JwtService.destroyToken();
    ApiService.setHeader('');
  },
  // The server no longer accepts our sign-in: clear it and say why on the login page
  expireSession(state) {
    state.isAuthenticated = false;
    state.username = null;
    state.token = '';
    state.roomId = null;
    state.errors = "";
    state.sessionExpired = true;
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    JwtService.destroyToken();
    ApiService.setHeader('');
  },
  clearSessionExpired(state) {
    state.sessionExpired = false;
  },
  setRoomId(state, {id}) {
    state.roomId = id;
  },
  leaveRoomId(state)
  {
    state.roomId = null;
  },
  setUserId(state, id) {
    state.userId = id;
  },
  setToken(state, token) {
    state.token = token;
  },
  setUsername(state, username) {
    state.username = username;
    localStorage.setItem('username', username);
  },
  logout(state) {
    state.token = '';
    state.username = '';
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    ApiService.setHeader(''); // Remove token from axios
  },
  setErrors(state, errors) {
    state.errors = errors;
  }
};

export default {
  namespaced: true,
  state,
  mutations,
  getters,
  actions
}
