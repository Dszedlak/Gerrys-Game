<template>
  <div class="help-page">
    <div class="help-container">
      <!-- Header -->
      <div class="help-header">
        <div class="help-icon">📖</div>
        <h1 class="help-title">Gerry's Game Rules</h1>
        <p class="help-subtitle">Version 4.24 - Complete Guide</p>
      </div>

      <!-- Table of Contents -->
      <div class="help-section toc-section">
        <div class="section-header">
          <span class="section-icon">📋</span>
          <h2>Table of Contents</h2>
        </div>
        <div class="section-content">
          <div class="toc-grid">
            <a href="#objective" class="toc-link">🎯 Objective</a>
            <a href="#starting" class="toc-link">🚀 Starting the Game</a>
            <a href="#turn" class="toc-link">🎲 During Turn</a>
            <a href="#jobs" class="toc-link">💼 Jobs</a>
            <a href="#governments" class="toc-link">🏛️ Governments</a>
            <a href="#bleeding" class="toc-link">🩸 Bleeding Effect</a>
            <a href="#assignments" class="toc-link">📝 Assignments</a>
            <a href="#titles" class="toc-link">👑 Titles</a>
            <a href="#court" class="toc-link">⚖️ Court</a>
            <a href="#tiles" class="toc-link">🎮 Game Board Tiles</a>
            <a href="#death" class="toc-link">💀 Running Out of Time</a>
            <a href="#endgame" class="toc-link">🏇 End Game - Four Horsemen</a>
          </div>
        </div>
      </div>

      <!-- Key Words -->
      <div class="help-section">
        <div class="section-header">
          <span class="section-icon">📚</span>
          <h2>Key Words</h2>
        </div>
        <div class="section-content">
          <div class="keyword-list">
            <div class="keyword-item">
              <span class="keyword-term">Round</span>
              <span class="keyword-def">When all players have had a single turn and can start on any player.</span>
            </div>
            <div class="keyword-item">
              <span class="keyword-term">Alive Player</span>
              <span class="keyword-def">A player who still has time remaining on their clock.</span>
            </div>
            <div class="keyword-item">
              <span class="keyword-term">Item</span>
              <span class="keyword-def">Refers to a job, a title, each collectable (equipped or in hand), completed assignment slips, or revolution tokens.</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Objective -->
      <div id="objective" class="help-section">
        <div class="section-header">
          <span class="section-icon">🎯</span>
          <h2>Objective</h2>
        </div>
        <div class="section-content">
          <div class="objective-card">
            <p class="objective-main">The winner is the <strong>last person alive</strong> with time still on your clock.</p>
            <div class="objective-notes">
              <p>⚠️ It is possible that <strong>the game itself can win</strong> if players lose to a scenario or "die" at the same time.</p>
              <p>⭐ There is also a scenario card in which a singular player can win the game instantly.</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Starting the Game -->
      <div id="starting" class="help-section">
        <div class="section-header">
          <span class="section-icon">🚀</span>
          <h2>Starting the Game</h2>
        </div>
        <div class="section-content">
          <ol class="step-list">
            <li>
              <strong>Set Your Clock</strong>
              <p>Every player starts with <span class="highlight">24 hours</span> on their clocks.</p>
            </li>
            <li>
              <strong>Starting Government</strong>
              <p><span class="highlight">Democracy</span> is the starting government.</p>
            </li>
            <li>
              <strong>Shuffle Decks</strong>
              <p>Shuffle the collectable deck, scenario card deck, government oppression deck, bandage deck and assignment slips.</p>
            </li>
            <li>
              <strong>Choose Starting Player</strong>
              <p>The starting player is chosen from a random <span class="highlight">Wheel of Names</span>.</p>
            </li>
            <li>
              <strong>Select Jobs</strong>
              <p>The starting player chooses a Tier 1 job, and every other player does the same following the game rotation.</p>
            </li>
            <li>
              <strong>Deal Collectables</strong>
              <p>All players are dealt <span class="highlight">two collectables</span>.</p>
            </li>
            <li>
              <strong>Start The Reaper Timer</strong>
              <p>Start the <span class="highlight">2-hour timer</span> for The Reaper.</p>
            </li>
            <li>
              <strong>Begin!</strong>
              <p>The starting player rolls the die and moves the amount shown around the game board.</p>
            </li>
          </ol>
        </div>
      </div>

      <!-- During Turn -->
      <div id="turn" class="help-section">
        <div class="section-header">
          <span class="section-icon">🎲</span>
          <h2>During Turn</h2>
        </div>
        <div class="section-content">
          <div class="info-block">
            <h4>Beginning of Turn</h4>
            <p>Calculate your income and subtract effects on yourself. Your payment is the sum of your job payment, government effect, etc. If you have <strong>bleeding effect</strong>, this is removed <em>before</em> you are paid or any actions are undertaken.</p>
            <p class="warning-text">⚠️ It is YOUR responsibility to keep on top of what you should be paid and to use any abilities.</p>
          </div>

          <div class="info-block">
            <h4>Movement</h4>
            <p>Roll a single die to determine how far you progress around the board and complete the action of the tile you land on. You must roll once per turn for movement.</p>
          </div>

          <div class="info-block">
            <h4>Actions You Can Perform (except during scenario cards)</h4>
            <ul class="action-list">
              <li>Use collectables</li>
              <li>Use abilities or government oppression</li>
              <li>Complete and receive rewards for assignments</li>
              <li>Apply for a title</li>
              <li>Trade and negotiate with other players</li>
              <li>Resign from your job</li>
            </ul>
          </div>

          <div class="warning-box">
            <p><strong>Important:</strong> There is no set order in a turn except payment minus bleeding effect. You <strong>cannot</strong> perform any of these actions when it is not your turn. A player may trade or negotiate with you during their turn, but whoever's turn it is takes precedence.</p>
          </div>
        </div>
      </div>

      <!-- Jobs -->
      <div id="jobs" class="help-section">
        <div class="section-header">
          <span class="section-icon">💼</span>
          <h2>Jobs</h2>
        </div>
        <div class="section-content">
          <div class="info-block">
            <p>When you visit the <strong>Job Centre</strong> (any of the two marked tiles), you receive a Job Opportunity collectable.</p>
            <p>The three factions are: <span class="faction finance">Finance</span>, <span class="faction public">Public Service</span>, and <span class="faction illicit">Illicit</span>.</p>
          </div>

          <div class="rules-list">
            <div class="rule-item">
              <span class="rule-icon">📋</span>
              <p>If you are already employed, you must <strong>resign from your post</strong> before accepting a new Tier 1 role.</p>
            </div>
            <div class="rule-item">
              <span class="rule-icon">🚫</span>
              <p>If you land on the second Job Centre square on your next turn, you do <strong>not</strong> get offered another job. This also applies to the Senate & Hospital.</p>
            </div>
            <div class="rule-item">
              <span class="rule-icon">⏳</span>
              <p>When you accept a <strong>Tier 3 job</strong>, you cannot use its ability until your following turn.</p>
            </div>
          </div>

          <div class="special-job">
            <h4>🎭 Chaos Creator (Special)</h4>
            <p>The "roll the die" effect is also the player's movement roll.</p>
          </div>
        </div>
      </div>

      <!-- Governments -->
      <div id="governments" class="help-section">
        <div class="section-header">
          <span class="section-icon">🏛️</span>
          <h2>Governments</h2>
        </div>
        <div class="section-content">
          <div class="info-block">
            <p>At every stage of the game a government will be in power. The <strong>starting government is always Democracy</strong>.</p>
            <p>Each government has specific characteristics which affect <span class="highlight">government leaders</span> (dictator or politburo members) and <span class="highlight">peasants</span> (non-government leaders).</p>
          </div>

          <div class="gov-rules">
            <h4>Government Oppression</h4>
            <p>Government leaders can introduce government oppression by spending <strong>2 hours at the Senate</strong>. There is no limit to the amount of government oppression that can be passed under a single government. Each government oppression can only be used by a single government leader.</p>
          </div>

          <div class="gov-rules">
            <h4>Approval Voting</h4>
            <p>During each government, players have an <strong>approval vote</strong> which is set to "approve" by default at the start of any new government.</p>
            <ul>
              <li>Players can change their approval status at the Senate by spending <strong>1 hour</strong></li>
              <li>When the majority of votes reject the current government, a <strong>government vote</strong> takes place by all alive players</li>
              <li>If the vote passes: government is removed, all oppressions are removed, a new government is installed (cannot be the previous type)</li>
              <li>If the vote fails: the player who instigated receives <strong>+1 heat</strong></li>
            </ul>
            <p>The government can also be altered or overthrown by scenario cards.</p>
          </div>
        </div>
      </div>

      <!-- Bleeding Effect -->
      <div id="bleeding" class="help-section">
        <div class="section-header">
          <span class="section-icon">🩸</span>
          <h2>Bleeding Effect</h2>
        </div>
        <div class="section-content">
          <div class="bleed-info">
            <p>Some activities may lead to a player obtaining bleeding effect. Each number on the counter equates to <strong>10 minutes</strong> of bleeding effect and the player loses this much time per turn.</p>
            <div class="bleed-cap">
              <span class="cap-label">Bleeding Cap:</span>
              <span class="cap-value">60 minutes</span>
            </div>
          </div>

          <div class="info-block">
            <h4>Reducing Bleeding</h4>
            <ul>
              <li>Purchase hospital items from the Hospital</li>
              <li>Certain jobs, collectables, and scenario cards can reduce bleeding</li>
            </ul>
            <p class="warning-text">⚠️ If you land on a later hospital tile on your next turn, you do not receive treatment as you have not left the hospital.</p>
          </div>

          <div class="bonus-info">
            <span class="bonus-icon">⭐</span>
            <p>Players with <strong>no bleeding effect</strong> are allowed to hold a <strong>bonus collectable</strong>.</p>
          </div>
        </div>
      </div>

      <!-- Assignments -->
      <div id="assignments" class="help-section">
        <div class="section-header">
          <span class="section-icon">📝</span>
          <h2>Assignments</h2>
        </div>
        <div class="section-content">
          <div class="assignment-limits">
            <div class="limit-box">
              <span class="limit-number">6</span>
              <span class="limit-label">Maximum assignments in play</span>
            </div>
            <div class="limit-box">
              <span class="limit-number">2</span>
              <span class="limit-label">Maximum against one player</span>
            </div>
          </div>

          <div class="info-block">
            <p>During the game, assignments will be revealed targeting specific players. If a player completes the assignment directed at an opposition player, they can <strong>claim the reward</strong> and keep the assignment slip – this supports obtaining a Title.</p>
          </div>

          <div class="rules-list">
            <div class="rule-item">
              <span class="rule-icon">🔄</span>
              <p>Completed assignment slips act like items and can be traded. Once traded in for a Manager title, they are discarded for the rest of the game.</p>
            </div>
            <div class="rule-item">
              <span class="rule-icon">🚫</span>
              <p>You <strong>cannot</strong> complete an assignment against yourself.</p>
            </div>
            <div class="rule-item">
              <span class="rule-icon">1️⃣</span>
              <p>You cannot complete more than <strong>one assignment</strong> on a single turn.</p>
            </div>
            <div class="rule-item">
              <span class="rule-icon">🔁</span>
              <p>If you land on assignment slip tile and all slots are taken, you can replace an assignment (not targeted against yourself) and keep the same target.</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Titles -->
      <div id="titles" class="help-section">
        <div class="section-header">
          <span class="section-icon">👑</span>
          <h2>Titles</h2>
        </div>
        <div class="section-content">
          <div class="info-block">
            <p>Once you have acquired a <strong>Tier 3 Job</strong>, you can apply for a title and earn additional income and abilities. You cannot use these abilities unless you have a Tier 3 position. You can only hold <strong>one title at a time</strong>.</p>
          </div>

          <div class="title-cards">
            <!-- Manager -->
            <div class="title-card manager">
              <div class="title-header">
                <span class="title-icon">📊</span>
                <h4>Manager</h4>
              </div>
              <div class="title-pay">
                <span class="pay-label">Pay:</span>
                <span class="pay-value">40 minutes/turn</span>
              </div>
              <div class="title-abilities">
                <h5>Abilities:</h5>
                <ul>
                  <li>+1 to die against War</li>
                  <li>Win all ties against War</li>
                </ul>
              </div>
              <div class="title-req">
                <h5>Requirements:</h5>
                <p>A completed assignment slip</p>
              </div>
            </div>

            <!-- Senior -->
            <div class="title-card senior">
              <div class="title-header">
                <span class="title-icon">⭐</span>
                <h4>Senior</h4>
              </div>
              <div class="title-pay">
                <span class="pay-label">Pay:</span>
                <span class="pay-value">50 minutes/turn</span>
              </div>
              <div class="title-abilities">
                <h5>Abilities:</h5>
                <ul>
                  <li>+1 to die against War</li>
                  <li>Win all ties against War</li>
                  <li>+1 collectable in hand</li>
                </ul>
              </div>
              <div class="title-req">
                <h5>Requirements:</h5>
                <p>Promotion card and no bleeding effect</p>
              </div>
            </div>

            <!-- Executive -->
            <div class="title-card executive">
              <div class="title-header">
                <span class="title-icon">💎</span>
                <h4>Executive</h4>
              </div>
              <div class="title-pay">
                <span class="pay-label">Pay:</span>
                <span class="pay-value">1 hour/turn</span>
              </div>
              <div class="title-abilities">
                <h5>Abilities:</h5>
                <ul>
                  <li>+1 to die against War</li>
                  <li>Win all ties against War</li>
                  <li>+1 collectable in hand</li>
                  <li>Use the ability of another available Tier 3 job</li>
                </ul>
              </div>
              <div class="title-req">
                <h5>Requirements:</h5>
                <p>No bleeding effect, no heat, and at least one equipped collectable</p>
              </div>
            </div>
          </div>

          <div class="executive-note">
            <p><strong>Executive Note:</strong> The additional ability from another Tier 3 job does not count as a separate item. When you choose a Tier 3 job ability, it is attached to the executive and cannot be changed. If you lose the executive title, you lose the Tier 3 job along with it.</p>
          </div>
        </div>
      </div>

      <!-- Court -->
      <div id="court" class="help-section">
        <div class="section-header">
          <span class="section-icon">⚖️</span>
          <h2>Court</h2>
        </div>
        <div class="section-content">
          <div class="court-info">
            <p>While in court, you must roll a <strong>5 or higher</strong> to avoid receiving +1 heat.</p>
            <div class="judge-rule">
              <span class="judge-icon">👨‍⚖️</span>
              <p>If there is a <strong>Judge</strong> present in the game, they over-rule and decide if you are innocent or guilty. However, they may abstain in judgement so you will have to roll the die.</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Game Board Tiles -->
      <div id="tiles" class="help-section">
        <div class="section-header">
          <span class="section-icon">🎮</span>
          <h2>Game Board Tiles</h2>
        </div>
        <div class="section-content">
          <div class="tiles-grid">
            <!-- Start -->
            <div class="tile-card">
              <div class="tile-icon start">🏁</div>
              <h4>Start</h4>
              <p>Activate any job abilities which are dependent on passing the Start Tile; this includes landing on the Start tile itself.</p>
            </div>

            <!-- Collectables -->
            <div class="tile-card">
              <div class="tile-icon collectables">🎴</div>
              <h4>Collectables / Promotions</h4>
              <p>Draw a free collectable. Purchase up to 5 additional collectables (1 hour each) of which only 1 can be a promotion card (2 hours).</p>
              <p class="tile-note">Max: 5 in hand + 2 equipped. You may go above but must end turn with 5.</p>
            </div>

            <!-- Assignment Slip -->
            <div class="tile-card">
              <div class="tile-icon assignment">📋</div>
              <h4>Assignment Slip</h4>
              <p>Draw an Assignment Slip and place it on the assignment board for all to see. Draw a counter from the black bag and place it to the right of the assignment slip.</p>
            </div>

            <!-- Scenario Card -->
            <div class="tile-card">
              <div class="tile-icon scenario">🎭</div>
              <h4>Scenario Card</h4>
              <p>Draw the top scenario card from the deck and follow the instructions on the card.</p>
            </div>

            <!-- Job Centre -->
            <div class="tile-card">
              <div class="tile-icon job">💼</div>
              <h4>Job Centre</h4>
              <p>Takes up two tiles. Receive a job opportunity card on any Job Centre tile. Landing on the first tile also gives you a promotion card.</p>
            </div>

            <!-- Time Virus -->
            <div class="tile-card">
              <div class="tile-icon virus">🦠</div>
              <h4>Time Virus</h4>
              <p>Nominate a player who will lose time. Roll a die: 1 = 30 min, 2 = 1 hour... up to 6 = 3 hours. You don't steal their time; it's lost to the virus.</p>
            </div>

            <!-- Senate -->
            <div class="tile-card wide">
              <div class="tile-icon senate">🏛️</div>
              <h4>Senate</h4>
              <p>Takes up three tiles. Receive a shortcut card on any Senate tile. Options (one per visit):</p>
              <ul>
                <li>1 hour: Change your approval status</li>
                <li>2 hours: Change another player's approval status</li>
                <li>2 hours: Purchase government oppression (if gov leader)</li>
              </ul>
              <p class="tile-note">Third Senate tile also lets you Time Virus a player.</p>
            </div>

            <!-- Hospital -->
            <div class="tile-card">
              <div class="tile-icon hospital">🏥</div>
              <h4>Hospital</h4>
              <p>Takes up two tiles. Receive a hospital item card. Purchase up to 5 additional hospital items for 30 minutes each.</p>
            </div>

            <!-- Go to Job Centre -->
            <div class="tile-card">
              <div class="tile-icon goto">➡️</div>
              <h4>Go to Job Centre</h4>
              <p>Jump immediately to the centre tile named "Job Centre". You have passed the Start tile.</p>
            </div>

            <!-- Black Market -->
            <div class="tile-card">
              <div class="tile-icon market">🕶️</div>
              <h4>Black Market</h4>
              <p>Spend 2 hours to purchase a used collectable from the discard pile. Only one per visit.</p>
              <p class="tile-note">At game start, a Revolution Token is placed in the discard pile and can be purchased here.</p>
            </div>

            <!-- Jail -->
            <div class="tile-card wide">
              <div class="tile-icon jail">🔒</div>
              <h4>Jail</h4>
              <p>Sent here with 3 heat tokens. You lose your job but keep collectables; heat resets to zero. If you hold a title, you get demoted by one rank; managers lose their title. Being sent to jail ends your turn.</p>
              <p>Next turn: Pay <strong>8 hours</strong> (after bleeding), move to Start, and continue your turn normally.</p>
              <p class="tile-note">You're still involved in activities while in jail and can be a government member. You cannot receive heat whilst in jail.</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Running Out of Time -->
      <div id="death" class="help-section death-section">
        <div class="section-header">
          <span class="section-icon">💀</span>
          <h2>Running Out of Time</h2>
        </div>
        <div class="section-content">
          <div class="death-info">
            <p class="death-main">When your clock reaches 0, <strong>you die</strong>.</p>
            <p>You lose your job, title, and any government oppressions. Your player bust remains on the tile you died on and your collectables are left out for other players to loot your body.</p>
          </div>

          <div class="loot-rules">
            <h4>Looting Rules</h4>
            <ul>
              <li>If you die in jail, your bust moves to the Start Tile</li>
              <li>If a player <strong>passes</strong> your body whilst moving, they can take a <strong>single collectable</strong></li>
              <li>If a player <strong>lands on</strong> or <strong>advances directly to</strong> your body, they take <strong>all</strong> your collectables</li>
              <li>Your player bust is removed once all collectables have been looted</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- End Game -->
      <div id="endgame" class="help-section endgame-section">
        <div class="section-header">
          <span class="section-icon">🏇</span>
          <h2>End Game - The Four Horsemen of the Apocalypse</h2>
        </div>
        <div class="section-content">
          <div class="info-block">
            <p>When a player dies in game, they become a <strong>Servant of the Reaper</strong>; they continue to roll once per turn with each roll added to the central counter.</p>
            <p>The Four Horsemen are <span class="horseman-name pestilence">Pestilence</span>, <span class="horseman-name war">War</span>, <span class="horseman-name famine">Famine</span> & <span class="horseman-name death">Death</span> who are present depending what is on the counter.</p>
            <p>Each horseman activates <strong>5 times</strong> before moving to the next, unleashed every time the counter reaches or exceeds a multiple of 5.</p>
          </div>

          <!-- The Reaper -->
          <div class="reaper-card">
            <div class="reaper-header">
              <span class="reaper-icon">💀</span>
              <h4>The Reaper</h4>
            </div>
            <p>The Reaper is an additional player who rolls <strong>twice per turn</strong> after the last player in the round. These rolls are added to the central counter.</p>
            <p>The Reaper appears after <strong>2 hours</strong>.</p>
            <div class="reaper-warning">
              ⚠️ When the Reaper arrives, the <strong>bleeding cap of 60 minutes is removed</strong> from all alive players.
            </div>
          </div>

          <!-- Horsemen -->
          <div class="horsemen-grid">
            <!-- Pestilence -->
            <div class="horseman-card pestilence">
              <div class="horseman-header">
                <span class="horseman-icon">🦠</span>
                <h4>Pestilence</h4>
                <span class="horseman-range">(1-25)</span>
              </div>
              <p>Upon each activation, each alive player is sanctioned with <strong>20 minutes bleeding effect</strong>.</p>
            </div>

            <!-- War -->
            <div class="horseman-card war">
              <div class="horseman-header">
                <span class="horseman-icon">⚔️</span>
                <h4>War</h4>
                <span class="horseman-range">(26-50)</span>
              </div>
              <p>The Reaper/servant rolls the 8-sided red die and adds 1. Each alive player rolls 6-sided die to beat it.</p>
              <ul>
                <li><strong>Win:</strong> Rewarded with 1 hour</li>
                <li><strong>Lose:</strong> Pay war cost of 2 items (job, title, collectables, assignment slips)</li>
                <li><strong>No items:</strong> Receive +1 heat</li>
                <li><strong>Tie:</strong> Reroll</li>
              </ul>
            </div>

            <!-- Famine -->
            <div class="horseman-card famine">
              <div class="horseman-header">
                <span class="horseman-icon">🍂</span>
                <h4>Famine</h4>
                <span class="horseman-range">(51-75)</span>
              </div>
              <p>During Famine, <strong>no income is earned from jobs</strong>. Time can still be earned through assignments, being a government leader, or transferring time.</p>
              <p>Upon each activation, each player must remove <strong>1.5 hours</strong> from their clock. At the end of Famine, all 7.5 hours are returned to each player.</p>
            </div>

            <!-- Death -->
            <div class="horseman-card death">
              <div class="horseman-header">
                <span class="horseman-icon">☠️</span>
                <h4>Death</h4>
                <span class="horseman-range">(76-100)</span>
              </div>
              <p>Upon each activation, all alive players must remove the number shown on the <strong>black die in hours</strong> from their clock.</p>
            </div>
          </div>

          <!-- Developer's Note -->
          <div class="dev-note">
            <h4>Developer's Note</h4>
            <p>With the introduction of the Reaper, it is deemed <strong>un-sportsmanship</strong> to deliberately kill yourself in this game. As an alive player, you have voting abilities, especially when governments change; you always have an important role to play.</p>
            <p>To increase game speed, you are also encouraged to plan your turn in advance with notes.</p>
          </div>
        </div>
      </div>

      <!-- Support Section -->
      <div class="help-section support-section">
        <div class="section-header">
          <span class="section-icon">📞</span>
          <h2>Need More Help?</h2>
        </div>
        <div class="section-content">
          <div class="support-card">
            <p class="support-text">If you're experiencing issues with the app or need assistance, please call our dedicated support hotline:</p>
            <div class="support-number">
              <span class="phone-icon">📱</span>
              <span class="phone-number">079G0 FUCK YOURSELF</span>
            </div>
            <p class="support-note">Our team of highly trained professionals are standing by 24/7 to not help you.</p>
          </div>
        </div>
      </div>

      <!-- Back Button -->
      <div class="help-footer">
        <button class="back-btn" @click="$router.push({ name: 'Home' })">
          ← Back to Leaderboard
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'HelpPage'
}
</script>

<style scoped>
.help-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0B0F19 0%, #1A1F2E 50%, #0B0F19 100%);
  padding: 40px 20px;
}

.help-container {
  max-width: 1000px;
  margin: 0 auto;
}

/* Header */
.help-header {
  text-align: center;
  margin-bottom: 48px;
}

.help-icon {
  font-size: 4rem;
  margin-bottom: 16px;
}

.help-title {
  font-size: 2.5rem;
  font-weight: 800;
  background: linear-gradient(135deg, #EAB308 0%, #FCD34D 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 12px 0;
}

.help-subtitle {
  color: #64748B;
  font-size: 1.1rem;
  margin: 0;
}

/* Sections */
.help-section {
  background: #1A1F2E;
  border-radius: 16px;
  border: 1px solid #22D3EE33;
  margin-bottom: 24px;
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 24px;
  background: #0B0F19;
  border-bottom: 1px solid #22D3EE22;
}

.section-icon {
  font-size: 1.5rem;
}

.section-header h2 {
  margin: 0;
  color: #F1F5F9;
  font-size: 1.3rem;
  font-weight: 700;
}

.section-content {
  padding: 24px;
}

/* Table of Contents */
.toc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.toc-link {
  display: block;
  padding: 12px 16px;
  background: #0B0F19;
  border: 1px solid #334155;
  border-radius: 8px;
  color: #94A3B8;
  text-decoration: none;
  transition: all 0.2s ease;
}

.toc-link:hover {
  border-color: #22D3EE;
  color: #22D3EE;
  transform: translateX(4px);
}

/* Keywords */
.keyword-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.keyword-item {
  display: flex;
  gap: 16px;
  padding: 12px 16px;
  background: #0B0F19;
  border-radius: 8px;
}

.keyword-term {
  color: #EAB308;
  font-weight: 700;
  min-width: 120px;
}

.keyword-def {
  color: #94A3B8;
}

/* Objective */
.objective-card {
  text-align: center;
  padding: 24px;
  background: linear-gradient(135deg, #0B0F1980, #1A1F2E80);
  border: 1px solid #EAB30844;
  border-radius: 12px;
}

.objective-main {
  font-size: 1.4rem;
  color: #F1F5F9;
  margin: 0 0 20px 0;
}

.objective-main strong {
  color: #EAB308;
}

.objective-notes p {
  color: #94A3B8;
  margin: 8px 0;
}

/* Step List */
.step-list {
  list-style: none;
  padding: 0;
  margin: 0;
  counter-reset: step-counter;
}

.step-list li {
  counter-increment: step-counter;
  position: relative;
  padding-left: 60px;
  margin-bottom: 24px;
}

.step-list li:last-child {
  margin-bottom: 0;
}

.step-list li::before {
  content: counter(step-counter);
  position: absolute;
  left: 0;
  top: 0;
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #22D3EE 0%, #0891B2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #0B0F19;
  font-weight: 800;
  font-size: 1.1rem;
}

.step-list li strong {
  color: #F1F5F9;
  font-size: 1.1rem;
  display: block;
  margin-bottom: 4px;
}

.step-list li p {
  color: #94A3B8;
  margin: 0;
  line-height: 1.5;
}

.highlight {
  color: #22D3EE;
  font-weight: 600;
}

/* Info Blocks */
.info-block {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #33415544;
}

.info-block:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.info-block h4 {
  color: #EAB308;
  margin: 0 0 12px 0;
  font-size: 1.1rem;
}

.info-block p {
  color: #94A3B8;
  margin: 8px 0;
  line-height: 1.6;
}

.info-block ul {
  color: #94A3B8;
  margin: 12px 0;
  padding-left: 24px;
}

.info-block li {
  margin-bottom: 8px;
}

.warning-text {
  color: #F59E0B !important;
}

.warning-box {
  background: #78350F22;
  border: 1px solid #F59E0B44;
  border-radius: 8px;
  padding: 16px;
  margin-top: 16px;
}

.warning-box p {
  color: #FCD34D;
  margin: 0;
}

/* Action List */
.action-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 8px;
  list-style: none;
  padding: 0;
  margin: 12px 0 0 0;
}

.action-list li {
  padding: 10px 16px;
  background: #0B0F19;
  border-radius: 6px;
  color: #94A3B8;
}

/* Jobs Section */
.faction {
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
}

.faction.finance { color: #22C55E; background: #22C55E22; }
.faction.public { color: #3B82F6; background: #3B82F622; }
.faction.illicit { color: #EF4444; background: #EF444422; }

.rules-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 20px 0;
}

.rule-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  background: #0B0F19;
  border-radius: 8px;
}

.rule-icon {
  font-size: 1.2rem;
  flex-shrink: 0;
}

.rule-item p {
  color: #94A3B8;
  margin: 0;
  line-height: 1.5;
}

.special-job {
  background: linear-gradient(135deg, #7C3AED22, #A855F722);
  border: 1px solid #A855F744;
  border-radius: 10px;
  padding: 16px;
  margin-top: 16px;
}

.special-job h4 {
  color: #A855F7;
  margin: 0 0 8px 0;
}

.special-job p {
  color: #C4B5FD;
  margin: 0;
}

/* Government Rules */
.gov-rules {
  background: #0B0F19;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 16px;
}

.gov-rules:last-child {
  margin-bottom: 0;
}

.gov-rules h4 {
  color: #EAB308;
  margin: 0 0 12px 0;
}

.gov-rules p {
  color: #94A3B8;
  margin: 8px 0;
  line-height: 1.5;
}

.gov-rules ul {
  color: #94A3B8;
  margin: 12px 0 0 0;
  padding-left: 20px;
}

.gov-rules li {
  margin-bottom: 6px;
}

/* Bleeding Section */
.bleed-info {
  text-align: center;
  margin-bottom: 24px;
}

.bleed-info p {
  color: #94A3B8;
  margin: 0 0 16px 0;
}

.bleed-cap {
  display: inline-flex;
  gap: 12px;
  padding: 12px 24px;
  background: linear-gradient(135deg, #DC262622, #EF444422);
  border: 1px solid #EF444444;
  border-radius: 8px;
}

.cap-label {
  color: #FCA5A5;
}

.cap-value {
  color: #EF4444;
  font-weight: 700;
}

.bonus-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: linear-gradient(135deg, #22C55E11, #10B98122);
  border: 1px solid #22C55E44;
  border-radius: 10px;
  margin-top: 20px;
}

.bonus-icon {
  font-size: 1.5rem;
}

.bonus-info p {
  color: #86EFAC;
  margin: 0;
}

/* Assignments */
.assignment-limits {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-bottom: 24px;
}

.limit-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px 32px;
  background: #0B0F19;
  border: 2px solid #22D3EE44;
  border-radius: 12px;
}

.limit-number {
  font-size: 2.5rem;
  font-weight: 800;
  color: #22D3EE;
}

.limit-label {
  color: #64748B;
  font-size: 0.9rem;
  text-align: center;
}

/* Titles */
.title-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.title-card {
  background: #0B0F19;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #334155;
}

.title-card.manager { border-color: #22C55E44; }
.title-card.senior { border-color: #3B82F644; }
.title-card.executive { border-color: #EAB30844; }

.title-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.title-icon {
  font-size: 1.5rem;
}

.title-header h4 {
  margin: 0;
  color: #F1F5F9;
  font-size: 1.2rem;
}

.title-pay {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  padding: 8px 12px;
  background: #1A1F2E;
  border-radius: 6px;
}

.pay-label {
  color: #64748B;
}

.pay-value {
  color: #22C55E;
  font-weight: 600;
}

.title-abilities h5,
.title-req h5 {
  color: #94A3B8;
  font-size: 0.85rem;
  margin: 0 0 8px 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.title-abilities ul {
  list-style: none;
  padding: 0;
  margin: 0 0 16px 0;
}

.title-abilities li {
  color: #94A3B8;
  padding: 4px 0;
  font-size: 0.9rem;
}

.title-abilities li::before {
  content: "✓ ";
  color: #22D3EE;
}

.title-req p {
  color: #94A3B8;
  margin: 0;
  font-size: 0.9rem;
}

.executive-note {
  background: #78350F22;
  border: 1px solid #F59E0B44;
  border-radius: 8px;
  padding: 16px;
}

.executive-note p {
  color: #FCD34D;
  margin: 8px 0;
  font-size: 0.95rem;
}

.executive-note p:first-child {
  margin-top: 0;
}

.executive-note p:last-child {
  margin-bottom: 0;
}

/* Court */
.court-info {
  text-align: center;
}

.court-info > p {
  color: #F1F5F9;
  font-size: 1.1rem;
  margin: 0 0 20px 0;
}

.judge-rule {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: #0B0F19;
  border-radius: 10px;
  text-align: left;
}

.judge-icon {
  font-size: 1.5rem;
}

.judge-rule p {
  color: #94A3B8;
  margin: 0;
  line-height: 1.5;
}

/* Tiles Grid */
.tiles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.tile-card {
  background: #0B0F19;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 20px;
}

.tile-card.wide {
  grid-column: span 2;
}

@media (max-width: 700px) {
  .tile-card.wide {
    grid-column: span 1;
  }
}

.tile-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  margin-bottom: 12px;
}

.tile-icon.start { background: #22C55E22; }
.tile-icon.collectables { background: #A855F722; }
.tile-icon.assignment { background: #3B82F622; }
.tile-icon.scenario { background: #EC489922; }
.tile-icon.job { background: #EAB30822; }
.tile-icon.virus { background: #EF444422; }
.tile-icon.senate { background: #22D3EE22; }
.tile-icon.hospital { background: #F4728022; }
.tile-icon.goto { background: #6366F122; }
.tile-icon.market { background: #78716C22; }
.tile-icon.jail { background: #64748B22; }

.tile-card h4 {
  color: #F1F5F9;
  margin: 0 0 8px 0;
  font-size: 1.1rem;
}

.tile-card p {
  color: #94A3B8;
  margin: 8px 0;
  font-size: 0.9rem;
  line-height: 1.5;
}

.tile-card ul {
  color: #94A3B8;
  margin: 8px 0;
  padding-left: 20px;
  font-size: 0.9rem;
}

.tile-card li {
  margin-bottom: 4px;
}

.tile-note {
  color: #64748B !important;
  font-style: italic;
  font-size: 0.85rem !important;
}

/* Death Section */
.death-section {
  border-color: #DC262644;
}

.death-section .section-header {
  background: linear-gradient(135deg, #0B0F19, #1C100F);
}

.death-info {
  text-align: center;
  margin-bottom: 24px;
}

.death-main {
  font-size: 1.3rem;
  color: #FCA5A5;
  margin: 0 0 12px 0;
}

.death-main strong {
  color: #EF4444;
}

.death-info p {
  color: #94A3B8;
  margin: 0;
}

.loot-rules {
  background: #0B0F19;
  border-radius: 10px;
  padding: 20px;
}

.loot-rules h4 {
  color: #EAB308;
  margin: 0 0 12px 0;
}

.loot-rules ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.loot-rules li {
  color: #94A3B8;
  padding: 8px 0;
  border-bottom: 1px solid #33415544;
}

.loot-rules li:last-child {
  border-bottom: none;
}

/* End Game Section */
.endgame-section {
  border-color: #7C3AED44;
}

.endgame-section .section-header {
  background: linear-gradient(135deg, #0B0F19, #1A0F2E);
}

.horseman-name {
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
}

.horseman-name.pestilence { color: #22C55E; background: #22C55E22; }
.horseman-name.war { color: #EF4444; background: #EF444422; }
.horseman-name.famine { color: #F59E0B; background: #F59E0B22; }
.horseman-name.death { color: #A855F7; background: #A855F722; }

/* Reaper Card */
.reaper-card {
  background: linear-gradient(135deg, #0B0F19, #1A0F2E);
  border: 2px solid #A855F7;
  border-radius: 12px;
  padding: 24px;
  margin: 24px 0;
}

.reaper-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.reaper-icon {
  font-size: 2rem;
}

.reaper-header h4 {
  margin: 0;
  color: #A855F7;
  font-size: 1.4rem;
}

.reaper-card > p {
  color: #C4B5FD;
  margin: 8px 0;
  line-height: 1.5;
}

.reaper-warning {
  margin-top: 16px;
  padding: 12px 16px;
  background: #EF444422;
  border: 1px solid #EF444444;
  border-radius: 8px;
  color: #FCA5A5;
  font-weight: 500;
}

/* Horsemen Grid */
.horsemen-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.horseman-card {
  background: #0B0F19;
  border-radius: 12px;
  padding: 20px;
  border: 2px solid;
}

.horseman-card.pestilence { border-color: #22C55E44; }
.horseman-card.war { border-color: #EF444444; }
.horseman-card.famine { border-color: #F59E0B44; }
.horseman-card.death { border-color: #A855F744; }

.horseman-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.horseman-icon {
  font-size: 1.5rem;
}

.horseman-header h4 {
  margin: 0;
  flex: 1;
}

.horseman-card.pestilence h4 { color: #22C55E; }
.horseman-card.war h4 { color: #EF4444; }
.horseman-card.famine h4 { color: #F59E0B; }
.horseman-card.death h4 { color: #A855F7; }

.horseman-range {
  color: #64748B;
  font-size: 0.85rem;
}

.horseman-card > p {
  color: #94A3B8;
  margin: 8px 0;
  font-size: 0.9rem;
  line-height: 1.5;
}

.horseman-card ul {
  list-style: none;
  padding: 0;
  margin: 12px 0 0 0;
}

.horseman-card li {
  color: #94A3B8;
  padding: 4px 0;
  font-size: 0.85rem;
}

/* Developer Note */
.dev-note {
  background: #1E293B;
  border-left: 4px solid #22D3EE;
  border-radius: 0 8px 8px 0;
  padding: 20px;
}

.dev-note h4 {
  color: #22D3EE;
  margin: 0 0 12px 0;
}

.dev-note p {
  color: #94A3B8;
  margin: 8px 0;
  line-height: 1.5;
}

/* Support Section */
.support-section {
  border-color: #EAB30844;
}

.support-card {
  text-align: center;
  padding: 20px;
}

.support-text {
  color: #94A3B8;
  font-size: 1rem;
  margin: 0 0 24px 0;
}

.support-number {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  padding: 16px 32px;
  background: linear-gradient(135deg, #EAB308 0%, #CA8A04 100%);
  border-radius: 12px;
  margin-bottom: 16px;
}

.phone-icon {
  font-size: 1.5rem;
}

.phone-number {
  color: #0B0F19;
  font-size: 1.4rem;
  font-weight: 800;
  letter-spacing: 1px;
}

.support-note {
  color: #64748B;
  font-size: 0.9rem;
  font-style: italic;
  margin: 0;
}

/* Footer */
.help-footer {
  text-align: center;
  margin-top: 32px;
}

.back-btn {
  padding: 14px 32px;
  background: transparent;
  border: 2px solid #22D3EE;
  border-radius: 12px;
  color: #22D3EE;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.back-btn:hover {
  background: #22D3EE22;
  transform: translateY(-2px);
}

/* Responsive */
@media (max-width: 600px) {
  .help-title {
    font-size: 2rem;
  }
  
  .toc-grid {
    grid-template-columns: 1fr;
  }
  
  .keyword-item {
    flex-direction: column;
    gap: 4px;
  }
  
  .keyword-term {
    min-width: auto;
  }
  
  .step-list li {
    padding-left: 50px;
  }
  
  .step-list li::before {
    width: 36px;
    height: 36px;
    font-size: 1rem;
  }
  
  .assignment-limits {
    flex-direction: column;
    gap: 16px;
  }
  
  .title-cards {
    grid-template-columns: 1fr;
  }
  
  .tiles-grid {
    grid-template-columns: 1fr;
  }
  
  .horsemen-grid {
    grid-template-columns: 1fr;
  }
}
</style>
