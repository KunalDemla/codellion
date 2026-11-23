import { useCallback, useEffect, useRef, useState } from 'react';
import { createQuizApi } from './api.js';

const timeout = Number(import.meta.env.VITE_API_REQUEST_TIMEOUT_MS);
export const api = createQuizApi({
  baseUrl: import.meta.env.VITE_API_BASE_URL || '/api',
  timeoutMs: Number.isSafeInteger(timeout) && timeout > 0 && timeout <= 120_000 ? timeout : 8000,
  answerReviewPath: import.meta.env.VITE_ANSWER_REVIEW_PATH || undefined,
});
const conflict = new Set(['ROUND_NOT_ACTIVE', 'ROUND_NOT_RESOLVED', 'DAILY_CLOSED', 'STALE_DRAFT']);
const inputKey = run => run?.currentRound ? run.id + '/' + run.currentRound.number : null;

export function useDaily(preferences) {
  const [daily, setDaily] = useState(null);
  const [run, setRun] = useState(null);
  const [draft, setDraft] = useState({ text: '', revision: 0, key: null });
  const [now, setNow] = useState(() => Date.now());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [rejected, setRejected] = useState(false);
  const [action, setAction] = useState(0);
  const anchor = useRef({ time: Date.now(), local: performance.now() });
  const current = useRef(null);
  const draftRef = useRef(draft);
  const locked = useRef(false);
  const lastSnapshotTime = useRef(0);

  const currentTime = useCallback(() => anchor.current.time + performance.now() - anchor.current.local, []);
  const updateDraft = useCallback(value => {
    draftRef.current = value;
    setDraft(value);
  }, []);
  const apply = useCallback((payload, { replace = false, forceDraft = false } = {}) => {
    const previous = current.current;
    const incoming = payload.run;
    const time = Date.parse(payload.serverTime);
    if (!replace && previous && incoming && (previous.id !== incoming.id
      || previous.version > incoming.version
      || (previous.version === incoming.version && time < lastSnapshotTime.current))) return;
    const key = inputKey(incoming);
    const previousDraft = draftRef.current;
    const serverDraft = incoming?.currentRound?.draft || { text: '', revision: 0 };
    if (previousDraft.key !== key || forceDraft || previousDraft.revision <= serverDraft.revision) {
      updateDraft({ ...serverDraft, key });
    }
    if (previousDraft.key !== key) setRejected(false);
    anchor.current = { time, local: performance.now() };
    lastSnapshotTime.current = time;
    current.current = incoming;
    setRun(incoming);
    setNow(currentTime());
  }, [currentTime, updateDraft]);

  const load = useCallback(async () => {
    if (locked.current) return;
    locked.current = true;
    setBusy(true);
    setError('');
    try {
      const payload = await api.daily();
      setDaily(payload);
      apply(payload, { replace: true });
    } catch (cause) {
      setError(cause.message);
    } finally {
      locked.current = false;
      setBusy(false);
    }
  }, [apply]);

  const refresh = useCallback(async (id, forceDraft = false) => {
    const payload = await api.run(id);
    if (current.current?.id === id) apply(payload, { forceDraft });
  }, [apply]);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => {
    const timer = setInterval(() => setNow(currentTime()), 100);
    return () => clearInterval(timer);
  }, [currentTime]);

  const deadline = run?.currentRound ? Date.parse(run.currentRound.answerEndsAt) : null;
  const due = deadline !== null && now >= Math.min(deadline, Date.parse(run.resetsAt));
  useEffect(() => {
    if (due && !busy) void refresh(run.id).catch(cause => setError(cause.message));
  }, [due, run?.id, busy, action, refresh]);

  const resetDue = daily && now >= Date.parse(daily.resetsAt)
    && (!run || !['ready_to_surface', 'round_reveal', 'completed'].includes(run.phase));
  useEffect(() => {
    if (resetDue) void load();
  }, [resetDue, load]);

  async function transact(task) {
    if (locked.current) return;
    locked.current = true;
    setBusy(true);
    setError('');
    try {
      await task();
    } catch (cause) {
      if (cause.code === 'DAILY_CLOSED') {
        locked.current = false;
        await load();
      } else if (conflict.has(cause.code) && current.current) {
        const forceDraft = cause.code === 'STALE_DRAFT';
        await refresh(current.current.id, forceDraft).catch(problem => setError(problem.message));
        if (forceDraft) setError('Another tab updated the draft. The latest answer is loaded.');
      } else {
        setError(cause.message);
      }
    } finally {
      locked.current = false;
      setBusy(false);
    }
  }

  async function save(activeRun, value) {
    try {
      const saved = await api.saveDraft(activeRun.id, activeRun.currentRound.number, {
        text: value.text, revision: value.revision,
      });
      if (current.current?.id === activeRun.id) apply(saved);
    } catch (cause) {
      const latest = draftRef.current;
      if (latest.key !== value.key || latest.revision !== value.revision || locked.current) return;
      if (conflict.has(cause.code)) {
        await refresh(activeRun.id, cause.code === 'STALE_DRAFT').catch(problem => setError(problem.message));
      } else {
        setError('Draft could not be saved. You can still submit your answer.');
      }
    }
  }

  function edit(text) {
    const activeRun = current.current;
    if (!activeRun?.currentRound) return;
    const value = { text, revision: draftRef.current.revision + 1, key: inputKey(activeRun) };
    updateDraft(value);
    setRejected(false);
    setError('');
    void save(activeRun, value);
  }

  function submit() {
    const activeRun = current.current;
    const activeDraft = draftRef.current;
    if (!activeRun?.currentRound || !activeDraft.text.trim()) return;
    void transact(async () => {
      const number = activeRun.currentRound.number;
      const body = {
        text: activeDraft.text, draftRevision: activeDraft.revision, previewCorrections: preferences.corrections,
      };
      const reply = await api.guess(activeRun.id, number, body);
      apply(reply);
      if (reply.outcome === 'rejected' && current.current?.currentRound?.number === number) {
        if (preferences.clearRejected) edit('');
        setRejected(true);
      }
    });
  }

  function next() {
    const activeRun = current.current;
    const number = activeRun?.rounds.at(-1)?.number;
    if (!number) return;
    void transact(async () => {
      const reply = await api.advance(activeRun.id, number);
      apply(reply);
    });
  }

  return {
    daily, run, now, busy, error, rejected, draft,
    edit, submit, next, load,
    start: () => void transact(async () => apply(await api.start(daily.dailyId), { replace: true })),
    retry: () => {
      setError('');
      if (due) setAction(value => value + 1);
      else if (run) void refresh(run.id).catch(cause => setError(cause.message));
      else void load();
    },
  };
}
