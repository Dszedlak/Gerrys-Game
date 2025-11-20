import axios from "axios";
import { API_URL } from "@/common/config";

const ApiService = {
  init() {
    // Set the base URL for axios
    axios.defaults.baseURL = API_URL;
    // Set token from localStorage if available
    const token = localStorage.getItem('token');
    if (token) {
      this.setHeader(token);
    }
  },
  setHeader(token) {
    if (token) {
      axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common["Authorization"];
    }
  },
  get(resource) {
  console.debug('[ApiService] GET', axios.defaults.baseURL + '/' + resource)
  return axios.get(resource);
  },
  post(resource, data) {
  console.debug('[ApiService] POST', axios.defaults.baseURL + '/' + resource, data)
  return axios.post(resource, data);
  },
  put(resource, data) {
  console.debug('[ApiService] PUT', axios.defaults.baseURL + '/' + resource, data)
  return axios.put(resource, data);
  },
  delete(resource) {
  console.debug('[ApiService] DELETE', axios.defaults.baseURL + '/' + resource)
  return axios.delete(resource);
  }
};

export default ApiService;