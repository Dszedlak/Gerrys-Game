import ApiService from "./ApiService"

class QuizService {
	getQuizzes() {
		return ApiService.get("quizzes");
	}

	getQuiz(quizId) {
		return ApiService.get(`quiz/${quizId}`);
	}

	createQuiz(data) {
		return ApiService.post("quizzes", data);
	}

	updateQuiz(data, quizId) {
		return ApiService.put(`quiz/${quizId}`, data);
	}

	deleteQuiz(quizId) {
		return ApiService.delete(`quiz/${quizId}`);
	}
}

export default new QuizService();