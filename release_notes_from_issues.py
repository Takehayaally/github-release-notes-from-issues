from __future__ import annotations

import argparse
import json
from pathlib import Path


SECTION_RULES = {
    "Added": {"feature", "enhancement", "added"},
    "Fixed": {"bug", "fix", "fixed"},
    "Docs": {"docs", "documentation"},
    "Changed": {"change", "changed", "refactor"},
}


def load_issues(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "items" in payload:
        payload = payload["items"]
    if not isinstance(payload, list):
        raise ValueError("Issues file must be a list or an object with an items list.")
    return payload


def labels_for(issue: dict) -> set[str]:
    labels = issue.get("labels", [])
    names = set()
    for label in labels:
        if isinstance(label, dict):
            names.add(str(label.get("name", "")).lower())
        else:
            names.add(str(label).lower())
    return names


def section_for(issue: dict) -> str:
    labels = labels_for(issue)
    for section, rule_labels in SECTION_RULES.items():
        if labels & rule_labels:
            return section
    return "Other"


def render_release_notes(issues: list[dict], version: str) -> str:
    grouped = {section: [] for section in [*SECTION_RULES.keys(), "Other"]}
    for issue in issues:
        if issue.get("state", "closed") != "closed":
            continue
        grouped[section_for(issue)].append(issue)

    lines = [f"# Release Notes {version}", ""]
    for section, section_issues in grouped.items():
        if not section_issues:
            continue
        lines.extend([f"## {section}", ""])
        for issue in section_issues:
            number = issue.get("number", "")
            title = issue.get("title", "Untitled")
            url = issue.get("html_url", "")
            suffix = f" ([#{number}]({url}))" if number and url else f" (#{number})" if number else ""
            lines.append(f"- {title}{suffix}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create release notes from GitHub issues JSON.")
    parser.add_argument("--issues", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--out", default="RELEASE_NOTES.md")
    args = parser.parse_args(argv)

    issues = load_issues(Path(args.issues))
    output = render_release_notes(issues, args.version)
    Path(args.out).write_text(output, encoding="utf-8")
    print(f"Wrote release notes for {len(issues)} issues to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
