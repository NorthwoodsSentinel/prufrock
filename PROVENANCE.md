# Provenance of the gate (NOR-391)

Where each part of this repo's tooling and rules came from, and what was changed. Built 2026-11-15 for NOR-391 (part of NOR-381, which brings the owner's repositories under Cliff Hall's tooling as he uses it). The owner's default, set while ruling on the source's rules on 2026-11-14: where the source's way and ours differ, the source's way stands until there is a stated reason to depart.

## Sources

| Short name | Repository | Commit | Read for |
| --- | --- | --- | --- |
| servers | `modelcontextprotocol/servers` (public), the source's second repository | `e1d154ee03703da9bb00b81f36a6704cae6caa3d` | **The Python tooling.** Its Python servers (`src/fetch`, `src/git`, `src/time`) each have `pyproject.toml`, `.python-version` and `uv.lock`, a `[dependency-groups] dev` (git) or `[tool.uv] dev-dependencies` of pyright, ruff, pytest and pytest-cov, and `[tool.coverage.run] branch = true`. Its root runs them through `scripts/validate-py.mjs` (#4865 there) and `scripts/coverage-py.mjs` with `scripts/lib/py-coverage.mjs` (#4855), from `.github/workflows/python.yml`. |
| fleet-mcp | `NorthwoodsSentinel/fleet-mcp` (private) | `f1bea961a1f5d1c8a641d760d5bec94368674d82` (origin/main) | The worked example: `AGENTS.md` (blob `058b489b`), `.github/workflows/main.yml` (blob `7932a098`) and `dco.yml` (blob `9d3165be`), and its copies of the MCP Inspector's scripts. Its own `PROVENANCE.md` traces each of those to WALL-E and to the Inspector. |
| inspector | `modelcontextprotocol/inspector` (public), branch `v2/main` | `d330df9617e44ec893bc1a53618662239342d433` | Not copied from directly. It is where fleet-mcp's (through WALL-E's) `AGENTS.md`, sign-off check, action-pin guard and scope-check lesson came from. |
| prufrock | this repo | `c70792d644055f8a63696310360ba66df841cc3d` (origin/HEAD when the branch was cut) | The product: `README.md`, `pyproject.toml`, `prufrock/*.py`, and `c70792d` itself (fleet routing, fail loudly), read first and left unchanged in behaviour. |

**License note**: the servers and Inspector `LICENSE` files state that the MCP project is in a licensing transition from the MIT License to Apache-2.0: code contributions are under Apache-2.0 (or MIT where relicensing consent was not given), and documentation contributions (excluding specifications) are under CC-BY-4.0. The scripts in `scripts/` are copies of that project's code and keep their attribution headers. This repo itself is declared MIT in `pyproject.toml` and has no `LICENSE` file; how to carry the source's license text for `scripts/` is an owner decision, listed in the pull request.

## How to read the tables

- **KEEP**: the source unchanged (a provenance paragraph at the top may be added).
- **ADAPT**: the source with the smallest edit this repo's facts require. The row says what changed and why.
- **OURS**: no counterpart in a source.
- Copied scripts were committed byte-for-byte first (`NOR-391: copy the gate scripts unedited from their sources`), so `git diff` of the next commit shows every edit.

## Table 1: files

| File | Source | Verdict | What changed and why |
| --- | --- | --- | --- |
| `pyproject.toml` `[dependency-groups] dev` | servers `src/git/pyproject.toml` (blob `e33c52f0`) | ADAPT | His four tools and their floors: pyright `>=1.1.407`, ruff `>=0.17.3`, pytest `>=8.0.0`, pytest-cov `>=7.1.0`. pytest-asyncio left out: prufrock has no async code. The existing `[project.optional-dependencies] dev` extra is left as it was (it is part of the published metadata). |
| `pyproject.toml` `[tool.pytest.ini_options]` | servers `src/git/pyproject.toml` | ADAPT | `testpaths`, `python_files`, `python_classes`, `python_functions` kept; the asyncio settings left out (no async code). |
| `pyproject.toml` `[tool.coverage.run]`, `[tool.coverage.report]` | servers `src/git/pyproject.toml` | ADAPT | `branch = true`, `show_missing = true` kept; `source` names this package (`prufrock`). |
| `.python-version` | servers `src/git/.python-version`, `src/time/.python-version` (`3.10`) | KEEP | `3.10` is also this repo's `requires-python` floor. |
| `uv.lock` | servers (each Python server commits one) | OURS (generated) | Written by `uv lock` with uv 0.13.8. CI pins the same uv (`CI_UV_VERSION`). |
| No `[tool.ruff]` table | servers (none of its Python servers has one) | KEEP | ruff's default rule set for the locked version is the lint, as there. ruff reads a user-level configuration only when a project has none; the lock pins the version, and CI has no user configuration. |
| No pyright configuration | servers (none) | KEEP | pyright's default mode over the repo, as there. |
| `scripts/validate-py.mjs` | servers `scripts/validate-py.mjs` (blob `ceef6d43`) | ADAPT | His `STEPS`, `runCommand`, `validateServers`, `summarize` unchanged. Discovery removed: this repo is one package at its root, so `main()` runs the chain once there and refuses arguments. The header lists the edits. |
| `scripts/validate-py.test.mjs` | servers (blob `bc9b702f`) | ADAPT | Discovery tests removed with the functions; one test added for the no-arguments rule. |
| `scripts/coverage-py.mjs` | servers (blob `94e320bc`) | ADAPT | Same discovery edit; failing files printed as the report names them (no `src/<server>/` prefix). |
| `scripts/coverage-py.test.mjs` | servers (blob `2307575b`) | ADAPT | One expectation follows the prefix edit; one test added for the no-arguments rule. |
| `scripts/lib/py-coverage.mjs` | servers (blob `2ba4af39`) | KEEP | The per-file check: every measured file at >= 90% on lines and on branches, exact integer comparison, no exclude list, a report without branch coverage refused. |
| `scripts/lib/py-coverage.test.mjs` | servers (blob `78da52dd`) | KEEP | |
| `scripts/verify-coverage-scope-py.mjs` and its test | inspector's `scripts/verify-coverage-scope.mjs` lesson (#2709 there), as fleet-mcp's `AGENTS.md` states it | OURS | The source's scope check is written for Vitest globs. This one compares `coverage.json` with `git ls-files prufrock`: every tracked `.py` file must be measured, every other tracked file must be named by exact path in `EXCLUDED` with a reason citing its follow-up, stale entries fail, untracked measured files fail. |
| `scripts/verify-action-pins.mjs` | fleet-mcp (blob `011a04c4`) | KEEP | Code unchanged. A provenance paragraph, and the ticket in the failure message (NOR-391 for fleet-mcp's NOR-355). fleet-mcp's "every job is checked" kept, for this repo's own reason (public repo; the owner's scope asks for every action pinned). |
| `scripts/verify-action-pins.test.mjs` | fleet-mcp (blob `82686195`) | KEEP | A provenance paragraph only. |
| `scripts/dco-check.mjs`, `scripts/dco-check.test.mjs` | fleet-mcp (blobs `5338fedd`, `7fd4bd08`) | KEEP | A provenance paragraph only. `main` is this repo's default branch, so `--base origin/main` holds. Kept in Node, copied verbatim, rather than rewritten in Python: the source's way, and a rewrite would lose its tests and its review history. |
| `scripts/lib/main-module.mjs`, its test | fleet-mcp (blobs `b35c2374`, `66adff99`) | KEEP | A provenance paragraph only (imported by the sign-off check and the scope check). |
| `package.json`, `package-lock.json` | servers' and fleet-mcp's root `package.json` (`npm run` scripts as the gate's entry points) | ADAPT | Scripts only, plus one devDependency, `yaml` 2.9.1 (fleet-mcp's version), which the action-pin guard imports. `format` is `ruff format`. `local:gate` = `validate`, `local:dco`, `coverage`, in fleet-mcp's order. |
| `.github/workflows/main.yml` | fleet-mcp `main.yml`; servers `python.yml` for the Python steps | ADAPT | fleet-mcp's shape (one `validate` job, every `local:gate` stage but `local:dco`, least privilege, SHA pins, `persist-credentials: false`). Bun setup replaced by servers' `astral-sh/setup-uv` (his major, v7: v7.6.0) and `actions/setup-python` with `python-version-file`. uv pinned once (`CI_UV_VERSION`), a departure from servers, which leaves setup-uv on its default: `uv.lock` was written by that version. `timeout-minutes: 30`, provisional (the dlib build). No Inspector smoke: not an MCP server. |
| `.github/workflows/dco.yml` | fleet-mcp `dco.yml` | ADAPT | Triggers, jobs, steps and pins unchanged. Comments: the ruleset remarks (no ruleset here) and who merges (the owner). One behaviour line: the PR job's checkout returns to the source's `persist-credentials: false`, because this repo is public (fleet-mcp set `true` only because its private fetch needed the token). |
| `.gitignore` | (tool outputs) | OURS | `coverage.json`, `.coverage`, `.pytest_cache/`, `.venv/`, `node_modules/` added, so no gate reads generated output. |
| `tests/test_*.py` | none | OURS | One file per module. Synthetic text and generated images only; the fleet bridge, the anthropic package, Whisper and face_recognition replaced by fakes. |
| `AGENTS.md` | fleet-mcp `AGENTS.md` | ADAPT | Table 2. |
| `README.md` "Development" section | fleet-mcp's rule "update README.md when the developer setup changes" | OURS | The gate commands, in four lines. |

## Table 2: `AGENTS.md`, section by section

| Section | fleet-mcp section | Verdict | What changed and why |
| --- | --- | --- | --- |
| Title and what the repo is | Title, lines 1-6 | ADAPT | prufrock's description from `README.md` and `cli.py`; public; the owner merges. The fleet-routing paragraph is OURS, from commit `c70792d`, so no later change undoes it by accident. The memoir paragraph is OURS (owner, NOR-381: memoir material never enters the repo). |
| Rules here, procedures in skills | lines 8-12 | KEEP | Marker: no procedures yet. "line by line" became "section by section" (this file's table is by section). |
| Skills index | Skills index | ADAPT | No skills yet; the rule that a new skill adds its row kept. |
| Development setup | Development setup | ADAPT | Bun replaced by uv (servers' Python way: `uv sync --locked`, `uv run --frozen`). "Prufrock stays Python" is the owner's (NOR-381). The source's runner rule (`npx`) kept. |
| Dependency placement | Dependency placement | ADAPT | npm `overrides` rule replaced by where a Python dependency goes and that `uv.lock` changes with `pyproject.toml`. |
| Dependency updates are issue-driven | same | ADAPT | Kept, condensed; marker "No sweeps yet". The pin rule kept with "every job", for this repo's reason (public CI vouches for installed code). |
| The upstream watch | same | ADAPT | Upstreams named for this repo (the gate's source files). The model-safety rules kept, condensed. |
| Contributing | Contributing | ADAPT | fleet-mcp's "an agent merges its own PR" does not apply: this repo is public, and the owner's scope for NOR-381 is "open PRs" only. The ticket line accepts `Part of NOR-<PARENT> — NOR-<N>` for a child ticket. |
| Project Status and Direction | same | ADAPT | Repo name; public. |
| Maintenance Rules | same | KEEP | "header comment" says a module docstring in Python. |
| Maintaining the skills | same | ADAPT | Condensed to "the four rules apply when the first skill is added" (no skills, no `verify:skills`). |
| Issue-driven Work Style | same | KEEP, two edits | "Closes" generalised to "the ticket on the first line"; the personal-data scan added to "when work is complete"; the Codex stop rule gains the owner's two-failed-rounds limit for NOR-381 and the owner's 2026-10-30 rule (security fixed; anything else ticketed). |
| Responding to Code Reviews | same | KEEP | Condensed. |
| Always test new or modified code | same | ADAPT | The bar stays the source's (>= 90 per file, never lowered, CI enforces). Mapped to Python: coverage.py measures lines and branches only; statements are its lines and it has no function dimension, so four become two (servers' own reasoning in `py-coverage.mjs`). Ignore annotation is `# pragma: no cover  # <reason>`. Exact-path exclusion only for a file coverage.py cannot measure, with the scope check named. Test-file naming lesson kept. Tests-call-no-model rule is OURS. |
| Test-gate timeouts | same | ADAPT | Vitest specifics removed; the rules kept. |
| Mandatory pre-push gate | same | ADAPT | This repo's stages. |
| Waiting on long-running work | same | KEEP | Condensed. |
| Build output is never a gate target | same | ADAPT | This repo's generated paths. |
| Lint has no warning tier | same | ADAPT | ruff has no warning level; ruff's default rules and pyright's default mode, as in servers' Python servers. Inline waivers name their code and carry a reason. |
| Typescript instructions | same | ADAPT → "Python instructions" | Prufrock is Python. Recorded exception: `prufrock/fleet_bridge.ts`. The fail-loudly rule is from `c70792d`. |
| Cloudflare work | same | not applicable | Prufrock has no Worker. |
| Memoir material and personal data | none | OURS | The owner's hard limits for this repo (NOR-381). The identifier list itself stays outside this public repo. |
| Only the owner does | same | ADAPT | Merging (public repo), rulesets and branch protection, releases, and the fleet backend's default added; Worker and Cloudflare lines removed. |

## Coverage: what "four dimensions" means here

The source's bar is ">= 90 on all four dimensions — lines, statements, functions, and branches — per file", enforced by Vitest's V8 coverage for TypeScript. The source's own Python gate (servers, #4855) maps it to coverage.py: `num_statements`/`covered_lines` (a Python statement is what coverage.py counts as a line, so "lines" and "statements" are one figure) and `num_branches`/`covered_branches` with `branch = true`. coverage.py has no function dimension. Its `fail_under` setting is global, so one well-tested module could carry an untested one; `scripts/lib/py-coverage.mjs` therefore checks **each file** at >= 90% on both, in integers (89.96% fails), and refuses a report measured without branches. This repo uses that script unchanged.

## Product-code edits the gate required

All behaviour-preserving; listed with reasons in the pull request: `ruff format` over every file; ruff's safe fixes (import order, f-strings without placeholders, a redundant `pass`); `set(...)` of a generator to a set comprehension (2); `if c: return False / return True` to `return not c` (1); `check=False` written out on two `subprocess.run` calls (the default); `Image.LANCZOS` to `Image.Resampling.LANCZOS` (the same value, available since Pillow 9.1; the floor is 10.0); `load_json` annotated `-> Any` in two files (it returns parsed JSON); eight deliberate broad `except` clauses given `# noqa: BLE001` with their reasons (one also `S112`, a silent `continue`); two `# pyright: ignore` with reasons (a Pillow stub gap; the API reply's first block, which still raises as before if it is not text).
