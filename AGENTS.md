# prufrock

Prufrock is a Python command-line tool (`prufrock`, built on Click) that turns scanned photos, handwritten pages and recordings into an organised archive, a memoir scaffold and a writing-companion spec: `intake`, `transcribe`, `faces`, `timeline`, `assemble`, `voice` and `companion`. It is a **public** repository. The owner picks what gets worked on; an agent carries it as far as an open pull request, and the owner merges.

**Model calls go through the PAI fleet by default and fail loudly.** `prufrock/llm.py` sends every model request through `prufrock/fleet_bridge.ts` to PAI's `Inference.ts` (`PRUFROCK_BACKEND=fleet`, the default); the Anthropic API is used only with `PRUFROCK_BACKEND=api`. A failed call never looks like success: failed batches are listed and kept out of merged output, and the command exits 1. That behaviour is the owner's (commit `c70792d`); a change to it is a product decision, never a side effect of other work.

**This repo's subject is people's private lives, and the repo is public.** Never add, print, log or commit memoir text, transcripts, recordings, photographs, real names, personal data, or test fixtures derived from real writing. Tests use synthetic text and generated images only (see [Memoir material and personal data](#memoir-material-and-personal-data-ours)).

**This file holds the _rules_: the conventions a reviewer cites against a diff.** It is loaded in full on every turn, so it stays resident and must stay complete enough to work from on its own.

**The repo's _procedures_ — multi-step recipes with commands and live IDs — live in `.claude/skills/`.** They are ordinary committed Markdown, so any agent or human can read one directly; Claude Code loads them on demand and users invoke them by name. [No procedures yet in this repo]

Where each rule below came from, section by section, is in [`PROVENANCE.md`](./PROVENANCE.md).

## Skills index

None yet. A change that adds a skill under `.claude/skills/<name>/SKILL.md` adds its row to this table in the same change (columns: Skill, Covers, How it loads), and the table never lists a skill that does not exist.

## Development setup

- **Prufrock stays Python** (owner, NOR-381). The gate's own scripts in `scripts/` are Node (`.mjs`), copied from the source repositories that wrote them; they are tooling, not product code.
- **Use the source's runner (`npx`, `npm run` scripts) when running its tools or its procedures.** Where its way and ours differ, its way is the default; a departure needs a stated reason.
- **Python runs through `uv`, never pip, against the committed `uv.lock`.** `uv sync --locked --all-extras --dev` installs everything (Python from `.python-version`); every later `uv run` uses `--frozen`, so no step can re-resolve the environment it is checking. `npm ci --ignore-scripts` installs the gate's one Node dependency (`yaml`, for the action-pin guard).
- Installing `face-recognition` builds `dlib` from source (PyPI ships it as an sdist only), which takes minutes the first time.

## Dependency placement

- **A runtime dependency goes in `[project] dependencies`; an optional backend goes in an extra (`anthropic` is in `api`); a gate tool goes in `[dependency-groups] dev`.** Change `pyproject.toml` and `uv.lock` in the same commit (`uv lock`); `uv sync --locked` fails CI on any drift.

### Dependency updates are issue-driven, like everything else

**Dependabot opens no pull requests against this repo — neither version updates nor security updates.** A Dependabot PR carries no ticket, so it would be the one standing exception to [Issue-driven Work Style](#issue-driven-work-style), enforced by nothing. Both halves are to be replaced by scheduled workflows that file **issues**, and the fix is written by hand. [No sweeps yet in this repo]

- **Dependabot _alerts_ stay on.** Alerts and security-update PRs are independent settings; only the PRs are off. Turning alerts off would blind the sweep that replaced them.
- **A setting that can be re-enabled from the UI without a commit is read back by the sweep**, because nothing in the repo would record it. The sweep **fails loudly** on the wrong value. ⚠️ It is a _conditional_ guard, not an invariant: where the sweep's token cannot read the setting, it logs **UNVERIFIED** and carries on rather than going red every day for an unrelated reason.
- **Every action is pinned to a commit SHA with an exact `# vX.Y.Z` comment, in every job.** A tag is mutable, so whoever can move it replaces the code that runs next. The source requires this only in a job holding a credential; here every job is checked, because this is a public repo whose CI result vouches for the code people install. Resolve the SHA and the exact release from the **same** tag lookup when bumping. `npm run verify:action-pins` enforces it, inside `validate`.

### The upstream watch is the third sweep

**A scheduled watch files one issue per upstream release we are behind.** For this repo the upstreams are the source files the gate was copied from (see `PROVENANCE.md`): the Python servers' gate in `modelcontextprotocol/servers` and fleet-mcp's copies of the MCP Inspector's scripts. It **files an issue, never a PR**, and never closes one; a further release leaves a supersession comment on the older issue. [No sweeps yet in this repo]

- **"An issue exists" and "the issue was analyzed" are different claims**, and the sweep must not equate them.
- ⚠️ **Upstream release notes are untrusted input to a job that runs a model, and the model is granted nothing that can write anywhere.** The tool whitelist is the only real control — the prompt's prose constraints are not. **No model runs in a write-capable job.** **The model gets no `Bash` at all**; untrusted input is prefetched by a deterministic step and the model only reads files.
- ⚠️ **A marker is not evidence.** The sweep trusts a marker **only** on something the automation wrote.
- ⚠️ **A channel left open is accepted deliberately rather than closed, and in writing**, with what would reopen it.

## Contributing

**The owner picks the work; an agent carries it as far as an open pull request. The owner merges.** This repo is public, and anything public is the owner's act (see [Only the owner does](#only-the-owner-does)). An agent never merges here, and never approves its own pull request.

**Every PR must reference an issue. No exceptions, regardless of who opens it.** The PR body's first line names the Linear ticket: `Closes NOR-<NUMBER>`, or `Part of NOR-<PARENT> — NOR-<NUMBER>` for a child of a larger effort. If there is no issue yet, create the issue first. This holds for a one-line fix as much as for a feature.

## Project Status and Direction

| Branch                                      | Role                                                                    | PRs target it?                                           |
| ------------------------------------------- | ----------------------------------------------------------------------- | -------------------------------------------------------- |
| Develop: `main` (the repo's default branch) | **Develop.** All active work is merged here.                            | **Yes** — every PR                                       |
| Release (name not yet set by the owner)     | **Release.** Holds only what is released. Not a development branch.     | **No** — it only receives merges from the develop branch |

- **Repo**: `NorthwoodsSentinel/prufrock` (public)
- **Issue tracker**: Linear, team key `NOR`

Cut feature branches from the **develop branch**, never from the release branch.

## Maintenance Rules

### Keep documentation files up to date

- When adding, removing, renaming, or changing the purpose of any file or folder, update the corresponding entry in README.md.
- When the structure of the project, the tech stack, or the developer setup changes, update README.md.
- When adding new commands, dependencies, or architectural patterns, update the relevant sections of README.md as well.
- When rules for implementation and testing change, update this file and the matching row of `PROVENANCE.md`.
- **When a _procedure_ changes, update the skill that owns it — not this file.** Two copies of a command sequence is strictly worse than one, because the stale copy is indistinguishable from the live one.
- **Every file here carries a header comment explaining its own purpose and the reasoning behind it** (a module docstring in Python). Read the source rather than looking for a second copy of that reasoning in this file. This applies to new files and to files a change touches; there is no bulk migration of existing files.

### Maintaining the skills

When the first skill is added, the source's four rules apply: a skills check runs in the gate and fails on malformed metadata; every skill declares `disable-model-invocation` explicitly (default `false`); a model-invoked skill carries committed eval cases, positives and negatives (running them spends metered model calls, which the owner has not yet approved); and the listing budget is re-checked when a skill is added. Keep skills in the repo-root `.claude/skills/`; nested skills directories do not load at startup. **If a convention lived solely in a skill body it could vanish mid-session**, which is why rules stay here.

## Issue-driven Work Style

All work is driven by tickets in Linear (team key `NOR`).

- **Before starting work, check Linear for the relevant ticket.**
- **Every item of work is a real Linear issue.** Before creating a new issue, check Linear for a matching item — **never create a duplicate**.
  - **The one exception is a privately reported vulnerability**, which is tracked privately until the reviewed fix is ready. **Accepting and publishing an advisory are outward-facing and stay human-gated; never automate or bulk-apply either.**
- **Only issues are tickets — never PRs.** A PR is tracked through its linked issue.
- **Label work run through this process — every issue and every PR, no exceptions.** Exactly one label marks an issue or PR as tracked by this process; the label's name is not yet set by the owner. Set it at **create time**, never by backfilling.
- **Label by type — exactly one of `bug` / `enhancement` / `documentation` / `chore` / `question`** on every issue you create or triage. A **PR** needs no type label — it is classified through the issue it closes.
- **`Backlog` ⇔ filed, not approved; `Todo` ⇔ approved by the owner.** Moving a ticket into `Todo` _is_ the approval act. The owner does it for new work; an agent may do it for a follow-up it filed inside work the owner already approved. Never park an unreviewed issue in `Todo`. **An agent starts work only on a ticket that is in `Todo`.**
- **Every ticket has a Priority.** Derive it with a rubric rather than asserting it. No rubric exists yet; until one does, the owner sets Priority or it stays unset.
- **`Done` means the work shipped.** Exactly two things earn a ticket a place in Done: its **PR merged**, or it is a **parent whose last sub-issue closed**. Anything else is `Canceled` or `Duplicate`, never `Done`.
- **When work begins**, assign the issue to yourself, set Status to **In Progress**, and create the feature branch **in a new git worktree** — never by switching branches in the primary checkout, which concurrent agent sessions share. Start the session in that worktree, or open this file first and say so: the rules load only from the directory a session starts in.
- **When work is complete**, run `npm run format` then `npm run local:gate`, **sign off every commit** (`Signed-off-by:` matching the author; the repo-owned sign-off check fails a PR on any unsigned commit with no partial credit (`.github/workflows/dco.yml`, job `DCO`); it gates merges only once the owner makes it a **required** status check in a repository ruleset [Not yet in this repo]; a PR showing the check as missing or "expected" is an outage, not a pass), open a PR against the develop branch with the ticket on the body's first line, run the personal-data scan before every push ([below](#memoir-material-and-personal-data-ours)), and set Status to **In Review**.
- **After opening a PR, run a Codex review loop to exhaustion — unprompted.** Codex runs through the `codex-review` wrapper. Stop on the **first** clean round (no confirming round "just to be sure"), a round holding only out-of-scope findings, or **two failed rounds on a PR: then stop and leave it open with the findings listed**. **Weigh each finding against the issue the PR closes and decline scope expansion.** A security finding is fixed; anything else becomes a ticket and a known limitation.
- **If new tasks are discovered during development, create issues** in Linear. They arrive in `Backlog`.
- **Pace bulk GitHub writes: 1 s between requests, never in parallel, under 80 a minute and 500 an hour.** After a refusal, wait out `retry-after`, or a minute without one; a refused create can still go through, so look before retrying.

### Responding to Code Reviews

- it is not necessary to implement all suggestions
- **judge each suggestion against the issue the PR closes.** Fix defects in what the PR added; decline, with a reason, suggestions that expand the PR beyond what the issue calls for, and file an issue for any that is worth doing on its own
- you are free to implement suggestions in a different way, or to ignore one if there is a good reason
- after making the changes, respond to each review comment with what was done (or why it was ignored)
- **that response goes in the review comment's own thread — a rollup comment does not discharge it.** Reply inline first, per comment; then post the PR-level summary **in addition**, because inline replies go hidden once the fix is pushed. Resolving a thread is the reviewer's act.

## Always test new or modified code

- **Ensure all code has corresponding tests.** Every file in the package must clear the bar, and **CI enforces it**: a PR that drops any file below the bar fails. The bar is the source's: **≥ 90 per file on every dimension the coverage tool measures, never lowered.** For Python that is coverage.py with `branch = true`, which measures **two** dimensions: **lines** (coverage.py's statements; a Python "statement" is what it counts as a line) and **branches**. The TypeScript gate's four (lines, statements, functions, branches) collapse to these two because coverage.py has no function dimension and its line and statement counts are the same number (the source's own reasoning, `scripts/lib/py-coverage.mjs`). coverage.py's own `fail_under` is global, so the bar is enforced per file by that script, reading `coverage.json`: `npm run coverage`.
- **A genuinely-unreachable branch is annotated at the source, never waved through by lowering the gate.** Use `# pragma: no cover  # <reason>`, with its reason. Reach for it only when the branch is genuinely impossible to exercise.
- **A file coverage.py cannot measure is excluded by exact path only, with a reason citing its follow-up**, in `EXCLUDED` in `scripts/verify-coverage-scope-py.mjs`. Today that is one file: `prufrock/fleet_bridge.ts` (TypeScript run by Bun). No other exclusion of first-party code is permitted.
- **The measured scope is checked, not assumed.** `scripts/verify-coverage-scope-py.mjs`, the last step of `npm run coverage`, fails naming each tracked file under `prufrock/` that the report does not measure and `EXCLUDED` does not name, each stale exclusion, and each measured file git does not track. Fix that by fixing the configuration, never by excusing the file. Keep new product modules inside `prufrock/`.
- **Tests never call a model, the fleet, Whisper or face detection.** Replace them with fakes (`monkeypatch`, a stand-in module in `sys.modules`), so the suite needs no network, no PAI install, no Bun and no key.
- **In unit tests that expect error output, keep it out of the result**: assert on what was written and on the exit code, not on console text.
- **Keep a test file's exact filename** (`tests/test_<module>.py`). A runner can silently _skip_ a file its pattern misses and still exit 0; `npm run test:scripts` names each script test by path for the same reason.

### Test-gate timeouts are chosen values, stated once

- **A test that races is fixed with an awaited condition or a fake, never with headroom.**
- **A rule about what the code _does_ is asserted at runtime, not read out of the source.**
- **A budget is stated, which is not the same as raised.** Measure before raising a budget that a passing test can spend in full.
- **An inner budget must be strictly smaller than the budget enclosing it.**
- **Retries stay off.** A retry turns a load-induced red into a silent green and hides a real race.
- **Every CI job declares `timeout-minutes`, sized from observed runs**: roughly twice the slowest run observed, rounded up to the next five minutes, stated per job with the range it was read from.
- **Do not scale a fixed sleep.** Replace one with a condition wait when it actually flakes.

## Mandatory pre-push gate

`validate` runs the action-pin guard, the gate scripts' own tests, then the Python chain (`scripts/validate-py.mjs`): `uv sync --locked`, `ruff check`, `ruff format --check`, `pyright`, `pytest`, `uv build`. `local:gate` is `validate`, then the local-only sign-off stage `local:dco`, then `coverage` (per-file coverage, then the scope check). CI runs every stage of `npm run local:gate` except `local:dco`; the pull request's commits are checked by the `DCO` workflow.

- **ALWAYS run `npm run format` (`ruff format`) before committing.** `validate` runs the non-fixing format check and fails in CI on any unformatted file.
- **`npm run local:gate` is the mandatory pre-push command.** It runs **every check** CI runs, plus one local-only step.
- **`npm run validate` is the fast inner-loop check and is NOT an acceptable substitute.**

## Waiting on long-running work

**When you are waiting for something to finish, arm a notifier and stop. Never spend turns polling.** Background the command itself, or a single loop that exits on the condition. **The one genuine exception is state the harness cannot observe** — a CI run, a remote review — and that poll belongs **inside a single backgrounded loop that exits when the condition holds**, at 30 s or more for a remote API. ⚠️ **If a notifier is already armed, that settles it — wait.**

## Build output is never a gate target

**No gate — lint, format, or typecheck — may read generated output.** The gated surface is first-party source only. Here the build and the tools write `dist/`, `build/`, `.venv/`, `node_modules/`, `.ruff_cache/`, `.pytest_cache/`, `.coverage` and `coverage.json`; all are in `.gitignore`, and ruff and pyright skip them by default. When a build starts writing to a new location, add it to `.gitignore` in the same change. **Never widen an ignore to silence a finding in first-party code.**

## Lint has no warning tier

**ruff has no warning level: every finding it reports fails `validate`, exactly as an error does.** The rule set is ruff's default for the locked version, as in the source's Python servers (no `[tool.ruff]` table); pyright runs in its default mode, as there.

- **Do not silence a finding to satisfy the gate.** A finding is a defect to fix. If a rule genuinely must be waived on a line, use its inline comment **with a one-line justification**: `# noqa: <CODE>  # <reason>` for ruff, `# pyright: ignore[<rule>]  # <reason>` for pyright. A bare `# noqa`, a bare `# type: ignore`, a widened exclude, or a rule turned off in configuration is not an acceptable fix.

## Python instructions

- Prufrock is Python (`requires-python = ">=3.10"`; CI and the gate use `.python-version`). **Recorded exception:** `prufrock/fleet_bridge.ts` is the fleet backend's TypeScript bridge, run by Bun; it stays as it is.
- Annotate function signatures; let pyright infer the rest. Prefer a narrower type or a type guard to a cast. `Any` is for values that really are unconstrained (parsed JSON), and says so.
- Catch the narrowest exception that can happen. Where a broad `except Exception` is deliberate (a failed batch is recorded and the run goes on), it carries `# noqa: BLE001  # <what happens to the failure>`.
- **A failure never looks like success.** Keep the fail-loudly rule of `c70792d`: a failed step is reported, kept out of merged output, and makes the command exit non-zero.

## Memoir material and personal data (OURS)

- **Nothing from anyone's life enters this repository.** No memoir text, transcripts, recordings, photographs, face data, names of real people, addresses, dates tied to a person, client names, or fixtures derived from real writing — not in code, tests, docs, commit messages, PR text or CI logs. Test data is synthetic text and generated images, written in the test itself.
- **Scan before every push.** Run the owner's scrub check on every changed file (exit 2 stops the push; a hit is hand-checked and must be a placeholder) and a fixed-string search of the full diff for the owner's private identifier list, which is kept outside this repo. Report the counts in the PR.
- **The pipeline's output directory (`prufrock-output/`) is in `.gitignore` and stays there.**

## Only the owner does

- Picking new work: a new direction or a new repo effort.
- Merging a pull request in this public repo.
- Spending.
- Secrets.
- Repository settings, rulesets and branch protection.
- Releases and publishing (tags, GitHub Releases, package uploads).
- Deploys.
- Changing what the fleet backend does by default (`PRUFROCK_BACKEND`, `prufrock/llm.py`, `prufrock/fleet_bridge.ts`).
- Anything public or sent to other people.
