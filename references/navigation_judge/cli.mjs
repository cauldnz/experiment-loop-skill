#!/usr/bin/env node

import path from "node:path";

import { judgeViewer } from "./src/index.mjs";


function argument(name) {
  const index = process.argv.indexOf(`--${name}`);
  return index >= 0 ? process.argv[index + 1] : null;
}

const viewer = argument("viewer");
const out = argument("out");
if (!viewer || !out) {
  console.error("Usage: node cli.mjs --viewer <viewer.html> --out <evidence-dir>");
  process.exit(2);
}

const evidence = await judgeViewer({
  viewerPath: path.resolve(viewer),
  evidenceDir: path.resolve(out),
});
console.log(`NAVIGATION JUDGE: ${evidence.status.toUpperCase()} (${viewer})`);
process.exit(evidence.status === "pass" ? 0 : 1);
