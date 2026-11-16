#!/usr/bin/env python3
"""Audit files and recorded review attestations; this does not fact-check prose."""

import argparse
from datetime import datetime
import json
from pathlib import Path
import re

from build_outputs import body_count, render_html, sha256


def audit(manifest, base):
    errors, warnings, counts = [], [], {}

    def issue(code, message, warning=False):
        (warnings if warning else errors).append({"code": code, "message": message})

    def items(name):
        value = manifest.get(name)
        if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
            issue("schema", name + " must be a list of objects.")
            return []
        return value

    def index(name):
        result = {}
        for item in items(name):
            key = item.get("id")
            if not isinstance(key, str) or not key.strip() or key in result:
                issue("schema", name + " entries need unique nonempty string IDs.")
            else:
                result[key] = item
        return result

    def string(item, key):
        return isinstance(item.get(key), str) and bool(item[key].strip())

    if type(manifest.get("schema_version")) is not int or manifest.get("schema_version") != 1:
        issue("schema", "schema_version must be 1.")
    artifacts, sources, claims, reviews = (index(name) for name in ("artifacts", "sources", "claims", "reviews"))
    contents, texts, hashes, paths = {}, {}, {}, {}
    canonical = {key: value for key, value in artifacts.items() if value.get("kind") == "article"}
    if not canonical:
        issue("schema", "At least one canonical article is required.")
    for key, artifact in artifacts.items():
        label = "Artifact " + key
        if artifact.get("kind") not in {"article", "txt", "html"}:
            issue("schema", label + " kind must be article, txt, or html.")
        if artifact.get("language") not in {"zh", "en"} or not string(artifact, "author_id"):
            issue("schema", label + " requires language zh/en and author_id.")
        if not string(artifact, "path"):
            issue("schema", label + " requires a path.")
            continue
        path = (base / artifact["path"]).resolve()
        if path in paths:
            issue("duplicate_path", label + " shares a path with " + paths[path] + ".")
        paths[path] = key
        try:
            contents[key] = path.read_bytes()
            hashes[key] = sha256(contents[key])
            texts[key] = contents[key].decode("utf-8")
            if texts[key].startswith("\ufeff"):
                raise ValueError("UTF-8 BOM is unsupported.")
        except (OSError, UnicodeError, ValueError) as exc:
            issue("file", label + ": " + str(exc))
            continue
        if not re.fullmatch(r"[0-9a-f]{64}", str(artifact.get("sha256", ""))):
            issue("schema", label + " requires a lowercase SHA-256 digest.")
        elif artifact["sha256"] != hashes[key]:
            issue("artifact_hash", label + " SHA-256 differs from the current file.")
        if key in canonical:
            bounds = artifact.get("expected_body_count")
            if (not isinstance(bounds, dict) or any(type(bounds.get(k)) is not int for k in ("min", "max"))
                    or bounds["min"] < 0 or bounds["max"] < bounds["min"]):
                issue("schema", label + " requires expected_body_count with integer 0 <= min <= max.")
            try:
                count, notes = body_count(texts[key], artifact.get("language"))
                counts[key] = {"count": count, "unit": "Han characters" if artifact.get("language") == "zh" else "English words"}
                for note in notes:
                    issue("markdown", label + ": " + note, True)
                if isinstance(bounds, dict) and type(bounds.get("min")) is int and type(bounds.get("max")) is int and not bounds["min"] <= count <= bounds["max"]:
                    issue("body_count", f"{label} body count {count} is outside {bounds['min']}–{bounds['max']}.")
            except ValueError as exc:
                issue("markdown", label + ": " + str(exc))

    for key, artifact in artifacts.items():
        if artifact.get("kind") not in {"txt", "html"}:
            continue
        origin = artifact.get("canonical_id")
        if origin not in canonical:
            issue("schema", "Derived artifact " + key + " requires a canonical_id referring to an article.")
            continue
        if any(artifact.get(field) != canonical[origin].get(field) for field in ("language", "author_id")):
            issue("schema", "Derived artifact " + key + " language and author_id must match its canonical article.")
        if origin in texts and key in contents:
            try:
                expected = contents[origin] if artifact["kind"] == "txt" else render_html(texts[origin], Path(canonical[origin]["path"]).stem)[0]
                if contents[key] != expected:
                    issue("derived_mismatch", "Derived artifact " + key + " differs from its canonical " + artifact["kind"].upper() + " output; rebuild it.")
            except ValueError as exc:
                issue("markdown", "Cannot verify derived artifact " + key + ": " + str(exc))
    for key in canonical:
        kinds = [item.get("kind") for item in artifacts.values() if item.get("canonical_id") == key]
        for kind in ("txt", "html"):
            if kinds.count(kind) != 1:
                issue("outputs", "Article " + key + " requires exactly one " + kind.upper() + " output.")

    for key, source in sources.items():
        if source.get("status") not in {"read", "unread", "unavailable"} or not string(source, "locator"):
            issue("schema", "Source " + key + " requires status read/unread/unavailable and a locator.")
        if "read_at" not in source:
            issue("schema", "Source " + key + " requires read_at (null unless read).")
        if source.get("status") == "read":
            try:
                stamp = datetime.fromisoformat(source.get("read_at", "").replace("Z", "+00:00"))
                if stamp.tzinfo is None:
                    raise ValueError("timezone missing")
            except (ValueError, TypeError, AttributeError):
                issue("source_read", "Source " + key + " marked read requires an ISO-8601 read_at timestamp with timezone.")
        elif source.get("read_at") is not None:
            issue("schema", "Source " + key + " must use read_at null unless its status is read.")

    if not claims:
        issue("claim_coverage", "No claims were declared; a reviewer must confirm that no factual claims were omitted.", True)
    for key, claim in claims.items():
        label = "Claim " + key
        status = claim.get("status")
        if status not in {"support", "partial", "unverified", "conflict"} or type(claim.get("critical")) is not bool:
            issue("schema", label + " requires status support/partial/unverified/conflict and boolean critical.")
        source_ids = claim.get("source_ids")
        if not isinstance(source_ids, list) or any(not isinstance(value, str) for value in source_ids):
            issue("schema", label + " source_ids must be a list of source IDs.")
            source_ids = []
        for source_id in source_ids:
            if source_id not in sources:
                issue("unknown_source", label + " references unknown source " + source_id + ".")
        if claim.get("critical"):
            if status != "support" or not source_ids:
                issue("critical_claim", label + " must be supported and have at least one source.")
            for source_id in source_ids:
                if source_id in sources and sources[source_id].get("status") != "read":
                    issue("critical_claim", label + " cites source " + source_id + " that was not recorded as read.")
        elif status != "support":
            issue("claim_status", label + " is " + str(status) + "; reviewers must assess its treatment.", True)
        elif not source_ids or any(sources.get(source_id, {}).get("status") != "read" for source_id in source_ids):
            issue("claim_support", label + " declares support without recorded read sources; source review must resolve this.", True)
        occurrences = claim.get("occurrences")
        if not isinstance(occurrences, list) or not occurrences:
            issue("claim_occurrence", label + " requires at least one quote/path/language occurrence.")
            continue
        for occurrence in occurrences:
            if not isinstance(occurrence, dict) or any(not string(occurrence, field) for field in ("path", "language", "quote")):
                issue("schema", label + " occurrences require nonempty path, language, and quote strings.")
                continue
            target = paths.get((base / occurrence["path"]).resolve())
            if target not in canonical:
                issue("claim_occurrence", label + " occurrence path must identify a canonical article.")
            elif occurrence["language"] != canonical[target].get("language"):
                issue("claim_occurrence", label + " occurrence language differs from its article.")
            elif target in texts and occurrence["quote"] not in texts[target]:
                issue("claim_occurrence", label + " exact quote was not found in " + target + ".")

    lanes = {key: set() for key in canonical}
    for key, review in reviews.items():
        label = "Review " + key
        lane = review.get("lane")
        valid = lane in {"readability", "source", "overall"} and string(review, "reviewer_id") and review.get("decision") in {"approve", "changes_requested"}
        if not valid:
            issue("schema", label + " requires a valid lane, reviewer_id, and decision approve/changes_requested.")
        if review.get("decision") == "changes_requested":
            issue("review_changes", label + " requests changes.")
        bound = review.get("artifact_hashes")
        if not isinstance(bound, dict) or not bound:
            issue("schema", label + " requires nonempty artifact_hashes keyed by artifact ID.")
            bound = {}
        findings = review.get("findings")
        if not isinstance(findings, list):
            issue("schema", label + " requires a findings list (may be empty).")
            findings = []
            valid = False
        for finding in findings:
            if not isinstance(finding, dict) or not string(finding, "message") or finding.get("severity") not in {"blocker", "major", "minor", "info"} or finding.get("status") not in {"open", "resolved"}:
                issue("schema", label + " findings require message, severity blocker/major/minor/info, and status open/resolved.")
                valid = False
                continue
            if finding["status"] == "open":
                is_blocker = finding["severity"] == "blocker"
                issue("unresolved_blocker" if is_blocker else "review_finding", label + ": " + finding["message"], not is_blocker)
                if is_blocker:
                    valid = False
        for artifact_id, digest in bound.items():
            if artifact_id not in artifacts:
                issue("unknown_artifact", label + " binds unknown artifact " + artifact_id + ".")
                continue
            if digest != hashes.get(artifact_id) or artifact_id not in hashes:
                issue("stale_review", label + " hash does not match the current bytes of " + artifact_id + "; review this draft again.")
                continue
            if review.get("reviewer_id") == artifacts[artifact_id].get("author_id"):
                issue("self_review", label + " reviewer is also the author of " + artifact_id + ".")
                continue
            if valid and review.get("decision") == "approve" and artifact_id in canonical:
                lanes[artifact_id].add(lane)
    for key, completed in lanes.items():
        for missing in sorted({"readability", "source", "overall"} - completed):
            issue("missing_review", "Article " + key + " lacks a current independent approved " + missing + " review.")
    return {"ok": not errors, "schema_version": 1, "semantic_verification_performed": False,
            "scope": "Deterministic files, counts, claim declarations, and review attestations only; no source reading, fact-checking, prose quality judgment, or page-count verification.",
            "body_counts": counts, "errors": errors, "warnings": warnings,
            "error_count": len(errors), "warning_count": len(warnings)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("Manifest must be a JSON object.")
        result = audit(manifest, args.manifest.resolve().parent)
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, AttributeError) as exc:
        result = {"ok": False, "semantic_verification_performed": False, "errors": [{"code": "manifest", "message": str(exc)}], "warnings": [], "error_count": 1, "warning_count": 0}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
