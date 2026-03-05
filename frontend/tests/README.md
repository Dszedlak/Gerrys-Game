# Testing Infrastructure Setup Complete! 🎉

You now have a **complete testing system** to test your multiplayer game frontend **without needing real players**.

## What You Got

### 1. **Mock Services**
- `MockSocket` - Simulate real-time WebSocket events from other players
- `MockApiService` - Simulate backend API calls
- Full event tracking and verification

### 2. **Game Fixtures**  
- `gameFixtures.createPlayer()` - Create test players
- `gameFixtures.createPlayers(n)` - Create multiple players
- `gameFixtures.createGameScenario(n)` - Full game setup with admin + players
- `gameFixtures.getGovernments()` / `getJobs()` - Game data

### 3. **Example Tests**
Four complete test files showing you exactly how to test:
- **room-sockets.spec.js** - Socket events and multiplayer interactions
- **api-service.spec.js** - API calls and responses
- **game-scenarios.spec.js** - Complete game workflows
- **composables.spec.js** - Vue composables with mocks

### 4. **Documentation**
- **TESTING_GUIDE.md** - Comprehensive guide with examples
- **TESTING_CHEATSHEET.md** - Quick reference

## 30-Second Quickstart

```bash
cd frontend
npm install
npm run test:watch
```

Now create a test file in `tests/unit/` and start testing! 🚀

## What Can You Test Now?

### ✅ Clock Updates
```javascript
socket.simulateServerEvent('updateClock', { data: '150' });
expect(component.clock).toBe('150');
```

### ✅ Multiplayer Voting
```javascript
players.forEach(p => {
  socket.simulateServerEvent('playerVoted', { 
    user_id: p.user_id, 
    vote: 'approve' 
  });
});
```

### ✅ Game Events
- Government changes
- Job assignments
- Player joins/leaves
- Jail mechanics
- Tax/budget changes
- Game end conditions

### ✅ API Calls
- Join room
- Get leaderboard
- Update player state
- Request approvals

### ✅ Complete Game Flows
From start to end, with multiple players and events happening together.

## Example: Test Your First Feature

Let's say you want to test the clock component:

**1. Create** `tests/unit/RoomClock.spec.js`:
```javascript
import { mount } from '@vue/test-utils';
import RoomClock from '@/components/RoomClock.vue';
import { createMockSocket } from '../mocks/mockSocket';

describe('RoomClock', () => {
  it('should update when clock changes', async () => {
    const socket = createMockSocket();
    const wrapper = mount(RoomClock, {
      props: { clock: '100', socket }
    });

    socket.simulateServerEvent('updateClock', { data: '50' });
    await wrapper.vm.$nextTick();

    expect(wrapper.emitted('update-clock')).toBeTruthy();
  });
});
```

**2. Run** it:
```bash
npm run test:watch
```

**3. Fix any issues**, watch tests pass! ✅

## File Structure

```
frontend/
├── tests/
│   ├── setup.js                 # Jest config
│   ├── unit/
│   │   ├── room-sockets.spec.js        # Socket examples
│   │   ├── api-service.spec.js         # API examples
│   │   ├── game-scenarios.spec.js      # Game flow examples
│   │   └── composables.spec.js         # Composable examples
│   ├── mocks/
│   │   ├── mockSocket.js        # WebSocket simulator
│   │   └── mockApiService.js    # API simulator
│   └── fixtures/
│       └── gameFixtures.js      # Test data generators
├── TESTING_GUIDE.md             # Full documentation
├── TESTING_CHEATSHEET.md        # Quick reference
└── jest.config.js               # Jest configuration
```

## Next: Using These in Your Code

### Option 1: Pass Mock to Component (Cleanest)

Your component accepts socket as a prop:
```vue
<script>
export default {
  props: { socket: Object },
  mounted() {
    this.socket.on('updateClock', (data) => { /* handle */ });
  }
}
</script>
```

Test it:
```javascript
const socket = createMockSocket();
const wrapper = mount(MyComponent, { props: { socket } });
socket.simulateServerEvent('updateClock', { data: '50' });
```

### Option 2: Provide via Injection

In your app:
```javascript
app.provide('socket', socket);
```

In tests:
```javascript
const socket = createMockSocket();
const wrapper = mount(MyComponent, {
  global: { provide: { socket } }
});
```

### Option 3: Mock Composable Import

In tests:
```javascript
jest.mock('@/composables/useSocket', () => ({
  useSocket: () => createMockSocket()
}));
```

## Running Tests

```bash
npm test                  # Run once
npm run test:watch        # Auto-rerun on save
npm run test:coverage     # Get coverage report
```

## Helpful Tips

### 1. Inspect Emitted Events
```javascript
const events = socket.getEmittedEventsOfType('playerVoted');
console.log(events); // See all vote events
```

### 2. Check Request History
```javascript
const requests = api.getRequestHistory();
expect(api.wasRequestMade('POST', '/api/rooms')).toBe(true);
```

### 3. Simulate Delays
```javascript
api.setResponse('GET', '/api/slow', data, 500); // 500ms delay
```

### 4. Track Event Order
```javascript
const allEvents = socket.getEmittedEvents();
// Returns: [{ event, data, timestamp }, ...]
```

## Common Questions

**Q: How do I test my actual Room.vue component?**  
A: See `TESTING_GUIDE.md` section "Testing Your Actual Components"

**Q: Can I test just the business logic without components?**  
A: Yes! See `composables.spec.js` for testing composables directly

**Q: How do I add my own events?**  
A: Just call `socket.simulateServerEvent('myEvent', { custom: 'data' })`

**Q: Where do I find all available events?**  
A: Check `TESTING_GUIDE.md` "Available Events to Simulate"

## Troubleshooting

**Tests won't run:**
- Run `npm install` in `frontend/` directory
- Make sure you're using Node.js 14+

**Mock not working:**
- Import from correct path: `../mocks/mockSocket` (relative to your test)
- Check file is in `tests/mocks/` directory

**Events not triggering:**
- Use `simulateServerEvent()` not `emit()`
- Make sure composable calls `setupSocketListeners()`

## Next Steps

1. ✅ Run `npm run test:watch`
2. ✅ Open `tests/unit/room-sockets.spec.js` and see tests pass
3. ✅ Copy a test pattern for your component
4. ✅ Make it test your actual code
5. ✅ Watch it fail, then fix the code to make it pass!

## You're All Set! 

Start testing without needing to gather people. Test **every edge case**, **every event**, **every game state** in seconds.

**Questions?** Check `TESTING_GUIDE.md` for detailed explanations and patterns.

Happy Testing! 🎮
