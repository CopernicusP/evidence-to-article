#!/usr/bin/env python3
"""Audit files and recorded review attestations; this does not fact-check prose."""

import argparse
from datetime import datetime
import json
from pathlib import Path
import re

from build_outputs import body_count, render_html, sha256


def review_time(review, field, issue):
    value = review.get(field)
    if isinstance(value, str):
        try:
            stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if stamp.tzinfo is not None:
                return stamp
        except ValueError:
            pass
    issue("review_time", f"Review {review['id']} requires an ISO-8601 {field} with timezone.")
    return None


def audit_criterion_reviews(article, current, outputs, issue):
    """Check the declared assignments and sequence, not the truth of a review."""
    article_id = article["id"]
    required = article.get("required_criteria")
    if (not isinstance(required, list) or not required
            or any(not isinstance(item, str) or not item.strip() or item != item.strip()
                   or item == "holistic" for item in required)
            or len(set(required)) != len(required)):
        issue("review_plan", f"Article {article_id} requires unique nonempty required_criteria; holistic is reserved.")
        return

    assignments = {}
    owners = {}
    specialists = []
    for review in current:
        criterion = review.get("criterion")
        if criterion != "holistic" and criterion not in required:
            issue("review_criterion", f"Review {review['id']} has no declared criterion for article {article_id}.")
            continue
        if criterion in assignments:
            issue("duplicate_review", f"Article {article_id} has more than one current {criterion} review.")
            continue
        assignments[criterion] = review
        reviewer = review["reviewer_id"]
        author = article.get("author_id")
        if reviewer != reviewer.strip() or (isinstance(author, str) and reviewer.strip() == author.strip()):
            issue("review_identity", f"Review {review['id']} needs a distinct, unpadded reviewer ID.")
        if reviewer in owners:
            issue("review_independence", f"Article {article_id} assigns {owners[reviewer]} and {criterion} to {reviewer}.")
        owners[reviewer] = criterion
        if criterion != "holistic":
            specialists.append(review)

    for criterion in [*required, "holistic"]:
        if criterion not in assignments:
            issue("missing_criterion", f"Article {article_id} lacks a current approved {criterion} review.")

    lanes = {review["lane"] for review in specialists}
    for missing in sorted({"readability", "source", "overall"} - lanes):
        issue("missing_review", f"Article {article_id} lacks a current {missing} specialist review.")
    delivery_files = {key for review in specialists if review["lane"] == "overall"
                      for key in review["artifact_hashes"]}
    for missing in sorted(outputs - delivery_files):
        issue("delivery_review", f"Article {article_id} lacks an overall specialist review bound to {missing}.")

    completed = [review_time(review, "completed_at", issue) for review in specialists]
    final = assignments.get("holistic")
    if final is None:
        return
    if final["lane"] != "overall":
        issue("review_criterion", f"Holistic review {final['id']} must use the overall lane.")
    start = review_time(final, "started_at", issue)
    end = review_time(final, "completed_at", issue)
    if start and end and end < start:
        issue("review_order", f"Holistic review {final['id']} finishes before it starts.")
    if start and any(stamp and stamp > start for stamp in completed):
        issue("review_order", f"Article {article_id} has a specialist sign-off after its holistic review started.")


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

    version = manifest.get("schema_version")
    if type(version) is not int or version not in (1, 2):
        issue("schema", "schema_version must be 1 or 2.")
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

    current_reviews = {key: [] for key in canonical}
    for key, review in reviews.items():
        label = "Review " + key
        lane = review.get("lane")
        valid = lane in {"readability", "source", "overall"} and string(review, "reviewer_id") and review.get("decision") in {"approve", "changes_requested"}
        if not valid:
            issue("schema", label + " requires a valid lane, reviewer_id, and decision approve/changes_requested.")
        if version == 2 and review.get("reviewer_type") not in ("agent", "human"):
            issue("review_identity", label + " requires reviewer_type agent or human.")
            valid = False
        if review.get("decision") == "changes_requested":
            issue("review_changes", label + " requests changes.")
        bound = review.get("artifact_hashes")
        if not isinstance(bound, dict) or not bound:
            issue("schema", label + " requires nonempty artifact_hashes keyed by artifact ID.")
            bound = {}
        if version == 2 and not canonical.keys() & bound.keys():
            issue("review_binding", label + " must bind the canonical article it assesses.")
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
                current_reviews[artifact_id].append(review)
    for key, current in current_reviews.items():
        if version == 2:
            outputs = {artifact_id for artifact_id, artifact in artifacts.items()
                       if artifact.get("canonical_id") == key and artifact.get("kind") in ("txt", "html")}
            audit_criterion_reviews(canonical[key], current, outputs, issue)
        else:
            completed = {review["lane"] for review in current}
            for missing in sorted({"readability", "source", "overall"} - completed):
                issue("missing_review", "Article " + key + " lacks a current independent approved " + missing + " review.")
    contracts = {1: "legacy_lanes", 2: "independent_criteria_and_holistic"}
    contract = contracts.get(version) if type(version) is int else None
    return {"ok": not errors, "schema_version": version, "review_contract": contract, "semantic_verification_performed": False,
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
