import { useEffect, useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";

const EXAMPLES = {
  analyze:
    "Hi, I need an e-commerce website with payment integration within 10 days. My budget is $300.",
  agreement:
    "I will design one logo for your bakery. Includes 2 revisions. Final files in PNG and SVG.",
  request:
    "Great work! Can you also make some social media posts and business cards?",
};

/* ---------- small helpers ---------- */

function Icon({ name }) {
  const paths = {
    analyze: "M4 5h16M4 12h10M4 19h16",
    scope: "M12 3l9 4v5c0 5-4 8-9 9-5-1-9-4-9-9V7l9-4zM9 12l2 2 4-4",
    history: "M12 7v5l3 2M3 12a9 9 0 1 0 3-6.7M3 4v4h4",
    proposal: "M7 3h8l4 4v14H7zM15 3v4h4M10 12h6M10 16h6",
    sun: "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4",
    moon: "M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z",
  };
  return (
    <svg
      className="icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={paths[name]} />
    </svg>
  );
}

function CopyButton({ text, label = "Copy" }) {
  const [done, setDone] = useState(false);
  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setDone(true);
      setTimeout(() => setDone(false), 1800);
    } catch {
      /* clipboard not available */
    }
  }
  return (
    <button type="button" className="btn btn-quiet" onClick={copy}>
      {done ? "Copied" : label}
    </button>
  );
}

function Section({ title, action, children }) {
  return (
    <section className="section">
      <div className="section-head">
        <h3>{title}</h3>
        {action}
      </div>
      {children}
    </section>
  );
}

function Loading() {
  return (
    <div className="panel skeleton" aria-busy="true" aria-live="polite">
      <div className="sk sk-title" />
      <div className="sk" />
      <div className="sk" />
      <div className="sk sk-short" />
    </div>
  );
}

function EmptyState({ title, text }) {
  return (
    <div className="empty">
      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  );
}

async function post(path, body) {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error("Request failed");
  return res.json();
}

const CONNECTION_ERROR =
  "Could not reach the backend. Make sure the server is running on port 8000, then try again.";

/* ---------- Message analyzer ---------- */

function AnalyzeView() {
  const [message, setMessage] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function run() {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      setResult(await post("/analyze", { message }));
    } catch {
      setError(CONNECTION_ERROR);
    }
    setLoading(false);
  }

  const facts = result && [
    ["Project type", result.project_type, result.project_type === "Unknown"],
    ["Budget", result.budget, !result.budget],
    ["Deadline", result.deadline, !result.deadline],
  ];

  return (
    <div className="workspace">
      <div className="input-col">
        <div className="panel">
          <label htmlFor="client-message">Client message</label>
          <textarea
            id="client-message"
            rows={9}
            placeholder="Paste the message your client sent you."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
          />
          <div className="actions">
            <button
              type="button"
              className="btn btn-primary"
              onClick={run}
              disabled={loading || !message.trim()}
            >
              {loading ? "Analyzing" : "Build project plan"}
            </button>
            <button
              type="button"
              className="btn btn-quiet"
              onClick={() => setMessage(EXAMPLES.analyze)}
            >
              Use an example
            </button>
          </div>
        </div>
      </div>

      <div className="output-col">
        {error && <p className="alert" role="alert">{error}</p>}
        {loading && <Loading />}
        {!loading && !result && !error && (
          <EmptyState
            title="Your project plan will appear here"
            text="Paste a client message and build the plan. You will get the requirements, what is missing, questions to ask and the risks."
          />
        )}

        {result && (
          <div className="panel result">
            <dl className="facts">
              {facts.map(([label, value, missing]) => (
                <div key={label} className={missing ? "fact is-missing" : "fact"}>
                  <dt>{label}</dt>
                  <dd>{missing ? "Not mentioned" : value}</dd>
                </div>
              ))}
            </dl>

            {result.requirements?.length > 0 && (
              <Section title="Requirements found">
                <div className="chips">
                  {result.requirements.map((r) => (
                    <span className="chip" key={r}>{r}</span>
                  ))}
                </div>
              </Section>
            )}

            {result.missing_fields?.length > 0 && (
              <Section title="Missing from the message">
                <ul className="flags">
                  {result.missing_fields.map((m) => (
                    <li key={m}>{m}</li>
                  ))}
                </ul>
              </Section>
            )}

            {result.suggested_questions?.length > 0 && (
              <Section
                title="Questions to ask the client"
                action={
                  <CopyButton
                    label="Copy questions"
                    text={result.suggested_questions.map((q) => `- ${q}`).join("\n")}
                  />
                }
              >
                <ul className="plain">
                  {result.suggested_questions.map((q) => (
                    <li key={q}>{q}</li>
                  ))}
                </ul>
              </Section>
            )}

            {result.plan?.risks?.length > 0 && (
              <Section title="Risks to watch">
                <ul className="flags">
                  {result.plan.risks.map((r) => (
                    <li key={r}>{r}</li>
                  ))}
                </ul>
              </Section>
            )}

            {result.plan?.tasks?.length > 0 && (
              <Section title="Task breakdown">
                <ol className="steps">
                  {result.plan.tasks.map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ol>
              </Section>
            )}

            {result.plan?.deliverables?.length > 0 && (
              <Section title="Deliverables">
                <ul className="plain">
                  {result.plan.deliverables.map((d) => (
                    <li key={d}>{d}</li>
                  ))}
                </ul>
              </Section>
            )}

            <p className="note">{result.plan?.note}</p>
          </div>
        )}
      </div>
    </div>
  );
}

/* ---------- Scope check ---------- */

const VERDICT_STYLE = {
  "In scope": "ok",
  Unclear: "warn",
  "Partially out of scope": "warn",
  "Out of scope": "bad",
};

function ScopeView() {
  const [agreement, setAgreement] = useState("");
  const [request, setRequest] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function run() {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      setResult(await post("/scope-check", { agreement, new_request: request }));
    } catch {
      setError(CONNECTION_ERROR);
    }
    setLoading(false);
  }

  function fillExample() {
    setAgreement(EXAMPLES.agreement);
    setRequest(EXAMPLES.request);
  }

  return (
    <div className="workspace">
      <div className="input-col">
        <div className="panel">
          <label htmlFor="agreement">Original agreement</label>
          <textarea
            id="agreement"
            rows={5}
            placeholder="Paste what you agreed to deliver."
            value={agreement}
            onChange={(e) => setAgreement(e.target.value)}
          />
          <label htmlFor="new-request">New client request</label>
          <textarea
            id="new-request"
            rows={5}
            placeholder="Paste what the client is asking for now."
            value={request}
            onChange={(e) => setRequest(e.target.value)}
          />
          <div className="actions">
            <button
              type="button"
              className="btn btn-primary"
              onClick={run}
              disabled={loading || !agreement.trim() || !request.trim()}
            >
              {loading ? "Checking" : "Check scope"}
            </button>
            <button type="button" className="btn btn-quiet" onClick={fillExample}>
              Use an example
            </button>
          </div>
        </div>
      </div>

      <div className="output-col">
        {error && <p className="alert" role="alert">{error}</p>}
        {loading && <Loading />}
        {!loading && !result && !error && (
          <EmptyState
            title="No scope check yet"
            text="Add your agreement and the client's new request. You will see whether the work is covered and get a polite reply you can send."
          />
        )}

        {result && (
          <div className="panel result">
            <div className={`verdict ${VERDICT_STYLE[result.verdict] || "warn"}`}>
              <strong>{result.verdict}</strong>
              <span>{result.explanation}</span>
            </div>

            <div className="split">
              <Section title="Covered by the agreement">
                {result.in_scope?.length ? (
                  <ul className="plain">
                    {result.in_scope.map((i) => <li key={i}>{i}</li>)}
                  </ul>
                ) : (
                  <p className="muted">Nothing found.</p>
                )}
              </Section>
              <Section title="Not in the agreement">
                {result.out_of_scope?.length ? (
                  <ul className="flags">
                    {result.out_of_scope.map((i) => <li key={i}>{i}</li>)}
                  </ul>
                ) : (
                  <p className="muted">Nothing found.</p>
                )}
              </Section>
            </div>

            {result.revision_note && (
              <p className="callout">{result.revision_note}</p>
            )}

            <Section
              title="Suggested reply"
              action={<CopyButton label="Copy reply" text={result.suggested_reply} />}
            >
              <p className="reply">{result.suggested_reply}</p>
            </Section>

            <p className="note">{result.note}</p>
          </div>
        )}
      </div>
    </div>
  );
}

/* ---------- App shell ---------- */

const NAV = [
  { id: "analyze", label: "Message analyzer", icon: "analyze" },
  { id: "scope", label: "Scope check", icon: "scope" },
  { id: "history", label: "Project history", icon: "history", soon: true },
  { id: "proposals", label: "Proposals", icon: "proposal", soon: true },
];

const TITLES = {
  analyze: {
    h: "Turn a client message into a plan",
    p: "Find the requirements, the gaps and the risks before you quote.",
  },
  scope: {
    h: "Check a request against your agreement",
    p: "Spot extra work early and reply without losing the client.",
  },
};

function getInitialTheme() {
  try {
    const saved = localStorage.getItem("fp-theme");
    if (saved === "light" || saved === "dark") return saved;
  } catch {
    /* storage not available */
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export default function App() {
  const [tab, setTab] = useState("analyze");
  const [theme, setTheme] = useState(getInitialTheme);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    try {
      localStorage.setItem("fp-theme", theme);
    } catch {
      /* storage not available */
    }
  }, [theme]);

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="logo" aria-hidden="true">FP</span>
          <div>
            <strong>FreelancePilot</strong>
            <span>Plan before you quote</span>
          </div>
        </div>

        <nav aria-label="Main">
          {NAV.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`nav-item ${tab === item.id ? "active" : ""}`}
              disabled={item.soon}
              aria-current={tab === item.id ? "page" : undefined}
              onClick={() => setTab(item.id)}
            >
              <Icon name={item.icon} />
              <span>{item.label}</span>
              {item.soon && <em>Soon</em>}
            </button>
          ))}
        </nav>

        <div className="theme-switch" role="group" aria-label="Color theme">
          <button type="button" aria-pressed={theme === "light"} onClick={() => setTheme("light")}>
            <Icon name="sun" />
            <span>Light</span>
          </button>
          <button type="button" aria-pressed={theme === "dark"} onClick={() => setTheme("dark")}>
            <Icon name="moon" />
            <span>Dark</span>
          </button>
        </div>
      </aside>

      <main className="main">
        <header className="page-head">
          <h1>{TITLES[tab].h}</h1>
          <p>{TITLES[tab].p}</p>
        </header>
        {tab === "analyze" ? <AnalyzeView /> : <ScopeView />}
      </main>
    </div>
  );
}
