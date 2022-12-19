import ApiService from '@/services/ApiService'
import JwtService from '@/services/JwtService'
import AuthenticationService from '@/services/AuthenticationService'

const state = {
  errors: null,
  username: null,
  isAuthenticated: !!JwtService.getToken(), 
  roomId: null
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
    state.errors = "";
    JwtService.saveToken(token);
  },
  purgeAuth(state) {
    state.isAuthenticated = false;
    state.username = null;
    state.errors = "";
    JwtService.destroyToken();
  },
  setRoomId(state, {id}) {
    state.roomId = id;
  },
  leaveRoomId(state)
  {
    state.roomId = null;
  }
};

export default {
  state,
  mutations,
  getters,
  actions
}
