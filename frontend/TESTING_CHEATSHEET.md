// Quick Testing Cheat Sheet for Gerry's Game
// ============================================

// ===== IMPORT WHAT YOU NEED =====
import { createMockSocket } from '../mocks/mockSocket';
import { createMockApiService } from '../mocks/mockApiService';
import { gameFixtures } from '../fixtures/gameFixtures';

// ===== CREATE A MOCK SOCKET (for testing real-time events) =====
const socket = createMockSocket();

// Simulate server sending an event to your player
socket.simulateServerEvent('updateClock', { data: '150' });

// Check what events were triggered
const events = socket.getEmittedEventsOfType('updateClock');
expect(events[0].data.data).toBe('150');

// ===== CREATE A MOCK API (for testing backend calls) =====
const api = createMockApiService();

// Set up a fake response for an endpoint
api.setResponse('GET', '/api/rooms/1', {
  id: 1,
  name: 'Test Room'
});

// Make a "call"
const response = await api.get('/api/rooms/1');
expect(response.data.name).toBe('Test Room');

// ===== CREATE TEST PLAYERS =====
const player = gameFixtures.createPlayer();
const players = gameFixtures.createPlayers(3);
const admin = gameFixtures.createPlayer({ is_admin: true });

// ===== CREATE A FULL GAME SCENARIO =====
const scenario = gameFixtures.createGameScenario(4); // 4 players
// scenario.admin = admin player
// scenario.players = all players
// scenario.room = the room data

// ===== SIMULATE MULTIPLAYER EVENTS =====
players.forEach((player, index) => {
  socket.simulateServerEvent('playerVoted', {
    user_id: player.user_id,
    vote: index < 2 ? 'approve' : 'reject'
  });
});

// Check all votes
const votes = socket.getEmittedEventsOfType('playerVoted');
expect(votes).toHaveLength(3);

// ===== GET GOVERNMENTS & JOBS =====
const governments = gameFixtures.getGovernments();
const jobs = gameFixtures.getJobs();

// ===== CHECK REQUEST HISTORY =====
expect(api.wasRequestMade('POST', '/api/rooms')).toBe(true);
const history = api.getRequestHistory();

// ===== RUN TESTS =====
// npm test                 - Run all tests once
// npm run test:watch       - Auto-rerun when you save
// npm run test:coverage    - Get coverage report
