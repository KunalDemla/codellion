import React, { memo, useEffect, useState } from 'react';
import { ArrowRight, BarChart3, Check, ChevronDown, Clipboard, Search, Terminal, Trophy } from 'lucide-react';
import { countdown, TIERS } from './domain.js';
import { CLEARANCE_LABELS } from './clearance.js';
import { api } from './use-daily.js';

const tiersByRarity = Object.entries(TIERS).reverse();

const AnswerBrowser = memo(function AnswerBrowser({ runId, round }) {
  const [q, setQuery] = useState('');
  const [tier, setTier] = useState('');
  const [page, setPage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  const [cursor, setCursor] = useState(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError('');
    if (!cursor) setPage(null);
    const request = setTimeout(() => {
      api.answers(runId, round, { q, tier, cursor }).then(
        reply => {
          if (!active) return;
          setPage(previous => cursor && previous?.nextCursor === cursor
            ? { ...reply, items: [...previous.items, ...reply.items] }
            : reply);
        },
        cause => { if (active) setError(cause.message); },
      ).finally(() => { if (active) setLoading(false); });
    }, q && !cursor ? 100 : 0);
    return () => { active = false; clearTimeout(request); };
  }, [runId, round, q, tier, retry, cursor]);

  function selectTier(value) {
    if (tier === value) return;
    setCursor(null);
    setTier(value);
  }

  return (
    <div className="answer-browser">
      <div className="search-box"><Search size={17} />
        <input type="search" maxLength={128} aria-label="Search answers and aliases" placeholder="Search answers and aliases"
          value={q} onChange={e => { setCursor(null); setQuery(e.target.value); }} />
      </div>
      <div className="filter-pills" role="group" aria-label="Filter by tier">
        <button aria-pressed={tier === ''} onClick={() => selectTier('')}>All{page && <small>{page.total}</small>}</button>
        {tiersByRarity.map(([key, value]) => (
          <button key={key} aria-pressed={tier === key} style={{ '--tier': value.tone }} onClick={() => selectTier(key)}>{value.label}{page && <small>{page.tierCounts[key]}</small>}</button>
        ))}
      </div>
      {page?.items.length > 0 && <>
        <p className="browser-status" role="status">Showing {page.items.length} of {page.matched} accepted answers</p>
        <div className="accepted-groups" role="region" aria-label="Accepted answers" tabIndex={0}>
          {tiersByRarity.map(([key, value]) => {
            const items = page.items.filter(answer => answer.tier === key);
            if (!items.length) return null;
            return <section key={key} className="accepted-group" style={{ '--tier': value.tone }}>
              <h3>{value.label}<span>+{value.points} points</span></h3>
              <ul className="accepted-list">
                {items.map(answer => <li key={answer.id}>
                  <strong>{answer.label}</strong>{answer.isYourAnswer && <span className="your-answer">Your answer</span>}
                  {answer.note && <p>{answer.note}</p>}
                  {answer.aliases?.length > 0 && <details className="accepted-aliases">
                    <summary>{answer.aliases.length === 1 ? '1 alias' : answer.aliases.length + ' aliases'}</summary>
                    <ul aria-label="Accepted aliases">{answer.aliases.map(alias => <li key={alias}>{alias}</li>)}</ul>
                  </details>}
                </li>)}
              </ul>
            </section>;
          })}
        </div>
      </>}
      {!loading && page?.matched === 0 && <p className="browser-status" role="status">No accepted answers match this search.</p>}
      {error && <p className="browser-status" role="alert">{error} <button className="quiet-button" onClick={() => setRetry(value => value + 1)}>Retry</button></p>}
      {loading && <p className="browser-status" role="status">Loading answers…</p>}
      {page?.nextCursor && <button className="quiet-button" onClick={() => setCursor(page.nextCursor)} disabled={loading}>Load more answers <ChevronDown size={15} /></button>}
    </div>
  );
});

function ScoreChart({ results, maxScore }) {
  return (
    <section className="panel result-panel" aria-labelledby="breakdown">
      <h2 id="breakdown"><BarChart3 size={20} /> Round scores</h2>
      <ol className="score-chart" aria-label="Points earned per round">
        {results.rounds.map(round => {
          const tier = round.match ? TIERS[round.match.tier] : null;
          return (
            <li key={round.number} style={{ '--tier': tier?.tone ?? '#526058' }}>
              <div className="bar-space">
                <div className={round.points === 100 ? 'score-bar full' : 'score-bar'} style={{ '--height': round.points + '%' }}><span>{round.points}</span></div>
              </div>
              <span className="chart-label">{String(round.number).padStart(2, '0')}</span>
            </li>
          );
        })}
      </ol>
      {results.standings?.sampleSize > 1 && (
        <div className="standings">
          <p>Daily percentile <strong>{results.standings.betterThanPercent}%</strong></p>
          <ol className="histogram" aria-label="Daily score distribution">
            {results.standings.histogram.map(bucket => (
              <li key={bucket.minScore} title={bucket.minScore + '–' + bucket.maxScore + ': ' + bucket.count + ' runs'}
                className={results.score >= bucket.minScore && results.score <= bucket.maxScore ? 'your-bucket' : ''}
                style={{ '--height': (100 * bucket.count / Math.max(...results.standings.histogram.map(item => item.count))) + '%' }} />
            ))}
          </ol>
          <div className="histogram-labels"><span>0</span><span>{maxScore}</span></div>
        </div>
      )}
    </section>
  );
}

function shareResult(results, maxScore, includeLink) {
  const row = results.rounds.map(round => round.match ? TIERS[round.match.tier].symbol : '⬛').join('');
  const text = 'ROOT ACCESS #' + String(results.dayNumber).padStart(3, '0') + '\n' + results.score + '/' + maxScore + '\n' + row;
  return includeLink ? text + '\n' + window.location.origin + window.location.pathname : text;
}

export default function Results({ run, now, preferences, loadDaily }) {
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');
  const [request, setRequest] = useState(0);
  const [expanded, setExpanded] = useState(run.rounds[0]?.number ?? null);
  const [copied, setCopied] = useState(false);
  const [shareText, setShareText] = useState('');

  useEffect(() => {
    let active = true;
    const load = () => api.results(run.id).then(
      data => { if (active) { setResults(data); setError(''); } },
      cause => { if (active) setError(cause.message); },
    );
    void load();
    return () => { active = false; };
  }, [run.id, request]);

  if (!results) {
    return <main className="container loading" aria-live="polite">{error
      ? <>{error} <button className="quiet-button" onClick={() => setRequest(value => value + 1)}>Retry</button></>
      : 'Loading your results…'}</main>;
  }

  async function copy() {
    const text = shareResult(results, run.rules.maxScore, preferences.shareLink);
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setShareText('');
    } catch {
      setShareText(text);
    }
  }

  const resetReached = now >= Date.parse(run.resetsAt);
  const remaining = results.nextDailyOpensAt ? Date.parse(results.nextDailyOpensAt) - now : null;
  return (
    <main className="container results">
      <div className="panel result-hero">
        <div>
          <p className="eyebrow"><span className="signal" /> DAILY RUN #{String(results.dayNumber).padStart(3, '0')}</p>
          <h1>Run complete<span>.</span></h1>
          <p className="result-band" style={{ '--tier': TIERS[results.band].tone }}><Trophy size={18} /> {CLEARANCE_LABELS[results.band]} clearance</p>
        </div>
        <div className="final-score">
          <p className="panel-label">FINAL SCORE</p>
          <strong><span data-testid="final-score">{results.score}</span><small> / {run.rules.maxScore}</small></strong>
        </div>
      </div>
      <div className="result-grid">
        <ScoreChart results={results} maxScore={run.rules.maxScore} />
        <section className="panel result-panel logbook" aria-label="Your logbook">
          <h2><Terminal size={20} /> Your logbook</h2>
          <dl>
            <div><dt>Current streak</dt><dd>{results.logbook.currentStreak}</dd></div>
            <div><dt>Runs played</dt><dd>{results.logbook.played}</dd></div>
            <div><dt>Average score</dt><dd>{Math.round(results.logbook.averageScore)}</dd></div>
            <div><dt>Best score</dt><dd>{results.logbook.bestScore}</dd></div>
          </dl>
          <button className="primary-button" onClick={copy}>{copied ? <Check size={18} /> : <Clipboard size={18} />} {copied ? 'Copied' : 'Copy result'}</button>
          {shareText && <label className="share-fallback">Share text<textarea readOnly value={shareText} onFocus={event => event.target.select()} /></label>}
          {resetReached
            ? <button className="quiet-button" onClick={loadDaily}>Open the new daily <ArrowRight size={16} /></button>
            : remaining !== null && <p className="result-reset">Next run in <strong>{countdown(remaining)}</strong></p>}
        </section>
      </div>
      <section className="panel result-panel review" aria-labelledby="review-heading">
        <h2 id="review-heading"><Search size={20} /> Answer review</h2>
        {api.canReview && <p className="review-intro">Open a round to see every accepted answer and its aliases.</p>}
        {results.rounds.map(round => {
          const match = round.match;
          const open = expanded === round.number;
          const row = <>
            <span className="review-number">{String(round.number).padStart(2, '0')}</span>
            <span className="review-question"><strong>{round.prompt.text}</strong><small>{match?.label ?? (round.submittedText || 'No answer')}</small></span>
            <span className="review-points">+{round.points}</span>
          </>;
          const style = { '--tier': match ? TIERS[match.tier].tone : '#a7b2a9' };
          return <div className="review-round" key={round.number}>
            {api.canReview
              ? <button className="review-toggle" aria-expanded={open} style={style}
                  onClick={() => setExpanded(open ? null : round.number)}>{row}<ChevronDown size={18} /></button>
              : <div className="review-toggle review-static" style={style}>{row}</div>}
            {api.canReview && open && <AnswerBrowser runId={run.id} round={round.number} key={round.number} />}
          </div>;
        })}
      </section>
    </main>
  );
}
