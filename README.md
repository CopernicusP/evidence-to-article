# Evidence to Article

An agent workflow for turning a supplied research report or evidence packet into
a Chinese explanatory article and an English blog. It combines editorial
instructions, separate review responsibilities, and small deterministic Python
helpers for exports and audit records.

This repository contains reusable instructions and tools. It is not an
autonomous backend, a hosted publishing service, or a model-training pipeline.
An agent or person still reads the evidence, writes the articles, and performs
the reviews.

## Two layers

1. **Generic core:** the skill's editorial workflow, language guidance, review
   lanes, Markdown exporter, and manifest checker.
2. **User-supplied organization profile:** the current audience, channel rules,
   terminology, approved examples, required qualifications, and publication
   permissions. Supply this explicitly for each run. Keep private profiles and
   client material outside this public repository.

Start from [the profile template](docs/organization-profile.template.md) when a
profile is useful. The scripts do not discover or load organizational context;
the executing agent reads the profile named in the run brief.

## Quick start

Python 3.9 or newer is sufficient for the helpers; there are no third-party
Python dependencies. Place `skills/evidence-to-article` in the personal skill
directory supported by your agent, or have the agent read
[`SKILL.md`](skills/evidence-to-article/SKILL.md) directly. Consult that agent's
documentation for installation details.

Give the agent the source packet, desired outputs, audience, source cutoff,
length requirements, and any applicable profile. Ask it to use the
`evidence-to-article` workflow. Keep the run in a separate private folder.

Once the reviewed canonical Markdown drafts and real review records exist,
these commands run from the repository root:

```bash
python3 skills/evidence-to-article/scripts/build_outputs.py --input /path/to/private-run/article-zh.md --out-dir /path/to/private-run/outputs
python3 skills/evidence-to-article/scripts/build_outputs.py --input /path/to/private-run/article-en.md --out-dir /path/to/private-run/outputs
python3 skills/evidence-to-article/scripts/check_run.py --manifest /path/to/private-run/run.json
python3 -m unittest discover -s tests -v
```

Replace `/path/to/private-run` with your own run directory. Build outputs before
completing the manifest's artifact hashes. After a draft changes, regenerate
outputs and obtain fresh reviews for the changed bytes. The checker requires
current, independent approvals in readability, source, and overall lanes.

中文快速开始：向执行代理提供原始材料、读者对象、中文和英文交付要求、资料截止日期及明确适用的机构配置，请它按照本工作流写作和复核。将每次任务的材料保存在独立的私有目录中；锁定 Markdown 文稿后，运行上述导出与检查命令。脚本核对文件、字数约定和复核记录，不能代替阅读原始证据，也不能证明事实正确。

## What the helpers check

- TXT is an exact byte copy of canonical Markdown; HTML uses a documented,
  limited Markdown subset and embedded styles. Each build records SHA-256
  digests and rendering warnings.
- The manifest checker checks declared body-count bounds, file hashes, export
  equality, exact claim quotations, critical-claim/source declarations,
  independent review identities, current review hashes, and open blockers.
- JSON reports separate errors from warnings. Validation errors return a
  nonzero exit code. The two test fixtures are entirely synthetic; their source
  reading and review records are explicitly simulated.

Read the [manifest contract](skills/evidence-to-article/references/manifest-contract.md)
for the schema, counting conventions, and supported Markdown. A source marked
`read` or a claim marked `support` is a recorded attestation. The checker does
not open that source, hash its contents, or establish semantic truth. It binds
reviews to article bytes; it does not certify source versions. It does not
grade writing, detect AI authorship, certify a rendered page count, or grant
publication approval. Actual source review and requested document/platform
previews remain separate work.

## Repository contents

```text
skills/evidence-to-article/  Generic agent instructions and Python helpers
docs/                      Empty organization-profile template
tests/                     Portable synthetic workflow tests
```

No private profiles, client cases, publisher article text, credentials, or
generated client deliverables belong here. `.gitignore` excludes common run and
local-material directories, but inspect changes before committing; an ignore
file cannot classify every sensitive file.

MIT licensed. See [LICENSE](LICENSE).
