import { test } from 'node:test';
import assert from 'node:assert/strict';
import { CLEARANCE_LABELS } from '../src/clearance.js';
import { countdown, scoreBand, TIERS } from '../src/domain.js';
import { newQuizId } from '../src/api.js';

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
