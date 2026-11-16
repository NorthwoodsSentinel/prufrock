#!/usr/bin/env node
// prufrock (NOR-391), OURS: the coverage scope check for this repo's one
// Python package. `npm run coverage` runs it after `scripts/coverage-py.mjs`,
// which has just written a fresh `coverage.json` (that script deletes any
// stale report first, and `&&` stops this one from running if it failed).
//
// Why it exists. The per-file gate (`scripts/lib/py-coverage.mjs`) judges only
// the files that reach the report. The lesson the source learned the hard way
// (the MCP Inspector's `scripts/verify-coverage-scope.mjs`, #2709 there: a
// report that fell from 418 files to 11 and stayed green) is that the run
// measuring fewer files than it should must not be silent: "Fix that by
// fixing the globs, never by excusing the files." coverage.py with
// `source = ["prufrock"]` already reports a Python file no test imports (at
// 0%), so the gap here is narrower: a file in the package that coverage.py
// cannot measure at all (today, `prufrock/fleet_bridge.ts`), or a `source`
// setting that stops matching. This compares the report with an independent
// list: the files git tracks under `prufrock/`.
//
// The rules (the unit tests pin each):
//
//   - Every tracked `.py` file under `prufrock/` must be in the report.
//   - Every other tracked file under `prufrock/` must be named, by exact
//     path, in `EXCLUDED`, with a reason that cites its follow-up. No globs.
//   - An `EXCLUDED` entry that names no tracked file, or a `.py` file the
//     report measures, is stale and fails.
//   - A file in the report that git does not track fails too: the gate's
//     verdict must be about the committed tree.
//   - No tracked files, or an unreadable report, is a failure, never a pass.

import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { readCoverageReport } from "./lib/py-coverage.mjs";
import { isMainModule } from "./lib/main-module.mjs";

/** The package directory whose tracked files the report must account for. */
export const PACKAGE_DIR = "prufrock";

/**
 * Tracked files in the package that coverage.py cannot measure, by exact
 * path. Each reason cites the follow-up that brings the file under a gate.
 * @type {Record<string, string>}
 */
export const EXCLUDED = {
  "prufrock/fleet_bridge.ts":
    "TypeScript run by Bun, not Python, so coverage.py cannot measure it; " +
    "follow-up F1 in the NOR-391 pull request (a Bun test with a stand-in " +
    "Inference.ts, plus format, lint and typecheck for this file).",
};

const GLOB_CHARS = /[*?[\]{}]/;

/**
 * @param {{
 *   tracked: string[],
 *   reportFiles: string[],
 *   excluded?: Record<string, string>,
 *   packageDir?: string,
 * }} input
 * @returns {string[]} one message per problem; empty means in scope
 */
export function checkScope({
  tracked,
  reportFiles,
  excluded = EXCLUDED,
  packageDir = PACKAGE_DIR,
}) {
  const norm = (/** @type {string} */ p) => p.replaceAll("\\", "/");
  const inPackage = tracked
    .map(norm)
    .filter((p) => p.startsWith(`${packageDir}/`));
  const measured = new Set(reportFiles.map(norm));
  const trackedSet = new Set(inPackage);
  const problems = [];

  if (inPackage.length === 0) {
    problems.push(
      `no tracked files under ${packageDir}/; the scope cannot be checked`,
    );
    return problems;
  }

  for (const [entry, reason] of Object.entries(excluded)) {
    if (GLOB_CHARS.test(entry)) {
      problems.push(`EXCLUDED entry ${entry} is a pattern; exact paths only`);
    } else if (typeof reason !== "string" || reason.trim() === "") {
      problems.push(`EXCLUDED entry ${entry} has no reason`);
    } else if (!trackedSet.has(entry)) {
      problems.push(`EXCLUDED entry ${entry} names no tracked file (stale)`);
    } else if (measured.has(entry)) {
      problems.push(
        `EXCLUDED entry ${entry} is measured by the report (stale); remove it`,
      );
    }
  }

  for (const file of inPackage) {
    if (file.endsWith(".py")) {
      if (!measured.has(file)) {
        problems.push(
          `${file} is tracked but not in the coverage report; check [tool.coverage.run] source in pyproject.toml`,
        );
      }
    } else if (!(file in excluded)) {
      problems.push(
        `${file} is tracked but coverage.py cannot measure it and EXCLUDED does not name it`,
      );
    }
  }

  for (const file of [...measured].sort()) {
    if (!trackedSet.has(file)) {
      problems.push(`${file} is in the report but not tracked by git`);
    }
  }
  return problems;
}

/**
 * Files git tracks under the package directory.
 * @param {string} root
 * @returns {{ files: string[] } | { error: string }}
 */
export function trackedFiles(root, packageDir = PACKAGE_DIR) {
  const result = spawnSync("git", ["ls-files", "-z", "--", packageDir], {
    cwd: root,
    encoding: "utf8",
  });
  if (result.error || result.status !== 0) {
    return {
      error: `git ls-files failed: ${result.error?.message ?? result.stderr}`,
    };
  }
  return { files: result.stdout.split("\0").filter(Boolean) };
}

/**
 * @param {string} root
 * @param {{ log?: (line: string) => void, error?: (line: string) => void }} [io]
 * @returns {number} exit code
 */
export function main(root, io = {}) {
  const log = io.log ?? console.log;
  const error = io.error ?? console.error;
  const read = readCoverageReport(path.join(root, "coverage.json"));
  if ("error" in read) {
    error(`[coverage:scope] ${read.error}`);
    return 1;
  }
  const files = /** @type {{ files?: unknown }} */ (read.report)?.files;
  if (!files || typeof files !== "object" || Array.isArray(files)) {
    error("[coverage:scope] not a coverage.py JSON report (no `files` object)");
    return 1;
  }
  const tracked = trackedFiles(root);
  if ("error" in tracked) {
    error(`[coverage:scope] ${tracked.error}`);
    return 1;
  }
  const problems = checkScope({
    tracked: tracked.files,
    reportFiles: Object.keys(files),
  });
  if (problems.length > 0) {
    error(
      [`[coverage:scope] ${problems.length} problem(s):`, ...problems.map((p) => `  ${p}`)].join("\n"),
    );
    return 1;
  }
  const excludedCount = Object.keys(EXCLUDED).length;
  log(
    `[coverage:scope] OK (${Object.keys(files).length} file(s) measured; ${excludedCount} excluded by exact path: ${Object.keys(EXCLUDED).join(", ")})`,
  );
  return 0;
}

if (isMainModule(import.meta.url)) {
  process.exitCode = main(
    path.resolve(path.dirname(fileURLToPath(import.meta.url)), ".."),
  );
}
