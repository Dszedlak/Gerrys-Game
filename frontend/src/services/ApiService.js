import axios from 'axios'
import Vue from 'vue';
import VueAxios from 'vue-axios'
import JwtService from '@/services/JwtService'
import { API_URL } from "@/common/config";

class ApiService {
	init() {
		Vue.use(VueAxios, axios);
		Vue.axios.defaults.baseURL = API_URL;
	}

	setHeader() {
		Vue.axios.defaults.headers.common[
			"Authorization"
		] = `Bearer ${JwtService.getToken()}`;
	}

	get(resource) {
		return Vue.axios.get(`${resource}`);
	}

	post(resource, params) {
		return Vue.axios.post(`${resource}`, params);
	}

	put(resource, params) {
		return Vue.axios.put(`${resource}`, params);
	}

	delete(resource) {
		return Vue.axios.delete(`${resource}`);
	}
}

export default new ApiService();