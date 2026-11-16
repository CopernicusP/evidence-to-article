"""Portable tests using synthetic prose and simulated attestations.

The read timestamps and approval records below are test inputs, not evidence of
real source reading or editorial review. No factual client or market case is
represented. All generated files live in a temporary directory.
"""

import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "skills" / "evidence-to-article" / "scripts"
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS))
from build_outputs import MarkdownError, body_count, inline, render_html  # noqa: E402
from check_run import audit  # noqa: E402


ARTICLES = {
    "en": """# A simulated interview-note example

This simulated note separates observations from interpretations. [1]

## Make the distinction visible

An interview note is easier to review when a reader can see what was said and what the writer inferred. **Keep the original wording** when quoting a participant.

- Record the context of the conversation.
- Label an inference before sharing it.

## Sources

[1] [Synthetic workflow note](evidence.md), a simulated test fixture.
""",
    "zh": """# 一份模拟访谈笔记

这份模拟笔记把观察和推断分开记录。[1]

## 给读者留下判断空间

一份有用的笔记应当说明哪些内容来自原话，哪些是作者的理解。引用受访者时，**保留原来的措辞**，方便另一位编辑检查。

- 记下谈话发生的背景。
- 分享前标明尚未验证的推断。

## 参考来源

[1] [合成流程笔记](evidence.md)，仅用于模拟脚本测试。
""",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_cli(script, *args):
    process = subprocess.run(
        [sys.executable, str(SCRIPTS / script), *map(str, args)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"},
        check=False,
    )
    if process.stderr:
        raise AssertionError(process.stderr)
    return process.returncode, json.loads(process.stdout)


def write_manifest(directory, manifest):
    path = directory / "run.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def make_simulated_fixture(directory):
    directory.mkdir()
    (directory / "evidence.md").write_text(
        "# SYNTHETIC TEST EVIDENCE — NOT A REAL CASE\n"
        "All claim, source-reading, and reviewer records in this fixture are simulated.\n"
        "This simulated note separates observations from interpretations.\n"
        "这份模拟笔记把观察和推断分开记录。\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": 1,
        "simulation": "All source-reading and review attestations are simulated test inputs.",
        "artifacts": [],
        "sources": [{"id": "simulated-source", "locator": "evidence.md", "status": "read", "read_at": "2026-01-01T09:00:00Z", "note": "Simulated read attestation for a synthetic test only."}],
        "claims": [{"id": "simulated-claim", "critical": True, "status": "support", "source_ids": ["simulated-source"], "occurrences": [], "note": "Synthetic claim and simulated support decision."}],
        "reviews": [],
    }
    for language, text in ARTICLES.items():
        source = directory / f"article-{language}.md"
        source.write_text(text, encoding="utf-8")
        code, result = run_cli("build_outputs.py", "--input", source, "--out-dir", directory / "outputs")
        if code != 0 or not result["ok"]:
            raise AssertionError(result)
        count, notes = body_count(text, language)
        if notes:
            raise AssertionError(notes)
        article_id = language + "-md"
        author = "simulated-writer-" + language
        manifest["artifacts"].append({"id": article_id, "path": source.name, "language": language, "author_id": author, "kind": "article", "sha256": digest(source), "expected_body_count": {"min": count, "max": count}})
        for kind in ("txt", "html"):
            derived = directory / "outputs" / f"article-{language}.{kind}"
            manifest["artifacts"].append({"id": language + "-" + kind, "path": derived.relative_to(directory).as_posix(), "language": language, "author_id": author, "kind": kind, "canonical_id": article_id, "sha256": digest(derived)})
        quote = "This simulated note separates observations from interpretations." if language == "en" else "这份模拟笔记把观察和推断分开记录。"
        manifest["claims"][0]["occurrences"].append({"path": source.name, "language": language, "quote": quote})
        for lane in ("readability", "source", "overall"):
            manifest["reviews"].append({"id": language + "-simulated-" + lane, "lane": lane, "reviewer_id": "simulated-reviewer-" + lane, "decision": "approve", "artifact_hashes": {article_id: digest(source)}, "findings": [], "note": "Simulated approval record; no real editorial review is represented."})
    write_manifest(directory, manifest)
    return manifest


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="evidence-to-article-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.valid = self.root / "valid"
        self.manifest = make_simulated_fixture(self.valid)

    def test_valid_bilingual_outputs_and_metadata(self):
        code, report = run_cli("check_run.py", "--manifest", self.valid / "run.json")
        self.assertEqual(code, 0, report)
        self.assertTrue(report["ok"])
        self.assertEqual(report["warnings"], [])
        self.assertFalse(report["semantic_verification_performed"])
        for language in ARTICLES:
            source = self.valid / f"article-{language}.md"
            txt = self.valid / "outputs" / f"article-{language}.txt"
            page = self.valid / "outputs" / f"article-{language}.html"
            metadata = json.loads((self.valid / "outputs" / f"article-{language}.outputs.json").read_text(encoding="utf-8"))
            self.assertEqual(txt.read_bytes(), source.read_bytes())
            self.assertEqual(metadata["input"]["sha256"], digest(source))
            self.assertIn('href="evidence.md"', page.read_text(encoding="utf-8"))
            for entry in metadata["artifacts"]:
                self.assertEqual(entry["sha256"], digest(Path(entry["path"])))

    def test_invalid_fixture_rejects_stale_reviews_claims_and_output_drift(self):
        invalid = self.root / "invalid"
        shutil.copytree(self.valid, invalid)
        broken = copy.deepcopy(self.manifest)
        source = invalid / "article-en.md"
        source.write_text(source.read_text(encoding="utf-8").replace("An interview note is easier", "A clear interview note is easier"), encoding="utf-8")
        code, _ = run_cli("build_outputs.py", "--input", source, "--out-dir", invalid / "outputs")
        self.assertEqual(code, 0)
        for artifact in broken["artifacts"]:
            artifact["sha256"] = digest(invalid / artifact["path"])
            if artifact["id"] == "en-md":
                count, _ = body_count(source.read_text(encoding="utf-8"), "en")
                artifact["expected_body_count"] = {"min": count, "max": count}
        # Updated derivative hashes ensure canonical comparison must catch drift.
        for kind in ("txt", "html"):
            path = invalid / "outputs" / f"article-zh.{kind}"
            path.write_text(path.read_text(encoding="utf-8").replace("这份模拟笔记把观察和推断分开记录。", "模拟测试故意误改了这句话。"), encoding="utf-8")
            next(item for item in broken["artifacts"] if item["id"] == "zh-" + kind)["sha256"] = digest(path)
        broken["claims"][0]["status"] = "unverified"
        broken["sources"][0].update(status="unread", read_at=None)
        broken["reviews"][0]["findings"] = [{"message": "Simulated blocker: synthetic evidence needs rereading.", "severity": "blocker", "status": "open"}]
        code, report = run_cli("check_run.py", "--manifest", write_manifest(invalid, broken))
        errors = [item["code"] for item in report["errors"]]
        self.assertEqual(code, 1)
        self.assertFalse(report["ok"])
        self.assertEqual(errors.count("derived_mismatch"), 2)
        self.assertEqual(errors.count("stale_review"), 3)
        self.assertIn("critical_claim", errors)
        self.assertIn("unresolved_blocker", errors)

    def test_quotes_independent_review_and_required_lanes(self):
        absent_quote = copy.deepcopy(self.manifest)
        absent_quote["claims"][0]["occurrences"][0]["quote"] = "This sentence is absent from the synthetic article."
        self.assertIn("claim_occurrence", [e["code"] for e in audit(absent_quote, self.valid)["errors"]])
        self_review = copy.deepcopy(self.manifest)
        self_review["reviews"][0]["reviewer_id"] = "simulated-writer-en"
        codes = [e["code"] for e in audit(self_review, self.valid)["errors"]]
        self.assertIn("self_review", codes)
        self.assertIn("missing_review", codes)

    def test_body_count_conventions(self):
        english = "# Heading words\n\nOne well-made reader’s note.\n\n## Sources\n\nIgnored source words.\n"
        chinese = "# 标题\n\n正文。[中文链接](https://example.com/长网址)\n\n## 参考来源\n\n来源文字。\n"
        self.assertEqual(body_count(english, "en")[0], 4)
        self.assertEqual(body_count(chinese, "zh")[0], 6)

    def test_inline_text_is_not_rewritten(self):
        for text in ("revenue_growth_rate", "3 * 4 * 5"):
            self.assertEqual(inline(text, set()), (text, text))
        self.assertEqual(inline("_hello_ **world**", set())[1], "hello world")

    def test_unsupported_markdown_fails_explicitly(self):
        cases = (
            "# Article\n\n> Quoted block\n",
            "# Article\n\n| A | B |\n|---|---|\n",
            "# Article\n\n![Image](photo.png)\n",
            "# Article\n\n    indented code\n",
            "1. Parent\n  1. Child\n",
            "# Article\n\nA footnote.[^one]\n",
        )
        for text in cases:
            with self.subTest(text=text), self.assertRaises(MarkdownError):
                render_html(text)

    def test_schema_errors_are_json_failures(self):
        malformed = copy.deepcopy(self.manifest)
        malformed["artifacts"][0]["language"] = []
        code, report = run_cli("check_run.py", "--manifest", write_manifest(self.valid, malformed))
        self.assertEqual(code, 1)
        self.assertFalse(report["ok"])
        boolean_version = copy.deepcopy(self.manifest)
        boolean_version["schema_version"] = True
        self.assertIn("schema", [e["code"] for e in audit(boolean_version, self.valid)["errors"]])
        unread_timestamp = copy.deepcopy(self.manifest)
        unread_timestamp["sources"][0]["status"] = "unread"
        self.assertTrue(any("must use read_at null" in e["message"] for e in audit(unread_timestamp, self.valid)["errors"]))


if __name__ == "__main__":
    unittest.main()
