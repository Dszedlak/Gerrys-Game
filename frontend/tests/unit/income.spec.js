/**
 * Tests for useIncome - the single source of truth for per-turn income.
 *
 * These mirror backend/app/websocket/sockets.py -> balanceChange().
 * If one side changes, these tests should fail.
 */

import { describe, it, expect } from '@jest/globals';
import { useIncome } from '@/composables/useIncome';

const { computeIncomeBreakdown, formatMinutes } = useIncome();

const JOBS = [
  { id: 0, tier: 0, name: 'Unemployed' },
  { id: 7, tier: 1, name: 'Teacher' },
  { id: 14, tier: 2, name: 'Accountant' },
  { id: 15, tier: 3, name: 'CFO' },
  { id: 22, tier: 3, name: 'Chancellor' },
  { id: 9, tier: 3, name: 'Doctor' },
  { id: 10, tier: 3, name: 'Charity Commissioner' }
];

function player(overrides = {}) {
  return { user_id: 1, job_name: 'Unemployed', perk: null, bleed: 0, ...overrides };
}

const net = (p, ctx = {}) =>
  computeIncomeBreakdown(p, { jobs: JOBS, ...ctx }).net;

describe('useIncome - job tiers', () => {
  it('pays 10 minutes per job tier', () => {
    expect(net(player({ job_name: 'Unemployed' }))).toBe(0);
    expect(net(player({ job_name: 'Teacher' }))).toBe(10);
    expect(net(player({ job_name: 'Accountant' }))).toBe(20);
    expect(net(player({ job_name: 'CFO' }))).toBe(30);
  });

  it('treats an unknown job as no income rather than throwing', () => {
    expect(net(player({ job_name: 'Nonexistent Job' }))).toBe(0);
  });
});

describe('useIncome - titles', () => {
  it('adds the title bonus on top of job income', () => {
    expect(net(player({ job_name: 'CFO', perk: 'Manager' }))).toBe(40);
    expect(net(player({ job_name: 'CFO', perk: 'Senior' }))).toBe(50);
    expect(net(player({ job_name: 'CFO', perk: 'Executive' }))).toBe(60);
  });
});

describe('useIncome - bleed', () => {
  it('deducts 10 minutes per bleed counter', () => {
    expect(net(player({ job_name: 'CFO', bleed: 1 }))).toBe(20);
    expect(net(player({ job_name: 'CFO', bleed: 3 }))).toBe(0);
  });

  it('can go negative', () => {
    expect(net(player({ job_name: 'Teacher', bleed: 4 }))).toBe(-30);
  });
});

describe('useIncome - government', () => {
  const communism = {
    type: 'Communism',
    members: [
      { user_id: 1, role: 'politburo' },
      { user_id: 2, role: 'politburo' }
    ]
  };

  it('gives politburo members +10', () => {
    expect(net(player({ user_id: 1, job_name: 'CFO' }), { government: communism })).toBe(40);
  });

  it('charges peasants -20', () => {
    expect(net(player({ user_id: 3, job_name: 'CFO' }), { government: communism })).toBe(10);
  });

  it('gives the dictator +10 and nobody else a bonus', () => {
    const dictatorship = { type: 'Dictatorship', members: [{ user_id: 2, role: 'dictator' }] };
    expect(net(player({ user_id: 2, job_name: 'CFO' }), { government: dictatorship })).toBe(40);
    expect(net(player({ user_id: 3, job_name: 'CFO' }), { government: dictatorship })).toBe(30);
  });

  it('applies no income effect under Democracy or Republic', () => {
    const republic = {
      type: 'Republic',
      members: [
        { user_id: 1, role: 'head_of_state' },
        { user_id: 2, role: 'advisor' }
      ]
    };
    expect(net(player({ user_id: 1, job_name: 'CFO' }), { government: republic })).toBe(30);
    expect(net(player({ user_id: 1, job_name: 'CFO' }), { government: { type: 'Democracy' } })).toBe(30);
  });
});

describe('useIncome - Charity Commissioner', () => {
  const allPlayers = [
    { user_id: 1, job_name: 'CFO' },
    { user_id: 2, job_name: 'Charity Commissioner' }
  ];

  it('takes 20 minutes from every opposition player', () => {
    expect(net(player({ user_id: 1, job_name: 'CFO' }), { allPlayers })).toBe(10);
  });

  it('does not penalise the Charity Commissioner themselves', () => {
    expect(net(player({ user_id: 2, job_name: 'Charity Commissioner' }), { allPlayers })).toBe(30);
  });

  it('does nothing when no Charity Commissioner is in the game', () => {
    const noCommissioner = [
      { user_id: 1, job_name: 'CFO' },
      { user_id: 2, job_name: 'Teacher' }
    ];
    expect(net(player({ user_id: 1, job_name: 'CFO' }), { allPlayers: noCommissioner })).toBe(30);
  });
});

describe('useIncome - breakdown lines', () => {
  it('itemises every contributing effect', () => {
    const { lines, net: total } = computeIncomeBreakdown(
      player({ user_id: 1, job_name: 'CFO', perk: 'Manager', bleed: 2 }),
      {
        jobs: JOBS,
        government: { type: 'Communism', members: [{ user_id: 9, role: 'politburo' }] },
        allPlayers: [
          { user_id: 1, job_name: 'CFO' },
          { user_id: 2, job_name: 'Charity Commissioner' }
        ]
      }
    );

    const labels = lines.map(l => l.label);
    expect(labels).toEqual([
      'Job — CFO (Tier 3)',
      'Title — Manager',
      'Government — Communism (peasant)',
      'Charity Commissioner in game',
      'Bleed ×2'
    ]);

    // 30 + 10 - 20 - 20 - 20
    expect(total).toBe(-20);
    expect(lines.reduce((s, l) => s + l.minutes, 0)).toBe(total);
  });

  it('omits effects that do not apply', () => {
    const { lines } = computeIncomeBreakdown(player({ job_name: 'Teacher' }), { jobs: JOBS });
    expect(lines.map(l => l.label)).toEqual(['Job — Teacher (Tier 1)']);
  });

  it('returns an empty breakdown for a missing player', () => {
    expect(computeIncomeBreakdown(null, { jobs: JOBS })).toEqual({ lines: [], net: 0 });
  });
});

describe('useIncome - formatting', () => {
  it('formats signed hours and minutes', () => {
    expect(formatMinutes(0)).toBe('+00:00');
    expect(formatMinutes(40)).toBe('+00:40');
    expect(formatMinutes(90)).toBe('+01:30');
    expect(formatMinutes(-20)).toBe('-00:20');
    expect(formatMinutes(-150)).toBe('-02:30');
  });
});
