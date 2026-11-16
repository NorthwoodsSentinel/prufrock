// prufrock (NOR-391), OURS: tests for scripts/verify-coverage-scope-py.mjs.
// Run by `npm run test:scripts`, which names this file by path (a glob that
// matches nothing would still exit 0). `main` is driven against a throwaway
// git repository so the git listing and the exit codes are covered too.

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { after, describe, it } from "node:test";

import {
  EXCLUDED,
  checkScope,
  main,
  trackedFiles,
} from "./verify-coverage-scope-py.mjs";

const scratch = mkdtempSync(path.join(tmpdir(), "scope-py-"));
after(() => rmSync(scratch, { recursive: true, force: true }));

const ex = { "prufrock/bridge.ts": "follow-up F1" };

describe("checkScope", () => {
  it("passes when every tracked file is measured or excluded", () => {
    assert.deepEqual(
      checkScope({
        tracked: ["prufrock/a.py", "prufrock/bridge.ts", "README.md"],
        reportFiles: ["prufrock/a.py"],
        excluded: ex,
      }),
      [],
    );
  });

  it("fails a tracked Python file missing from the report", () => {
    const problems = checkScope({
      tracked: ["prufrock/a.py", "prufrock/b.py", "prufrock/bridge.ts"],
      reportFiles: ["prufrock/a.py"],
      excluded: ex,
    });
    assert.equal(problems.length, 1);
    assert.match(problems[0], /prufrock\/b\.py is tracked but not in the coverage report/);
  });

  it("fails a tracked non-Python file that EXCLUDED does not name", () => {
    const problems = checkScope({
      tracked: ["prufrock/a.py", "prufrock/other.ts", "prufrock/bridge.ts"],
      reportFiles: ["prufrock/a.py"],
      excluded: ex,
    });
    assert.deepEqual(problems, [
      "prufrock/other.ts is tracked but coverage.py cannot measure it and EXCLUDED does not name it",
    ]);
  });

  it("fails a stale entry that names no tracked file", () => {
    const problems = checkScope({
      tracked: ["prufrock/a.py"],
      reportFiles: ["prufrock/a.py"],
      excluded: ex,
    });
    assert.deepEqual(problems, [
      "EXCLUDED entry prufrock/bridge.ts names no tracked file (stale)",
    ]);
  });

  it("fails an entry for a file the report measures", () => {
    const problems = checkScope({
      tracked: ["prufrock/a.py"],
      reportFiles: ["prufrock/a.py"],
      excluded: { "prufrock/a.py": "follow-up" },
    });
    assert.match(problems[0], /is measured by the report \(stale\)/);
  });

  it("refuses a pattern and an entry with no reason", () => {
    const problems = checkScope({
      tracked: ["prufrock/a.py", "prufrock/x.ts"],
      reportFiles: ["prufrock/a.py"],
      excluded: { "prufrock/*.ts": "follow-up", "prufrock/x.ts": " " },
    });
    assert.ok(problems.includes("EXCLUDED entry prufrock/*.ts is a pattern; exact paths only"));
    assert.ok(problems.includes("EXCLUDED entry prufrock/x.ts has no reason"));
  });

  it("fails a measured file git does not track", () => {
    const problems = checkScope({
      tracked: ["prufrock/a.py"],
      reportFiles: ["prufrock/a.py", "prufrock/new.py"],
      excluded: {},
    });
    assert.deepEqual(problems, ["prufrock/new.py is in the report but not tracked by git"]);
  });

  it("fails when nothing is tracked", () => {
    assert.match(
      checkScope({ tracked: ["README.md"], reportFiles: [], excluded: {} })[0],
      /no tracked files under prufrock\//,
    );
  });

  it("reads Windows separators as forward slashes", () => {
    assert.deepEqual(
      checkScope({
        tracked: ["prufrock\\a.py"],
        reportFiles: ["prufrock\\a.py"],
        excluded: {},
      }),
      [],
    );
  });

  it("names this repo's one exclusion with a reason that cites its follow-up", () => {
    assert.deepEqual(Object.keys(EXCLUDED), ["prufrock/fleet_bridge.ts"]);
    assert.match(EXCLUDED["prufrock/fleet_bridge.ts"], /follow-up F1/);
  });
});

function git(cwd, ...args) {
  const r = spawnSync("git", args, { cwd, encoding: "utf8" });
  assert.equal(r.status, 0, r.stderr);
}

function repo(name, files, report) {
  const root = path.join(scratch, name);
  mkdirSync(path.join(root, "prufrock"), { recursive: true });
  git(root, "init", "-q");
  for (const f of files) writeFileSync(path.join(root, f), "");
  if (files.length) git(root, "add", ...files);
  if (report !== undefined) writeFileSync(path.join(root, "coverage.json"), report);
  return root;
}

const silent = () => {
  const lines = { log: [], error: [] };
  return {
    lines,
    io: { log: (l) => lines.log.push(l), error: (l) => lines.error.push(l) },
  };
};

describe("main", () => {
  it("exits 0 on a report that accounts for every tracked file", () => {
    const root = repo(
      "ok",
      ["prufrock/a.py", "prufrock/fleet_bridge.ts"],
      JSON.stringify({ files: { "prufrock/a.py": {} } }),
    );
    const { lines, io } = silent();
    assert.equal(main(root, io), 0);
    assert.match(lines.log[0], /OK \(1 file\(s\) measured; 1 excluded by exact path: prufrock\/fleet_bridge\.ts\)/);
  });

  it("exits 1 naming each problem", () => {
    const root = repo(
      "bad",
      ["prufrock/a.py", "prufrock/b.py", "prufrock/fleet_bridge.ts"],
      JSON.stringify({ files: { "prufrock/a.py": {} } }),
    );
    const { lines, io } = silent();
    assert.equal(main(root, io), 1);
    assert.match(lines.error[0], /1 problem\(s\):\n {2}prufrock\/b\.py is tracked but not in the coverage report/);
  });

  it("exits 1 when the report is missing", () => {
    const root = repo("missing", ["prufrock/a.py"]);
    const { lines, io } = silent();
    assert.equal(main(root, io), 1);
    assert.match(lines.error[0], /was not written/);
  });

  it("exits 1 on a report with no files object", () => {
    const root = repo("nofiles", ["prufrock/a.py"], JSON.stringify({ files: [] }));
    const { lines, io } = silent();
    assert.equal(main(root, io), 1);
    assert.match(lines.error[0], /not a coverage\.py JSON report/);
  });

  it("exits 1 outside a git repository", () => {
    const root = path.join(scratch, "nogit");
    mkdirSync(root);
    writeFileSync(path.join(root, "coverage.json"), JSON.stringify({ files: {} }));
    const { lines, io } = silent();
    assert.equal(main(root, io), 1);
    assert.match(lines.error[0], /git ls-files failed/);
  });
});

describe("trackedFiles", () => {
  it("lists only files under the package directory", () => {
    const root = repo("list", ["prufrock/a.py", "README.md"], undefined);
    writeFileSync(path.join(root, "README.md"), "");
    assert.deepEqual(trackedFiles(root), { files: ["prufrock/a.py"] });
  });
});
