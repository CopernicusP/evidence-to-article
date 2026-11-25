#!/usr/bin/env python3
"""Audit files and recorded review attestations; this does not fact-check prose."""

import argparse
import hashlib
import math
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
    """Check coverage of the declared criteria and exports for one article."""
    article_id = article["id"]
    required = article.get("required_criteria")
    if (not isinstance(required, list) or not required
            or any(not isinstance(item, str) or not item.strip() or item != item.strip()
                   or item == "holistic" for item in required)
            or len(set(required)) != len(required)):
        issue("review_plan", f"Article {article_id} requires unique nonempty required_criteria; holistic is reserved.")
        return

    assignments = {}
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


def audit_review_team(manifest, canonical, current_reviews, issue):
    """Check reviewer independence and the last specialist sign-off across the package."""
    writers = {article["author_id"].strip() for article in canonical.values()
               if isinstance(article.get("author_id"), str)}
    if "integrator_id" in manifest:
        integrator = manifest["integrator_id"]
        if not isinstance(integrator, str) or not integrator or integrator != integrator.strip():
            issue("review_identity", "integrator_id must be a nonempty, unpadded writer ID.")
        else:
            writers.add(integrator)
    elif len(writers) > 1:
        issue("review_identity", "Name one integrator_id for a run with multiple canonical authors.")

    # A review can bind several language versions. Check its identity and time once.
    active = {review["id"]: review for group in current_reviews.values() for review in group}
    assignments = {}
    specialist_finishes = []
    final_starts = []
    holistic_reader = None
    for review in active.values():
        reviewer = review["reviewer_id"]
        criterion = review.get("criterion")
        if not isinstance(criterion, str):
            continue  # Article coverage reports undeclared or missing criteria.
        if reviewer != reviewer.strip() or reviewer.strip() in writers:
            issue("review_identity", f"Review {review['id']} needs an unpadded reviewer ID independent of all writers.")
        role = (criterion, review["reviewer_type"])
        if reviewer in assignments and assignments[reviewer] != role:
            issue("review_independence", f"{reviewer} has conflicting criteria or reviewer types in this run.")
        assignments[reviewer] = role

        end = review_time(review, "completed_at", issue)
        if criterion == "holistic":
            if holistic_reader is not None and reviewer != holistic_reader:
                issue("review_independence", "Use one holistic reviewer for the complete editorial package.")
            holistic_reader = reviewer
            if review["lane"] != "overall":
                issue("review_criterion", f"Holistic review {review['id']} must use the overall lane.")
            start = review_time(review, "started_at", issue)
            if start and end and end < start:
                issue("review_order", f"Holistic review {review['id']} finishes before it starts.")
            if start:
                final_starts.append((review["id"], start))
        elif end:
            specialist_finishes.append(end)

    last_specialist = max(specialist_finishes, default=None)
    for review_id, start in final_starts:
        if last_specialist and start < last_specialist:
            issue("review_order", f"Holistic review {review_id} started before all specialists completed this run.")


def nonblank(value):
    return isinstance(value, str) and bool(value.strip())


def revision_file(base, record, path_key, hash_key):
    """Check the exact evidence bytes using portable paths relative to the run."""
    relative = record.get(path_key)
    if (not nonblank(relative) or "\\" in relative or ":" in relative
            or any(part in ("", ".", "..") for part in relative.split("/"))):
        raise ValueError(f"{path_key} requires a path inside the run directory.")
    path = base / relative
    if path.resolve() != base.resolve() / relative or not path.is_file():
        raise ValueError(f"{path_key} must identify a regular file inside the run.")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if record.get(hash_key) != digest.hexdigest():
        raise ValueError(f"{hash_key} differs from the current {path_key}.")
    return path


def active_requirements(plan, canonical):
    rounds = plan.get("rounds") if isinstance(plan, dict) else None
    if not isinstance(rounds, list) or not rounds:
        raise ValueError("The frozen plan needs the initial brief and its subsequent rounds.")
    active, seen, versions = {}, set(), set()
    for index, entry in enumerate(rounds):
        if not isinstance(entry, dict) or not nonblank(entry.get("version")) or entry["version"] in versions:
            raise ValueError("Each round needs a unique version.")
        versions.add(entry["version"])
        rows = entry.get("requirements")
        if not isinstance(rows, list) or (index == 0 and not rows):
            raise ValueError("Each round needs a requirements list; the original brief cannot be empty.")
        earlier = dict(active)
        for row in rows:
            if not isinstance(row, dict) or any(not nonblank(row.get(k)) for k in ("id", "article_id", "source", "requirement")):
                raise ValueError("Each requirement needs an ID, canonical article ID, source locator and requirement.")
            req_id, article_id = row["id"], row["article_id"]
            if req_id in seen or article_id not in canonical:
                raise ValueError(f"Requirement {req_id} needs a unique ID and known article.")
            seen.add(req_id)
            replacements = row.get("supersedes", [])
            if (not isinstance(replacements, list) or any(not nonblank(k) for k in replacements)
                    or (replacements and not nonblank(row.get("reason")))):
                raise ValueError(f"{req_id} needs valid supersedes IDs and a reason for the later instruction.")
            for old in replacements:
                if old not in active or old not in earlier or earlier[old]["article_id"] != article_id:
                    raise ValueError(f"{req_id} can supersede only an active requirement from an earlier round for this article.")
                del active[old]
            active[req_id] = row
    return active


def audit_body_render(base, target, render):
    if not isinstance(target, dict) or not nonblank(target.get("delivery_role")):
        raise ValueError("page_range needs its delivery role and bounds.")
    lo, hi = target.get("min"), target.get("max")
    if not all(type(x) in (int, float) and 0 < x < float("inf") for x in (lo, hi)) or lo > hi:
        raise ValueError("page_range requires positive, finite min and max in order.")
    if not isinstance(render, dict):
        raise ValueError("A rendered body-page requirement needs body_render evidence.")
    revision_file(base, render, "delivery_path", "delivery_sha256")
    pdf = revision_file(base, render, "render_path", "render_sha256")
    with pdf.open("rb") as stream:
        if stream.read(5) != b"%PDF-":
            raise ValueError("render_path must identify the measured PDF.")
    fractions = render.get("body_page_fractions")
    if (not isinstance(fractions, list) or not fractions
            or any(type(x) not in (int, float) or not 0 <= x <= 1 for x in fractions)):
        raise ValueError("Provide one finite occupied body fraction from 0 to 1 per physical page.")
    pages = math.fsum(fractions)
    if not lo <= pages <= hi:
        raise ValueError(f"Body occupies {pages:g} equivalent pages, outside {lo:g}–{hi:g}; exclude references and unused space.")
    return pages


def audit_cumulative(manifest, base, canonical, texts, hashes, current_reviews):
    """Validate the frozen scope and current records, not the semantic content of a fix."""
    record = manifest.get("cumulative_revision")
    if manifest.get("schema_version") != 2 or not isinstance(record, dict):
        raise ValueError("Cumulative checking requires schema 2 and a cumulative_revision object.")
    path = revision_file(base, record, "plan_path", "plan_sha256")
    if path.stat().st_size > 4 * 1024 * 1024:
        raise ValueError("Revision plan exceeds the supported 4 MiB.")
    plan = json.loads(path.read_text(encoding="utf-8"))
    active = active_requirements(plan, canonical)
    if "previous_plan" in plan:
        previous = plan["previous_plan"]
        if not isinstance(previous, dict):
            raise ValueError("previous_plan requires the earlier plan path and its archived hash.")
        previous_path = revision_file(base, previous, "path", "sha256")
        if previous_path.stat().st_size > 4 * 1024 * 1024:
            raise ValueError("Archived revision plan exceeds the supported 4 MiB.")
        archived = json.loads(previous_path.read_text(encoding="utf-8"))
        old_rounds = archived.get("rounds") if isinstance(archived, dict) else None
        rounds = plan["rounds"]
        if (not isinstance(old_rounds, list) or not old_rounds or len(rounds) <= len(old_rounds)
                or rounds[:len(old_rounds)] != old_rounds):
            raise ValueError("Carry forward all frozen rounds unchanged, then append the new round.")
    checks = record.get("checks")
    if not isinstance(checks, dict) or set(checks) != set(active):
        missing = sorted(set(active) - set(checks if isinstance(checks, dict) else ()))
        raise ValueError(f"Current checks must cover exactly the active requirements. Missing IDs: {missing}.")
    pages = {}
    for key, requirement in active.items():
        article_id = requirement["article_id"]
        check = checks[key]
        if (not isinstance(check, dict) or check.get("status") != "verified"
                or not nonblank(check.get("evidence")) or not nonblank(check.get("quote"))):
            raise ValueError(f"{key} needs a verified disposition, comparison evidence and current article quote.")
        if (article_id not in hashes or check.get("article_sha256") != hashes[article_id]
                or check["quote"] not in texts.get(article_id, "")):
            raise ValueError(f"{key} is stale or its quoted passage is absent from the current article.")
        if "prior_fix" in requirement:
            prior = requirement["prior_fix"]
            if not isinstance(prior, dict) or not nonblank(prior.get("quote")):
                raise ValueError(f"{key} needs the corresponding quote from the previously accepted version.")
            archived = revision_file(base, prior, "path", "sha256")
            if prior["quote"] not in archived.read_text(encoding="utf-8"):
                raise ValueError(f"{key} prior fix quote is absent from its archived version.")
        if "page_range" in requirement:
            pages[key] = audit_body_render(base, requirement["page_range"], check.get("body_render"))
    checks_hash = sha256(json.dumps(checks, sort_keys=True, ensure_ascii=False,
                                   separators=(",", ":"), allow_nan=False).encode("utf-8"))
    for article_id in {row["article_id"] for row in active.values()}:
        if "revision_continuity" not in canonical[article_id].get("required_criteria", []):
            raise ValueError(f"{article_id} needs the revision_continuity criterion.")
        for criterion in ("revision_continuity", "holistic"):
            matching = [r for r in current_reviews[article_id] if r.get("criterion") == criterion]
            if (len(matching) != 1 or matching[0].get("revision_plan_sha256") != record["plan_sha256"]
                    or matching[0].get("revision_checks_sha256") != checks_hash):
                raise ValueError(f"{article_id} needs a current {criterion} approval bound to the complete plan and checks hashes.")
    return {"plan_sha256": record["plan_sha256"], "checks_sha256": checks_hash, "verified_requirements": len(active),
            "body_page_equivalents": pages, "layout_independently_measured": False}


def audit(manifest, base, require_cumulative=False):
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
    if version == 2:
        audit_review_team(manifest, canonical, current_reviews, issue)
    for key, current in current_reviews.items():
        if version == 2:
            outputs = {artifact_id for artifact_id, artifact in artifacts.items()
                       if artifact.get("canonical_id") == key and artifact.get("kind") in ("txt", "html")}
            audit_criterion_reviews(canonical[key], current, outputs, issue)
        else:
            completed = {review["lane"] for review in current}
            for missing in sorted({"readability", "source", "overall"} - completed):
                issue("missing_review", "Article " + key + " lacks a current independent approved " + missing + " review.")
    cumulative = None
    if require_cumulative or "cumulative_revision" in manifest:
        try:
            cumulative = audit_cumulative(manifest, base, canonical, texts, hashes, current_reviews)
        except (OSError, UnicodeError, ValueError, TypeError, OverflowError, RecursionError) as exc:
            issue("cumulative_revision", str(exc))
    contracts = {1: "legacy_lanes", 2: "independent_criteria_and_holistic"}
    contract = contracts.get(version) if type(version) is int else None
    return {"ok": not errors, "schema_version": version, "review_contract": contract, "semantic_verification_performed": False,
            "cumulative_revision": cumulative,
            "scope": "Deterministic files, counts, claim declarations, and review attestations only; no source reading, fact-checking, prose quality judgment, or page-count verification.",
            "body_counts": counts, "errors": errors, "warnings": warnings,
            "error_count": len(errors), "warning_count": len(warnings)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--require-cumulative", action="store_true", help="Require the frozen revision plan and current checks.")
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("Manifest must be a JSON object.")
        result = audit(manifest, args.manifest.resolve().parent, require_cumulative=args.require_cumulative)
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, AttributeError) as exc:
        result = {"ok": False, "semantic_verification_performed": False, "errors": [{"code": "manifest", "message": str(exc)}], "warnings": [], "error_count": 1, "warning_count": 0}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
