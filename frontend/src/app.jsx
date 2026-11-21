import React, { useCallback, useEffect, useRef, useState } from 'react';
import { ArrowRight, Braces, ChevronDown, CircleHelp, Clock3, Code2, CornerDownLeft, KeyRound, Layers3, Settings2, Terminal, X } from 'lucide-react';
import { countdown, scoreBand, TIERS } from './domain.js';
import { CLEARANCE_LABELS } from './clearance.js';
import { useDaily } from './use-daily.js';
import Results from './results.jsx';
import AccessSequence from './access-sequence.jsx';

const defaults = { corrections: true, clearRejected: false, reducedMotion: false, shareLink: false };
const preferenceKey = 'root-access/settings/v1';
const pad = value => String(value).padStart(2, '0');
const tierEntries = Object.entries(TIERS).reverse();

function preferencesFromStorage() {
  try {
    return { ...defaults, ...JSON.parse(localStorage.getItem(preferenceKey) || '{}') };
  } catch {
    return defaults;
  }
}

function Header({ open }) {
  return (
    <header className="site-header">
      <div className="header-inner">
        <div className="wordmark"><span className="brand-icon"><Terminal size={20} /></span> ROOT<span>ACCESS</span></div>
        <nav aria-label="Quiz tools">
          <button className="quiet-button help-button" onClick={() => open('rules')}><CircleHelp size={17} /> <span>How to play</span></button>
          <button className="icon-button" aria-label="Settings" onClick={() => open('settings')}><Settings2 size={19} /></button>
        </nav>
      </div>
    </header>
  );
}

function Dialog({ kind, close, preferences, change }) {
  const ref = useRef(null);
  useEffect(() => { ref.current.showModal(); }, []);
  const options = [
    ['corrections', 'Preview answer corrections', 'Confirm a suggested spelling before it scores.'],
    ['clearRejected', 'Clear rejected answers', 'Empty the field after an unsuccessful guess.'],
    ['reducedMotion', 'Reduce motion', 'Keep interface transitions still.'],
    ['shareLink', 'Include a link in shared results', 'Append the quiz URL to your copied score.'],
  ];
  return (
    <dialog ref={ref} onClose={close} aria-labelledby="dialog-heading">
      <div className="dialog-head">
        <h2 id="dialog-heading">{kind === 'rules' ? 'How to play' : 'Settings'}</h2>
        <button className="icon-button" onClick={() => ref.current.close()} aria-label="Close"><X size={20} /></button>
      </div>
      {kind === 'rules' ? (
        <>
          <ol className="rules-list">
            <li><strong>One daily run.</strong> Everyone gets the same seven programming prompts.</li>
            <li><strong>25 seconds per prompt.</strong> Read the prompt during a 3-second preview. A rejected guess can be retried while time remains.</li>
            <li><strong>Go for the unusual.</strong> A valid answer locks the round. Any text still in the field is checked when time runs out.</li>
            <li><strong>See what you missed.</strong> Advance at your own pace. After the last round, browse the full answer lists and share your score.</li>
          </ol>
          <div className="dialog-tiers">
            {tierEntries.map(([key, tier]) => <span key={key} style={{ color: tier.tone }}>{tier.label} · {tier.points}</span>)}
          </div>
        </>
      ) : (
        <div className="settings-list">
          {options.map(([key, label, description]) => (
            <label key={key} className="setting">
              <span><strong>{label}</strong><small>{description}</small></span>
              <input type="checkbox" role="switch" checked={preferences[key]} onChange={event => change(key, event.target.checked)} />
            </label>
          ))}
        </div>
      )}
    </dialog>
  );
}

function Landing({ daily, now, start, busy }) {
  const date = new Date(daily.opensAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' });
  return (
    <main className="container landing">
      <div className="hero">
        <div className="hero-image" aria-hidden="true">
          <img src={import.meta.env.BASE_URL + 'processor.webp'} alt="" fetchPriority="high" />
          <span className="image-corner corner-top" /><span className="image-corner corner-bottom" />
        </div>
        <div className="hero-copy">
          <p className="eyebrow"><span className="signal" /> DAILY RUN #{String(daily.dayNumber).padStart(3, '0')} <span className="eyebrow-divider">/</span> {date.toUpperCase()}</p>
          <h1>Get to <span>root<span className="cursor-period">.</span></span></h1>
          <p className="hero-summary">The daily programming quiz. Find valid answers few other developers would think of.</p>
          <button className="primary-button start-button" onClick={start} disabled={busy}>
            <Terminal size={20} /> {busy ? 'Starting…' : 'Start daily run'} <ArrowRight size={20} />
          </button>
          <div className="hero-timer"><Clock3 size={15} /> New run in <strong>{countdown(Date.parse(daily.resetsAt) - now)}</strong></div>
        </div>
      </div>
      <section className="rules-strip" aria-label="Daily quiz rules">
        <div><span className="rule-icon"><Braces size={23} /></span><p><strong>{daily.rules.roundCount} prompts</strong><small>Code, tooling &amp; computer science</small></p></div>
        <div><span className="rule-icon"><Clock3 size={23} /></span><p><strong>{daily.rules.answerSeconds} seconds each</strong><small>Retry while the clock is running</small></p></div>
        <div><span className="rule-icon"><KeyRound size={23} /></span><p><strong>Rarer answers score more</strong><small>One attempt per day</small></p></div>
      </section>
    </main>
  );
}

function Footer() {
  return (
    <footer className="container site-footer">
      <span><Code2 size={15} /> ROOT ACCESS</span>
    </footer>
  );
}

function Clearance({ score, maxScore }) {
  const percentage = (score / maxScore) * 100;
  const clearance = CLEARANCE_LABELS[scoreBand(score)];
  return (
    <aside className="clearance panel">
      <p className="panel-label"><Layers3 size={17} /> Answer tiers</p>
      <div className="clearance-scale">
        {tierEntries.map(([key, tier]) => (
          <div key={key} style={{ '--tier': tier.tone }}>
            <span className="tier-dot" /><span>{tier.label}</span><small>+{tier.points}</small>
          </div>
        ))}
      </div>
      <div className="clearance-readout">
        <span>Current clearance</span><strong>{clearance}</strong>
        <div className="meter" role="meter" aria-label="Total score" aria-valuemin={0} aria-valuemax={maxScore} aria-valuenow={score}>
          <i style={{ width: percentage + '%' }} />
        </div>
        <small>{score} / {maxScore} points</small>
      </div>
    </aside>
  );
}

function RoundProgress({ run, number: active }) {
  return (
    <div className="round-header">
      <div><p className="eyebrow"><span className="signal" /> DAILY RUN #{String(run.dayNumber).padStart(3, '0')}</p>
        <p className="round-count">Prompt {pad(active)} <span>/ {pad(run.rules.roundCount)}</span></p></div>
      <ol className="round-markers" aria-label="Round progress">
        {Array.from({ length: run.rules.roundCount }, (_, index) => {
          const result = run.rounds[index];
          const isCurrent = index + 1 === active && !result;
          const style = result?.match ? { '--pip': TIERS[result.match.tier].tone } : undefined;
          return <li key={index} title={'Prompt ' + (index + 1)} style={style} className={isCurrent ? 'current' : result ? 'settled' : ''} aria-current={isCurrent ? 'step' : undefined}>{pad(index + 1)}</li>;
        })}
      </ol>
      <div className="run-score"><p className="panel-label">Score</p><strong>{run.score}<small> / {run.rules.maxScore}</small></strong></div>
    </div>
  );
}

function ActiveRound({ game, dialogOpen, reducedMotion }) {
  const { run, now, draft, edit, busy, rejected, submit, next } = game;
  const round = run.currentRound;
  const result = run.rounds.at(-1);
  const [seen, setSeen] = useState(() => run.rounds.length);
  const routing = Boolean(!round && result && result.number > seen && !reducedMotion);
  const finish = useCallback(() => setSeen(result.number), [result?.number]);
  useEffect(() => {
    if (reducedMotion && !round && result && result.number > seen) finish();
  }, [reducedMotion, round, result, seen, finish]);
  const displayed = routing
    ? { ...run, score: run.score - result.points, rounds: run.rounds.slice(0, -1) }
    : run;
  const isPreview = round && now < Date.parse(round.answerStartsAt);
  const isDue = round && now >= Math.min(Date.parse(round.answerEndsAt), Date.parse(run.resetsAt));
  const seconds = round ? Math.max(0, Math.ceil((Date.parse(isPreview ? round.answerStartsAt : round.answerEndsAt) - now) / 1000)) : 0;
  const canAnswer = Boolean(round && !isPreview && !isDue);
  const tier = result?.match ? TIERS[result.match.tier] : null;
  const input = useRef(null);
  useEffect(() => {
    if (canAnswer && !dialogOpen) input.current?.focus();
  }, [canAnswer, round?.number, dialogOpen]);
  useEffect(() => {
    if (round || !result || dialogOpen || routing) return;
    const onKey = event => {
      if (event.key !== 'Enter' || event.repeat || event.isComposing || event.altKey || event.metaKey
        || event.ctrlKey || event.shiftKey || event.target.closest?.('button, input, a, textarea, select, [contenteditable]')) return;
      event.preventDefault();
      next();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [round, result, dialogOpen, routing, next]);

  return (
    <main className="container play">
      <RoundProgress run={displayed} number={round?.number ?? result.number} />
      <div className="play-grid">
        <section className={'panel terminal-panel ' + (!round ? 'reveal-panel' : '')} key={round ? 'prompt-' + round.number : 'reveal-' + result.number}>
          <div className="terminal-heading">
            <span><Terminal size={17} /> {round ? 'PROMPT ' + pad(round.number) : 'ROUND ' + pad(result.number) + ' RESULT'}</span>
            {round && <span className="topic-label">{round.prompt.topic || 'Programming'}</span>}
            {!round && <span className="topic-label">{routing ? 'Checking access' : 'Saved'}</span>}
          </div>
          {round ? (
            <>
              <div className="prompt-content">
                <h1>{round.prompt.text}</h1>
                <p>Obscure valid answers unlock higher tiers.</p>
              </div>
              <div className="answer-zone">
                {isPreview || isDue ? (
                  <div className="preview-line"><Clock3 size={20} /> {isDue ? 'Checking final answer…' : <>Answer window opens in <strong>{seconds}</strong></>}</div>
                ) : (
                  <>
                    <div className={'timer-row ' + (seconds <= 3 ? 'urgent' : '')}>
                      <span><Clock3 size={15} /> TIME REMAINING</span>
                      <span><strong role="timer" aria-label="Seconds remaining">{seconds}</strong> s</span>
                    </div>
                    <div className={'meter timer-meter ' + (seconds <= 3 ? 'urgent' : '')}><i style={{ width: (seconds / run.rules.answerSeconds) * 100 + '%' }} /></div>
                    <form onSubmit={event => { event.preventDefault(); submit(); }}>
                      <div className="answer-field"><span aria-hidden="true">&gt;_</span><input ref={input} aria-label="Your answer" placeholder="Type one answer" type="text"
                        autoComplete="off" autoCorrect="off" autoCapitalize="none" spellCheck={false} maxLength={256} enterKeyHint="send"
                        value={draft.text} readOnly={busy} onChange={event => edit(event.target.value)} /></div>
                      <button className="primary-button submit-button" disabled={!draft.text.trim() || busy}>Submit <CornerDownLeft size={17} /></button>
                    </form>
                    <div className="answer-feedback" aria-live="polite">
                      {round.correction && <div className="correction"><strong>{round.correction.originalText} → {round.correction.canonicalText}</strong><span>Submit again to confirm, or edit your answer.</span></div>}
                      {rejected && <span className="rejected">No match. Try another answer.</span>}
                    </div>
                  </>
                )}
              </div>
            </>
          ) : routing ? (
            <AccessSequence result={result} finish={finish} />
          ) : (
            <>
              <div className="reveal-content" style={{ '--tier': tier?.tone ?? '#a7b2a9' }}>
                <div className="reveal-key"><KeyRound size={32} strokeWidth={1.65} /></div>
                <p className="eyebrow">{tier?.label || '0 points'}</p>
                <h1>{result.match?.label ?? (result.submittedText ? 'No match logged' : 'No answer logged')}</h1>
                {result.submittedText && !result.match && <p className="miss-text">{result.submittedText}</p>}
                {result.match && <div className="round-score"><strong>+{result.points} points</strong></div>}
                {result.match?.note && <p>{result.match.note}</p>}
              </div>
              <div className="reveal-actions"><button className="primary-button" onClick={next} disabled={busy}>
                {run.phase === 'ready_to_surface' ? 'View results' : 'Next prompt'}
                {run.phase === 'ready_to_surface' ? <ArrowRight size={19} /> : <ChevronDown size={19} />}
              </button></div>
            </>
          )}
        </section>
        <Clearance score={displayed.score} maxScore={run.rules.maxScore} />
      </div>
    </main>
  );
}

export default function App() {
  const [preferences, setPreferences] = useState(preferencesFromStorage);
  const [dialog, setDialog] = useState(null);
  const [systemMotion, setSystemMotion] = useState(() => matchMedia('(prefers-reduced-motion: reduce)').matches);
  useEffect(() => {
    const query = matchMedia('(prefers-reduced-motion: reduce)');
    const change = event => setSystemMotion(event.matches);
    query.addEventListener('change', change);
    return () => query.removeEventListener('change', change);
  }, []);
  const reducedMotion = preferences.reducedMotion || systemMotion;
  const game = useDaily(preferences);
  const { daily, run, now, load, error, retry, busy } = game;
  function change(key, value) {
    const updated = { ...preferences, [key]: value };
    setPreferences(updated);
    try { localStorage.setItem(preferenceKey, JSON.stringify(updated)); } catch { /* Preferences still apply in this tab. */ }
  }
  return (
    <div className={reducedMotion ? 'shell reduced-motion' : 'shell'}>
      <a className="skip-link" href="#main-content">Skip to quiz</a>
      <Header open={setDialog} />
      <div id="main-content" tabIndex={-1}>
        {error && <div className="container notice" role="alert"><span>{error}</span><button className="quiet-button" onClick={retry}>Retry</button></div>}
        {!daily && !error && <main className="container loading" aria-live="polite">Loading the daily quiz…</main>}
        {daily && !run && <Landing daily={daily} now={now} start={game.start} busy={busy} />}
        {run?.phase === 'expired' && <main className="container panel expired"><h1>The daily run has reset.</h1><button className="primary-button" onClick={load}>Load today's run <ArrowRight size={18} /></button></main>}
        {run?.phase === 'completed' && <Results key={run.id} run={run} now={now} loadDaily={load} preferences={preferences} />}
        {run && !['expired', 'completed'].includes(run.phase) && <ActiveRound game={game} dialogOpen={Boolean(dialog)} reducedMotion={reducedMotion} />}
      </div>
      <Footer />
      {dialog && <Dialog kind={dialog} close={() => setDialog(null)} preferences={preferences} change={change} />}
    </div>
  );
}
