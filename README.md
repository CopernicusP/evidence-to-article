# Evidence to Article

从研究资料到可读的中英文文章。  
Turn a research report or evidence packet into a Chinese article and an English blog with a clear point of view and traceable claims.

Evidence to Article is the reusable writing and review core. It helps an agent choose a useful angle, explain the evidence in the reader's order, preserve an appropriate authorial voice, and review the finished text independently. Organization-specific wrappers provide audience, length, brand and delivery requirements.

Current version: **0.3.1** · [Writing skill](skills/evidence-to-article/SKILL.md) · [Bilingual example](examples/library-hours/README.md) · [Organization profile](docs/organization-profile.template.md)

## Try it

Install the `skills/evidence-to-article` folder in the personal skill directory supported by your agent, or give the agent the [SKILL.md](skills/evidence-to-article/SKILL.md) URL and ask it to read the linked references as needed. Installation depends on your host application. The workflow runs in that agent; this repository does not host a writing service.

Attach the research or source material and use a brief like this:

```text
Use evidence-to-article to turn the attached research into:
- a Chinese explanatory article for non-specialist readers;
- an English blog based on the same evidence.

Audience: [who is reading and why]
Purpose: [the one thing the reader needs to understand]
Length and formats: [your requirements]
Evidence cutoff: [date]
Voice: grounded personal — make the author's analysis visible,
without inventing firsthand experience or strengthening the claims.
Organization profile: [path or omit]

Choose the angle and structure. Write each language independently and
assign each applicable check to an independent reviewer. Have one writer integrate the findings, run the specialist rechecks, then have a fresh reviewer read the revised article end to end.
```

中文也可以直接说：

> 使用 evidence-to-article，把这份研究写成中文阅读稿和英文 Blog。读者是___，需要弄清___，篇幅是___。希望作者有自己的判断、语气自然；事实、条件和归因保留。按读者的理解顺序写，不要照着研究提纲压缩。

## What 0.3.1 adds

Where a draft assumes specialist knowledge, a fresh reader explains it in their own words before seeing the evidence or the writer’s rationale. The writer uses that account to repair the missing premise, preserve figures needed to judge scale and explain each party’s choices and limits. A reported human misunderstanding reopens an earlier agent approval. The [editorial rubric](skills/evidence-to-article/references/editorial-decisions.md) describes how to record the answer and test the revision.

## Review workflow

A revision begins with the editor's actual review copy and comment anchors. Writers and reviewers now have concrete tests for which numbers earn space, what changes for a specified reader, and how the ending answers the opening. Each applicable check has a separate reviewer. Reviewers can cover the same criterion across languages. After one writer integrates the corrections and all specialists recheck the revision, one fresh reviewer reads every article in the shared brief for problems that only emerge across sections or languages.

New runs use manifest version 2 to record this review sequence. Version 1 remains supported for older runs. The [manifest contract](skills/evidence-to-article/references/manifest-contract.md) specifies their different guarantees.

## Grounded authorial voice

[Grounded authorial voice](skills/evidence-to-article/references/authorial-voice.md) makes personality an editorial choice. Choose what deserves attention, explain why, and let the reader follow the reasoning. First person, humor and rhythm are available when they fit the genre. They are not quotas or substitutes for evidence.

For example, the [invented library notice](examples/library-hours/README.md) supports this observation:

> 我更在意周五多出来的这两个小时：试行时读者晚上能多待一会儿，座位却不会增加。

The writer can make that comparison without claiming to have visited the library or predicting that it will be less crowded. The example is synthetic teaching material, not a real organization or a client publication.

## Core, adapter and run

| Layer | Responsibility | Where it belongs |
| --- | --- | --- |
| Evidence to Article | Angle, structure, voice, language adaptation, review and export checks | This public project |
| Organization adapter | Audience, channel lengths, terminology, selected voice, approved samples and delivery permissions | A separate organization profile or wrapper |
| Article run | Source packet, drafts, actual review records and deliverables | An isolated authorized work folder |

Adapters should reference a tested core version and commit, not maintain a second copy of the writing engine. When a reusable method improves, update this core; when a company requirement changes, update that company's profile. The executing agent reads the supplied profile. The Python helpers do not fetch, load or apply it automatically.

Use [the profile template](docs/organization-profile.template.md) to add an adapter. Private profiles, client articles, internal feedback and credentials stay outside this public repository.

For topic-to-research routing, editable channel requirements and optional podcast/video production, use the public **[Editorial Playbook](https://github.com/CopernicusP/editorial-playbook)**. It references this core rather than copying the writing engine; private organization profiles and production runs stay separate.

## Workflow

The agent reads the evidence, selects an angle, writes the requested channels and assigns the required checks to independent specialists. One writer incorporates their findings. After specialist rechecks, a separate reviewer reads the complete revision before handoff. A source ledger tracks material claims, attribution, dates, numerical measures and uncertainty.

Reader feedback is recorded with its actual scope. A publication is not automatically a writing-quality benchmark; an agent approval is not proof that a reader enjoyed the article. Keep useful authorial judgment while checking whether a rewrite changed the meaning.

## Export and audit helpers

Python 3.9 or newer is sufficient; the helpers have no third-party Python dependencies. After the canonical Markdown and real review records exist, run from the repository root:

```bash
python3 skills/evidence-to-article/scripts/build_outputs.py --input /path/to/private-run/article-zh.md --out-dir /path/to/private-run/outputs
python3 skills/evidence-to-article/scripts/build_outputs.py --input /path/to/private-run/article-en.md --out-dir /path/to/private-run/outputs
python3 skills/evidence-to-article/scripts/check_run.py --manifest /path/to/private-run/run.json
python3 -m unittest discover -s tests -v
```

TXT preserves the canonical Markdown bytes. HTML renders a documented subset with embedded styles. The checker validates hashes, export consistency, declared length bounds, exact claim quotations, source declarations and current review attestations for the selected manifest version. It reports errors separately from warnings.

These scripts do not read evidence, certify factual truth, judge prose, detect AI authorship or approve publication. Word/PDF rendering and target-platform previews remain separate checks. See the [manifest contract](skills/evidence-to-article/references/manifest-contract.md) for exact conventions. The test fixtures simulate sources and review records; they are not evidence of editorial quality.

## Contributing

A useful issue includes a short non-confidential input, the requested audience and voice, the actual output, and the passage that failed. Explain the missing reasoning or meaning change rather than assigning an AI score. Do not post client material without permission.

The project includes an agent workflow and local utilities, not a trained model, an unattended publishing backend or a hosted application. Improvements should keep that distinction clear.

If you find the workflow useful, a GitHub star or a concrete example of an improvement helps other users discover the project.

MIT licensed. See [LICENSE](LICENSE).
