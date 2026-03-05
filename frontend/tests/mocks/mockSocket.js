/**
 * Mock WebSocket Service
 * Simulates socket.io-client for testing without a real backend
 * Allows you to manually trigger events for testing multiplayer scenarios
 */
export class MockSocket {
  constructor() {
    this.listeners = {};
    this.emittedEvents = [];
    this.connected = true;
  }

  /**
   * Register event listener
   */
  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  /**
   * Emit event to all listeners
   */
  emit(event, data) {
    this.emittedEvents.push({ event, data, timestamp: Date.now() });
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => {
        callback(data);
      });
    }
  }

  /**
   * Remove a specific listener
   */
  off(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(
        fn => fn !== callback
      );
    }
  }

  /**
   * Remove all listeners for event
   */
  offAll(event) {
    if (event) {
      delete this.listeners[event];
    } else {
      this.listeners = {};
    }
  }

  /**
   * For testing: manually trigger a server event
   * This simulates the server sending an event to the client
   */
  simulateServerEvent(event, data) {
    this.emit(event, data);
  }

  /**
   * For testing: get all events that were emitted
   */
  getEmittedEvents() {
    return this.emittedEvents;
  }

  /**
   * For testing: get events of a specific type
   */
  getEmittedEventsOfType(event) {
    return this.emittedEvents.filter(e => e.event === event);
  }

  /**
   * For testing: clear emitted events history
   */
  clearEmittedEvents() {
    this.emittedEvents = [];
  }

  /**
   * For testing: get current listeners
   */
  getListeners() {
    return this.listeners;
  }

  /**
   * Disconnect the socket
   */
  disconnect() {
    this.connected = false;
    this.emit('disconnect', {});
  }

  /**
   * Reconnect the socket
   */
  connect() {
    this.connected = true;
    this.emit('connect', {});
  }
}

/**
 * Create a real-looking socket instance for testing
 */
export function createMockSocket() {
  return new MockSocket();
}

/**
 * Helper to simulate a multi-player event scenario
 * Usage: simulateMultiplayerEvent(socket, 'updateClock', [player1, player2, player3])
 */
export function simulateMultiplayerUpdate(socket, eventName, updates) {
  updates.forEach(update => {
    socket.simulateServerEvent(eventName, update);
  });
}
