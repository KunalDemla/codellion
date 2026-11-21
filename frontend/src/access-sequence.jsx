import React, { useEffect } from 'react';
import { Braces, Cpu, KeyRound, Shield, Terminal, UserRound, X } from 'lucide-react';
import { TIERS } from './domain.js';
import './access-sequence.css';

const gates = [Terminal, Braces, UserRound, Shield, Cpu, KeyRound];
const levels = Object.entries(TIERS);

export default function AccessSequence({ result, finish }) {
  const target = result.match ? levels.findIndex(([key]) => key === result.match.tier) : -1;
  const granted = target >= 0;
  const duration = granted ? 1430 + target * 148 : 1050;
  const reach = granted ? (target + .5) / levels.length : .082;
  const tier = levels[target]?.[1];
  const state = granted ? 'granted' : 'denied';

  useEffect(() => {
    const fallback = setTimeout(finish, duration + 170);
    return () => clearTimeout(fallback);
  }, [duration, finish]);

  return (
    <div className={'access-sequence ' + state} data-testid="access-sequence" style={{
      '--signal-color': tier?.tone ?? '#f6a98d', '--sequence-time': duration + 'ms',
      '--reach': reach * 100 + '%',
    }} onAnimationEnd={event => {
      if (event.target === event.currentTarget && event.animationName === 'sequence-lifetime') finish();
    }}>
      <div className="sequence-grid" aria-hidden="true" />
      <div className="sequence-copy">
        <p className="eyebrow"><span className="signal" /> ACCESS CHECK</p>
        <h2>{granted ? 'Routing answer' : 'No access granted'}</h2>
      </div>
      <div className="access-route" aria-hidden="true">
        <div className="access-rail"><i /><b /></div>
        <ol>
          {levels.map(([key, value], index) => {
            const Icon = gates[index];
            const hit = index <= target;
            const gateAt = duration * (.08 + .64 * ((index + .5) / (target + .5)));
            return (
              <li key={key} className={hit ? 'reached' + (index === target ? ' target' : '') : ''}
                style={{ '--gate-tone': value.tone, '--gate-at': Math.max(0, gateAt) + 'ms' }}>
                <div className="gate-icon"><Icon size={23} strokeWidth={1.65} /></div>
                <span>{value.label}</span>
              </li>
            );
          })}
        </ol>
        {!granted && <div className="denied-pulse"><X size={21} /></div>}
      </div>
      <div className="sequence-footer">
        <p className="sequence-status" role="status">{granted ? 'Verifying answer tier…' : 'Round closed with zero points.'}</p>
        <button className="quiet-button" onClick={finish}>Skip animation</button>
      </div>
    </div>
  );
}
