# Frontend Testing Guide

## Overview

You now have a complete testing infrastructure to test every part of your frontend **without needing actual players**. This includes:

- **Mock Socket Service**: Simulate real-time multiplayer events
- **Mock API Service**: Simulate backend API calls  
- **Game Fixtures**: Realistic test data generators
- **Example Tests**: Real testing patterns you can copy

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Run Tests

```bash
# Run all tests once
npm test

# Run tests in watch mode (auto-rerun when you save)
npm run test:watch

# Run with coverage report
npm run test:coverage
```

## How to Use the Mocks

### Testing Socket Events (Multiplayer Scenarios)

```javascript
import { createMockSocket } from '../mocks/mockSocket';
import { gameFixtures } from '../fixtures/gameFixtures';

// Create mock socket
const socket = createMockSocket();

// Create test players
const players = gameFixtures.createPlayers(3);

// Simulate server sending events
socket.simulateServerEvent('updateClock', { 
  data: '100' 
});

socket.simulateServerEvent('playerVoted', {
  user_id: players[0].user_id,
  vote: 'approve'
});

// Assert what happened
const voteEvents = socket.getEmittedEventsOfType('playerVoted');
expect(voteEvents).toHaveLength(1);
expect(voteEvents[0].data.vote).toBe('approve');
```

### Testing API Calls

```javascript
import { createMockApiService } from '../mocks/mockApiService';

const api = createMockApiService();

// Setup mock responses
api.setResponse('GET', '/api/rooms', [
  { id: 1, name: 'Room A' },
  { id: 2, name: 'Room B' }
]);

// Make "API calls"
const response = await api.get('/api/rooms');
expect(response.data).toHaveLength(2);

// Check what requests were made
expect(api.wasRequestMade('GET', '/api/rooms')).toBe(true);
```

### Using Game Fixtures

```javascript
import { gameFixtures } from '../fixtures/gameFixtures';

// Create a single player
const player = gameFixtures.createPlayer({
  username: 'TestPlayer',
  clock: '100'
});

// Create multiple players
const players = gameFixtures.createPlayers(4, {
  approval_status: 'pending'
});

// Create a full game scenario
const scenario = gameFixtures.createGameScenario(3);
// scenario.admin - the admin player
// scenario.players - all players
// scenario.room - the room state
```

## Example Test Patterns

### Testing a Clock Update

```javascript
it('should update clock when server sends event', () => {
  const socket = createMockSocket();
  
  // Simulate server event
  socket.simulateServerEvent('updateClock', { data: '150' });
  
  // Your component/composable would listen and update
  // Then you assert it worked
  const events = socket.getEmittedEventsOfType('updateClock');
  expect(events[0].data.data).toBe('150');
});
```

### Testing a Multi-Player Scenario

```javascript
it('should handle voting from all players', () => {
  const socket = createMockSocket();
  const players = gameFixtures.createPlayers(4);
  
  // Simulate each player voting
  players.forEach((player, index) => {
    socket.simulateServerEvent('playerVoted', {
      user_id: player.user_id,
      vote: index < 2 ? 'approve' : 'reject'
    });
  });
  
  // Check all votes were recorded
  const votes = socket.getEmittedEventsOfType('playerVoted');
  expect(votes).toHaveLength(4);
  const approvals = votes.filter(v => v.data.vote === 'approve');
  expect(approvals).toHaveLength(2);
});
```

### Testing a Complete Game Flow

```javascript
it('should progress through full game', async () => {
  const socket = createMockSocket();
  const api = createMockApiService();
  
  // Setup API
  api.setResponse('GET', '/api/rooms/1', gameFixtures.createRoom());
  
  // Get room state
  const room = await api.get('/api/rooms/1');
  
  // Simulate game events in order
  socket.simulateServerEvent('gameStarted', {});
  socket.simulateServerEvent('clockRunning', { clock: '100' });
  socket.simulateServerEvent('clockRunning', { clock: '50' });
  socket.simulateServerEvent('gameEnded', { winner: room.data.participants[0].username });
  
  // Verify sequence
  const events = socket.getEmittedEvents();
  expect(events[0].event).toBe('gameStarted');
  expect(events[3].event).toBe('gameEnded');
});
```

## Testing Your Actual Components

### Step 1: Create a Test File

Create `tests/unit/MyComponent.spec.js`:

```javascript
import { describe, it, expect, beforeEach } from '@jest/globals';
import { mount } from '@vue/test-utils';
import MyComponent from '@/components/MyComponent.vue';
import { createMockSocket } from '../../mocks/mockSocket';

describe('MyComponent', () => {
  let socket;
  
  beforeEach(() => {
    socket = createMockSocket();
  });

  it('should render', () => {
    const wrapper = mount(MyComponent, {
      props: {
        socket: socket
      }
    });
    expect(wrapper.exists()).toBe(true);
  });

  it('should respond to socket events', async () => {
    const wrapper = mount(MyComponent, {
      props: {
        socket: socket
      }
    });

    // Simulate server event
    socket.simulateServerEvent('someEvent', { data: 'test' });
    
    // Wait for changes
    await wrapper.vm.$nextTick();
    
    // Assert component updated
    expect(wrapper.text()).toContain('expected text');
  });
});
```

### Step 2: Update Your Component

Make your component accept a socket via prop:

```vue
<template>
  <div>{{ message }}</div>
</template>

<script>
export default {
  props: {
    socket: Object  // Accept mock or real socket
  },
  data() {
    return {
      message: ''
    };
  },
  mounted() {
    this.socket.on('someEvent', (data) => {
      this.message = data.data;
    });
  }
}
</script>
```

### Step 3: Run Your Test

```bash
npm test -- MyComponent.spec.js
```

## Available Fixtures

### Game Fixtures

- `gameFixtures.createPlayer(overrides)` - Single player
- `gameFixtures.createPlayers(count, overrides)` - Multiple players
- `gameFixtures.createRoom(overrides)` - Game room
- `gameFixtures.getGovernments()` - List of governments
- `gameFixtures.getJobs()` - List of jobs
- `gameFixtures.createGameScenario(playerCount)` - Full game setup

### Available Events to Simulate

Common socket events you can test:

- `updateClock` - Clock update
- `playerVoted` - Player cast vote
- `userClockUpdate` - Individual clock update
- `gameEnded` - Game finished
- `playerJoined` - New player joined
- `playerDisconnected` - Player left
- `putInJail` - Player jailed
- `releaseFromJail` - Player freed
- `approvalStatusRequested` - Vote requested
- `governmentChanged` - Government type changed
- `jobAssigned` - Player assigned job
- `taxImposed` - Tax applied
- `taxRefundGiven` - Tax refund given

Add more as needed for your game!

## Tips & Tricks

### 1. Check What Events Were Emitted

```javascript
const allEvents = socket.getEmittedEvents();
// Returns: [{ event: 'name', data: {...}, timestamp }, ...]
```

### 2. Clear Event History

```javascript
socket.clearEmittedEvents();
```

### 3. Simulate Delays

```javascript
// Simulate slow API
api.setResponse('GET', '/endpoint', response, 500); // 500ms delay
```

### 4. Check Request History

```javascript
const history = api.getRequestHistory();
// Check what methods and endpoints were called
```

### 5. Create Custom Fixtures

Extend game fixtures for your specific scenarios:

```javascript
const myCustomPlayer = gameFixtures.createPlayer({
  username: 'MySpecialPlayer',
  clock: '999',
  is_admin: true,
  bleed: 100
});
```

## Next Steps

1. **Run the example tests**: `npm run test:watch`
2. **Study the test files** in `tests/unit/` to see patterns
3. **Create tests for your components** following the examples
4. **Add more fixture data** as you identify common test scenarios
5. **Test edge cases**: What happens when players disconnect? Multiple events at once? Invalid data?

## Common Issues

### Tests can't find modules
Make sure you're in the `frontend` directory when running `npm test`

### Socket events not firing
Check that you're calling `simulateServerEvent()` not `emit()`

### Component doesn't update
Add `await wrapper.vm.$nextTick()` after socket events

## Questions?

See the example test files for complete working examples of every pattern!
