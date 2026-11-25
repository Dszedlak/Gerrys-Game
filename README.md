#GerrysGame
AWS/Docker hosted app made for Mr.Gerrys Game.

WELCOME TO GERRYS GAME!
90% Complete.

## Recent Changes (v5 → v6)

### Board view (new — replaces the Tabletopia board):
- **v4.27 cards are in** (from `Gerrys_Game_Cards.xlsx`, now the default version): all 30 scenario cards, 31 assignment slips (+3 hours each), the 14 collectables, Promotions, Job Opportunities, Bandages/Painkillers and Shortcuts (dealt on the Senate). Contraband cards have red names; reusable cards (Hell Bent, Charm, Efficiency) stay after use. 44 of the 69 distinct cards act automatically — court cases (5+ to win, or the Judge decides if one is in play), roll tables (Experimental Drug, Gerry's Slot Machine), everyone-rolls checks (Secret Police, Curfew), faction job losses, Mafia, Annual Bonus and more; the rest show their instructions for the table.
- **Government oppressions** (16 cards from the Oppressions tab): anyone on a Senate tile can introduce one for 2 hours (a Senate action; max 4 in play; none under Democracy). Government leaders use them on their turn against a player of their choice: Politburo 2 each, Dictator 3, Head of State 1 per enemy of the state (state enemies only). A card can't be used the turn it's introduced, works once per turn, and all are removed when the government changes; the admin can remove one (Chief Justice). Steal time, bleeding, Time Virus, heat and demote apply automatically.
- **Medical Kit** comes from both the collectable deck and the Hospital.
- **Card automation** lives in `backend/app/data_collections/game_versions/automation.json`, matched by card name, so a new spreadsheet keeps it. Drop new spreadsheets in `.../game_versions/spreadsheets/`.
- **Rules brought in line with the v4.27 cards:** Democracy doubles all purchase prices; government income is Politburo +20, Dictator +30, Head of State +20, advisors +10; the Chancellor is a Public Service job.
- **Waiting lobby.** A new room opens on a lobby: everyone presses *I'm ready*; the host can *Start game* once everyone is, or *Force start* at any time. Then everyone rolls the die on the board (the host can roll for anyone away from their keyboard); the highest roll goes first, a tie at the top rolls again, and the rest follow in order of their rolls.
- **Sign-in sessions** last 30 days and are checked every time the site loads: if the server no longer accepts yours (expired, or the server was reset), you're signed out and asked to sign in again instead of looking signed in. Registering signs you straight in (no more false "error" message).
- **The room now opens on a playable board.** The 20-tile track from the physical board (Start → Job Centre → Senate → Hospital, clockwise), with the decks, dice tray, Jail and the Reaper's counter in the centre. The old table view is one click away (`📋 Table` / `🎲 Board view`) and the choice is remembered.
- **Server-authoritative turns.** Once someone wins the roll for the first turn, every pawn goes to Start and the Reaper's 2-hour timer begins. On your turn: collect income → roll → resolve the tile → end turn. Dice are rolled on the server; you can only roll once and only on your own turn.
- **Animated** — the die tumbles in 3D, then your pawn hops tile by tile; *Go to the Job Centre* glides you across.
- **Rules applied automatically:** passing or landing on Start removes 1 heat; landing on the second tile of the Job Centre, Senate or Hospital on consecutive turns gives no access; purchase limits (5 collectables, max 1 promotion; 5 hospital items, ×2 with a Doctor; 1 Black Market buy).
- **Tile actions in the turn panel:** buy collectables/promotions/hospital items/Black Market, release the **Time Virus** (pick a victim, the server rolls and takes 30 min per pip), draw an **assignment target** from the black bag, set your approval at the Senate.
- **Jail on the board:** *Go to Jail* (offered when your heat is full) resets heat, removes your job, drops your title one rank and ends your turn; paying the jail fee walks your pawn to Start.
- **The Reaper:** dead players roll into the central counter on their turn; once the Reaper arrives it rolls twice at the end of each round. Every multiple of 5 announces the horseman (Pestilence / War / Famine / Death). Horseman *effects* are announced, not applied — apply them as usual.
- **Civ 6-style player ledger** across the top, in turn order: portrait in the player's pawn colour, clock, income per turn (hover for the breakdown), bleed, heat pips, job/tier, title and approval. Your own bleed/heat have +/− on hover.
- **Public game log** of every roll, purchase, virus, jailing and manual move; the big moments also pop up as toasts.
- **Manual moves:** click a tile to move your own pawn on your turn (shortcuts, scenario cards); the admin can move anyone. Manual moves skip tile effects and are logged.
- **Game versions (card sets).** Every set of Scenario cards, Assignment slips and Collectables is a *game version* (e.g. `4.27`), stored in the database with its patch notes. When you create a room you pick the version to play (the latest is preselected); the room keeps it for the whole game, so publishing a new version never changes a game in progress, and no restart is needed.
  - Versions come from a spreadsheet: one sheet each for Scenario / Assignments / Collectables, with Title and Text columns, plus optional Copies, Equip and Effects (what the game does automatically, e.g. `time all -30; steal choose 1.5h`). The full format is at the top of `backend/app/card_import.py`, and `backend/app/data_collections/game_versions/card-template.xlsx` is an example.
  - Publish one: `python manage_cards.py import cards.xlsx --key 4.28 --name "v4.28" --notes-file notes.txt --default --bundle` (`check` to preview, `list`, `export <key> out.xlsx`, `default <key>`). `--bundle` also saves it to `data_collections/game_versions/` so it ships with the code.
  - Over the web: `POST /api/game-versions` (multipart `file`, `key`, `name`, `notes`, optional `make_default`/`dry_run`), allowed for usernames listed in the `GAME_DATA_ADMINS` environment variable. `GET /api/game-versions/<key>/export` downloads a version as .xlsx.
- **Card decks.** Fresh decks are shuffled from the room's version when the admin starts the board.
- **Cards dealt on landing, straight into your hand:** Collectables → a collectable (none under the Republic); Job Centre → a Job Opportunity; the Promotion Card square → a Promotion card *and* a Job Opportunity; Hospital → a bandage. The no-access rule applies on the second Job Centre/Hospital tile. Buying collectables, promotions and hospital items also deals the card into your hand.
- **Discard piles** for collectables, scenario cards and assignment slips, face up for everyone (click the Collectable deck on the board, or *Discard pile* under your cards). The Black Market lets you choose any used collectable; a card with the `takediscard` effect lets its player take one; the admin can hand any used collectable to any player.
- **Admin shuffle** (Admin tools in the turn panel): shuffle the Scenario, Collectable or Assignment deck, or all of them, with their discard piles put back in. Landing on a Scenario tile draws a card that pops up for everyone and the game applies its effects (time, steal/give, bleed, heat, move, Jail, draw, miss a turn; anything else is a "resolve by hand" note). Cards that need a victim ask the drawer to pick one.
- **Assignment board.** Landing on an Assignment Slip draws a slip and a black-bag target onto the board (max 6, max 2 per target; when full you replace one and its target stays). Anyone but the target can *Claim* it once per turn, which runs its reward and keeps the slip.
- **Collectables in hand.** Everyone is dealt 2 at the start, draws 1 free on a Collectables tile, and buying draws more. Hands are private (sent only to their owner). Use, equip (max 2, shown next to your name), give or discard; discards feed the Black Market.
- **Big dice roll** in the middle of the board for every player, and on your turn you can click the die to roll. Rolls and card flips animate even when Windows "animation effects" are off.
- **"You" panel** with your clock, job, title, approval, bleed and heat, always visible. The player strip is compact and shows no clocks (time is private, as at the table), so the board is about a third bigger.
- **Board / Table switch and Full screen** live in the top navigation bar while you're in a room. Full screen hides the browser tabs, bookmarks and address bar (Esc to leave).
- The game log can be minimised to a single line.
- Board state is stored on the room (`room.board_state`, added automatically on startup) so it survives a server restart.
- Tests: `python backend/tests/test_board_rules.py`, `test_board_cards.py`, `test_card_import.py`, and `frontend/tests/unit/board*.spec.js`.

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

