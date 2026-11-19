#GerrysGame
AWS/Docker hosted app made for Mr.Gerrys Game.

WELCOME TO GERRYS GAME!
90% Complete.

## Recent Changes (v5 → v6)

### Governments:
- **Republic restored as a selectable government**: previously dropped from the government list, so it could not be picked even though the server still accepted it
  - Head of state is elected by a **popular vote** of all alive players
  - The elected head of state then appoints **two advisors**
  - Head of state and advisors show **different icons** in the player table
  - Only the admin can conclude the vote; ties break deterministically on the lowest user id
  - Only the player who actually won the vote can appoint advisors

- **Enemies of the State**: the head of state and advisors can nominate any player other than the head of state
  - A player becomes a state enemy when the **head of state and at least one advisor** agree
  - Voting is deliberately informal — votes can be cast and changed at any time, with no formal round
  - The room is now **told out loud** when a player is declared an enemy (⚔️) and when one is forgiven (🕊️)
  - Who voted for whom is visible to the government only; everyone else sees just the outcome

- **Dictatorship is now genuinely blind**: bid amounts were previously broadcast to every player on every bid
  - The room is told **who** became dictator, never **how much** they spent
  - You still see your own bid, and it survives a page refresh

- **Anarchy is selectable again** (it was missing from the government list)

### Jobs:
- **Tier 3 jobs are now unique per game** — only one player can be the Doctor, the Chancellor, the CFO and so on. Tier 1 and Tier 2 jobs can still be held by several players. Jobs already taken appear in the dropdown as `CFO — taken by NotPaul` and cannot be selected, and the server rejects the change too, so it holds even if the page is tampered with.
- **The job dropdown is now grouped by tier** (Unemployed / Tier 1 / Tier 2 / Tier 3) and sorted alphabetically within each group.
- **Charity Commissioner**: while one is in the game, every **other** player loses 20 minutes of turn income. The Charity Commissioner is not affected.
- **Doctor**: while one is in the game, **Hospital items cost double** (60 minutes each). A reminder is shown in the room to all players, and the rule applies to the Doctor too.
- **Chancellor**: when voting to change government, the Chancellor's vote **counts twice in favour of change**. A vote to remain in the same government counts once — this is now spelled out in the voting modal, and the results screen marks the Chancellor's weighted vote.
- **Tax Officer renamed to Stock Broker** (Tier 3, Finance).

### Room layout — everything now fits on one screen:
- **The whole game fits without scrolling.** Previously the player table didn't begin until 750px down the page, so on a 1080p monitor (especially at 125% Windows scaling) you had to scroll to see anyone else's stats. The roster now starts at ~227px and six players fit with room to spare.
- **New top HUD**, Civ 6 style, in three tiers: the clock sits centred at the top with the −1h…−10 buttons to its left and +10…+1h to its right; below that your income, government and max collectables; below that Jail, Black Market and any active reminders.
- **Get Paid is now a `+` beside your income**, since the income figure already tells you what you will receive.
- **Leave Room and Admin Controls moved into the navbar**, where they stay out of the way of the game itself.
- **The Jail button now shows the fee** — `Jail: Buy Freedom (8.0)` — and tracks the government, so it reads `(12.0)` under a Dictatorship.
- **The player table now uses the full screen width** — it was previously capped at 1400px, leaving ~520px of a 1920px monitor empty.
- **Compact rows** (44px, down from 60px) so more players fit at once.
- **Dropped players are collapsed** behind a `▸ Dropped players (N)` summary instead of permanently occupying space.
- **The income breakdown now overlays** instead of pushing the table down when you expand it.
- **State-enemy announcements are toasts** in the corner. They previously appeared inline, shoving the whole roster down and yanking it back when they expired.
- **The layout is now responsive** — the HUD wraps and the roster scrolls sideways on narrow screens. It previously had no height budgeting at all.

### Economy & UI:
- **Income breakdown**: a new bar above the government strip shows **your income per turn**, and expands into a line-by-line breakdown of job, title, government, bleed and any Charity Commissioner penalty — so it is clear what you are earning and what is working against you.
- The player table's **Income** column and the new breakdown are now driven by a **single shared calculation**, so they can no longer disagree with each other.
- **Max collectables corrected**: no bleeding effect now allows **6**, any bleeding allows **5** (a Senior still adds one on top). It was previously one lower in both cases.

### Fixes:
- The server emitted `error` messages for rejected actions (invalid job, jail fee and so on) but **nothing was listening**, so every one of them was silently dropped. They now appear as a toast.
- `Room.vue`'s root element was `id="app"`, duplicating `App.vue`'s root. That made `#app { min-height: 100vh }` apply twice, adding a phantom full screen of height below the navbar and forcing the page to scroll even when the content fitted.
- Removed ~920 lines of dead CSS from `Room.vue` left behind when the room was split into components (the styles were copied, not moved) — including a duplicate of the clock card and two copies of the old player table. Also deleted `styles/global.css`, which was never imported, and the orphaned `RoomHeader.vue`, `RoomClock.vue` and `RoomGetPaidButton.vue`.
- The per-voter state-enemy breakdown was being broadcast to the whole room despite being intended for the government only.
- `defaultGovernments` was referenced in `Room.vue` without being imported, which threw if the server's collections never arrived.
- Perk icons requested `manager.png` / `senior.png` / `executive.png` while the files on disk are `.PNG` — harmless on Windows, broken on a case-sensitive host.

### Corrections to the notes below:
The v4.21 → v5 entries describe three things that the code does not do. For the record: the politburo is **2** members (not 3), non-politburo players pay **20** minutes per turn (not 10), and "balance the books" takes **50% of every alive player's time and shares it equally** — there is no 12-hour cap.

---

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

