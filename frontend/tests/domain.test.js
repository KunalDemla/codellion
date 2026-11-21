import { test } from 'node:test';
import assert from 'node:assert/strict';
import { CLEARANCE_LABELS } from '../src/clearance.js';
import { countdown, scoreBand, TIERS } from '../src/domain.js';
import { createQuizApi, newQuizId } from '../src/api.js';

test('clearance labels are distinct from answer tiers and cover all score boundaries', () => {
  const bounds = [0, 150, 151, 250, 251, 350, 351, 449, 450, 700];
  assert.deepEqual(bounds.map(score => CLEARANCE_LABELS[scoreBand(score)]), [
    'Visitor', 'Visitor', 'Member', 'Member', 'Operator', 'Operator', 'Maintainer', 'Maintainer', 'Admin', 'Admin',
  ]);
  assert.ok(Object.values(TIERS).every(tier => !Object.values(CLEARANCE_LABELS).includes(tier.label)));
});

test('the countdown rounds up and stops at zero', () => {
  assert.equal(countdown(3_661_001), '01:01:02');
  assert.equal(countdown(-1000), '00:00:00');
});

test('guest and run IDs are v4 UUIDs without requiring a secure context', () => {
  const ids = Array.from({ length: 8 }, () => newQuizId());
  for (const id of ids) assert.match(id, /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
  assert.equal(new Set(ids).size, ids.length);
});

test('the player reset clears old progress and keeps runs started after the reset', async () => {
  const today = '2026-11-21';
  const serverTime = today + 'T14:00:00Z';
  const oldKey = 'root-access:codellion:v1:/api';
  const oldId = newQuizId();
  const settings = 'root-access/settings/v1';
  const entries = new Map([
    [oldKey, JSON.stringify({ playerId: oldId, runs: { [today]: { started: true, phase: 'completed' } } })],
    [settings, '{"sound":false}'],
  ]);
  const storage = {
    getItem: key => entries.get(key),
    setItem: (key, value) => entries.set(key, value),
    removeItem: key => entries.delete(key),
  };
  let playerId;
  const fetcher = async (url, options) => {
    if (url === '/api/today') return Response.json({
      date: today, serverTime, resetAt: '2026-11-22T00:00:00Z',
      questions: [{ promptId: 'p1', prompt: 'Name a programming language.' }],
    });
    assert.equal(url, '/api/games');
    ({ playerId } = JSON.parse(options.body));
    return Response.json({});
  };
  const config = { baseUrl: '/api', timeoutMs: 5000, storage, fetcher, clock: () => Date.parse(serverTime) };
  const api = createQuizApi(config);
  assert.equal((await api.daily()).run, null);
  assert.equal(entries.has(oldKey), false);
  assert.equal(entries.get(settings), '{"sound":false}');
  const { run } = await api.start(today);
  assert.notEqual(playerId, oldId);
  assert.equal((await createQuizApi(config).daily()).run.id, run.id);
});
