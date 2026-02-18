#GerrysGame
AWS/Docker hosted app made for Mr.Gerrys Game.

WELCOME TO GERRYS GAME!
90% Complete.

## Recent Changes (Version 4.21 → v5)

### New Features:
- **End Game History Graph**: When clicking "End Game?", a graph displays showing all players' clock values over time throughout the game session
  - Historical data is captured every 5 seconds during gameplay
  - Chart shows time in DD•HH•MM format on Y-axis
  - Color-coded lines for each player
  - "End Game & Close Room" button to finalize after viewing stats

- **Job Title Perks**: Three new perk tiers available via icon buttons
  - Manager: +10 minute bonus on "Get Paid"
  - Senior: +20 minute bonus on "Get Paid"
  - Executive: +30 minute bonus on "Get Paid"
  - Visual icons displayed next to player names in table

- **Heat System**: New "Heat" column added to player table
  - Independent counter with +/- buttons
  - Min: 0, Max: 10
  - Tracks heat level per player

- **Communist Government Enhancements**:
  - "Spin Wheel" button to select 3 politburo members randomly
  - "Share the Wealth" button for politburo to redistribute time
  - Wealth redistribution caps at 12 hours per person, rounded to nearest 10 minutes
  - Communist government applies -10 minute penalty on "Get Paid"

- **Dropped Players System**: Players with 00•00•00 clock time automatically move to separate "Dropped Players" section
  - Grayed out table with strikethrough styling
  - Real-time updates for all users in room

- **New Job & Government Options**:
  - "Unemployed" job option added (Tier 0, no income)
  - "Anarchy" government type added

### Quality of Life Changes:
- **Instant Updates**: Job, perk, bleed, and heat changes now update instantly without waiting for server sync
  - Targeted socket events replace full room state broadcasts
  - Eliminated flickering between old and new values
  - Reduced update latency from ~7 seconds to instant

- **Value Caps Enforced**:
  - Bleed: 0-64 range enforced on frontend
  - Heat: 0-10 range enforced on frontend
  - Can decrease from above-cap values back to normal range

- **Clock Persistence**: Player clock values now persist when refreshing the page (F5)
  - Fixed issue where clocks reset to 01•00•00 on page reload
  - Database properly retains participant data

- **Socket Room Broadcasting Fix**: Fixed issue where real-time updates only reached the triggering user
  - Converted room identifiers from integers to strings for consistency
  - All users now receive updates immediately when any player's state changes

- **Background Thread Optimization**:
  - Reduced room_state broadcast frequency from every 1 second to every 5 seconds
  - Prevents targeted updates from being overwritten by stale data
  - Clock history snapshots captured every 5 seconds

TO DO:
  - add admin panel
  - add profile picture and profile changes
        - 50% complete
  - in the leaderboard, have a victory quote from each user (maybe, fun I guess)
  - ~~Add a chart to track peoples clocks/time bank over time~~ ✅ COMPLETED

