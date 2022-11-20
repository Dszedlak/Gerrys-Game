import ApiService from "./ApiService"

class AuthenticationService {
  verifyToken() {
    return ApiService.get("auth/verify-token");
  }

  register(data) {
    return ApiService.post("auth/register", data);
  }

  login(data) {
    return ApiService.post("auth/login", data);
  }
};

export default new AuthenticationService();