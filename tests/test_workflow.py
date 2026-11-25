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


def with_criterion_reviews(legacy):
    manifest = copy.deepcopy(legacy)
    manifest["schema_version"] = 2
    manifest["integrator_id"] = "simulated-integrating-writer"
    manifest["reviews"] = []
    for article in manifest["artifacts"]:
        if article["kind"] != "article":
            continue
        criteria = {"understanding": "readability", "reader_decision": "readability",
                    "evidence": "source", "format": "overall"}
        article["required_criteria"] = list(criteria)
        for criterion, lane in {**criteria, "holistic": "overall"}.items():
            review = {
                "id": article["id"] + "-" + criterion, "lane": lane, "criterion": criterion,
                "reviewer_id": "simulated-" + criterion, "reviewer_type": "agent", "decision": "approve",
                "artifact_hashes": {article["id"]: article["sha256"]}, "findings": [],
                "completed_at": "2000-01-01T09:00:00Z",
            }
            if criterion == "format":
                for output in manifest["artifacts"]:
                    if output.get("canonical_id") == article["id"]:
                        review["artifact_hashes"][output["id"]] = output["sha256"]
            if criterion == "holistic":
                review.update(reviewer_type="human", started_at="2000-01-01T09:10:00Z", completed_at="2000-01-01T09:30:00Z")
            manifest["reviews"].append(review)
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
        self.assertEqual(report["review_contract"], "legacy_lanes")
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

    def test_v2_declared_criteria_and_final_read(self):
        manifest = with_criterion_reviews(self.manifest)
        # Row order has no editorial meaning. Compare the recorded instants.
        manifest["reviews"].reverse()
        code, report = run_cli("check_run.py", "--manifest", write_manifest(self.valid, manifest))
        self.assertEqual(code, 0, report)
        self.assertEqual(report["schema_version"], 2)
        self.assertEqual(report["review_contract"], "independent_criteria_and_holistic")
        self.assertFalse(report["semantic_verification_performed"])

    def test_v2_rejects_missing_criteria_unrelated_extras_and_reused_reviewers(self):
        cases = [
            ("missing criterion", "missing_criterion", lambda m, r: m["reviews"].remove(r["reader_decision"])),
            ("undeclared criterion", "review_criterion", lambda m, r: r["reader_decision"].update(criterion="spare")),
            ("ambiguous plan", "review_plan", lambda m, r: m["artifacts"][0]["required_criteria"].append("understanding")),
            ("reserved criterion", "review_plan", lambda m, r: m["artifacts"][0]["required_criteria"].append("holistic")),
            ("duplicate approval", "duplicate_review", lambda m, r: m["reviews"].append(dict(r["evidence"], id="additional"))),
            ("same specialist", "review_independence", lambda m, r: r["evidence"].update(reviewer_id=r["format"]["reviewer_id"])),
            ("reused specialist as final reader", "review_independence", lambda m, r: r["holistic"].update(reviewer_id=r["reader_decision"]["reviewer_id"])),
            ("author as final reader", "self_review", lambda m, r: r["holistic"].update(reviewer_id="simulated-writer-en")),
            ("unrecorded reader type", "review_identity", lambda m, r: r["evidence"].pop("reviewer_type")),
            ("tool as final reader", "review_identity", lambda m, r: r["holistic"].update(reviewer_type="script")),
            ("no final read", "missing_criterion", lambda m, r: m["reviews"].remove(r["holistic"])),
            ("no delivery specialist", "missing_review", lambda m, r: r["format"].update(lane="readability")),
            ("unbound export", "delivery_review", lambda m, r: r["format"]["artifact_hashes"].pop("en-html")),
            ("no article binding", "review_binding", lambda m, r: r["format"]["artifact_hashes"].pop("en-md")),
            ("wrong final lane", "review_criterion", lambda m, r: r["holistic"].update(lane="source")),
            ("missing timestamp", "review_time", lambda m, r: r["understanding"].pop("completed_at")),
            ("no timezone", "review_time", lambda m, r: r["holistic"].update(started_at="2000-01-01T09:10:00")),
            ("overlapping final", "review_order", lambda m, r: r["holistic"].update(started_at="2000-01-01T09:10:00+01:00")),
            ("negative duration", "review_order", lambda m, r: r["holistic"].update(completed_at="2000-01-01T09:05:00Z")),
        ]
        for name, expected, edit in cases:
            with self.subTest(name=name):
                manifest = with_criterion_reviews(self.manifest)
                reviews = {r["criterion"]: r for r in manifest["reviews"] if "en-md" in r["artifact_hashes"]}
                edit(manifest, reviews)
                result = audit(manifest, self.valid)
                self.assertFalse(result["ok"])
                self.assertIn(expected, [error["code"] for error in result["errors"]])

    def test_v2_after_return_requires_fresh_specialists_and_whole_read(self):
        manifest = with_criterion_reviews(self.manifest)
        reviews = [r for r in manifest["reviews"] if "en-md" in r["artifact_hashes"]]
        final = next(r for r in reviews if r["criterion"] == "holistic")
        final["decision"] = "changes_requested"
        self.assertIn("review_changes", [e["code"] for e in audit(manifest, self.valid)["errors"]])

        source = self.valid / "article-en.md"
        source.write_text(source.read_text(encoding="utf-8").replace("An interview note", "An interview record"), encoding="utf-8")
        code, _ = run_cli("build_outputs.py", "--input", source, "--out-dir", self.valid / "outputs")
        self.assertEqual(code, 0)
        for artifact in manifest["artifacts"]:
            artifact["sha256"] = digest(self.valid / artifact["path"])
        hashes = {a["id"]: a["sha256"] for a in manifest["artifacts"]}
        self.assertIn("stale_review", [e["code"] for e in audit(manifest, self.valid)["errors"]])
        for review in reviews:
            if review is not final:
                review["artifact_hashes"] = {key: hashes[key] for key in review["artifact_hashes"]}
                review["completed_at"] = "2000-01-01T10:00:00Z"
        self.assertIn("stale_review", [e["code"] for e in audit(manifest, self.valid)["errors"]])
        final.update(decision="approve", artifact_hashes={"en-md": hashes["en-md"]})
        self.assertIn("review_order", [e["code"] for e in audit(manifest, self.valid)["errors"]])
        final.update(started_at="2000-01-01T10:05:00Z", completed_at="2000-01-01T10:20:00Z")
        self.assertIn("review_order", [e["code"] for e in audit(manifest, self.valid)["errors"]])
        other_final = next(r for r in manifest["reviews"] if r["id"] == "zh-md-holistic")
        other_final.update(started_at=final["started_at"], completed_at=final["completed_at"])
        self.assertTrue(audit(manifest, self.valid)["ok"])

    def test_v2_one_integrator_and_one_holistic_reader_for_the_package(self):
        manifest = with_criterion_reviews(self.manifest)
        reviews = {r["id"]: r for r in manifest["reviews"]}
        # Different specialists can own the same criterion on different translations.
        reviews["zh-md-evidence"]["reviewer_id"] = "simulated-other-source-reader"
        self.assertTrue(audit(manifest, self.valid)["ok"])

        # A single whole-package decision may bind both actual canonical files.
        english_final = reviews["en-md-holistic"]
        chinese_final = reviews["zh-md-holistic"]
        english_final["artifact_hashes"].update(chinese_final["artifact_hashes"])
        manifest["reviews"].remove(chinese_final)
        self.assertTrue(audit(manifest, self.valid)["ok"])

        del manifest["integrator_id"]
        self.assertIn("review_identity", [e["code"] for e in audit(manifest, self.valid)["errors"]])
        for artifact in manifest["artifacts"]:
            artifact["author_id"] = "simulated-single-writer"
        self.assertTrue(audit(manifest, self.valid)["ok"])
        manifest["integrator_id"] = " "
        self.assertIn("review_identity", [e["code"] for e in audit(manifest, self.valid)["errors"]])

    def test_v2_cross_language_conflicts(self):
        cases = [
            ("two holistic readers", "zh-md-holistic", "reviewer_id", "second-final-reader", "review_independence"),
            ("number reviewer takes reader implication", "zh-md-reader_decision", "reviewer_id", "en-number-reader", "review_independence"),
            ("source reviewer takes holistic read", "zh-md-holistic", "reviewer_id", "en-source-reader", "review_independence"),
            ("other-language writer as final", "zh-md-holistic", "reviewer_id", "simulated-writer-en", "review_identity"),
            ("other-language writer as specialist", "zh-md-format", "reviewer_id", "simulated-writer-en", "review_identity"),
            ("integrator as final", "zh-md-holistic", "reviewer_id", "simulated-integrating-writer", "review_identity"),
            ("integrator as specialist", "en-md-evidence", "reviewer_id", "simulated-integrating-writer", "review_identity"),
            ("specialist changes identity type", "zh-md-format", "reviewer_type", "human", "review_independence"),
            ("other language not ready when final began", "zh-md-evidence", "completed_at", "2000-01-01T09:15:00Z", "review_order"),
        ]
        for name, review_id, field, value, expected in cases:
            with self.subTest(case=name):
                manifest = with_criterion_reviews(self.manifest)
                reviews = {r["id"]: r for r in manifest["reviews"]}
                english = manifest["artifacts"][0]
                english["required_criteria"].remove("understanding")
                english["required_criteria"].append("number_relevance")
                reviews["en-md-understanding"].update(criterion="number_relevance", reviewer_id="en-number-reader")
                reviews["en-md-evidence"]["reviewer_id"] = "en-source-reader"
                reviews["zh-md-holistic"].update(started_at="2000-01-01T09:20:00Z")
                self.assertTrue(audit(manifest, self.valid)["ok"])
                reviews[review_id][field] = value
                result = audit(manifest, self.valid)
                self.assertIn(expected, [error["code"] for error in result["errors"]])

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
