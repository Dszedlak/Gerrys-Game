/**
 * Example: Testing API interactions
 * 
 * Shows how to test API calls without needing a real backend
 * You can:
 * 1. Mock API responses
 * 2. Make calls and verify they work
 * 3. Test error handling
 */

import { describe, it, expect, beforeEach } from '@jest/globals';
import { createMockApiService } from '../mocks/mockApiService';
import { gameFixtures } from '../fixtures/gameFixtures';

describe('API Service', () => {
  let mockApi;

  beforeEach(() => {
    mockApi = createMockApiService();
  });

  it('should fetch leaderboard', async () => {
    // Arrange
    const leaderboardData = [
      { rank: 1, username: 'TopPlayer', score: 10000 },
      { rank: 2, username: 'SecondPlace', score: 8000 },
      { rank: 3, username: 'ThirdPlace', score: 6000 }
    ];
    mockApi.setResponse('GET', '/api/leaderboard', leaderboardData);

    // Act
    const response = await mockApi.get('/api/leaderboard');

    // Assert
    expect(response.data).toHaveLength(3);
    expect(response.data[0].username).toBe('TopPlayer');
    expect(mockApi.wasRequestMade('GET', '/api/leaderboard')).toBe(true);
  });

  it('should create a room', async () => {
    // Arrange
    const newRoom = gameFixtures.createRoom({ id: 123 });
    mockApi.setResponse('POST', '/api/rooms', newRoom);

    // Act
    const response = await mockApi.post('/api/rooms', { name: 'Test Room' });

    // Assert
    expect(response.data.id).toBe(123);
    expect(response.data.name).toBe('Test Room');
  });

  it('should join a room', async () => {
    // Arrange
    const roomId = 1;
    const joinResponse = { success: true, message: 'Joined room' };
    mockApi.setResponse('POST', `/api/rooms/${roomId}/join`, joinResponse);

    // Act
    const response = await mockApi.post(`/api/rooms/${roomId}/join`, {});

    // Assert
    expect(response.data.success).toBe(true);
  });

  it('should update player clock', async () => {
    // Arrange
    const updateResponse = { clock: '50' };
    mockApi.setResponse('POST', '/api/player/clock', updateResponse);

    // Act
    const response = await mockApi.post('/api/player/clock', { clock: '50' });

    // Assert
    expect(response.data.clock).toBe('50');
  });

  it('should get room state', async () => {
    // Arrange
    const room = gameFixtures.createRoom();
    mockApi.setResponse('GET', `/api/rooms/${room.id}`, room);

    // Act
    const response = await mockApi.get(`/api/rooms/${room.id}`);

    // Assert
    expect(response.data.id).toBe(room.id);
    expect(response.data.participants).toHaveLength(3);
  });

  it('should handle API delays', async () => {
    // Arrange
    mockApi.setResponse('GET', '/api/slow-endpoint', { data: 'slow' }, 100);

    // Act
    const startTime = Date.now();
    await mockApi.get('/api/slow-endpoint');
    const duration = Date.now() - startTime;

    // Assert
    expect(duration).toBeGreaterThanOrEqual(100);
  });

  it('should track request history', async () => {
    // Arrange
    mockApi.setResponse('GET', '/api/rooms', []);
    mockApi.setResponse('POST', '/api/rooms', {});

    // Act
    await mockApi.get('/api/rooms');
    await mockApi.post('/api/rooms', { name: 'New Room' });

    // Assert
    const history = mockApi.getRequestHistory();
    expect(history).toHaveLength(2);
    expect(history[0].method).toBe('GET');
    expect(history[1].method).toBe('POST');
  });

  it('should handle failed government change requests', async () => {
    // Arrange
    // Note: Error is not configured, so it will fail
    
    // Act & Assert
    await expect(
      mockApi.put('/api/room/government', { governmentId: 2 })
    ).rejects.toBeDefined();
  });
});
