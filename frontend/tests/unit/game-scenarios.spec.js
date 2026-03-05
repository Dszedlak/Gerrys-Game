/**
 * Example: Testing Game Scenarios
 * 
 * Test complete game workflows using mocks
 * Shows how to orchestrate multiple events to test game flow
 */

import { describe, it, expect, beforeEach } from '@jest/globals';
import { createMockSocket } from '../mocks/mockSocket';
import { createMockApiService } from '../mocks/mockApiService';
import { gameFixtures } from '../fixtures/gameFixtures';

describe('Game Flow Scenarios', () => {
  let mockSocket;
  let mockApi;
  let gameState;

  beforeEach(() => {
    mockSocket = createMockSocket();
    mockApi = createMockApiService();
    gameState = gameFixtures.createGameScenario(4);
  });

  it('should handle a complete voting scenario', async () => {
    // Arrange - Setup 4 player game
    const players = gameFixtures.createPlayers(4);
    const admin = players[0];
    
    // Setup API responses
    mockApi.setResponse('GET', `/api/rooms/1`, gameFixtures.createRoom({
      admin_id: admin.user_id,
      participants: players
    }));

    // Act - Players vote
    players.forEach((player, index) => {
      // Each player emits a vote
      mockSocket.simulateServerEvent('playerVoted', {
        user_id: player.user_id,
        vote: index % 2 === 0 ? 'approve' : 'reject'
      });
    });

    // Resolve voting
    mockSocket.simulateServerEvent('votingResolved', {
      result: 'approve',
      approvals: 2,
      rejections: 2
    });

    // Assert
    const voteEvents = mockSocket.getEmittedEventsOfType('playerVoted');
    expect(voteEvents).toHaveLength(4);
    
    const resolvedEvents = mockSocket.getEmittedEventsOfType('votingResolved');
    expect(resolvedEvents[0].data.result).toBe('approve');
  });

  it('should simulate government takeover scenario', async () => {
    // Arrange
    const attacker = gameFixtures.createPlayer({ 
      user_id: 1, 
      username: 'PotentialDictator' 
    });
    const defenders = gameFixtures.createPlayers(3, { 
      approval_status: 'reject' 
    }).map((p, i) => ({ ...p, user_id: i + 2 }));
    
    // Act - Simulate takeover bid
    mockSocket.simulateServerEvent('takoverBidStarted', {
      bidder_id: attacker.user_id,
      bidder_name: attacker.username
    });

    defenders.forEach((defender, index) => {
      mockSocket.simulateServerEvent('takoverVote', {
        voter_id: defender.user_id,
        vote: index < 2 ? 'support' : 'oppose'
      });
    });

    // Determine outcome
    mockSocket.simulateServerEvent('takoverResolved', {
      success: true,
      new_government_type: 'Dictatorship',
      new_leader: attacker.username
    });

    // Assert
    const takoverEvents = mockSocket.getEmittedEventsOfType('takoverBidStarted');
    expect(takoverEvents).toHaveLength(1);
    
    const resolved = mockSocket.getEmittedEventsOfType('takoverResolved');
    expect(resolved[0].data.success).toBe(true);
    expect(resolved[0].data.new_leader).toBe('PotentialDictator');
  });

  it('should handle jail sequence', async () => {
    // Arrange
    const prisoner = gameFixtures.createPlayer({ user_id: 1 });
    
    // Act - Player gets jailed
    mockSocket.simulateServerEvent('putInJail', {
      user_id: prisoner.user_id,
      reason: 'stealing'
    });

    // Clock ticks while in jail
    for (let i = 0; i < 3; i++) {
      mockSocket.simulateServerEvent('jailClockTick', {
        user_id: prisoner.user_id,
        remaining_time: 3 - i
      });
    }

    // Released
    mockSocket.simulateServerEvent('releaseFromJail', {
      user_id: prisoner.user_id
    });

    // Assert
    const jailEvents = mockSocket.getEmittedEventsOfType('putInJail');
    expect(jailEvents).toHaveLength(1);
    
    const releaseEvents = mockSocket.getEmittedEventsOfType('releaseFromJail');
    expect(releaseEvents).toHaveLength(1);
    
    const allEvents = mockSocket.getEmittedEvents();
    expect(allEvents.length).toBeGreaterThan(4);
  });

  it('should handle job assignment workflow', async () => {
    // Arrange
    const players = gameFixtures.createPlayers(3);
    const jobs = gameFixtures.getJobs();

    // Act - Admin assigns jobs
    players.forEach((player, index) => {
      mockSocket.simulateServerEvent('jobAssigned', {
        user_id: player.user_id,
        job_id: jobs[index].id,
        job_name: jobs[index].name
      });
    });

    // Assert
    const jobEvents = mockSocket.getEmittedEventsOfType('jobAssigned');
    expect(jobEvents).toHaveLength(3);
    expect(jobEvents[0].data.job_name).toBe('Banker');
    expect(jobEvents[1].data.job_name).toBe('Farmer');
  });

  it('should handle rich player scenario', async () => {
    // Arrange
    const richPlayer = gameFixtures.createPlayer({ 
      user_id: 1, 
      username: 'RichPlayer' 
    });
    const poorPlayers = gameFixtures.createPlayers(3, { 
      clock: '10' 
    }).map((p, i) => ({ ...p, user_id: i + 2 }));

    // Act - Rich player gets taxed
    mockSocket.simulateServerEvent('taxImposed', {
      amount: '50',
      target_user_id: richPlayer.user_id,
      reason: 'wealth_redistribution'
    });

    // All players receive tax refund
    [richPlayer, ...poorPlayers].forEach(player => {
      mockSocket.simulateServerEvent('taxRefundGiven', {
        user_id: player.user_id,
        amount: '10'
      });
    });

    // Assert
    const taxEvents = mockSocket.getEmittedEventsOfType('taxImposed');
    expect(taxEvents[0].data.target_user_id).toBe(1);
    
    const refundEvents = mockSocket.getEmittedEventsOfType('taxRefundGiven');
    expect(refundEvents).toHaveLength(4); // rich + 3 poor
  });

  it('should track full game progression', async () => {
    // Arrange - Initialize game
    const players = gameFixtures.createPlayers(3);
    let eventLog = [];

    // Mock event tracking
    const trackEvent = (event) => {
      mockSocket.simulateServerEvent(event.name, event.data);
      eventLog.push(event.name);
    };

    // Act - Simulate game progression
    trackEvent({ name: 'gameStarted', data: { players: 3 } });
    trackEvent({ name: 'roundStarted', data: { round: 1 } });
    trackEvent({ name: 'clockRunning', data: { clock: '100' } });
    trackEvent({ name: 'clockRunning', data: { clock: '50' } });
    trackEvent({ name: 'clockEnded', data: { finalClock: '0' } });
    trackEvent({ name: 'roundEnded', data: { round: 1 } });
    trackEvent({ name: 'gameEnded', data: { winner: players[0].username } });

    // Assert
    expect(eventLog).toEqual([
      'gameStarted',
      'roundStarted',
      'clockRunning',
      'clockRunning',
      'clockEnded',
      'roundEnded',
      'gameEnded'
    ]);

    const allEvents = mockSocket.getEmittedEvents();
    expect(allEvents[0].event).toBe('gameStarted');
    expect(allEvents[allEvents.length - 1].event).toBe('gameEnded');
  });
});
