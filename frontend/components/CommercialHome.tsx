"use client";

import Link from "next/link";
import { useState } from "react";

const STAGES = ["Describe", "Review", "Share", "Answer", "Explore", "Summarise"];
const REASONS = ["Clearer handovers", "More time", "Nothing to change"];
const SAMPLE = [
  { id: 1, shift: "Day", rating: 3, minutes: 3, reason: "Clearer handovers", quote: "A short handover checklist would help us know what is still outstanding." },
  { id: 2, shift: "Day", rating: 4, minutes: 2, reason: "Nothing to change", quote: "The team talks things through well. Keep the quick morning catch-up." },
  { id: 3, shift: "Evening", rating: 2, minutes: 4, reason: "Clearer handovers", quote: "We sometimes find out about equipment problems after the day team has left." },
  { id: 4, shift: "Evening", rating: 4, minutes: 3, reason: "Clearer handovers", quote: "Most shifts go well. A written note about unfinished work would make the changeover easier." },
  { id: 5, shift: "Day", rating: 3, minutes: 5, reason: "More time", quote: "Please leave a few minutes between shifts so we can ask questions." },
  { id: 6, shift: "Evening", rating: 5, minutes: 2, reason: "Clearer handovers", quote: "A shared checklist could help new starters. Experienced colleagues already know the routine." },
];

export function CommercialHome() {
  const [stage, setStage] = useState(0);
  const [question, setQuestion] = useState("How clearly is work handed over between shifts?");
  const [rating, setRating] = useState<number | null>(null);
  const [reason, setReason] = useState(REASONS[0]);
  const [comment, setComment] = useState("");
  const [finished, setFinished] = useState(false);
  const [filter, setFilter] = useState("All shifts");
  const [evidence, setEvidence] = useState(false);

  const responses = finished && rating !== null
    ? [...SAMPLE, { id: 9, shift: "Day", rating, minutes: 3, reason, quote: comment.trim() }]
    : SAMPLE;
  const visible = responses.filter((row) => filter === "All shifts" || row.shift === filter);
  const started = visible.length + (filter === "All shifts" ? 2 : 1);
  const supporters = visible.filter((row) => row.reason === "Clearer handovers");
  const medianTimes = visible.map((row) => row.minutes).sort((a, b) => a - b);
  const middle = Math.floor(medianTimes.length / 2);
  const median = medianTimes.length % 2 ? medianTimes[middle] : (medianTimes[middle - 1] + medianTimes[middle]) / 2;

  return (
    <div className="commercial">
      <section className="commercial-hero" aria-labelledby="commercial-title">
        <div>
          <span className="commercial-kicker"><span aria-hidden="true">✳</span> A KapkotiSolution product</span>
          <h1 id="commercial-title">Listen closer.<br /><em>Know what<br className="wide-break" /> to change.</em></h1>
          <p className="commercial-lede">Turn employee feedback into a useful conversation. Ask better questions, hear the detail, and follow every finding back to what people said.</p>
          <div className="commercial-actions">
            <a className="btn btn-primary btn-lg" href="#walkthrough">Explore the experience <span aria-hidden="true">↗</span></a>
            <Link className="btn btn-secondary btn-lg" href="/demo">I have a demo pass</Link>
          </div>
          <p className="commercial-note">Three surveys to try. Included with a qualifying KapkotiSolution product.</p>
        </div>
        <div className="commercial-hero-art" aria-label="Illustrative employee conversation and finding">
          <div className="commercial-art-ring" aria-hidden="true" />
          <div className="commercial-chat-sheet">
            <div className="commercial-sheet-header"><span className="commercial-mark" aria-hidden="true">e.</span><span>One conversation.<small>A little more understanding.</small></span><span className="commercial-sample">Sample</span></div>
            <p className="commercial-bubble interviewer">What would make your next shift easier?</p>
            <p className="commercial-bubble respondent">Knowing what was left unfinished before we take over.</p>
            <p className="commercial-bubble interviewer">What would help you get that information?</p>
            <p className="commercial-bubble respondent">A short checklist we can both see.</p>
            <div className="commercial-conversation-foot"><span className="commercial-dot" /> A suggestion, in their own words</div>
          </div>
          <div className="commercial-insight-note"><span className="commercial-kicker">From words to a finding</span><strong>Make the handover clearer.</strong><p>Open the evidence. Understand the context. Decide what to do next.</p><a href="#insights">Explore sample findings <span aria-hidden="true">↗</span></a></div>
        </div>
      </section>

      <div className="commercial-promises" aria-label="Product principles"><span>Questions you review</span><span>Conversations with context</span><span>Findings with evidence</span><span>Your company&apos;s own workspace</span></div>

      <section className="commercial-section" id="walkthrough" aria-labelledby="walkthrough-title">
        <div className="commercial-section-heading"><div><span className="commercial-kicker">01 / See the whole journey</span><h2 id="walkthrough-title">A question is just<br />the beginning.</h2></div><p>Explore an employee handover survey from the first idea to the final recap. This walkthrough uses illustrative data. It makes no AI calls, and your sample text stays in this tab.</p></div>
        <div className="commercial-walkthrough">
          <div className="commercial-steps" role="group" aria-label="Walkthrough stages">
            {STAGES.map((name, index) => <button type="button" key={name} aria-pressed={stage === index} onClick={() => setStage(index)}><span>{String(index + 1).padStart(2, "0")}</span>{name}<span aria-hidden="true">↗</span></button>)}
          </div>
          <div className="commercial-stage" aria-live="polite">
            <span className="commercial-sample">Interactive sample / {STAGES[stage]}</span>
            {stage === 0 && <><h3>Start with the decision you need to make.</h3><p>Tell Elenchus what you need to learn. You review the questions before anyone answers.</p><label className="commercial-field">Example survey brief<textarea readOnly value="I want to understand what makes shift handovers difficult, and what our team would change. Keep it to three questions." rows={4} /></label><button className="btn btn-primary" onClick={() => setStage(1)}>Open the sample draft</button></>}
            {stage === 1 && <><h3>Your questions. Your final say.</h3><p>Try editing the first question. In the real demo, you can also change the answer types, choices and follow-up settings.</p><label className="commercial-field">1 / Rating, one to five<input maxLength={200} value={question} onChange={(event) => setQuestion(event.target.value)} /></label><div className="commercial-question-row"><span>2 / Single choice</span><strong>What would improve your next handover?</strong></div><div className="commercial-question-row"><span>3 / Optional comment</span><strong>What would you like us to understand?</strong></div><button className="btn btn-primary" disabled={!question.trim()} onClick={() => setStage(2)}>Review sharing</button></>}
            {stage === 2 && <><h3>Invite a conversation.</h3><p>Publishing freezes the questions. Share the survey link with your team. They can answer without creating a separate account.</p><div className="commercial-disclosure"><strong>Clear before the first answer</strong><p>We do not ask respondents for a name or email. Authors see participant labels. People can still identify themselves through what they write.</p></div><p className="commercial-note">The real demo allows twenty respondent sessions for each survey, including unfinished sessions.</p><button className="btn btn-primary" onClick={() => setStage(3)}>Answer the sample</button></>}
            {stage === 3 && <><h3>{question.trim() || "How clearly is work handed over between shifts?"}</h3><p>One means very unclear. Five means very clear.</p><div className="commercial-rating" role="group" aria-label="Handover clarity rating">{[1, 2, 3, 4, 5].map((value) => <button key={value} aria-pressed={rating === value} onClick={() => setRating(value)}>{value}</button>)}</div><label className="commercial-field">What would improve your next handover?<select value={reason} onChange={(event) => setReason(event.target.value)}>{REASONS.map((item) => <option key={item}>{item}</option>)}</select></label><label className="commercial-field">Anything else? <span>(optional, sample text only)</span><textarea value={comment} maxLength={500} rows={2} onChange={(event) => setComment(event.target.value)} /></label><button className="btn btn-primary" disabled={rating === null} onClick={() => { setFinished(true); setFilter("All shifts"); setStage(4); }}>See the sample results</button></>}
            {stage === 4 && <><h3>See participation and patterns together.</h3><p>{finished ? "Your sample answer is now included in the preview below." : "Six illustrative responses and two unfinished sessions show how the dashboard works."}</p><div className="commercial-mini-stats"><div><b>{responses.length}</b><span>Completed</span></div><div><b>{Math.round(responses.length / (responses.length + 2) * 100)}%</b><span>Completion</span></div><div><b>1 to 5</b><span>Actual rating scale</span></div></div><a className="btn btn-secondary" href="#insights">Explore the dashboard</a><button className="btn btn-primary" onClick={() => setStage(5)}>Read the sample recap</button></>}
            {stage === 5 && <><h3>Useful findings, with their working.</h3><div className="commercial-disclosure"><span className="commercial-kicker">Illustrative recap</span><strong>A clearer handover could help.</strong><p>Some respondents asked for written handover notes. Others described a routine that already works well.</p></div><p><strong>Respondent suggestion:</strong> a shared handover checklist.</p><p><strong>AI-proposed next step, illustrative:</strong> trial a checklist with one team and ask whether it helps. A person should assess this proposal.</p><p className="commercial-note">This is a small sample. It does not establish the cause of a problem or represent every employee.</p><a className="btn btn-primary" href="#insights" onClick={() => setEvidence(true)}>Inspect the supporting answers</a></>}
          </div>
        </div>
      </section>

      <section className="commercial-section commercial-insights" id="insights" aria-labelledby="insights-title">
        <div className="commercial-section-heading"><div><span className="commercial-kicker">02 / A dashboard you can question</span><h2 id="insights-title">The numbers tell you where.<br />The words tell you more.</h2></div><p>Change the shift filter and inspect the source answers. Every figure below comes from the same small illustrative dataset.</p></div>
        <div className="commercial-dashboard">
          <div className="commercial-dashboard-head"><div><strong>Shift handover pulse</strong><span>Sample dataset / one survey / {visible.length} completed responses</span></div><label>Show<select value={filter} onChange={(event) => { setFilter(event.target.value); setEvidence(false); }}><option>All shifts</option><option>Day</option><option>Evening</option></select></label></div>
          <div className="commercial-kpis"><div><span>Sessions started</span><b>{started}</b><small>Includes unfinished sessions</small></div><div><span>Responses completed</span><b>{visible.length}</b><small>{started - visible.length} still unfinished</small></div><div><span>Completion rate</span><b>{Math.round(visible.length / started * 100)}<i>%</i></b><small>{visible.length} completed / {started} started</small></div><div><span>Median response time</span><b>{median}<i> min</i></b><small>Completed responses only</small></div></div>
          <div className="commercial-dashboard-body"><div><div className="commercial-chart-heading"><h3>How clear is the handover?</h3><span>Rating distribution / n = {visible.length}</span></div><div className="commercial-bars" aria-label="Rating counts">{[1, 2, 3, 4, 5].map((score) => { const count = visible.filter((row) => row.rating === score).length; return <div key={score}><span>{score} / 5</span><div className="commercial-bar-track"><span style={{ inlineSize: `${count / visible.length * 100}%` }} /></div><b>{count}</b></div>; })}</div><p className="commercial-note">Counts of completed responses, on the question&apos;s actual scale. No invented score.</p></div><div className="commercial-finding"><span className="commercial-kicker">From the answers</span><h3>A clearer handover</h3><p><strong>{supporters.length} of {visible.length}</strong> completed respondents selected clearer handovers as their preferred improvement.</p><button className="commercial-text-button" aria-expanded={evidence} aria-controls="commercial-evidence" onClick={() => setEvidence(!evidence)}>{evidence ? "Close evidence" : "Read the supporting answers"} <span aria-hidden="true">↗</span></button><p className="commercial-note">A preference, not proof of a cause. Other views remain in the results.</p></div></div>
          {evidence && <div className="commercial-evidence" id="commercial-evidence"><h3>The words behind this finding</h3>{supporters.map((row) => <blockquote key={row.id}><p>{row.quote || "No additional comment supplied."}</p><cite>Participant {row.id} / {row.shift} shift / selected clearer handovers</cite></blockquote>)}<p className="commercial-note">Illustrative responses. Identifying details are not collected in this sample.</p></div>}
        </div>
      </section>

      <section className="commercial-section" id="summaries"><div className="commercial-section-heading"><div><span className="commercial-kicker">03 / A recap that stays accountable</span><h2>Read the headline.<br />Keep the evidence.</h2></div><p>Summaries should help you understand the feedback while keeping the details in reach.</p></div><div className="commercial-summary-grid"><article><span>01</span><h3>What people said</h3><p>A short recap, themes, exact counts and the answers that support them. Conflicting views and small samples stay visible.</p></article><article><span>02</span><h3>What people suggested</h3><p>Suggestions attributed to respondents remain tied to their words. Nothing is presented as an employee request unless someone actually asked for it.</p></article><article><span>03</span><h3>What you might do next</h3><p>AI-proposed actions are labelled for your review. Take the report with you as CSV or a PDF, with its scope and caveats intact.</p></article></div></section>

      <section className="commercial-section" id="access"><div className="commercial-section-heading"><div><span className="commercial-kicker">04 / Room to try. A reason to stay.</span><h2>One useful product.<br />Part of a bigger toolkit.</h2></div><p>No separate Elenchus subscription. Start with a private demo; unlock company access through a qualifying KapkotiSolution product.</p></div><div className="commercial-access-grid"><article className="commercial-demo-offer"><span className="commercial-kicker">The private demo</span><h3>Try the whole journey.</h3><div className="commercial-offer-number">3 <span>surveys, on us</span></div><ul><li>Up to 10 questions per survey</li><li>20 respondent sessions per survey</li><li>14 days of access from pass issue</li><li>Real invitations, conversations and results</li><li>A private workspace for your team&apos;s trial</li></ul><Link className="btn btn-primary btn-lg" href="/demo">Enter your demo pass</Link><a className="commercial-text-button" href="mailto:pawankapkoti3889@gmail.com?subject=Elenchus%20demo%20pass">Request a pass <span aria-hidden="true">↗</span></a><p className="commercial-note">Passes are issued manually in this phase. Editing is free; deleting a survey does not reset the three-survey allowance.</p></article><article className="commercial-customer-offer"><span className="commercial-kicker">For KapkotiSolution customers</span><h3>Included. For your company.</h3><p>Buy a qualifying product and get full Elenchus features at no extra product charge, with an agreed monthly response allowance.</p><div className="commercial-product-links"><a href="https://sedno-demo.pages.dev">Sedno <span>Business operations ↗</span></a><a href="https://floormind.pages.dev">FloorMind <span>Factory intelligence ↗</span></a></div><ul><li>Unlimited survey creation</li><li>Company-wide access, activated after purchase verification</li><li>Active subscriptions qualify while active</li><li>One-time purchases qualify permanently</li></ul><a className="btn btn-secondary btn-lg" href="mailto:pawankapkoti3889@gmail.com?subject=Activate%20Elenchus%20customer%20access">Request customer activation</a></article></div></section>

      <section className="commercial-section" id="roadmap"><div className="commercial-section-heading"><div><span className="commercial-kicker">05 / Where we are going</span><h2>A clear path forward.</h2></div><p>The release follows these stages. Features appear as available only when the corresponding service is ready.</p></div><div className="commercial-roadmap"><article><span className="commercial-sample">First / Discover</span><h3>Explore without signing in</h3><p>The interactive walkthrough, sample dashboard and evidence-led summary explain the experience before you request a pass.</p></article><article><span className="commercial-sample">Then / Try and use</span><h3>Your complete feedback loop</h3><p>Private passes, three surveys, anonymous respondent entry, results, summaries and exports. Qualifying customers receive manually activated access.</p></article><article><span className="commercial-sample">Later / Planned</span><h3>A conversational front door</h3><p>A chatbot will ask for your email, company and survey goal, verify your details and issue a demo pass. Cross-survey comparisons and action tracking follow later.</p></article></div></section>

      <section className="commercial-section commercial-faq"><span className="commercial-kicker">A few useful details</span><h2>Before you start.</h2><details><summary>What happens after my third survey?</summary><p>You can continue using existing surveys and reading results within the demo&apos;s response and time limits. New survey creation stops. A qualifying KapkotiSolution purchase can unlock your workspace after verification.</p></details><details><summary>Do respondents need a Google or Microsoft account?</summary><p>Respondents entering through a demo survey link do not need a separate sign-in. We do not ask them for a name or email. Their written answers can still contain identifying details, so the invitation explains this before they respond.</p></details><details><summary>Is the dashboard above live customer data?</summary><p>No. It is an interactive sample. Its figures are calculated from illustrative responses. Your real workspace shows only your company&apos;s own results.</p></details><details><summary>What does free customer access include?</summary><p>Full features and unlimited survey creation at no additional Elenchus product charge. A monthly response allowance is agreed when access is activated. Existing subscriptions qualify while active; one-time purchases qualify permanently.</p></details><details><summary>What is planned for the chatbot?</summary><p>It will help visitors explain their needs and request a pass. Email verification and application rules will control pass issuance and allowances. The chatbot is planned for a later phase.</p></details></section>

      <section className="commercial-final"><span className="commercial-kicker">Start with one good question</span><h2>What is your team<br />trying to tell you?</h2><div className="commercial-actions"><Link className="btn btn-primary btn-lg" href="/demo">Enter a demo pass</Link><a className="btn btn-secondary btn-lg" href="#walkthrough">Explore the sample</a></div></section>
      <footer className="commercial-footer"><Link href="/" className="commercial-footer-brand">elenchus<span>A KapkotiSolution product</span></Link><p>Employee feedback, with the conversation intact.</p><div><a href="mailto:pawankapkoti3889@gmail.com">Contact</a><a href="https://github.com/Pawansingh3889/elenchus">Source</a><Link href="/signin">Customer sign-in</Link></div></footer>
    </div>
  );
}
