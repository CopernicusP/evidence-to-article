#!/usr/bin/env python3
"""Render the documented Markdown subset without rewriting article text (stdlib only)."""

import argparse
import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import urlsplit


class MarkdownError(ValueError):
    pass


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def inline(text, warnings):
    """Return HTML and visible text; unsupported inline markers remain literal."""
    rendered, visible, pos = [], [], 0
    token = re.compile(
        r"\[([^\[\]\n]+)\]\(([^\s()]+)\)|`([^`\n]+)`|"
        r"\*\*([^\s*](?:[^*\n]*[^\s*])?)\*\*|"
        r"(?<!\w)__([^\s_](?:[^_\n]*[^\s_])?)__(?!\w)|"
        r"\*([^\s*](?:[^*\n]*[^\s*])?)\*|"
        r"(?<!\w)_([^\s_](?:[^_\n]*[^\s_])?)_(?!\w)"
    )
    for match in token.finditer(text):
        prefix = text[pos:match.start()]
        rendered.append(html.escape(prefix))
        visible.append(prefix)
        label, target, code, bold_star, bold_under, italic_star, italic_under = match.groups()
        if target is not None:
            scheme = urlsplit(target).scheme.lower()
            if scheme and scheme not in {"http", "https", "mailto"}:
                raise MarkdownError("Unsupported link scheme: " + scheme)
            label_html, label_text = inline(label, warnings)
            rendered.append('<a href="' + html.escape(target, quote=True) + '">' + label_html + '</a>')
            visible.append(label_text)
        else:
            content = next(value for value in (code, bold_star, bold_under, italic_star, italic_under) if value is not None)
            tag = "code" if code is not None else "strong" if bold_star is not None or bold_under is not None else "em"
            rendered.append("<" + tag + ">" + html.escape(content) + "</" + tag + ">")
            visible.append(content)
        pos = match.end()
    rendered.append(html.escape(text[pos:]))
    visible.append(text[pos:])
    # Remaining Markdown syntax is retained literally, never silently stripped.
    remainder = token.sub("", text)
    if re.search(r"\]\(|\[[^\]]+\]\[|\*\*|__|~~|`|\\[\W]", remainder):
        warnings.add("Unsupported or unmatched inline markup retained literally; inspect HTML.")
    return "".join(rendered), "".join(visible)


def parse_markdown(text):
    """Return (blocks, warnings). Each block is (kind, value, text, line_number)."""
    blocks, warnings, paragraph = [], set(), []
    paragraph_start = 0
    previous_list_line = False

    def flush():
        if paragraph:
            blocks.append(("p", None, "\n".join(paragraph), paragraph_start))
            paragraph.clear()

    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            flush()
            previous_list_line = False
            continue
        if (re.match(r"^\s*(```|~~~|>|!\[)", line)
                or re.match(r"^\s*\[[^\]]+\]:", line)
                or re.match(r"^\s+(?:[-*+]|\d+[.)])\s", line)
                or line.startswith(("    ", "\t"))
                or re.search(r"</?[A-Za-z][^>]*>", line)
                or re.match(r"^\s*\|", line)
                or re.match(r"^\s*[-:]+\s*\|", line)
                or re.match(r"^\s*(?:-{3,}|\*{3,}|_{3,}|={3,})\s*$", line)
                or re.match(r"^(?:\s*[-*_]){3,}\s*$", line)):
            raise MarkdownError(f"Line {number}: unsupported Markdown block; use headings, paragraphs, or flat lists.")
        if "![" in line or re.search(r"\[\^[^\]]+\]", line):
            raise MarkdownError(f"Line {number}: images and footnotes are unsupported; use ordinary links/citations.")
        if line.endswith("  "):
            warnings.add(f"Line {number}: two-space Markdown hard break retained as whitespace; use separate paragraphs if needed.")
        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        bullet = re.match(r"^([-*+]|\d+[.)])\s+(.+)$", line)
        if heading:
            flush()
            blocks.append(("h", len(heading[1]), heading[2], number))
        elif bullet:
            flush()
            marker = bullet[1]
            blocks.append(("ol" if marker[0].isdigit() else "ul", int(re.match(r"\d+", marker)[0]) if marker[0].isdigit() else None, bullet[2], number))
        else:
            if previous_list_line:
                warnings.add(f"Line {number}: list continuation rendered as a separate paragraph; use one line per list item or a blank separator.")
            if line.startswith("#"):
                warnings.add(f"Line {number}: heading-like text retained as a paragraph (headings need a space).")
            if "|" in line:
                warnings.add(f"Line {number}: pipe character retained as text; tables are unsupported.")
            if not paragraph:
                paragraph_start = number
            paragraph.append(line)
        previous_list_line = bool(bullet)
    flush()
    for _, _, value, _ in blocks:
        inline(value, warnings)
    return blocks, warnings


def body_count(text, language):
    blocks, warnings = parse_markdown(text)
    body = []
    for kind, level, value, _ in blocks:
        if kind == "h":
            if level == 2 and value.strip() in {"Sources", "参考来源"}:
                break
            continue
        body.append(inline(value, warnings)[1])
    visible = "\n".join(body)
    if language == "zh":
        count = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U0002ee5f\U00030000-\U000323af]", visible))
    elif language == "en":
        count = len(re.findall(r"[A-Za-z]+(?:['’\-][A-Za-z]+)*", visible))
    else:
        raise ValueError("language must be zh or en")
    return count, sorted(warnings)


def render_html(text, fallback_title="Article"):
    blocks, warnings = parse_markdown(text)
    title = next((inline(value, warnings)[1] for kind, _, value, _ in blocks if kind == "h"), fallback_title)
    output, list_kind = [], None
    for kind, level, value, _ in blocks:
        if kind != list_kind and list_kind:
            output.append("</" + list_kind + ">")
            list_kind = None
        content = inline(value, warnings)[0]
        if kind in {"ul", "ol"}:
            if list_kind is None:
                output.append("<" + kind + ">")
                list_kind = kind
            attribute = f' value="{level}"' if kind == "ol" else ""
            output.append("<li" + attribute + ">" + content + "</li>")
        elif kind == "h":
            output.append(f"<h{level}>" + content + f"</h{level}>")
        else:
            output.append("<p>" + content + "</p>")
    if list_kind:
        output.append("</" + list_kind + ">")
    page = """<!doctype html>
<html lang="und">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>""" + html.escape(title) + """</title>
<style>
:root{color-scheme:light}*{box-sizing:border-box}body{margin:0;background:#f7f6f2;color:#20251f;font:18px/1.75 Georgia,"Noto Serif CJK SC","Songti SC",serif}main{max-width:780px;margin:48px auto;padding:44px 54px;background:#fff;border:1px solid #e3e5de}h1,h2,h3,h4,h5,h6{line-height:1.3;color:#243b31;break-after:avoid}h1{font-size:2rem;margin:0 0 1.1em}h2{font-size:1.35rem;margin:1.8em 0 .7em}h3{font-size:1.12rem}p,ul,ol{margin:.85em 0}a{color:#235c4c;overflow-wrap:anywhere;text-underline-offset:3px}li{padding-left:.2em}code{font-size:.9em;background:#f2f3ef;padding:.1em .25em}p,li{orphans:3;widows:3}@media(max-width:640px){body{font-size:17px}main{margin:0;border:0;padding:28px 24px}h1{font-size:1.7rem}}@media print{body{background:#fff;font-size:11pt}main{max-width:none;margin:0;padding:0;border:0}a{color:inherit}@page{margin:20mm}}
</style>
</head>
<body><main>
""" + "\n".join(output) + "\n</main></body>\n</html>\n"
    return page.encode("utf-8"), sorted(warnings)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        source = args.input.read_bytes()
        text = source.decode("utf-8")
        if text.startswith("\ufeff"):
            raise ValueError("UTF-8 BOM is unsupported; save the canonical Markdown without a BOM.")
        page, warnings = render_html(text, args.input.stem)
        paths = {"txt": args.out_dir / (args.input.stem + ".txt"), "html": args.out_dir / (args.input.stem + ".html")}
        metadata_path = args.out_dir / (args.input.stem + ".outputs.json")
        if args.input.resolve() in {path.resolve() for path in [*paths.values(), metadata_path]}:
            raise ValueError("Output path would overwrite the input; use a Markdown input or another output directory.")
        args.out_dir.mkdir(parents=True, exist_ok=True)
        metadata = {"schema_version": 1, "input": {"path": str(args.input.resolve()), "sha256": sha256(source)}, "artifacts": [], "warnings": warnings}
        for kind, data in (("txt", source), ("html", page)):
            paths[kind].write_bytes(data)
            metadata["artifacts"].append({"kind": kind, "path": str(paths[kind].resolve()), "sha256": sha256(data)})
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, "metadata_path": str(metadata_path.resolve()), **metadata}, ensure_ascii=False, indent=2))
    except (OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
