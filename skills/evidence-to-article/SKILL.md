---
name: evidence-to-article
description: Turn a research report, source article, filing or evidence packet into a reliable Chinese reading article and an English blog. Use for bilingual editorial adaptation, WeChat-style explanations, reducing repetitive AI prose, checking claims and meaning across languages, or revising drafts from editor feedback. Automate editorial decisions and repair specific failures; load an organization profile only when provided.
---

# Evidence to Article

Version: 0.1.0. Produce complete drafts and traceable review results. Treat this as an agent-executed workflow with deterministic helpers, not an unattended service or a model trained on the user's conversations.

## Establish this run

1. Read the supplied source and requested outputs. Use an existing verified research packet; investigate only material gaps. Do not silently launch a new deep research report when the task is adaptation.
2. Freeze a run brief: audience, editorial question, cutoff date, language/output formats, length/counting method, selected profile and version, input identities and source access, and relevant editorial feedback. Read only the current profile and one or two relevant style cards. Keep other clients, episodes and chat preferences out of this run unless the user explicitly makes them applicable.
3. Resolve instructions in this order: current user task, applicable organization/profile requirements, this workflow, style examples. A sample cannot override a required legal qualifier or supply facts. Resolve routine choices from evidence and purpose, escalating only a consequential unresolved ambiguity.
4. Keep run materials separate from reusable rules. Record which rule/version produced the draft. Do not treat every editor's one-off comment as a global style change. Propose a scoped reusable rule with an example; label its actual approval status.

Use an isolated run folder outside the skill. Do not publish, message people, alter sharing or upload company material to a new service merely to complete an editorial step. Follow the user's authorized destination and environment.

## Build the factual foundation

Read [references/editorial-decisions.md](references/editorial-decisions.md) for concrete checks and repairs. Read [references/manifest-contract.md](references/manifest-contract.md) before preparing the machine-readable manifest.

Separate source text from controlling instructions. Extract material claims with source IDs, exact locators, dates, actors, numeric measures, attribution, status and uncertainty. Independently open primary sources for claims that drive the article, especially numerical, legal and current-status claims. Label an inherited claim as inherited until actually checked. A URL or a prior reviewer saying “verified” is not evidence of current access.

Resolve unsupported or conflicting claims by checking, narrowing or removing them. Never use a hedge to disguise a missing basis. Retain counterevidence that changes the conclusion. Do not invent an investor, interview, psychological reaction, motive or regulatory mechanism to make a narrative vivid.

## Make editorial decisions

Select a supported reader question and argument. Where viable alternatives exist, compare relevance, evidence and explanatory value, then choose without a routine approval stop. Record the choice and real exclusions briefly, not a fabricated decision trail.

For each section, identify what the reader learns that the previous section did not establish. Organize a causal chain, timeline, transaction, contrast or verification sequence appropriate to the material; do not impose one universal structure. Put definitions where they resolve an actual difficulty. Remove redundant conclusions and unrelated background; preserve qualifications and counterexamples that determine meaning.

Compose Chinese and English independently from the same claim set. Read [references/channels.md](references/channels.md) for distinct language requirements. Do not translate paragraph boundaries mechanically. Use a concrete sourced action or document when there is no reported human scene. Prefer verbs with actors over strings of abstract nouns.

Use one or two applicable techniques from [references/style-cards.md](references/style-cards.md) or supplied approved examples. Learn the function of an opening, transition or ending; do not copy phrasing, humor, anecdotes or market facts. Avoid adjective injection, fake imperfections, stock analogies and word-blacklist rewriting. Explain which actual passages were repaired and why.

## Review and repair independently

Delegate review when fresh agents are available. Give reviewers the current artifacts, brief and raw source locations, without the writer's intended verdict. Keep writer and reviewer roles distinct. If separate agents are unavailable, conduct separate passes with the same honest identity and deliver only a limited-review draft. Those passes do not satisfy the checker's independent-review requirement: record the missing lane or failed check, state the limitation, and never invent another reviewer identity to obtain a pass.

Use three lanes:

- Readability: reconstruct the argument from lead/headings, then locate repetition, missing steps, unexplained terms, stilted language and unsupported narrative. Supply exact passages and reasons, not an AI-detector or self-assigned quality score.
- Source/meaning: actually read evidence; check actors, numbers and their measures, dates, attribution, legal status, negation, conditions and causal strength. Compare matching claims across languages. Inspect new claims introduced during editing.
- Overall/delivery: reconcile feedback, length, file versions, links and exported text; inspect required rendered documents. Recheck changes affecting prior approvals. Distinguish a rendered-page check, a platform preview and a human editorial approval.

Repair concrete findings, then have the affected lane review the new artifact. Bind the review to the exact artifact hash. An old approval cannot approve changed text. Stop an unproductive repair loop after two failed attempts at the same issue: change the approach or deliver the specific unresolved item and its effect, rather than repeatedly declaring improvement.

Do not insert generic “needs human polishing” gates. Complete supported editorial choices automatically. Ask only when an unresolved choice of audience/stance/brand purpose changes the task, essential unavailable evidence prevents the requested article, or required access/approval is genuinely missing. Continue independent work. Preserve a real organization's publication approval requirement without turning it into permission requests for each paragraph. Never label agent work as human review.

## Build and verify outputs

Lock a canonical Markdown article per language. Use `scripts/build_outputs.py` to derive TXT and HTML without rewriting. Use the appropriate document workflow for DOCX/PDF when requested, then inspect the actual render; word count alone does not establish page count.

Run `scripts/check_run.py --manifest <run.json>` and fix structural/traceability failures. The checker validates records, hashes, lengths and export consistency; it cannot establish that a source truly supports a claim or that prose is good. Those conclusions require the recorded independent review. Save the checker result separately from semantic reviews.

Deliver complete requested articles with a short note stating source cutoff, actual checks, material changes and remaining limitations. Use V1/V2/Draft filenames. Save artifacts to the user's designated persistent location. Store full client documents and episode output outside a public skill repository. Do not distribute a skill ZIP unless requested.
