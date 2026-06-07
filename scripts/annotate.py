#!/usr/bin/env python3
"""Turn `anma check --json` output into GitHub PR annotations + a step summary.

Reads the JSON (written by the action to a file), emits `::error`/`::warning`
workflow commands on the offending file/line, writes a Markdown summary to
$GITHUB_STEP_SUMMARY, exports the violation/contract-error counts as step
outputs, and exits non-zero when the run should fail.

Single responsibility: this only interprets `anma check`. Sync-drift is handled
as its own step in action.yml.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import PurePosixPath


def _gh(line: str) -> None:
    print(line, flush=True)


def _emit_output(name: str, value) -> None:
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"{name}={value}\n")


def _summary(md: str) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(md + "\n")


def _rel(base: str, file: str) -> str:
    # anma emits file paths relative to the project `path`; annotations need
    # them relative to the repo root, so prefix with `path` when it isn't ".".
    if base and base not in (".", "./"):
        return str(PurePosixPath(base) / file)
    return file


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        _gh("::error title=ANMA::annotate.py: missing JSON path argument")
        return 1
    json_path = argv[1]
    base = os.environ.get("ANMA_PATH", ".")
    warn_only = os.environ.get("ANMA_WARN_ONLY", "false").lower() == "true"

    try:
        with open(json_path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        # `anma check` produced no parseable JSON — surface it, fail loudly.
        _gh(f"::error title=ANMA::could not read anma check output ({exc}). "
            f"See the step log above.")
        _emit_output("violations", -1)
        _emit_output("contract-errors", -1)
        return 1

    violations = data.get("violations", []) or []
    contract_errors = data.get("contract_errors", []) or []
    engine = data.get("engine", "builtin")

    fail_level = "warning" if warn_only else "error"

    for ce in contract_errors:
        msg = ce if isinstance(ce, str) else ce.get("message", str(ce))
        _gh(f"::{fail_level} title=ANMA contract error::{msg}")

    for v in violations:
        level = "warning" if (warn_only or v.get("deprecated")) else "error"
        f = _rel(base, v.get("file", ""))
        line = v.get("line", 1) or 1
        module = v.get("module", "?")
        message = v.get("message", "disallowed cross-module import")
        title = "ANMA boundary (deprecated dep)" if v.get("deprecated") else "ANMA boundary"
        loc = f"file={f},line={line}," if f else ""
        _gh(f"::{level} {loc}title={title}::{module}: {message}")

    _emit_output("violations", len(violations))
    _emit_output("contract-errors", len(contract_errors))

    # ---- step summary ----
    if not violations and not contract_errors:
        _summary(f"### ✅ ANMA — all module boundaries respected\n\n"
                 f"_engine: `{engine}`_")
    else:
        lines = [f"### ❌ ANMA — {len(violations)} violation(s)"
                 + (f", {len(contract_errors)} contract error(s)" if contract_errors else "")
                 + f"\n\n_engine: `{engine}`_\n"]
        if violations:
            lines.append("| Module | File | Line | Issue |")
            lines.append("|---|---|---:|---|")
            for v in violations:
                lines.append(f"| `{v.get('module','?')}` | "
                             f"`{_rel(base, v.get('file',''))}` | "
                             f"{v.get('line','')} | {v.get('message','')} |")
        if contract_errors:
            lines.append("\n**Contract errors:**\n")
            for ce in contract_errors:
                msg = ce if isinstance(ce, str) else ce.get("message", str(ce))
                lines.append(f"- {msg}")
        _summary("\n".join(lines))

    if warn_only:
        return 0
    return 1 if (violations or contract_errors) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
