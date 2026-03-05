/**
 * Test Fixtures and Game State Builders
 * Use these to create realistic test data for your game
 */

export const gameFixtures = {
  /**
   * Create a mock player
   */
  createPlayer(overrides = {}) {
    return {
      user_id: 1,
      username: 'TestPlayer',
      email: 'test@example.com',
      clock: '100',
      approval_status: null,
      header_vote: null,
      bleed: 0,
      heat: 0,
      is_admin: false,
      job_id: null,
      perk: null,
      is_active: true,
      ...overrides
    };
  },

  /**
   * Create multiple players
   */
  createPlayers(count, overrides = {}) {
    return Array.from({ length: count }, (_, i) => 
      this.createPlayer({
        user_id: i + 1,
        username: `Player${i + 1}`,
        email: `player${i + 1}@example.com`,
        ...overrides
      })
    );
  },

  /**
   * Create a game room
   */
  createRoom(overrides = {}) {
    return {
      id: 1,
      name: 'Test Room',
      code: 'TESTCODE',
      admin_id: 1,
      status: 'in_progress',
      participants: this.createPlayers(3),
      selectedGovernmentId: 1,
      governments: this.getGovernments(),
      jobs: this.getJobs(),
      ...overrides
    };
  },

  /**
   * Create game governments (dictatorships, democracies, etc)
   */
  getGovernments() {
    return [
      {
        id: 1,
        name: 'Democracy',
        icon: '🏛️',
        description: 'Everyone votes'
      },
      {
        id: 2,
        name: 'Dictatorship',
        icon: '👑',
        description: 'One person decides'
      },
      {
        id: 3,
        name: 'Anarchy',
        icon: '🔥',
        description: 'No rules'
      }
    ];
  },

  /**
   * Create available jobs
   */
  getJobs() {
    return [
      { id: 1, name: 'Banker', icon: '🏦' },
      { id: 2, name: 'Farmer', icon: '🚜' },
      { id: 3, name: 'Doctor', icon: '⚕️' },
      { id: 4, name: 'Teacher', icon: '📚' }
    ];
  },

  /**
   * Create a game state with multiple players to test multiplayer scenarios
   */
  createGameScenario(playerCount = 3) {
    const players = this.createPlayers(playerCount);
    return {
      admin: players[0],
      players: players,
      room: this.createRoom({
        admin_id: players[0].user_id,
        participants: players
      })
    };
  },

  /**
   * Create socket events for testing
   */
  createSocketEvent(eventName, data) {
    return {
      event: eventName,
      data: data,
      timestamp: Date.now()
    };
  }
};

// Export individual builders for convenience
export const playerBuilder = {
  aPlayer: () => gameFixtures.createPlayer(),
  withClock: (clock) => gameFixtures.createPlayer({ clock }),
  withApprovalStatus: (status) => gameFixtures.createPlayer({ approval_status: status }),
  withJobId: (jobId) => gameFixtures.createPlayer({ job_id: jobId }),
  withBleed: (amount) => gameFixtures.createPlayer({ bleed: amount }),
  withHeat: (amount) => gameFixtures.createPlayer({ heat: amount }),
  withAdmin: (isAdmin) => gameFixtures.createPlayer({ is_admin: isAdmin }),
};
