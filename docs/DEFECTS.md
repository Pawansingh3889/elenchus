# Defects

One line per defect: what was actually wrong, how it surfaced, what fixed it, and the
commit to read for the reasoning. The commit message carries the depth; this file exists
so you can scan the list without reading fifty of them.

**Adding a row.** A defect earns a row when it was wrong in a way a user or an author
would notice, not when a refactor tidied something. State what broke, not what the code
did. Newest first. If it is still open, put it in the table below this one and say what
would close it.

**How found** is worth recording because it says where to look next. `live run` means a
real conversation against a real model, which is where most of the ones that matter came
from. `probe-then-verify` means a payload was built whose correct verdict was known, run
through the real pipeline, and kept only when the verdict flipped: that method found ten
holes in one afternoon and is the cheapest thing on this list.

## Open

| # | Defect | How found | What would close it |
|---|--------|-----------|---------------------|
| O13 | The grounding gate waves a short message through instead of judging it, so "i'm on the filleting line" grounds `Dispatch` and `Maintenance` as readily as `Processing`: under the positional-word floor nothing is checked at all. The original O12 sentence was never refused; it was accepted, against every option | measured, 13 Sep 2026, 35 labelled pairs (`backend/tests/fixtures/grounding_pairs.json`) | Judge a short message against the question's own options rather than skipping it: accept only the option it points to, which is what the option-relative similarity being built in Phase 5 measures |
| O14 | One shared word grounds an option that says the opposite: "I loved the training, the trainer was great" is accepted as `No formal training`, because `training` appears in both. Word overlap cannot see negation or contradiction | measured, 13 Sep 2026, same labelled set | Needs meaning, not words: an option must be the closest of the question's options to what was said, by a margin, not merely share a word with it. Word overlap stays a fast first pass, never the last word on a contradiction |
| O12 | The grounding gate cannot see synonymy, so a described answer is refused: "i'm on the filleting line" against options including `Processing` is the same answer in meaning and shares nothing a string matcher can use | live run | Mitigated on this branch rather than closed: the refusal now becomes a follow-up naming the options, so it costs a question instead of the answer. Closing it properly needs semantics the matcher cannot have, which means another model call, and this codebase has already measured a judge at ~40% false positives |
| O10 | The grounding gate is all-or-nothing on a multi-select, so one unsupported option throws away the whole answer. "if it's a bit over we re-ice it and carry on, if it's properly warm i call the supervisor" was rejected twice: first for `Take corrective action`, then for `No action taken`, while `Report to supervisor` and the write-in `re-ice it and carry on` were both properly grounded in the same payload | live run | Drop the unsupported item and keep the rest, which is the rule defect 24 established for recap findings and the quote gate already uses. The engine has the grounded items in hand at the moment it refuses them |
| O1 | `refine` silently declines an instruction and reports the refusal as a decision: asked twice, on two prompt versions, to convert a select to `long_text`, it kept the select and noted "kept Q10 as a select question" | live run, twice | Validate the refined draft against the instruction, or return what it declined as a field the builder can show, rather than trusting prose nobody diffs |
| O3 | A `503` from the provider on a summary is final: nothing retries it, so the run has no summary until somebody clicks again | live run | Retry the summary call once at the service boundary, the way the schema rejection already retries |
| O4 | `when_unclear` questions still draw no probes at all: across two surveys and sixteen probe-enabled questions, every follow-up came from `always_once` | live run, twice | Unclear whether this is a fault. The prompt says most answers need none, and the answers given were complete. Recorded so the next person does not rediscover it as a surprise |
| O5 | A write-in stores the literal word "other" instead of the answer: "i'm on the data science crew" was recorded as `{"other": "other"}`, so the author reads a write-in with nothing in it | live run | The grounding gate skips any recorded text under three words, so a one-word write-in is never checked for source at all. Either check write-ins whatever their length, or refuse a write-in whose value is the marker word |
| O6 | A multi-select write-in keeps one item and silently drops the rest: "mostly Tableau and a bit of Python scripting" was recorded as `{"options": [], "other": ["Python scripting"]}` | live run | Half an answer is worse than none, because nothing marks it as partial. Probably a prompt rule that every item named goes in the list, plus a gate that counts the write-ins against the conjunctions in what they said |
| O7 | A usable number is thrown away as unanswerable: "a couple, maybe three including the IT bit" on a number question recorded `{"unanswerable": ...}` | live run | The engine is right to refuse a vague number and wrong to end there: this is what a follow-up is for. Probably worth forcing a probe before `flag_unanswerable` is allowed on a number question |

## Fixed

| # | Defect | How found | Fix | Commit |
|---|--------|-----------|-----|--------|
| 30 | Was O2: `generate` ignored the brief's question count, returning 11 when asked for exactly 10, twice. The other half of O2, open questions drafted as selects, has since become the drafting rule (free text is never drafted; the write-in carries what the options cannot), so the count was the half left to hold | live run, twice | An unambiguous count in the brief is parsed conservatively (softened, ranged, scoped or conflicting counts do not bind), pinned as `minItems`/`maxItems` in the tool schema, and enforced by the validator with the one retry. A count past the generation cap is a 422 before any model call | this branch |
| 29 | A follow-up recorded the answer it was asked about: "What made your first week a solid 4?" recorded `{"rating": 4}`, and "Can you share more about why you feel that way?" recorded `{"rating": 2}`. Grounded, correctly shaped, about the right question, so every gate passed it, and the author read a follow-up whose answer was the number they already had | live run, twice on different models | A value identical to the one already banked for that question is refused: a re-ask that returns the same value has added nothing. Matched on the value rather than read from the probe's wording, which is guesswork | this branch |
| 28 | A grounding-gate refusal reached the respondent as `503 llm_unavailable`: every provider call returned 200, the gate refused the model's content twice, and the respondent was told to retry a turn that would fail identically. Their message was lost | live run | An answer the engine cannot accept is what a probe is for, so it asks rather than failing. Bounded by the probe budget; with none left the turn still fails | this branch |
| 27 | One quote past the cap lost the whole recap: the model returned seven against a limit of six, the schema refused it twice, and the author was told the assistant was unavailable while nothing was unavailable | live run | Trim to the cap before validating, on the rule the quote and finding gates already use: drop, do not refuse | this branch |
| 26 | A recap written before quotes carried pseudonyms was served indefinitely, naming colleagues beside what they said, because the only thing that expires one is a change in the response count | reading a real recap on the rebuilt results page | A stored recap whose quotes are not attributed to `Respondent N` is withheld and regenerated | this branch |
| 25 | A run summary refused on its merits was reported as `503 llm_unavailable`, telling the author to retry something that would fail identically and discarding the checker's reasons. Defect 23 fixed the recap path and left this one | reading the code after 23 | `ConflictError` carrying the checker's own words, with a boundary test pinning the 409 | this branch |
| 24 | A checker miscount cost the author the whole recap: it refused "most" against a tally of 7 yes and 1 no, and an all-or-nothing verdict threw away five sound findings with it | live run | Verdict names which findings it will not stand behind; those are dropped like unsupported quotes, headline stays all-or-nothing | [#34](https://github.com/Pawansingh3889/elenchus/pull/34) `19a6fb5` |
| 23 | A recap refused on its merits was reported as `503 llm_unavailable`, telling the author to retry something that would fail identically and discarding the checker's reasons | live run | `ConflictError` carrying the checker's own words | [#34](https://github.com/Pawansingh3889/elenchus/pull/34) `19a6fb5` |
| 22 | A forced follow-up could be asked, answered, and thrown away: the force lapsed when the probe was issued, so `move_on` returned on the turn the answer arrived. 3 of 16 forced probes lost their answer | live run | `move_on` withheld while a probe is outstanding; recording or flagging resolves it | [#34](https://github.com/Pawansingh3889/elenchus/pull/34) `5de7ced` |
| 21 | Every recap finding about the first question lost its counts, because `question_position or -1` treats position 0 as absent | its own test | `is None` rather than `or` | [#34](https://github.com/Pawansingh3889/elenchus/pull/34) `5505ddb` |
| 20 | The engine never asked a follow-up: 8 runs, 4 probe-enabled questions, ~90 model turns, 80 answers, none of them a probe. `allow_follow_ups` could grant permission but not express intent | live run | `follow_up_policy` with `always_once`, enforced by withholding `record_answer` | [#34](https://github.com/Pawansingh3889/elenchus/pull/34) `7b77d2a` |
| 19 | The question-by-question report discarded every follow-up answer, so the elaboration an author most wants was visible only in the export and one run at a time | reading the code after 20 | `follow_ups` and `probed` on `QuestionReport`, kept out of the tallies | [#34](https://github.com/Pawansingh3889/elenchus/pull/34) `6bb9a3d` |
| 18 | A summary read a rating of 5 on a 1-to-5 scale as "5 out of 10": the value was real and only the scale invented, so no checker could catch it | live run | The scale goes to the model in the extract; the bound lives beside `AnswerType` | [#34](https://github.com/Pawansingh3889/elenchus/pull/34) `de8a942` |
| 17 | A write-in was stored with the marker the prompt forbids, reaching the report as `Other: there's a portable spot cooler`; obeyed on the single-select and ignored on the multi-select in the same conversation | live run | `validate_answer` strips the marker, and re-matches the option list so `Other: Days` is the option Days | [#34](https://github.com/Pawansingh3889/elenchus/pull/34) `de8a942` |
| 16 | Deleting a question reported that a visibility condition had been cleared, because the count compared the list before and after and the deleted question was in the before | reading the builder | Count against the questions that survive the delete | [#34](https://github.com/Pawansingh3889/elenchus/pull/34) `e96e47b` |
| 15 | On a multi-select, Confirm sent the ticked options and Send sent the typed text, so a respondent who ticked two and typed a third lost whichever half they did not press | live run | Confirm sends both as one message and says so when there is something to lose | `3b6da65` |
| 14 | Nothing stopped one person answering a survey repeatedly: one respondent had four runs on one survey, reported as four responses and four people agreeing | dashboard read wrong | `start_run` returns the unfinished run and 409s a finished one, keyed on the survey not the version | `f6f3b2b` |
| 13 | The dashboard counted people who walked away as responses: "6 responses" over four completed runs | dashboard read wrong | Completed and in-progress split apart | `aaccc84` |
| 12 | A probe that went nowhere took the answer with it: "tempereture" was recorded, then the probe drifted, then the whole question was flagged unanswerable and the real answer was gone | live run | `ask_follow_up` carries `answer_so_far`, required and nullable, banked before the probe is asked | `c53a3e9` |
| 11 | Every builder save reset who a survey was for: the client never sent `audience`, the schema defaulted it, and an HR survey silently became one for the whole respondent pool | probe-then-verify | `TemplateUpdate` requires the settings; the omission is a 422 naming the field | `9d68888` |
| 10 | An answer type the author had banned came straight back on the next unrelated refine, because nothing carried the ban forward | live run | `allowed_answer_types` on the template, checked on every write and withheld from the model's own schema | `c752a9c` |
| 9 | A bare "4" was recorded as "yes" to "would you recommend the new handover process?", a recommendation nobody made | live run | `ungrounded_yes_no`: the latest message must contain words | `b68fb40` |
| 8 | `GET /users` handed every user id, email and role to anyone who asked, and under the dev shim an id **is** the credential | code review | Caller must already be known, and the router is not mounted outside development | `6c86f24` |
| 7 | A refine returned the complete survey and replaced every row, so the first unrelated change silently dropped every conditional-visibility rule | code review | The brief carries each condition, numbered as the listing numbers them | `3787e1b` |
| 6 | While probing, the API still described the scripted question, so a yes/no probed with "could you describe the issues" showed Yes/No chips and stored the description as `{yes_no: true}` | code review | `awaiting_follow_up` on the response; the client renders the composer alone | `3787e1b` |
| 5 | Template drafting and run summarising lost failover entirely: one chatty turn from tier 1 became an immediate 503 with healthy tiers untried | code review | Whether a chatty turn costs a tier is the caller's to declare | `aeeaaba` |
| 4 | A missing prompt file raised `FileNotFoundError`, which the handler rendered as "cannot reach its database", sending operators to investigate a healthy Postgres | code review | Typed `PromptNotFoundError`, and the guard reads inline `load_prompt()` calls too | `aeeaaba` |
| 3 | Two messages arriving together on one run both read the budget and both wrote, so a double-clicked send corrupted run state | code review | One turn at a time per run | `8acf6d9` |
| 2 | Ten values the answer gate should have refused were accepted, tracing to four holes | probe-then-verify | Four holes closed at the validator | `5d2ece6` |
| 1 | Five of thirteen draft payloads with a known-wrong verdict were accepted: blank and colliding options reached published surveys | probe-then-verify | Refused at the schema gate | `7ccdb52` |

Rows 16 to 24 landed together in [#34](https://github.com/Pawansingh3889/elenchus/pull/34),
squash-merged as `88822eb`. Their hashes are therefore not in `main`'s history and will
not resolve in a fresh clone: `git show de8a942` fails. They resolve on the pull request,
which keeps all eighteen commits and is now the only place their reasoning survives,
because a squash keeps one message and discards the rest. That is the cost of squashing a
branch whose commit messages were the documentation, and it is worth knowing before doing
it again.

## Patterns worth noticing

Read down the "how found" column rather than the defects.

**Almost nothing here was found by the test suite.** The suite is what stops these coming
back; it is not what finds them. Every LLM-behaviour defect on this list came from a real
conversation, and the mocked suite passed before and after each one, because a fake model
does what the test tells it to and never tries to work around the design.

**The expensive ones are silent.** Nothing in 11, 14, 18 or 22 raised an error. A survey
changed who it was for, a person answered four times, a maximum severity rating read as
middling, and a forced probe threw away the answer it asked for, all with a green suite
and a page that looked right. What they have in common is that the wrong value was a
perfectly legal one.

**A model given a rule will follow it most of the time.** 17 is the clearest case: the
same model obeyed the no-marker rule on one question and ignored it two questions later
in the same conversation. Where the cost of the exception is real, the rule belongs in
code, and the prompt then reads as an explanation of what the code enforces rather than
as the enforcement.

**A gate whose false positives are expensive gets switched off.** 24 is the lesson: a
checker that is right most of the time and costs the author everything when it is wrong
is worse than one that costs a line. Both new gates on this list now drop the item they
doubt rather than refusing the whole artifact.
