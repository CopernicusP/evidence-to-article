# Editorial decisions and failure handling

Use these as tests of a passage or decision, not mandatory headings in the published article.

| Job formerly left to an editor | Execute | Evidence of completion | Repair automatically | Escalate only when |
| --- | --- | --- | --- | --- |
| Choose the angle | Pick the reader's unresolved question; compare plausible angles against relevance and source support | One chosen question and conclusion; source IDs; real reasons for exclusions | Narrow the question or choose a better-supported angle | Conflicting audiences, institutional stance or business purpose cannot be resolved from the task |
| Select material | Keep evidence, mechanisms, limits and counterevidence needed for the argument | Claim-to-source map with use in the article; exclusions that matter | Remove unsupported details, retrieve missing evidence, move optional background to notes | Essential evidence is inaccessible and removing it defeats the requested scope |
| Build structure | Give each section an explanation job; read lead/headings alone, then the full sequence | Reviewer's reconstruction and exact gaps/repetitions | Reorder, merge, cut or add a sourced connecting explanation | Alternative structures serve incompatible unstated purposes, not merely because a paragraph feels awkward |
| Make language natural | Locate abstract nouns without actors, translation syntax, empty transitions and repeated lessons | Exact before/after passages and reason; meaning check for affected claims | Rewrite, then recheck actors, scope, negation, dates and attribution | Requested voice conflicts with brand requirements and no approved example resolves it |
| Verify facts and meaning | Read original evidence independently, calculate where relevant and compare shared claims in both languages | Source accessed, date, locator, claim support and cross-language finding | Correct, qualify to the actual evidence, remove or obtain better support | Evidence cannot settle a material question; ask about scope, never ask a person to certify an unsupported fact |
| Finish files | Export locked text; measure length by agreed method; inspect actual render | Hashes, counts, equivalent text and links, render observations, unresolved findings | Fix formatting/export drift, then recheck affected artifacts | Required platform access is unavailable or conflicting specifications need a decision |

## Work from the reviewed copy

Follow the editor's file reference and identify the version. Inspect its comments, replies, anchors and tracked revisions when present. If comments were supplied as screenshots, record the visible anchor and any missing surrounding text. For each actionable note, identify the problem, make the smallest sufficient repair and reread the changed passage in context. An ambiguous anchor stays open until the intended passage can be identified. If another copy is accessible, say which one was inspected and distinguish independent improvements from responses to unseen feedback.

## Carry earlier revisions forward

For a continuing assignment, start with the original purpose, audience, length, structure and deliverables. Open the review copy and the version that resolved each previously accepted issue. Give each requirement a stable ID and cite the round, exact source and passage. Retain all agreed fixes, including ones absent from the newest comments. For a later instruction that actually replaces an earlier one, link their IDs and record the instruction author, locator and reason. If earlier evidence is unavailable, name the specific gap and keep the affected check open.

On the current copy, read each earlier fix beside its new counterpart. Quote or locate both passages and record how the requirement survives any rewrite. For a removal, anchor the current check to the surrounding passage and explain what the reviewer inspected. Check the actual delivered render as well as the canonical text. For example, restoring a paragraph can displace a chart caption or shorten the final body page. Count a half-filled body page as half a page and a sources-only page as zero. Keep the original typography, margins and spacing unless the brief changed. If the body is short, add the supported context the reader needs. Do another full-set read on the exported version after repairs. The latest comments alone do not define that read.

## Test the reader's answer

| Criterion | Question for its reviewer | Example using the synthetic library notice |
| --- | --- | --- |
| Numerical relevance | Read the passage before and after each cut. Can the reader still tell the baseline, size of change and measured outcome, if one exists? Retain the necessary units, period and comparison. Remove figures that do no explanatory work or move them to notes. | The old and new Friday closing times show the two additional hours. The four-week duration matters to a reader deciding whether the change is permanent. |
| Practical consequence | For each material party, what can they decide, receive or forgo? Explain a concrete trade-off or limit. Which benefits are intended, and which results have actually been observed? | A reader could visit later on Fridays during the trial. The unchanged seating leaves the chance of finding a seat uncertain. |
| Closing synthesis | Read the opening question and the ending together. Which earlier findings does the last paragraph join to answer the question? Include a future observation only when it would change that answer. | If the article asks whether evening access improves, close with the additional time and the unchanged seating. A generic promise to follow future updates leaves the answer unfinished. |

These questions can lead to different decisions about the same sentence. Accuracy alone cannot establish that a number belongs in the body. A procedural detail may be correct while leaving the reader's choices unexplained. Choose the closing perspective that fits the brief. The library example is fictional. Its source describes an approved four-week trial, a shift in Friday closing from six to eight, no change in seating, and no measurements of crowding.

## Check what a first-time reader understood

When the audience lacks the writer’s subject knowledge, assign `reader_teachback` in the readability lane to a fresh reviewer with the intended level of familiarity. Give them the current draft, an audience description and a neutral prompt such as “What changed, who can do what now, and which part did you have to guess?” Capture their first account in their own words and the passage they relied on. Until then, withhold the factual answer, the writer’s reasoning and earlier reviews. Label an agent’s response as a simulated audience reading. Attribute a human response only to the person who actually read that version.

Compare the unaided account with the evidence. Locate the first unsupported inference or missing premise. Repair that point with a short definition, a retained comparison or a concrete decision and its limit. Use the brief’s actual length tolerance to fit the explanation. For a strict limit, cut a weaker detail first. On a new test, use a fresh reader if the previous reviewer has already seen the answer key.

For example, a fictional workshop will try a waiting list to fill cancelled seats. When a seat opens the organizer offers it to the first person on the list, who can accept or pass. The organizer wants to fill the room. Someone arranging travel still needs a confirmed place. A reader who thinks joining guarantees admission has identified a missing explanation. To judge whether the trial filled more seats, the article needs comparable attendance before and after, the available capacity and the period measured. If only a proposal exists, describe its intended effect and leave the outcome open.

If an actual reader’s response conflicts with an agent’s approval, preserve their words and version, reopen the finding and repair it. When the new wording still needs that reader’s judgment, ask one targeted question such as “After joining the list, what would you still need before you could attend?” Record the version reread and their answer if received. Continue other checks while waiting and report any outstanding human response accurately.

## Preserve meaning during editing

For each changed material statement, compare actor and role; action; object or population; amount/unit/denominator/period; date versus as-of state; attribution; allegation versus finding; modal/negation; conditions; correlation versus cause. Check the surrounding paragraph. A sentence can preserve every number while changing what those numbers mean.

Use one ledger across languages, allowing different examples and emphasis when evidence supports them. Flag contradictions, not mere differences in length or order. References and identifiers may move to notes only if the reader can still understand and verify the claim.

## Prevent memory collisions

- Freeze profile, audience, cutoff and input versions at run start. Apply edits to that run before considering reusable rules.
- Classify feedback as factual correction, episode-specific choice, reusable style preference, formatting requirement or approval state. Keep origin, scope and status.
- Promote a rule only within its valid scope. A short-newsletter request must not shorten a later research report. A Chinese heading preference must not rewrite a quoted English source.
- Re-load a small explicit profile and selected examples for each run. Do not assume shared conversation history reliably identifies the current client or editor.
- Record automated checks and actual human decisions separately. Do not manufacture timestamps, identities, reading time or approval.

## Report limitations precisely

“The complaint was inaccessible, so the two allegations remain unverified” is actionable. “Needs human review” without a reason is not. A reviewer identifying no issue is not a promise of error-free output. One successful case demonstrates this run, not a general reduction in editing time.
