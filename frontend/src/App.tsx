import { useEffect, useState } from "react";
import { getQuestions } from "./services/api";
import type { Question } from "./types/question";
export default function App() {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => { getQuestions().then(setQuestions).catch((e: unknown) => setError(e instanceof Error ? e.message : "Unknown error")).finally(() => setLoading(false)); }, []);
  return <main className="shell">
    <header><div className="brand"><b>&gt;_</b> ROOT ACCESS</div><span className="status">● SYSTEM ONLINE</span></header>
    <section className="hero"><p>KNOWLEDGE IS AN ATTACK SURFACE</p><h1>THINK DEEPER.<br/><span>GO RARER.</span></h1><small>A technical knowledge challenge for curious minds.</small></section>
    <section className="panel"><div className="panelhead">AVAILABLE CHALLENGES <span>{questions.length} LOADED</span></div>
      {loading && <p className="muted">Connecting to challenge database...</p>}
      {error && <p className="error">API CONNECTION FAILED: {error}</p>}
      {questions.map((q, i) => <article key={q.id}><em>{String(i+1).padStart(2,"0")}</em><div><strong>{q.prompt}</strong><small>{q.category.toUpperCase()} · DIFFICULTY {q.difficulty}</small></div><b>↗</b></article>)}
    </section><footer>ROOT ACCESS · LOCAL DEVELOPMENT BUILD 0.1</footer>
  </main>;
}
