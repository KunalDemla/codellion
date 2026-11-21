import { RULES, scoreBand, TIERS } from './domain.js';

const iso = time => new Date(time).toISOString();
const problem = (message, code) => Object.assign(new Error(message), { code });
const promptShape = ({ promptId, prompt, category }) => ({ id: promptId, text: prompt, topic: category?.name });
const UTC_DAY_MS = 86_400_000;

function readJson(storage, key, fallback) {
  const value = storage.getItem(key);
  return value ? JSON.parse(value) : fallback;
}

export function newQuizId() {
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, byte => byte.toString(16).padStart(2, '0')).join('');
  return [hex.slice(0, 8), hex.slice(8, 12), hex.slice(12, 16), hex.slice(16, 20), hex.slice(20)].join('-');
}

function stats(history, dayNumber) {
  const played = history.length;
  const days = new Set(history.map(run => run.dayNumber));
  let day = days.has(dayNumber) ? dayNumber : dayNumber - 1;
  let currentStreak = 0;
  while (days.has(day--)) currentStreak++;
  return {
    played,
    currentStreak,
    averageScore: played ? history.reduce((sum, run) => sum + run.score, 0) / played : 0,
    bestScore: played ? Math.max(...history.map(run => run.score)) : 0,
  };
}

export function createQuizApi({
  baseUrl, timeoutMs, answerReviewPath, storage = localStorage,
  clock = Date.now, fetcher = fetch,
}) {
  const base = baseUrl.trim().replace(/\/+$/, '');
  const storageKey = 'root-access:codellion:v1:' + base;
  const read = () => readJson(storage, storageKey, { playerId: null, runs: {} });
  const write = state => storage.setItem(storageKey, JSON.stringify(state));
  let daily;
  let offset = 0;
  const now = () => clock() + offset;
  const snapshot = run => ({ run, serverTime: iso(now()) });

  function player() {
    const state = read();
    if (!state.playerId) {
      state.playerId = newQuizId();
      write(state);
    }
    return state.playerId;
  }

  function getRun(id) {
    const run = Object.values(read().runs).find(candidate => candidate.id === id && candidate.started);
    if (!run) throw problem('Run not found.', 'NOT_FOUND');
    return run;
  }

  function storeRun(run) {
    const state = read();
    const previous = state.runs[run.dailyId];
    run.version = Math.max(run.version, previous?.version || 0) + 1;
    state.runs[run.dailyId] = run;
    write(state);
  }

  async function request(path, body) {
    let response;
    try {
      response = await fetcher(base + path, {
        ...(body === undefined ? {} : {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
        }),
        signal: AbortSignal.timeout(timeoutMs),
      });
    } catch {
      throw new Error('Could not reach the quiz API. Check the connection and try again.');
    }
    const data = await response.json().catch(() => null);
    if (!response.ok || !data) {
      const serverCode = data?.error?.code;
      const code = ['daily_closed', 'not_current_daily_challenge'].includes(serverCode) ? 'DAILY_CLOSED' : serverCode;
      throw problem(data?.error?.message || 'The quiz API returned an unexpected response.', code);
    }
    return data;
  }

  function openRound(run, number) {
    const starts = now() + run.rules.previewSeconds * 1000;
    run.phase = 'preview';
    run.currentRound = {
      number, prompt: run.prompts[number - 1],
      answerStartsAt: iso(starts), answerEndsAt: iso(starts + run.rules.answerSeconds * 1000),
      draft: { text: '', revision: 0 }, correction: null, pending: null,
    };
    storeRun(run);
  }

  function settle(run, text, reply, trigger) {
    const round = run.currentRound;
    const match = reply?.accepted ? {
      label: reply.answer,
      tier: Object.keys(TIERS).find(key => TIERS[key].points === reply.score),
      note: reply.quip || null,
    } : null;
    if (match && !match.tier) throw new Error('The quiz API returned an unknown score tier.');
    run.rounds.push({
      number: round.number, prompt: round.prompt, submittedText: text || null, match,
      points: match ? reply.score : 0, receipt: match ? reply.receipt : null,
      outcome: match ? 'accepted' : text ? 'invalid' : 'unanswered', trigger,
    });
    run.score = run.rounds.reduce((total, entry) => total + entry.points, 0);
    run.currentRound = null;
    run.phase = round.number === run.rules.roundCount ? 'ready_to_surface' : 'round_reveal';
    storeRun(run);
  }

  async function submit(run, text, previewCorrections) {
    const body = { date: run.dailyId, playerId: player(), runId: run.id, promptId: run.currentRound.prompt.id, answer: text, previewCorrection: false };
    const reply = await request('/submit', body);
    if (reply.correction && !previewCorrections) return request('/submit', { ...body, answer: reply.correction });
    return reply;
  }

  async function reconcile(run) {
    if (['completed', 'ready_to_surface', 'expired'].includes(run.phase)) return run;
    if (now() >= Date.parse(run.resetsAt)) {
      run.phase = 'expired';
      run.currentRound = null;
      storeRun(run);
      return run;
    }
    const round = run.currentRound;
    if (!round) return run;
    if (now() >= Date.parse(round.answerEndsAt)) {
      const latest = round.draft.text.trim();
      const text = latest || round.pending?.text || '';
      const reply = text ? await submit(run, text, false) : null;
      const fresh = getRun(run.id);
      if (fresh.currentRound?.number === round.number) settle(fresh, text, reply, 'deadline');
      return fresh;
    } else if (now() >= Date.parse(round.answerStartsAt)) {
      run.phase = 'answering';
    }
    return run;
  }

  function editable(run, number) {
    const round = run.currentRound;
    if (now() >= Date.parse(run.resetsAt)) throw problem('The daily run has reset.', 'DAILY_CLOSED');
    if (round?.number !== number || now() < Date.parse(round.answerStartsAt)
      || now() >= Date.parse(round.answerEndsAt)) {
      throw problem('This round is no longer taking answers.', 'ROUND_NOT_ACTIVE');
    }
    return round;
  }

  function saveEdit(run, round, text, revision) {
    if (revision < round.draft.revision || (revision === round.draft.revision && text !== round.draft.text)) {
      throw problem('A newer draft is already saved.', 'STALE_DRAFT');
    }
    if (revision > round.draft.revision) {
      round.draft = { text, revision };
      round.correction = null;
      storeRun(run);
    }
  }

  return {
    canReview: Boolean(answerReviewPath),
    async daily() {
      const data = await request('/today');
      offset = Date.parse(data.serverTime) - clock();
      daily = {
        dailyId: data.date, dayNumber: data.dayNumber, resetsAt: data.resetAt, opensAt: data.date + 'T00:00:00Z',
        rules: { ...RULES, ...data.rules }, prompts: data.questions.map(promptShape),
      };
      const previous = read().runs[daily.dailyId];
      const run = previous?.started ? await reconcile(previous) : null;
      return { ...daily, ...snapshot(run) };
    },
    async start(date) {
      if (daily?.dailyId !== date) throw problem('Reload to open the current daily.', 'DAILY_CLOSED');
      const previous = read().runs[date];
      if (previous?.started) return snapshot(await reconcile(previous));
      const run = previous || {
        id: newQuizId(), ...daily, version: 0, rounds: [], score: 0, completedAt: null, started: false,
      };
      if (!previous) storeRun(run);
      await request('/games', { date, playerId: player(), runId: run.id });
      const saved = read().runs[date];
      if (saved.started) return snapshot(await reconcile(saved));
      run.started = true;
      openRound(run, 1);
      return snapshot(run);
    },
    async run(id) {
      return snapshot(await reconcile(getRun(id)));
    },
    async saveDraft(id, number, { text, revision }) {
      const run = getRun(id);
      saveEdit(run, editable(run, number), text, revision);
      return snapshot(run);
    },
    async guess(id, number, { text, draftRevision, previewCorrections }) {
      const run = getRun(id);
      const round = editable(run, number);
      saveEdit(run, round, text, draftRevision);
      round.pending = { text };
      storeRun(run);
      const reply = await submit(run, text, previewCorrections);
      // Another tab may already have opened the next prompt during the request.
      const fresh = getRun(id);
      if (fresh.currentRound?.number !== number) return { outcome: 'accepted', ...snapshot(fresh) };
      const active = fresh.currentRound;
      active.pending = null;
      if (reply.accepted) {
        settle(fresh, text, reply, 'explicit');
        return { outcome: 'accepted', ...snapshot(fresh) };
      }
      if (reply.correction && active.draft.revision === draftRevision) {
        active.draft.text = reply.correction;
        active.correction = { originalText: text, canonicalText: reply.correction };
      }
      storeRun(fresh);
      return { outcome: reply.correction ? 'correction_required' : 'rejected', ...snapshot(fresh) };
    },
    async advance(id, number) {
      const run = await reconcile(getRun(id));
      if (run.phase === 'completed' || run.rounds.length > number || run.currentRound?.number > number) return snapshot(run);
      if (run.phase === 'expired') throw problem('The daily run has reset.', 'DAILY_CLOSED');
      if (number !== run.rounds.length || !['round_reveal', 'ready_to_surface'].includes(run.phase)) {
        throw problem('This round is still active.', 'ROUND_NOT_RESOLVED');
      }
      if (number < run.rules.roundCount) {
        openRound(run, number + 1);
        return snapshot(run);
      }
      const summary = await request('/today/complete', {
        date: run.dailyId, playerId: player(), runId: run.id, record: true, score: run.score,
        receipts: run.rounds.map(round => round.receipt),
      });
      run.phase = 'completed';
      run.completedAt = iso(now());
      run.summary = summary;
      storeRun(run);
      return snapshot(run);
    },
    async results(id) {
      const run = getRun(id);
      const history = Object.values(read().runs).filter(previous => previous.phase === 'completed');
      return {
        dayNumber: run.dayNumber, score: run.score, band: scoreBand(run.score), rounds: run.rounds,
        standings: { sampleSize: run.summary.sample, betterThanPercent: run.summary.betterThan, histogram: run.summary.dist },
        logbook: stats(history, daily?.dayNumber ?? run.dayNumber),
        nextDailyOpensAt: now() < Date.parse(run.resetsAt) ? run.resetsAt : iso(Date.parse(run.resetsAt) + UTC_DAY_MS),
      };
    },
    answers(id, number, params) {
      const query = new URLSearchParams();
      for (const [key, value] of Object.entries(params)) if (value) query.set(key, value);
      const path = answerReviewPath.replace('{runId}', encodeURIComponent(id)).replace('{roundNumber}', String(number));
      return request(path + (query.size ? '?' + query : ''));
    },
  };
}
