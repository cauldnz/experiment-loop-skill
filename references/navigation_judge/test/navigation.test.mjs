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


function addWideAlternateTrack(manifest) {
  manifest.tracks.push({
    id: "alternate-track",
    label: "Alternate Track",
    hypothesis: "Exercise independent navigation state across tracks.",
  });
  for (let index = 3; index <= 6; index += 1) {
    const loop = structuredClone(manifest.iterations[1]);
    loop.id = `loop-00${index}`;
    loop.track_id = "alternate-track";
    loop.parent_ids = index === 3 ? ["loop-001"] : [`loop-00${index - 1}`];
    loop.artifacts[0].id = `result-00${index}`;
    loop.artifacts[0].path = `alternate-track/${loop.id}/result.txt`;
    manifest.iterations.push(loop);
  }
  manifest.champion.iteration_id = "loop-006";
  manifest.story.featured_artifact_id = "result-006";
}


async function reverseInteractionContract(viewerPath) {
  let rendered = await readFile(viewerPath, "utf8");
  const pattern = /(<script type="application\/json" id="interaction-contract">)(.*?)(<\/script>)/s;
  const match = rendered.match(pattern);
  assert.ok(match, "interaction contract is missing");
  const contract = JSON.parse(match[2]);
  contract.controls.reverse();
  rendered = rendered.replace(
    pattern,
    `$1${JSON.stringify(contract)}$3`
  );

  const marker = '"viewer_sha256":"';
  const valueStart = rendered.indexOf(marker) + marker.length;
  assert.ok(valueStart >= marker.length, "Viewer binding hash is missing");
  const normalized = `${rendered.slice(0, valueStart)}${"0".repeat(64)}${
    rendered.slice(valueStart + 64)
  }`;
  const viewerHash = createHash("sha256").update(normalized).digest("hex");
  rendered = `${rendered.slice(0, valueStart)}${viewerHash}${
    rendered.slice(valueStart + 64)
  }`;
  await writeFile(viewerPath, rendered, "utf8");
}


async function renderFixture({
  humanCriterionId = "clarity",
  reverseContract = false,
  wide = false,
} = {}) {
  const runDir = await mkdtemp(path.join(tmpdir(), "navigation-judge-"));
  const manifest = JSON.parse(
    await readFile(path.join(repoRoot, "templates", "manifest-template.json"), "utf8")
  );
  manifest.scorers.push({
    id: "human",
    type: "human_review",
    criterion_ids: [humanCriterionId],
    primary: false,
    weight: 1,
  });
  if (wide) addWideAlternateTrack(manifest);

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
  const viewerPath = path.join(runDir, "viewer.html");
  const rendered = spawnSync(
    "python",
    [
      "-m",
      "references.viewer_renderer.cli",
      "--data",
      runDir,
      "--out",
      viewerPath,
    ],
    { cwd: repoRoot, encoding: "utf8" }
  );
  assert.equal(rendered.status, 0, rendered.stderr);
  if (reverseContract) await reverseInteractionContract(viewerPath);
  return { runDir, viewerPath };
}


test("validates the canonical human feedback intake export", async () => {
  const fixture = await renderFixture({ humanCriterionId: "correctness" });
  try {
    const evidence = await judgeViewer({
      viewerPath: fixture.viewerPath,
      evidenceDir: fixture.runDir,
    });
    const human = evidence.steps.find((step) =>
      step.control.includes("#human-review-button")
    );

    assert.equal(
      evidence.status,
      "pass",
      JSON.stringify({ checks: evidence.checks, steps: evidence.steps }, null, 2)
    );
    assert.deepEqual(human.outcome.feedbackTypes, [
      "general",
      "criterion",
      "loop",
      "artifact",
    ]);
    assert.equal(human.outcome.bindingValid, true);
    assert.equal(human.outcome.criterionId, "correctness");
    assert.equal(human.outcome.verdict, "approve");
    assert.equal(human.outcome.recommendation, "keep");
    assert.equal(human.outcome.preferredIteration, null);
  } finally {
    await rm(fixture.runDir, { recursive: true, force: true });
  }
});


test("normalizes graph state for a wide multi-track Viewer", async () => {
  const fixture = await renderFixture({ reverseContract: true, wide: true });
  try {
    const evidence = await judgeViewer({
      viewerPath: fixture.viewerPath,
      evidenceDir: fixture.runDir,
    });
    const graphSteps = evidence.steps.filter((step) => step.control === ".graph-node");

    assert.equal(
      evidence.status,
      "pass",
      JSON.stringify({ checks: evidence.checks, steps: evidence.steps }, null, 2)
    );
    assert.equal(graphSteps.length, 1);
    assert.equal(graphSteps[0].outcome.inspectorVisible, true);
    assert.equal(graphSteps[0].outcome.selected, 1);
  } finally {
    await rm(fixture.runDir, { recursive: true, force: true });
  }
});
