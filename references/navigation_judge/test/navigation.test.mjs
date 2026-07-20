import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { judgeViewer } from "../src/index.mjs";


const packageDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const repoRoot = path.resolve(packageDir, "..", "..");


test("judges the shared Viewer contract end to end", async () => {
  const runDir = await mkdtemp(path.join(tmpdir(), "navigation-judge-"));
  try {
    const manifest = JSON.parse(
      await readFile(path.join(repoRoot, "templates", "manifest-template.json"), "utf8")
    );
    manifest.scorers.push({
      id: "human",
      type: "human_review",
      criterion_ids: ["clarity"],
      primary: false,
      weight: 1,
    });
    for (const loop of manifest.iterations) {
      for (const artifact of loop.artifacts) {
        const artifactPath = path.join(runDir, ...artifact.path.split("/"));
        const payload = Buffer.from(`${loop.id}\n`, "utf8");
        await mkdir(path.dirname(artifactPath), { recursive: true });
        await writeFile(artifactPath, payload);
        artifact.sha256 = createHash("sha256").update(payload).digest("hex");
      }
    }
    await writeFile(
      path.join(runDir, "manifest.json"),
      `${JSON.stringify(manifest, null, 2)}\n`,
      "utf8"
    );
    const rendered = spawnSync(
      "python",
      [
        "-m",
        "references.viewer_renderer.cli",
        "--data",
        runDir,
        "--out",
        path.join(runDir, "viewer.html"),
      ],
      { cwd: repoRoot, encoding: "utf8" }
    );
    assert.equal(rendered.status, 0, rendered.stderr);

    const evidence = await judgeViewer({
      viewerPath: path.join(runDir, "viewer.html"),
      evidenceDir: runDir,
    });
    assert.equal(evidence.status, "pass", JSON.stringify(evidence.checks, null, 2));
    assert.ok(evidence.checks.length >= 8);
    assert.ok(evidence.screenshots >= 5);
  } finally {
    await rm(runDir, { recursive: true, force: true });
  }
});
