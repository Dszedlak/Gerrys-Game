/**
 * Mock API Service
 * Simulates API calls for testing without a real backend
 */
export class MockApiService {
  constructor() {
    this.responses = {};
    this.requestHistory = [];
  }

  /**
   * Setup a mock response for a specific endpoint
   */
  setResponse(method, endpoint, response, delay = 0) {
    const key = `${method.toUpperCase()}:${endpoint}`;
    this.responses[key] = { response, delay };
  }

  /**
   * Simulate a GET request
   */
  async get(endpoint) {
    return this._request('GET', endpoint);
  }

  /**
   * Simulate a POST request
   */
  async post(endpoint, data) {
    return this._request('POST', endpoint, data);
  }

  /**
   * Simulate a PUT request
   */
  async put(endpoint, data) {
    return this._request('PUT', endpoint, data);
  }

  /**
   * Simulate a DELETE request
   */
  async delete(endpoint) {
    return this._request('DELETE', endpoint);
  }

  async _request(method, endpoint, data = null) {
    const key = `${method}:${endpoint}`;
    this.requestHistory.push({ method, endpoint, data, timestamp: Date.now() });

    if (this.responses[key]) {
      const { response, delay } = this.responses[key];
      if (delay > 0) {
        await new Promise(resolve => setTimeout(resolve, delay));
      }
      return { data: response };
    }

    // Default error if no response configured
    return Promise.reject({
      response: { status: 404, data: { message: 'Not configured' } }
    });
  }

  /**
   * Get request history for assertions
   */
  getRequestHistory() {
    return this.requestHistory;
  }

  /**
   * Clear request history
   */
  clearRequestHistory() {
    this.requestHistory = [];
  }

  /**
   * Check if a specific request was made
   */
  wasRequestMade(method, endpoint) {
    const key = `${method.toUpperCase()}:${endpoint}`;
    return this.requestHistory.some(req => req.method === method.toUpperCase() && req.endpoint === endpoint);
  }
}

export function createMockApiService() {
  return new MockApiService();
}
