#!/usr/bin/env python3
"""Check repository-local Markdown targets offline; leave external URLs alone."""
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


def links(text):
    # Examples in fenced code and inline code are not rendered links.
    text = re.sub(r"(?ms)^\s*(`{3,}|~{3,}).*?^\s*\1\s*$", "", text)
    text = re.sub(r"`[^`\n]*`", "", text)
    inline = re.findall(r"\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[^)]*)?\)", text)
    definitions = re.findall(r"(?m)^\s*\[[^\]]+\]:\s*(<[^>]+>|\S+)", text)
    return [target.strip("<>") for target in inline + definitions]


def check(root):
    errors = []
    for document in sorted(root.rglob("*.md")):
        if ".git" in document.parts:
            continue
        for target in links(document.read_text()):
            url = urlsplit(target)
            if url.scheme or url.netloc or not url.path:
                continue
            path = unquote(url.path)
            resolved = (root / path.lstrip("/") if path.startswith("/") else document.parent / path).resolve()
            if not resolved.is_relative_to(root):
                errors.append(f"{document.relative_to(root)}: target outside repository: {target}")
            elif not resolved.exists():
                errors.append(f"{document.relative_to(root)}: missing target: {target}")
    return errors


if __name__ == "__main__":
    problems = check(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve())
    for problem in problems:
        print(problem, file=sys.stderr)
    sys.exit(bool(problems))
