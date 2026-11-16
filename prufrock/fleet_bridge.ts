#!/usr/bin/env bun
// fleet_bridge: Prufrock's door into the PAI fleet's inference.
// Reads one JSON request on stdin: {system, user, images?, level?, timeoutMs?}
// Writes one JSON reply on stdout: {ok, text, error?, latencyMs}
// Routes through PAI's Inference.ts, which runs on the Claude subscription
// (it scrubs ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN from the child env).
// Inference.ts location: $PRUFROCK_INFERENCE, else $PAI_DIR/TOOLS/Inference.ts,
// else $HOME/.claude/PAI/TOOLS/Inference.ts.
import { existsSync } from "node:fs";
import { isAbsolute, join, resolve } from "node:path";

type Req = { system: string; user: string; images?: string[]; level?: "fast" | "standard" | "smart"; timeoutMs?: number };

function out(o: Record<string, unknown>, code = 0): never {
  process.stdout.write(JSON.stringify(o));
  process.exit(code);
}

function inferencePath(): string | null {
  const candidates = [
    process.env.PRUFROCK_INFERENCE,
    process.env.PAI_DIR ? join(process.env.PAI_DIR, "TOOLS", "Inference.ts") : undefined,
    process.env.HOME ? join(process.env.HOME, ".claude", "PAI", "TOOLS", "Inference.ts") : undefined,
  ].filter(Boolean) as string[];
  return candidates.find((p) => existsSync(p)) ?? null;
}

const raw = await new Response(Bun.stdin.stream()).text();
let req: Req;
try {
  req = JSON.parse(raw);
} catch (e) {
  out({ ok: false, error: `bad request JSON: ${(e as Error).message}` }, 2);
}
if (typeof req.system !== "string" || typeof req.user !== "string") out({ ok: false, error: "request needs string fields system and user" }, 2);

const images = (req.images ?? []).map((p) => (isAbsolute(p) ? p : resolve(p)));
const missing = images.filter((p) => !existsSync(p));
if (missing.length) out({ ok: false, error: `image not found: ${missing.join(", ")}` }, 2);

const path = inferencePath();
if (!path) out({ ok: false, error: "PAI Inference.ts not found (set PRUFROCK_INFERENCE or PAI_DIR, or use PRUFROCK_BACKEND=api)" }, 3);

const { inference } = await import(path);
const level = req.level ?? "standard";
if (!["fast", "standard", "smart"].includes(level)) out({ ok: false, error: `bad level: ${level}` }, 2);

const r = await inference({
  systemPrompt: req.system,
  userPrompt: req.user,
  level,
  imagePaths: images.length ? images : undefined,
  timeout: req.timeoutMs,
});
if (!r.success) out({ ok: false, error: r.error ?? "inference failed", latencyMs: r.latencyMs }, 1);
out({ ok: true, text: r.output, latencyMs: r.latencyMs });
