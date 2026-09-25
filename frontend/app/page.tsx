import Link from "next/link";

/**
 * The commercial front door, styled after floormind.pages.dev.
 *
 * Every claim on it is something the code does today, and nothing is priced: the plan
 * (docs/COMMERCIAL_PLAN.md) says prices and allowances wait for measured operating cost,
 * and never to invent them. A respondent still gets one click to their survey.
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

const PLANS = [
  {
    name: "Pilot",
    audience: "Employee feedback for one company, in its own private workspace.",
    price: "By arrangement",
    cadence: "Terms agreed with each pilot company",
    features: [
      "Owner, admin, author, analyst and respondent roles",
      "Google or Microsoft sign-in",
      "Conversational surveys in 8 languages",
      "Retention set by the workspace owner",
    ],
    popular: true,
  },
  {
    name: "Starter",
    audience: "One person running occasional surveys.",
    price: "After the pilot",
    cadence: "Priced once operating costs are measured",
    features: ["Survey categories as they are added", "A monthly allowance of completed responses"],
    popular: false,
  },
  {
    name: "Team",
    audience: "Shared workspaces, collaboration and higher usage.",
    price: "After the pilot",
    cadence: "Priced once operating costs are measured",
    features: ["Everything in Starter", "Named seats for authors and analysts"],
    popular: false,
  },
];

const SECURITY = [
  {
    area: "Company isolation",
    how: "Every customer table carries its workspace, enforced by forced PostgreSQL row-level security. Production refuses to start on a database role that could bypass it.",
  },
  {
    area: "Sign-in",
    how: "Google with a verified address, or Microsoft with an account linked in advance. An unknown identity is refused, never created.",
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
        <span className="eyebrow">Employee feedback, as a conversation</span>
        <h1>
          Surveys your people <span className="grad">answer by talking</span>
        </h1>
        <p className="lede">
          Elenchus runs each survey as a short chat. The engine decides which question is
          current and when the survey is finished; the model helps ask and record, and
          nothing it says is kept until it has been checked.
        </p>
        <div className="landing-ctas">
          <Link className="btn btn-primary btn-lg" href="/respond">
            Answer a survey
          </Link>
          <Link className="btn btn-secondary btn-lg" href="#pricing">
            See the pilot
          </Link>
        </div>
        <div className="landing-badges">
          <span className="badge">Private workspace per company</span>
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
          <h2>Start with a pilot</h2>
          <p className="subtitle">
            Plans are priced from measured running costs, so none is published until those
            numbers exist. Pilots run now, on agreed terms.
          </p>
        </div>
        <div className="landing-grid three plans">
          {PLANS.map((plan) => (
            <div className={plan.popular ? "plan popular" : "plan"} key={plan.name}>
              {plan.popular ? <span className="plan-flag">Open now</span> : null}
              <h3>{plan.name}</h3>
              <p className="for">{plan.audience}</p>
              <p className="price">{plan.price}</p>
              <p className="cadence">{plan.cadence}</p>
              <ul>
                {plan.features.map((feature) => (
                  <li key={feature}>{feature}</li>
                ))}
              </ul>
            </div>
          ))}
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
            Sign in
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
