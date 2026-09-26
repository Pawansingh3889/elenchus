import Link from "next/link";

/**
 * The front door, styled after floormind.pages.dev.
 *
 * Free with sign-in since 25 Sep 2026: anyone who signs in gets an account and can answer
 * the open surveys. Every claim on the page is something the code does today, and it
 * says plainly what signing in stores.
 */

const REPO = "https://github.com/Pawansingh3889/elenchus";

const STEPS = [
  {
    title: "Describe the survey",
    body: "Say what you need to learn in plain words, and a draft comes back as questions you review and edit. Or write it by hand.",
  },
  {
    title: "Publish it",
    body: "Publishing freezes the questions, so nobody's answer is re-pointed at wording they never saw. A new question set is a new survey.",
  },
  {
    title: "People answer by talking",
    body: "Each person has a short conversation in their own language, on their phone, with follow-ups when an answer is thin.",
  },
  {
    title: "Read what was said",
    body: "Results come with the structured answers and the full transcript behind every one, so a finding traces back to a person's words.",
  },
];

const RAILS = [
  {
    title: "The engine owns the survey",
    body: "Which question is current, when the survey is finished and how many follow-ups are spent are decided by code, not by the model.",
  },
  {
    title: "Answers are checked before they are kept",
    body: "Everything the model records arrives through a schema-constrained tool call and is validated against what the person actually said.",
  },
  {
    title: "Every turn is traced",
    body: "Each model call is recorded with its tokens, cost and latency, and three hosted tiers fail over in order when one is down.",
  },
];

const PROOF = [
  { value: "1,250+", label: "automated backend tests" },
  { value: "8", label: "respondent languages" },
  { value: "3", label: "model tiers with failover" },
  { value: "90 days", label: "default response retention" },
];

const FREE = [
  "Sign in with Google or Microsoft, and your account is made on the spot",
  "Answer every survey that is open to anyone signed in",
  "Talk it through in any of 8 languages, on your phone",
  "Your answers are recorded as you said them, and checked before they are kept",
];

const SECURITY = [
  {
    area: "Company isolation",
    how: "Every customer table carries its workspace, enforced by forced PostgreSQL row-level security. Production refuses to start on a database role that could bypass it.",
  },
  {
    area: "Sign-in",
    how: "Google with a verified address, or Microsoft. Your first sign-in creates a respondent account; an address that already has an account is never taken over by another sign-in.",
  },
  {
    area: "What we store",
    how: "Your email address, your name as the provider gives it, the time of each sign-in, and the answers and conversation of each survey you take.",
  },
  {
    area: "Access",
    how: "Five workspace roles. Only an owner or admin grants an analyst a survey, and every grant is recorded.",
  },
  {
    area: "Retention",
    how: "Responses are kept 90 days unless the owner sets otherwise. Expired answers and transcripts are purged, and each deletion is audited.",
  },
  {
    area: "Audit",
    how: "Account and access changes are written to append-only history in the same transaction as the change.",
  },
];

export default function Home() {
  return (
    <div className="landing">
      <section className="landing-hero">
        <span className="eyebrow">Free with sign-in</span>
        <h1>
          Surveys your people <span className="grad">answer by talking</span>
        </h1>
        <p className="lede">
          Elenchus runs each survey as a short chat. The engine decides which question is
          current and when the survey is finished; the model helps ask and record, and
          nothing it says is kept until it has been checked.
        </p>
        <div className="landing-ctas">
          <Link className="btn btn-primary btn-lg" href="/signin">
            Sign in free
          </Link>
          <Link className="btn btn-secondary btn-lg" href="/respond">
            Answer a survey
          </Link>
        </div>
        <div className="landing-badges">
          <span className="badge">Free, no card</span>
          <span className="badge">Google and Microsoft sign-in</span>
          <span className="badge">8 languages</span>
          <span className="badge">Every answer traceable</span>
        </div>
      </section>

      <section className="landing-section" id="how">
        <div className="section-head">
          <span className="eyebrow">How it works</span>
          <h2>From a question to an answer you can trust</h2>
        </div>
        <div className="landing-grid four">
          {STEPS.map((step, i) => (
            <div className="landing-card" key={step.title}>
              <span className="num">{i + 1}</span>
              <h3>{step.title}</h3>
              <p>{step.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="landing-section">
        <div className="section-head">
          <span className="eyebrow">On rails</span>
          <h2>The model is a collaborator, not the one in charge</h2>
          <p className="subtitle">
            A conversation is only useful if what gets recorded is what the person said.
          </p>
        </div>
        <div className="landing-grid three">
          {RAILS.map((rail) => (
            <div className="landing-card" key={rail.title}>
              <h3>{rail.title}</h3>
              <p>{rail.body}</p>
            </div>
          ))}
        </div>
        <div className="landing-proof">
          {PROOF.map((stat) => (
            <div className="stat" key={stat.label}>
              <b>{stat.value}</b>
              <span>{stat.label}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="landing-section" id="pricing">
        <div className="section-head">
          <span className="eyebrow">Pricing</span>
          <h2>Free. Sign in and start</h2>
          <p className="subtitle">
            There is no plan to choose and nothing to pay. Signing in is the whole of
            signing up.
          </p>
        </div>
        <div className="landing-grid one plans">
          <div className="plan popular">
            <span className="plan-flag">Free</span>
            <h3>Free</h3>
            <p className="for">For anyone with a Google or Microsoft account.</p>
            <p className="price">£0</p>
            <p className="cadence">No card, no trial that ends</p>
            <ul>
              {FREE.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
            <Link className="btn btn-primary btn-lg plan-cta" href="/signin">
              Sign in free
            </Link>
          </div>
        </div>
      </section>

      <section className="landing-section" id="security">
        <div className="section-head">
          <span className="eyebrow">Security</span>
          <h2>Each company&apos;s answers stay in its own workspace</h2>
        </div>
        <div className="landing-table">
          <table>
            <thead>
              <tr>
                <th scope="col">Area</th>
                <th scope="col">How it works</th>
              </tr>
            </thead>
            <tbody>
              {SECURITY.map((row) => (
                <tr key={row.area}>
                  <td>
                    <b>{row.area}</b>
                  </td>
                  <td>{row.how}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="landing-cta">
        <h2>Hear what your floor actually thinks</h2>
        <p>
          Start with one survey and one team. Answers are recorded as said, checked before
          they are kept, and traced back to the conversation they came from.
        </p>
        <div className="landing-ctas">
          <Link className="btn btn-primary btn-lg" href="/signin">
            Sign in free
          </Link>
          <a className="btn btn-ghost btn-lg" href={REPO}>
            View the repository
          </a>
        </div>
      </section>

      <footer className="landing-footer">
        <span>© 2026 Elenchus. Conversational surveys for employee feedback.</span>
        <a href={REPO}>Repository</a>
      </footer>
    </div>
  );
}
