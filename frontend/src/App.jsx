import { useEffect, useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";

const EXAMPLES = {
  analyze:
    "Hi, I need an e-commerce website with payment integration within 10 days. My budget is $300.",
  agreement:
    "I will design one logo for your bakery. Includes 2 revisions. Final files in PNG and SVG.",
  request: "Great work! Can you also make some social media posts and business cards?",
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

function Loading({ slow }) {
  return (
    <div className="panel skeleton" aria-busy="true" aria-live="polite">
      <div className="sk sk-title" />
      <div className="sk" />
      <div className="sk" />
      <div className="sk sk-short" />
      {slow && (
        <p className="muted small">
          The AI is thinking. This can take a few seconds up to a minute.
        </p>
      )}
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

/* ---------- API with sign-in token ---------- */

const TOKEN_KEY = "fp-token";
let authToken = null;
let onUnauthorized = () => {};

function loadToken() {
  try {
    authToken = localStorage.getItem(TOKEN_KEY);
  } catch {
    authToken = null;
  }
  return authToken;
}

function saveToken(token) {
  authToken = token;
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    /* storage not available */
  }
}

function clearToken() {
  authToken = null;
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage not available */
  }
}

async function request(method, path, body) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (authToken) headers.Authorization = `Bearer ${authToken}`;

  const res = await fetch(`${API}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    let detail = "";
    try {
      detail = (await res.json()).detail;
    } catch {
      /* no message from the server */
    }
    if (res.status === 401 && authToken) onUnauthorized();
    const error = new Error(typeof detail === "string" && detail ? detail : "Request failed");
    error.status = res.status;
    throw error;
  }
  return res.json();
}

const get = (path) => request("GET", path);
const post = (path, body) => request("POST", path, body);
const del = (path) => request("DELETE", path);

const CONNECTION_ERROR =
  "Could not reach the backend. Make sure the server is running on port 8000, then try again.";

/* ---------- AI helpers ---------- */

function useAIStatus() {
  const [status, setStatus] = useState(null);
  useEffect(() => {
    get("/ai/status")
      .then(setStatus)
      .catch(() =>
        setStatus({ running: false, model_installed: false, message: "Backend is not reachable." }),
      );
  }, []);
  return status;
}

function aiReady(status) {
  return Boolean(status?.running && status?.model_installed);
}

function AIToggle({ checked, onChange, status }) {
  const ready = aiReady(status);
  return (
    <div className="ai-toggle">
      <label>
        <input
          type="checkbox"
          checked={checked && ready}
          disabled={!ready}
          onChange={(e) => onChange(e.target.checked)}
        />
        <span>Add AI insights</span>
      </label>
      <p className="muted small">
        {status === null
          ? "Checking AI status."
          : ready
            ? status.provider === "groq"
              ? "Uses an online AI (Groq). Your text is sent to Groq to get the answer."
              : `Runs ${status.model} on your computer. Slower: can take up to a minute.`
            : `${status.message} Everything else works without AI.`}
      </p>
    </div>
  );
}

function AIList({ title, items, flag }) {
  if (!items || items.length === 0) return null;
  return (
    <>
      <h4 className="ai-sub">{title}</h4>
      <ul className={flag ? "flags" : "plain"}>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </>
  );
}

function AIError({ message }) {
  return (
    <Section title="AI insights">
      <p className="muted">{message} The rule-based result is still valid.</p>
    </Section>
  );
}

function AIAnalyzeInsights({ ai }) {
  if (!ai) return null;
  if (ai.error) return <AIError message={ai.error} />;
  return (
    <Section title="AI insights">
      {ai.summary && <p className="ai-summary">{ai.summary}</p>}
      <AIList title="Things the client may expect but did not say" items={ai.assumptions} />
      <AIList title="More questions to ask" items={ai.questions} />
      <AIList title="Extra risks" items={ai.risks} flag />
      <p className="muted small">
        Written by {ai.model}. AI can make mistakes, so check it before you use it.
      </p>
    </Section>
  );
}

function AIScopeOpinion({ ai }) {
  if (!ai) return null;
  if (ai.error) return <AIError message={ai.error} />;
  return (
    <Section
      title="AI second opinion"
      action={
        <span className={`pill ${ai.agrees_with_rules ? "agree" : "differ"}`}>
          {ai.agrees_with_rules ? "Matches the rules" : "Differs from the rules"}
        </span>
      }
    >
      <p className="ai-summary">
        <strong>{ai.verdict}.</strong> {ai.reasoning}
      </p>
      {!ai.agrees_with_rules && (
        <p className="ai-note">
          The AI and the rule check disagree. Read your agreement and decide for yourself.
        </p>
      )}
      {ai.reply && (
        <>
          <h4 className="ai-sub">AI reply draft</h4>
          <p className="reply">{ai.reply}</p>
          <CopyButton label="Copy AI reply" text={ai.reply} />
        </>
      )}
      <p className="muted small">
        Written by {ai.model}. AI can make mistakes, so check it before you use it.
      </p>
    </Section>
  );
}

/* ---------- Message analyzer ---------- */

function AnalyzeResult({ result }) {
  const facts = [
    ["Project type", result.project_type, result.project_type === "Unknown"],
    ["Budget", result.budget, !result.budget],
    ["Deadline", result.deadline, !result.deadline],
  ];

  return (
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
              <span className="chip" key={r}>
                {r}
              </span>
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

      <AIAnalyzeInsights ai={result.ai} />
      <p className="note">{result.plan?.note}</p>
    </div>
  );
}

function AnalyzeView() {
  const [message, setMessage] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [useAI, setUseAI] = useState(false);
  const aiStatus = useAIStatus();
  const aiOn = useAI && aiReady(aiStatus);

  async function run() {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      setResult(await post("/analyze", { message, use_ai: aiOn }));
    } catch {
      setError(CONNECTION_ERROR);
    }
    setLoading(false);
  }

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
          <AIToggle checked={useAI} onChange={setUseAI} status={aiStatus} />
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
        {error && (
          <p className="alert" role="alert">
            {error}
          </p>
        )}
        {loading && <Loading slow={aiOn} />}
        {!loading && !result && !error && (
          <EmptyState
            title="Your project plan will appear here"
            text="Paste a client message and build the plan. You will get the requirements, what is missing, questions to ask and the risks."
          />
        )}

        {result && <AnalyzeResult result={result} />}
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

function ScopeResult({ result }) {
  return (
    <div className="panel result">
      <div className={`verdict ${VERDICT_STYLE[result.verdict] || "warn"}`}>
        <strong>{result.verdict}</strong>
        <span>{result.explanation}</span>
      </div>

      <div className="split">
        <Section title="Covered by the agreement">
          {result.in_scope?.length ? (
            <ul className="plain">
              {result.in_scope.map((i) => (
                <li key={i}>{i}</li>
              ))}
            </ul>
          ) : (
            <p className="muted">Nothing found.</p>
          )}
        </Section>
        <Section title="Not in the agreement">
          {result.out_of_scope?.length ? (
            <ul className="flags">
              {result.out_of_scope.map((i) => (
                <li key={i}>{i}</li>
              ))}
            </ul>
          ) : (
            <p className="muted">Nothing found.</p>
          )}
        </Section>
      </div>

      {result.revision_note && <p className="callout">{result.revision_note}</p>}

      <Section
        title="Suggested reply"
        action={<CopyButton label="Copy reply" text={result.suggested_reply} />}
      >
        <p className="reply">{result.suggested_reply}</p>
      </Section>

      <AIScopeOpinion ai={result.ai} />
      <p className="note">{result.note}</p>
    </div>
  );
}

function ScopeView() {
  const [agreement, setAgreement] = useState("");
  const [request, setRequest] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [useAI, setUseAI] = useState(false);
  const aiStatus = useAIStatus();
  const aiOn = useAI && aiReady(aiStatus);

  async function run() {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      setResult(await post("/scope-check", { agreement, new_request: request, use_ai: aiOn }));
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
          <AIToggle checked={useAI} onChange={setUseAI} status={aiStatus} />
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
        {error && (
          <p className="alert" role="alert">
            {error}
          </p>
        )}
        {loading && <Loading slow={aiOn} />}
        {!loading && !result && !error && (
          <EmptyState
            title="No scope check yet"
            text="Add your agreement and the client's new request. You will see whether the work is covered and get a polite reply you can send."
          />
        )}

        {result && <ScopeResult result={result} />}
      </div>
    </div>
  );
}

/* ---------- Proposals ---------- */

function ProposalResult({ result }) {
  const ai = result.ai;
  const facts = [
    ["Project type", result.project_type, result.project_type === "Unknown"],
    ["Budget", result.budget, !result.budget],
    ["Deadline", result.deadline, !result.deadline],
  ];

  return (
    <div className="panel result">
      <dl className="facts">
        {facts.map(([label, value, missing]) => (
          <div key={label} className={missing ? "fact is-missing" : "fact"}>
            <dt>{label}</dt>
            <dd>{missing ? "Not mentioned" : value}</dd>
          </div>
        ))}
      </dl>

      {ai?.proposal && (
        <Section
          title="AI-written proposal"
          action={<CopyButton label="Copy proposal" text={ai.proposal} />}
        >
          <p className="reply pre">{ai.proposal}</p>
          <p className="muted small">
            Written by {ai.model}. AI can make mistakes. Check every detail before you send it.
          </p>
        </Section>
      )}
      {ai?.error && <AIError message={ai.error} />}

      <Section
        title={ai?.proposal ? "Basic draft (no AI)" : "Proposal draft"}
        action={<CopyButton label="Copy draft" text={result.draft} />}
      >
        <p className="reply pre">{result.draft}</p>
      </Section>

      {result.milestones?.length > 0 && (
        <Section title="Suggested milestones">
          {result.milestones.map((m) => (
            <div key={m.title} className="milestone">
              <h4 className="ai-sub">{m.title}</h4>
              <ul className="plain">
                {m.tasks.map((t) => (
                  <li key={t}>{t}</li>
                ))}
              </ul>
            </div>
          ))}
        </Section>
      )}

      <p className="note">{result.note}</p>
    </div>
  );
}

function ProposalView() {
  const [message, setMessage] = useState("");
  const [name, setName] = useState("");
  const [skills, setSkills] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [useAI, setUseAI] = useState(false);
  const aiStatus = useAIStatus();
  const aiOn = useAI && aiReady(aiStatus);

  async function run() {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      setResult(
        await post("/proposal", {
          message,
          freelancer_name: name,
          skills,
          use_ai: aiOn,
        }),
      );
    } catch {
      setError(CONNECTION_ERROR);
    }
    setLoading(false);
  }

  return (
    <div className="workspace">
      <div className="input-col">
        <div className="panel">
          <label htmlFor="p-message">Client message</label>
          <textarea
            id="p-message"
            rows={7}
            placeholder="Paste the job post or the message your client sent you."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
          />
          <label htmlFor="p-name">Your name</label>
          <input
            id="p-name"
            type="text"
            placeholder="For example: Asima"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <label htmlFor="p-skills">Your skills and experience</label>
          <textarea
            id="p-skills"
            rows={3}
            placeholder="For example: React and FastAPI developer, 2 years of experience."
            value={skills}
            onChange={(e) => setSkills(e.target.value)}
          />
          <AIToggle checked={useAI} onChange={setUseAI} status={aiStatus} />
          <div className="actions">
            <button
              type="button"
              className="btn btn-primary"
              onClick={run}
              disabled={loading || !message.trim()}
            >
              {loading ? "Writing" : "Write proposal"}
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
        {error && (
          <p className="alert" role="alert">
            {error}
          </p>
        )}
        {loading && <Loading slow={aiOn} />}
        {!loading && !result && !error && (
          <EmptyState
            title="Your proposal will appear here"
            text="Paste a client message and add your name and skills. You get a ready draft, suggested milestones and the questions to ask. Turn on AI for a more natural version."
          />
        )}
        {result && <ProposalResult result={result} />}
      </div>
    </div>
  );
}

/* ---------- History ---------- */

function formatDate(iso) {
  try {
    return new Date(iso).toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
  } catch {
    return iso;
  }
}

const KIND_LABEL = { analyze: "Message analysis", scope: "Scope check", proposal: "Proposal" };

function SavedInput({ record }) {
  const { input } = record;
  return (
    <div className="saved-input">
      {record.kind === "scope" ? (
        <>
          <h4>Original agreement</h4>
          <p>{input.agreement}</p>
          <h4>New client request</h4>
          <p>{input.new_request}</p>
        </>
      ) : (
        <>
          <h4>Client message</h4>
          <p>{input.message}</p>
          {record.kind === "proposal" && (input.freelancer_name || input.skills) && (
            <>
              <h4>Your details</h4>
              <p>{[input.freelancer_name, input.skills].filter(Boolean).join(" · ")}</p>
            </>
          )}
        </>
      )}
    </div>
  );
}

function SavedResult({ record }) {
  if (record.kind === "scope") return <ScopeResult result={record.result} />;
  if (record.kind === "proposal") return <ProposalResult result={record.result} />;
  return <AnalyzeResult result={record.result} />;
}

function HistoryView() {
  const [items, setItems] = useState(null);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState("");

  async function load() {
    try {
      setItems(await get("/history"));
      setError("");
    } catch {
      setError(CONNECTION_ERROR);
      setItems([]);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function open(id) {
    try {
      setSelected(await get(`/history/${id}`));
    } catch {
      setError(CONNECTION_ERROR);
    }
  }

  async function remove(id) {
    if (!window.confirm("Delete this item from your history?")) return;
    try {
      await del(`/history/${id}`);
      if (selected?.id === id) setSelected(null);
      load();
    } catch {
      setError(CONNECTION_ERROR);
    }
  }

  return (
    <div className="workspace">
      <div className="input-col">
        <div className="panel history-panel">
          <div className="section-head">
            <h3>Saved work</h3>
            <button type="button" className="btn btn-quiet" onClick={load}>
              Refresh
            </button>
          </div>

          {error && (
            <p className="alert" role="alert">
              {error}
            </p>
          )}
          {items === null && <p className="muted">Loading</p>}
          {items && items.length === 0 && !error && (
            <p className="muted">
              Nothing saved yet. Every message analysis and scope check you run is saved here
              automatically.
            </p>
          )}

          <ul className="history-list">
            {items?.map((item) => (
              <li key={item.id} className={selected?.id === item.id ? "is-open" : ""}>
                <button type="button" className="history-open" onClick={() => open(item.id)}>
                  <span className={`badge ${item.kind}`}>{KIND_LABEL[item.kind]}</span>
                  <strong>{item.title}</strong>
                  <span className="meta">
                    {item.summary} · {formatDate(item.created_at)}
                  </span>
                </button>
                <button
                  type="button"
                  className="history-delete"
                  onClick={() => remove(item.id)}
                  aria-label={`Delete: ${item.title}`}
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="output-col">
        {!selected && (
          <EmptyState
            title="Pick an item to review"
            text="Open any saved analysis or scope check to see the full result again."
          />
        )}
        {selected && (
          <>
            <div className="panel">
              <SavedInput record={selected} />
            </div>
            <div className="gap" />
            <SavedResult record={selected} />
          </>
        )}
      </div>
    </div>
  );
}

/* ---------- Sign in ---------- */

function AuthScreen({ onSignedIn }) {
  const [mode, setMode] = useState("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const isLogin = mode === "login";

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await post(isLogin ? "/auth/login" : "/auth/register", {
        name,
        email,
        password,
      });
      onSignedIn(data);
    } catch (err) {
      setError(err.status ? err.message : CONNECTION_ERROR);
    }
    setLoading(false);
  }

  function switchMode(next) {
    setMode(next);
    setError("");
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="brand brand-light">
          <span className="logo" aria-hidden="true">
            FP
          </span>
          <div>
            <strong>FreelancePilot</strong>
            <span>Plan before you quote</span>
          </div>
        </div>

        <h1>{isLogin ? "Welcome back" : "Create your account"}</h1>
        <p className="auth-sub">
          {isLogin
            ? "Sign in to see your saved plans, scope checks and proposals."
            : "Your work is saved to your own account. Nobody else can see it."}
        </p>

        <form onSubmit={submit}>
          {!isLogin && (
            <>
              <label htmlFor="a-name">Your name</label>
              <input
                id="a-name"
                type="text"
                autoComplete="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </>
          )}
          <label htmlFor="a-email">Email</label>
          <input
            id="a-email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <label htmlFor="a-password">Password</label>
          <input
            id="a-password"
            type="password"
            autoComplete={isLogin ? "current-password" : "new-password"}
            minLength={isLogin ? undefined : 8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {!isLogin && <p className="muted small">Use at least 8 characters.</p>}

          {error && (
            <p className="alert" role="alert">
              {error}
            </p>
          )}

          <button type="submit" className="btn btn-primary auth-submit" disabled={loading}>
            {loading ? "Please wait" : isLogin ? "Sign in" : "Create account"}
          </button>
        </form>

        <p className="auth-switch">
          {isLogin ? "New here?" : "Already have an account?"}{" "}
          <button
            type="button"
            className="link"
            onClick={() => switchMode(isLogin ? "register" : "login")}
          >
            {isLogin ? "Create an account" : "Sign in"}
          </button>
        </p>
      </div>
    </div>
  );
}

/* ---------- App shell ---------- */

const NAV = [
  { id: "analyze", label: "Message analyzer", icon: "analyze" },
  { id: "scope", label: "Scope check", icon: "scope" },
  { id: "history", label: "History", icon: "history" },
  { id: "proposals", label: "Proposals", icon: "proposal" },
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
  proposals: {
    h: "Write a proposal for a client",
    p: "Turn the client's message into a clear draft with milestones and questions.",
  },
  history: {
    h: "Your saved work",
    p: "Every analysis and scope check is saved here so you can come back to it.",
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
  const [session, setSession] = useState(null);
  const [checking, setChecking] = useState(() => Boolean(loadToken()));

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    try {
      localStorage.setItem("fp-theme", theme);
    } catch {
      /* storage not available */
    }
  }, [theme]);

  // If a saved token exists, check that it is still valid
  useEffect(() => {
    onUnauthorized = () => {
      clearToken();
      setSession(null);
    };
    if (!loadToken()) return;
    get("/auth/me")
      .then((user) => setSession({ user }))
      .catch(() => clearToken())
      .finally(() => setChecking(false));
  }, []);

  function handleSignedIn(data) {
    saveToken(data.token);
    setSession({ user: data.user });
    setTab("analyze");
  }

  async function signOut() {
    try {
      await post("/auth/logout");
    } catch {
      /* sign out locally even if the server is not reachable */
    }
    clearToken();
    setSession(null);
  }

  if (checking) {
    return (
      <div className="auth-shell">
        <p className="muted">Loading</p>
      </div>
    );
  }
  if (!session) return <AuthScreen onSignedIn={handleSignedIn} />;

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="logo" aria-hidden="true">
            FP
          </span>
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

        <div className="account">
          <div>
            <strong>{session.user.name}</strong>
            <span>{session.user.email}</span>
          </div>
          <button type="button" onClick={signOut}>
            Sign out
          </button>
        </div>

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
        {tab === "analyze" && <AnalyzeView />}
        {tab === "scope" && <ScopeView />}
        {tab === "proposals" && <ProposalView />}
        {tab === "history" && <HistoryView />}
      </main>
    </div>
  );
}
