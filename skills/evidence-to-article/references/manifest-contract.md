# Deterministic output and audit contract

These helpers use Python 3 and its standard library. They do not read sources,
judge prose, infer factual support, calculate an AI-detection score, or certify
layout. A successful audit means the files and the recorded human/agent review
attestations satisfy this contract. It does not prove that the attestations are
true or that every factual claim was included.

## Build deliverables

Run the commands in this reference from the `skills/evidence-to-article`
directory, or prepend that directory to each script path when working from
the repository root.

```bash
python scripts/build_outputs.py --input /work/article-zh.md --out-dir /work/outputs
python scripts/build_outputs.py --input /work/article-en.md --out-dir /work/outputs
```

Each command writes `<stem>.txt`, `<stem>.html`, and `<stem>.outputs.json`, and
prints JSON. TXT is an exact byte-for-byte UTF-8 copy of the canonical Markdown,
including its headings, citation markers, links, and line endings. It is not a
second edited draft. HTML renders that same content with embedded CSS and no
external assets or scripts. Its source title comes from the first heading, or
the input filename stem if there is no heading. Metadata records schema version,
absolute input/output paths, SHA-256 digests, and rendering warnings. Existing
outputs with these filenames are replaced; the input cannot be overwritten.

The deliberately limited Markdown subset supports ATX headings (`#` through
`######` followed by a space), paragraphs, flat unordered and ordered lists,
basic `[label](URL)` links without whitespace or parentheses in the URL, simple
bold/italic markers, and single-backtick inline code. Ordinary citation markers
such as `[1]` and bare URLs remain visible. Relative links and `http`, `https`,
and `mailto` links are allowed. Link labels can contain supported inline markup.
HTML escaping preserves literal text rather than interpreting it as HTML.
Relative link targets are preserved literally, not relocated when the output
directory differs from the input directory. Verify that they resolve from the
exported HTML location; use suitable absolute URLs or arrange authorized local
files beside the export when needed.

Nested lists, fenced/indented code, blockquotes, images, HTML tags, footnotes,
reference definitions, horizontal rules, setext headings, and conventional
pipe-table rows cause a clear error. Each list item must fit on one source line.
Some ambiguous constructs (for example, unmatched inline markers, table-like
pipe text, and two-space hard breaks) are retained literally with warnings;
unindented list continuations render as separate paragraphs with a warning.
Complex/nested inline formatting is outside
the subset. Inspect warnings and the rendered HTML before approval. No warning
licenses a missing citation or a change in meaning. Use ordinary paragraphs or
basic links to resolve unsupported syntax, then have the revised draft reviewed.

## Manifest versions

Run `python scripts/check_run.py --manifest /work/run.json`. Paths in a manifest
are relative to that manifest's directory, or absolute. All named files use
UTF-8 without a byte-order mark. New runs use `schema_version: 2`. Existing version 1 records remain valid under their original contract. The top-level object includes the version and four arrays: `artifacts`, `sources`, `claims`, and `reviews`. Each array uses
unique nonempty string `id` values. Unknown extra keys are allowed for notes.

### Artifacts

Every artifact has `id`, `path`, `language` (`zh` or `en`), `author_id`, `kind`,
and the lowercase 64-character `sha256` of its actual file bytes.

- `kind: "article"` identifies canonical Markdown. It also requires
  `expected_body_count: {"min": N, "max": N}` with nonnegative integer bounds.
- `kind: "txt"` or `"html"` requires `canonical_id` identifying its article.
  Language and author must match the canonical article. Each article requires
  exactly one TXT and one HTML output. Derived bytes must match a fresh build,
  even when their manifest hashes have been updated after an accidental edit.

There may be multiple articles per language. Counts apply only to canonical
articles, exclude all heading lines, and stop before an exact `## Sources` or
`## 参考来源` heading through the end of the file. Put sources last. Visible link
labels count; link targets and Markdown formatting markers do not. `zh` counts
Han characters (including extended Han ranges), not punctuation or Latin words.
`en` counts ASCII-letter words with internal apostrophes/hyphens; numerals do not
count. These are explicit measurement conventions, not universal linguistic
definitions. Set bounds to the actual agreed brief. There is no automatic
relationship between these counts and two or three rendered pages: inspect
print/PDF output separately when a page target matters.

### Sources and claims

Each source has `id`, `locator` (URL, local evidence path, or another resolvable
reference), `status` (`read`, `unread`, or `unavailable`), and `read_at` (an
ISO-8601 timestamp with timezone when read; otherwise `null`). The checker
validates the declaration, not the locator's existence, access, contents, or
truth. Use `read` only after a reviewer actually opened and read the evidence.

Each claim has `id`, boolean `critical`, `status` (`support`, `partial`,
`unverified`, or `conflict`), `source_ids` (an array), and `occurrences` (one or
more `{ "path": "article-en.md", "language": "en", "quote": "exact text" }`).
Quotes must occur exactly in a named canonical article, including Markdown if
present; every occurrence's language must match that article. Include an
occurrence for each language/draft in which the claim is asserted. Completeness
of this claim inventory is a source-review responsibility, not something this
script can establish by scanning prose.

Every critical claim must have status `support`, at least one declared source,
and all its declared sources recorded as read with valid timestamps. Unknown
source IDs fail. Noncritical partial/unverified/conflict claims produce warnings;
the source reviewer must confirm that qualifications and omissions are adequate,
or enter a blocker. An empty claim list produces a coverage warning. Never
change `status` merely to make the script pass.

### Review records common to both versions

Each review has `id`, `lane` (`readability`, `source`, or `overall`), `reviewer_id`,
`decision` (`approve` or `changes_requested`), `artifact_hashes` (an object from
artifact ID to exact SHA-256), and `findings` (an array, allowed to be empty).
Each finding has `message`, `severity` (`blocker`, `major`, `minor`, or `info`),
and `status` (`open` or `resolved`). Add optional IDs/evidence/resolution notes as
useful. An open blocker or a changes-requested decision fails the run; other
open findings produce warnings that must be read.

**Version 1 (legacy).** Each canonical article needs an approved review in all three lanes, bound to
its current file hash, by a reviewer different from that article's author.
One review may bind multiple artifacts. Lanes are separate responsibilities;
the checker does not enforce different people across lanes. Role identities
must honestly represent the agents or people who did the work. A stale hash
fails, even after a small wording edit. After changes, regenerate outputs and
obtain fresh review attestations; do not copy the current hash into an old
approval without actually reviewing the revised draft.
The manifest contains active reviews only. Replace superseded attestations in
this run and keep their history separately; any stale review listed here fails.

### Version 2 independent reviews and whole-article read

For each canonical article, add `required_criteria`, a nonempty array of unique, nonblank criterion names derived from the brief, without surrounding whitespace. Use consistent reviewer IDs without surrounding whitespace. Declare one top-level `integrator_id` when the canonical articles have multiple authors. For one author, omission means that author integrated the revisions. Supply the actual integrator’s ID explicitly if someone else integrated. Reserve `holistic` for the later whole-article review. As examples, `readability`, `source_meaning` and `delivery` address the base checks. Add `number_relevance`, `reader_implications`, `closing_synthesis`, `comment_closure` or other distinct requirements when the material calls for them. Record genuinely inapplicable criteria in the brief. The checker cannot infer the right scope from the prose.

Version 2 extends the shared review record with the following fields.

| Field | Applies to | Value |
| --- | --- | --- |
| `criterion` | Every review | One declared criterion or the reserved `holistic` |
| `reviewer_type` | Every review | `agent` or `human`, according to who actually inspected the artifact |
| `completed_at` | Every review | Timezone-aware ISO 8601 completion time |
| `started_at` | The `holistic` review | Timezone-aware ISO 8601 start time for the complete final read |

Provide exactly one current specialist approval for each declared criterion. A reviewer ID can repeat across articles only for the same criterion and must keep the same declared reader type. Separate people may review the same criterion in different languages. All canonical authors and the integrator are excluded from all reviewer roles throughout the run. Exactly one holistic reviewer ID must cover all canonical articles in the run. That person must be distinct from every specialist in the package. Every review applies to the exact current canonical bytes. Across the specialist records, cover all three existing lane families. Place delivery checks in `overall` and bind the actual TXT and HTML hashes as well as the canonical article. Multiple delivery specialists may cover the two exports between them. The final reviewer separately uses `lane: overall` and `criterion: holistic`.

For example, a read of an exported article with the three base checks needs four independent reviewers. If numerical relevance is a separate criterion, its reviewer can share the `readability` lane name while retaining their own criterion and identity. The whole read begins on or after every specialist's recorded completion across the entire run and must end on or after it starts. The one dedicated final reader may bind all canonical articles in one approval or record a separate hash-bound attestation per article under the same identity after reviewing the full package. Use separate manifests for unrelated briefs. If feedback causes an edit, the designated writer revises, regenerates outputs and obtains current specialist rechecks before the final read begins again. Keep superseded reviews and the actual resolution history outside the active snapshot.

A passing v2 audit verifies the declared coverage, identities, hashes and recorded ordering. It cannot establish who actually read a passage, what the writer did between revisions, who worked on a superseded draft but was omitted from the active manifest, whether the chosen criteria were complete, or whether publication was authorized. Check the assignment history when choosing independent reviewers. Record actual human reading and approval separately. Mechanical file checks can supply evidence to a reviewer.

### Cumulative revisions under version 2

For a continuing assignment, freeze a separate UTF-8 JSON plan **before editing**. Keep the plan digest with the run brief or use the adapter’s locked copy. Run `python scripts/check_run.py --manifest /work/run.json --require-cumulative`. The flag prevents a missing block from being treated as an ordinary run. Ordinary v2 manifests and archived v1 manifests follow their existing contracts. When an earlier plan exists, add `previous_plan: {"path":"history/plan.json","sha256":"…"}` to the new plan and retain the archived bytes. Its earlier rounds must be an unchanged prefix of the new sequence. Append the new instructions in a later round. This permits a targeted supersession without silently rewriting the historical record. A supervising workflow must compare this sequence with the actual brief, comments and prior plans. The checker cannot discover an undisclosed instruction or authenticate a rewritten plan.

A plan has one ordered `rounds` array. Each round names a unique `version` and lists its `requirements`. Start with the original brief. Each requirement contains a globally unique `id`, its canonical `article_id`, a `source` identifying the instruction or agreed change (including version and locator), and its `requirement` text. Requirements accumulate. An explicit later instruction may add `supersedes: ["older-id"]` plus its `reason`. Only active requirements for the same article from earlier rounds can be replaced. Cite the later instruction in the source. Example:

```json
{"rounds":[
  {"version":"Brief","requirements":[{"id":"audience","article_id":"guide","source":"Original brief, audience paragraph","requirement":"Explain how a first-time visitor obtains a place."}]},
  {"version":"Second draft","requirements":[{"id":"place","article_id":"guide","source":"Approved correction, waiting-list paragraph","requirement":"Keep the distinction between joining a queue and accepting an offered place."}]}
]}
```

For an earlier accepted textual fix, attach `prior_fix: {"path":"history/previous.md","sha256":"…","quote":"Previously approved wording"}` to that requirement. Use the archived canonical text or a faithful UTF-8 extract of the identified historical document. The checker verifies those bytes and the old quote whenever supplied. The current wording may differ if the reviewer can explain how it preserves the requirement. Record unavailable historical evidence as an open issue.

In the manifest, add `cumulative_revision: {"plan_path":"revision-plan.json","plan_sha256":"…","checks":{…}}`. Evidence paths in this block and plan are relative to the run directory. Keep a check for exactly each active requirement, keyed by its ID. It records `status: "verified"`, `article_sha256` for the current canonical bytes, an exact surviving `quote`, and concrete `evidence` of comparison with the original instruction or previous fix. A deleted passage can use an adjacent surviving quote and an explanation of the removal. Leave unresolved requirements open, including missing prior evidence or an unconfirmed change of scope.

If the brief gives a rendered body-page range, put `page_range: {"min":2,"max":3,"delivery_role":"guide_pdf"}` on that requirement. Add a `body_render` object to the current check containing `delivery_path`, `delivery_sha256`, `render_path`, `render_sha256` and `body_page_fractions`. For a PDF delivery, both file pairs can refer to that PDF. Otherwise bind the actual delivered file and its measured PDF export. Inspect each physical page using the agreed layout and content scope. Record the fraction of its normal usable body area actually occupied by qualifying content, with reference-only pages at zero. Exclude unfilled space, references and appendices. A list such as `[1,0.25,0]` totals 1.25 body pages and fails a two-page minimum. Include page observations and measurement method in `evidence`. The checker verifies file hashes, the PDF signature and the sum against the frozen range. Matching the PDF to its source, page count, occupied fractions and actual layout requires inspection of the render.

Each affected article declares `revision_continuity` in `required_criteria` and has that distinct specialist, followed by the shared holistic reviewer. Both reviews also bind `revision_plan_sha256` to the exact plan bytes and `revision_checks_sha256` to the complete current checks object, including the delivery and render hashes. To compute the latter, use `hashlib.sha256(json.dumps(checks, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()`. If a previously verified fix regresses, repair it, renew all affected records and submit the cumulative requirements to the final reader again. Never renew a signature without doing the review. The audit validates recorded coverage and current bytes. Whether the plan is complete, a fix is substantively preserved and an instruction genuinely superseded another remain review decisions.

### Legacy minimal shape example

The version 1 example below illustrates legacy fields only. Use the additional fields and independent assignments above for a new version 2 run. Replace the digest placeholders and
the evidence/claim/review declarations with actual work. Copy the review object
for the `source` and `overall` lanes after those reviews occur. A bilingual run
adds the English article and its outputs, claim occurrences, and three reviews.

```json
{
  "schema_version": 1,
  "artifacts": [
    {"id":"zh-md","path":"article-zh.md","language":"zh","author_id":"writer-zh","kind":"article","sha256":"REPLACE_WITH_ACTUAL_SHA256","expected_body_count":{"min":1800,"max":2400}},
    {"id":"zh-txt","path":"outputs/article-zh.txt","language":"zh","author_id":"writer-zh","kind":"txt","canonical_id":"zh-md","sha256":"REPLACE_WITH_ACTUAL_SHA256"},
    {"id":"zh-html","path":"outputs/article-zh.html","language":"zh","author_id":"writer-zh","kind":"html","canonical_id":"zh-md","sha256":"REPLACE_WITH_ACTUAL_SHA256"}
  ],
  "sources": [
    {"id":"s1","locator":"evidence/interview-notes.md","status":"read","read_at":"2026-11-16T09:00:00Z"}
  ],
  "claims": [
    {"id":"c1","critical":true,"status":"support","source_ids":["s1"],"occurrences":[{"path":"article-zh.md","language":"zh","quote":"从真实文章逐字复制的论断。"}]}
  ],
  "reviews": [
    {"id":"zh-readability","lane":"readability","reviewer_id":"reviewer-1","decision":"approve","artifact_hashes":{"zh-md":"REPLACE_WITH_ACTUAL_SHA256"},"findings":[]}
  ]
}
```

## Audit results

The checker prints a JSON report with `ok`, `schema_version`, `review_contract`, `body_counts`, `errors`, `warnings`, their counts, and `semantic_verification_performed: false`. The review contract is `legacy_lanes` for version 1 and `independent_criteria_and_holistic` for version 2. Exit code `0` means
no deterministic errors; `1` means a validation/file/rendering error. Invalid
CLI arguments use argparse's usual exit code `2`. Errors include missing files,
wrong artifact hashes, stale or self-authored reviews, missing lanes, unsupported
critical claims, missing exact claim quotes, open blockers, count violations,
and TXT/HTML drift. Warnings require attention even when the exit code is `0`.
