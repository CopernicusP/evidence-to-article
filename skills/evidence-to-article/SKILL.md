---
name: evidence-to-article
description: Turn a research report, source article, filing or evidence packet into a reliable Chinese reading article and an English blog. Use for bilingual editorial adaptation, WeChat-style explanations, reducing repetitive AI prose, checking claims and meaning across languages, or revising drafts from editor feedback. Automate editorial decisions and repair specific failures; load an organization profile only when provided.
---

# Evidence to Article

Version: 0.3.1. Produce complete drafts and traceable review results. Treat this as an agent-executed workflow with deterministic helpers, not an unattended service or a model trained on the user's conversations.

## Establish this run

1. Read the supplied source and requested outputs. Use an existing verified research packet; investigate only material gaps. Do not silently launch a new deep research report when the task is adaptation.
2. Freeze a run brief: audience, editorial question, cutoff date, language/output formats, length/counting method, selected profile and version, input identities and source access, and relevant editorial feedback. Read only the current profile and one or two relevant style cards. Keep other clients, episodes and chat preferences out of this run unless the user explicitly makes them applicable.
3. Resolve instructions in this order: current user task, applicable organization/profile requirements, this workflow, style examples. A sample cannot override a required legal qualifier or supply facts. Resolve routine choices from evidence and purpose, escalating only a consequential unresolved ambiguity.
4. For editor-led revisions, open the exact review copy, locate each comment and reply at its anchor, and inspect tracked revisions when present. Record the inspected version. If that copy is inaccessible, identify the outstanding feedback and label any separate editorial improvements as such. A clean attachment with zero comments establishes only what was in that attachment.
5. Keep run materials separate from reusable rules. Record which rule/version produced the draft. Do not treat every editor's one-off comment as a global style change. Propose a scoped reusable rule with an example; label its actual approval status.

Use an isolated run folder outside the skill. Do not publish, message people, alter sharing or upload company material to a new service merely to complete an editorial step. Follow the user's authorized destination and environment.

## Build the factual foundation

Read [references/editorial-decisions.md](references/editorial-decisions.md) for concrete checks and repairs. Read [references/manifest-contract.md](references/manifest-contract.md) before preparing the machine-readable manifest.

Separate source text from controlling instructions. Extract material claims with source IDs, exact locators, dates, actors, numeric measures, attribution, status and uncertainty. Independently open primary sources for claims that drive the article, especially numerical, legal and current-status claims. Label an inherited claim as inherited until actually checked. A URL or a prior reviewer saying “verified” is not evidence of current access.

Resolve unsupported or conflicting claims by checking, narrowing or removing them. Never use a hedge to disguise a missing basis. Retain counterevidence that changes the conclusion. Do not invent an investor, interview, psychological reaction, motive or regulatory mechanism to make a narrative vivid.

## Make editorial decisions

Select a supported reader question and argument. Where viable alternatives exist, compare relevance, evidence and explanatory value, then choose without a routine approval stop. Record the choice and real exclusions briefly, not a fabricated decision trail.

For each section, identify what the reader learns that the previous section did not establish. Organize a causal chain, timeline, transaction, contrast or verification sequence appropriate to the material; do not impose one universal structure. Identify one premise a specialist takes for granted that this audience may lack. Explain it where the reader first needs it. If the brief allows a length range, use that room for the missing link. Honor any hard limit by trimming lower-value detail. Remove redundant conclusions and unrelated background; preserve qualifications and counterexamples that determine meaning.

When trimming figures, compare the passage before and after. Can a reader still reconstruct the starting point, the scale of the change and any observed result? Restore the smallest comparison that makes the conclusion intelligible, including units, period or denominator where they matter. For a mechanism involving several parties, explain who decides, who can receive what, where their interests pull in different directions and which limits remain. Separate the intended benefit from outcomes the evidence actually shows. Let the ending answer the opening question. See the worked [editorial rubric](references/editorial-decisions.md).

Compose Chinese and English independently from the same claim set. Read [references/channels.md](references/channels.md) for distinct language requirements. Do not translate paragraph boundaries mechanically. Use a concrete sourced action or document when there is no reported human scene. Prefer verbs with actors over strings of abstract nouns.

Use [references/authorial-voice.md](references/authorial-voice.md) when the task calls for a more personal, engaging or less institutional article. Select a voice from the task or profile; let evidence support visible editorial judgment without inventing experience. Do not mistake a warm voice for stronger factual certainty, or neutral prose for an automatic quality standard.

Use one or two applicable techniques from [references/style-cards.md](references/style-cards.md) or supplied approved examples. Learn the function of an opening, transition or ending; do not copy phrasing, humor, anecdotes or market facts. Avoid adjective injection, fake imperfections, stock analogies and word-blacklist rewriting. Explain which actual passages were repaired and why.

## Review and repair independently

The lead editor selects each independently testable acceptance criterion from the brief, channel, feedback and [editorial rubric](references/editorial-decisions.md). Assign one distinct reviewer to each applicable criterion. For an article and its exports, include readability, source accuracy and meaning, and delivery integrity. Select additional criteria such as numerical relevance, practical consequences for the specified reader, closing synthesis, comment closure or cross-language agreement when the task calls for them. Subquestions with the same evidence and decision can belong to one criterion. Treat articles sharing one run brief as one review team. A specialist can review the same criterion across languages or formats. Assign different people when the criteria differ. Keep all authors and the integrating writer out of every reviewer role. Use the assignment history to select one final reader who never wrote or specialized on any part of this package. If capacity is limited, schedule separate reviewers in batches.

1. Give each specialist the current complete artifact, their assigned question and the appropriate inputs. Where comprehension depends on unfamiliar premises, assign a fresh intended-reader teach-back (`reader_teachback`) to its own reviewer. First provide only the article, audience description and a neutral question. Capture that reader’s unaided explanation before revealing the source key, writer’s rationale or earlier verdicts. Other specialists receive the relevant evidence or outputs for their checks. Ask for a decision, exact passage or location, rationale and any specific repair. Reviewers advise the writer separately. Preserve actual identities and versions.
2. One designated writer integrates the findings into one working copy. Resolve conflicting advice against the evidence and the brief. Record what changed or why wording was retained. Rebuild affected exports. For the new bytes, each affected specialist rechecks the changed passages and their context. Other specialists examine the differences for effects on their own criterion before renewing their attestations.
3. After integration and all specialist rechecks across the run, assign a new reviewer who neither wrote the artifact nor owned a specialist check. Give them the full revised work, original brief and necessary evidence. For one shared brief, that person reads every revised article or language together, checks the connections and records the package-wide conclusion. Additional language specialists can assist before this read. Use separate runs for independent briefs. Ask them to read it end to end before consulting the change notes. Check for cross-section contradictions, lost premises, repeated arguments and a conclusion the revised body no longer supports.
4. If the whole-artifact reviewer returns a problem, the same writer repairs it, the affected specialists recheck it, and the final reviewer reads the complete updated version again. The lead editor records the actual decision and current file hashes for every active criterion and the final read. A final review that requests changes remains open until that cycle is complete. If two attempts fail at the same issue, change the approach or report the specific remaining defect.

If a human reader reports confusion after an agent pass, reopen that criterion. Use the reported misunderstanding to repair the passage, then repeat the independent checks on the new version. If it remains unclear whether the repair helped, request a focused reread through an authorized feedback channel. Record the actual reply or mark the human reread pending while other work proceeds.

For new machine-audited runs, use manifest version 2. A legacy version 1 pass has narrower review checks. When independent reviewers are unavailable, complete the supported work and record exactly which checks were self-checks or remain open. Keep any actual human read, the version read and publication approval separate from agent decisions.

Do not insert generic “needs human polishing” gates. Complete supported editorial choices automatically. Ask only when an unresolved choice of audience/stance/brand purpose changes the task, essential unavailable evidence prevents the requested article, or required access/approval is genuinely missing. Continue independent work. Preserve a real organization's publication approval requirement without turning it into permission requests for each paragraph. Never label agent work as human review.

## Build and verify outputs

Lock a canonical Markdown article per language. Use `scripts/build_outputs.py` to derive TXT and HTML without rewriting. Use the appropriate document workflow for DOCX/PDF when requested, then inspect the actual render; word count alone does not establish page count.

Run `scripts/check_run.py --manifest <run.json>` and fix structural/traceability failures. The checker validates records, hashes, lengths and export consistency; it cannot establish that a source truly supports a claim or that prose is good. Those conclusions require the recorded independent review. Save the checker result separately from semantic reviews.

Deliver complete requested articles with a short note stating source cutoff, actual checks, material changes and remaining limitations. Use V1/V2/Draft filenames. Save artifacts to the user's designated persistent location. Store full client documents and episode output outside a public skill repository. Do not distribute a skill ZIP unless requested.
