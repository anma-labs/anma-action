# ANMA boundary check — GitHub Action

[![Marketplace](https://img.shields.io/badge/Marketplace-ANMA%20boundary%20check-2ea44f?logo=github)](https://github.com/marketplace/actions/anma-boundary-check)
[![test](https://github.com/anma-labs/anma-action/actions/workflows/test.yml/badge.svg)](https://github.com/anma-labs/anma-action/actions/workflows/test.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

Enforce module-dependency boundaries for AI-assisted code in CI — for **Python, Go,
and TypeScript** projects — with one step and no local Python setup.

This Action runs [`anma`](https://github.com/anma-labs/anma) against your repo,
fails the job on a disallowed cross-module import, and annotates the offending line
right on the pull request. It bundles its own Python, so it works the same in a Go
or TypeScript repo as in a Python one.

## Quickstart

```yaml
# .github/workflows/boundaries.yml
name: boundaries
on: [push, pull_request]

jobs:
  anma:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: anma-labs/anma-action@v1
```

That's it. The Action checks out nothing itself — run `actions/checkout` first — then
verifies your contracts and boundaries. A violation looks like this on the PR:

> ❌ `accounts` imports `billing` but it is not in `depends_on` — `src/domains/accounts/service.py:1`

## What it does

1. Installs `anma` from PyPI (the version you pin, or latest).
2. Runs `anma sync --check` — confirms the generated `CLAUDE.md` / hook / CI files
   are in sync with your `anma.yaml` contracts (catches drift).
3. Runs `anma check --json` — finds disallowed cross-module imports, annotates each
   offending file/line on the PR, and writes a summary table to the job.
4. Fails the job if there are violations, contract errors, or sync drift — unless
   `warn-only` is set.

By default it uses anma's **builtin** engine (zero extra dependencies, works on any
runner). The external backends (`go-arch-lint`, `dependency-cruiser`) are a future
opt-in; you do not need a Go or Node toolchain for this Action to work.

## Inputs

| Input | Default | Description |
|---|---|---|
| `path` | `.` | Project directory (the one containing `anma.yaml`). |
| `version` | latest | `anma` version to install from PyPI, e.g. `0.7.0`. |
| `python-version` | `3.12` | Python used to run `anma`. |
| `extras` | none | Optional anma extras, e.g. `tach`. |
| `sync-check` | `true` | Also run `anma sync --check` to catch artifact drift. |
| `warn-only` | `false` | Annotate but do not fail the job (gradual adoption). |

## Outputs

| Output | Description |
|---|---|
| `violations` | Number of disallowed cross-module imports found. |
| `contract-errors` | Number of contract errors found. |

## Examples

**Pin the anma version** (recommended for reproducible CI):

```yaml
      - uses: anma-labs/anma-action@v1
        with:
          version: "0.7.0"
```

**A project in a subdirectory** (monorepo):

```yaml
      - uses: anma-labs/anma-action@v1
        with:
          path: services/api
```

**Gradual adoption** — annotate violations without failing the build yet:

```yaml
      - uses: anma-labs/anma-action@v1
        with:
          warn-only: "true"
```

**Use the tach engine** (Python, more precise interface-level checks):

```yaml
      - uses: anma-labs/anma-action@v1
        with:
          extras: "tach"
```

The same workflow works unchanged for Go and TypeScript repos — the Action enforces
module→module boundaries from your `anma.yaml` regardless of language.

## Versioning

`@v1` tracks the Action's input/output interface and moves forward with
non-breaking updates. Pin `@v1.0.0` for an exact Action revision, and use the
`version:` input to pin the `anma` release it installs — the two are independent.

## License

Apache-2.0. `anma` itself is Apache-2.0 and lives at
[anma-labs/anma](https://github.com/anma-labs/anma);
docs at [anma-labs/anma/docs](https://github.com/anma-labs/anma/tree/main/docs).
