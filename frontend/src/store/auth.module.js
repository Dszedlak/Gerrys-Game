import ApiService from '@/services/ApiService'
import JwtService from '@/services/JwtService'
import AuthenticationService from '@/services/AuthenticationService'

const state = {
  token: localStorage.getItem('token') || '',
  username: localStorage.getItem('username') || '',
  errors: null,
  roomId: null, 
  userId: null
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
        ApiService.setHeader(data.token) // <-- add this line
        context.commit('setUser', {
          username: data.username,
          token: data.token
        });
        resolve(data);
      })
      .catch(({ response }) => {
        context.commit('setErrors', response.data.message);
        reject(response);
      });
    });
  },
  checkAuth(context) {
    if(JwtService.getToken()) {
      ApiService.setHeader();
      AuthenticationService.verifyToken()
      .then(({ data }) => {
        context.commit("setUser", {
          username: data.username, 
          token: JwtService.getToken()
        });
      })
      .catch(({ response }) => {
        context.commit("setError", response.data.errors);
      });
    }
    else {
      context.commit("purgeAuth");
    }
  }
};

const mutations = {
  setError(state, error) {
    state.errors = error;
  },
  setUser(state, { username, token }) {
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
