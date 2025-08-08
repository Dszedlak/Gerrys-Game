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
    return this.isAuthenticated;
  },
  roomId (state) {
    return this.roomId;
  }
};

const actions = {
  login(context, credentials)  {
    return new Promise(resolve => {
      AuthenticationService.login(credentials)
      .then(({ data }) => {
        context.commit('setUser', {
          username: credentials.username, 
          token: data.token
        });
        resolve(data);
      })
      .catch(({ response }) => {
        context.commit("setError", response.data.errors);
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
        context.commit('setUser', {
          username: credentials.username, 
          token: data.token
        });
        resolve(data);
      })
      .catch(({ response }) => {
        context.commit("setError", response.data.errors);
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
