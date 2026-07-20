import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

import { chromium } from "playwright";
import playwrightPackage from "playwright/package.json" with { type: "json" };


function check(name, status, detail = {}) {
  return { name, status, detail };
}

function slug(value) {
  return String(value).replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "").slice(0, 48);
}

async function viewerHash(viewerPath) {
  const bytes = await readFile(viewerPath);
  return createHash("sha256").update(bytes).digest("hex");
}

async function screenshot(page, shotsDir, index, label) {
  const filename = `${String(index).padStart(2, "0")}-${slug(label) || "state"}.png`;
  const output = path.join(shotsDir, filename);
  await page.screenshot({ path: output, fullPage: true });
  return `navigation-shots/${filename}`;
}

async function discoverControls(page, contractSelectors) {
  return page.evaluate((selectorsFromContract) => {
    const selectors = [
      '[role="tab"]',
      "select",
      "input",
      "a[href]",
      'button:not([role="tab"])',
      "details > summary",
    ];
    return Array.from(document.querySelectorAll(selectors.join(","))).map((element) => ({
      selector: element.id ? `#${element.id}` : null,
      tag: element.tagName.toLowerCase(),
      role: element.getAttribute("role"),
      text: (element.getAttribute("aria-label") || element.textContent || "").trim().slice(0, 80),
      coveredBy: selectorsFromContract.find((selector) => {
        try { return element.matches(selector); } catch { return false; }
      }) || null,
    }));
  }, contractSelectors);
}

async function executeTab(page, control, action, shotsDir, state) {
  const handle = page.locator(control.selector);
  await handle.click();
  await page.waitForTimeout(80);
  const result = await handle.evaluate((element) => {
    const panelId = element.getAttribute("aria-controls");
    const panel = panelId ? document.getElementById(panelId) : null;
    return {
      hash: location.hash,
      selected: element.getAttribute("aria-selected"),
      panelVisible: Boolean(panel && !panel.hidden),
    };
  });
  const passed =
    result.hash === action.expect_hash &&
    result.selected === "true" &&
    result.panelVisible;
  state.shotIndex += 1;
  const shot = await screenshot(page, shotsDir, state.shotIndex, `tab-${control.selector}`);
  state.steps.push({
    control: control.selector,
    action: "click",
    outcome: result,
    shot,
  });
  return passed;
}

async function activateView(page, view) {
  const tab = page.locator(`#tab-${view}`);
  if (await tab.count()) await tab.click();
  await page.waitForTimeout(40);
}

async function executeGraph(page, shotsDir, state) {
  await activateView(page, "topology");
  const nodes = page.locator(".graph-node");
  const count = await nodes.count();
  if (!count) return false;
  const tabStops = await nodes.evaluateAll((items) =>
    items.filter((item) => item.tabIndex === 0).length
  );
  const selected = nodes.nth(count - 1);
  await selected.click();
  await selected.focus();
  await page.keyboard.press("Enter");
  const outcome = await page.evaluate(() => ({
    hash: location.hash,
    selected: document.querySelectorAll('.graph-node[aria-pressed="true"]').length,
    tabStops: Array.from(document.querySelectorAll(".graph-node")).filter(
      (node) => node.tabIndex === 0
    ).length,
    inspectorVisible: Boolean(document.querySelector("#loop-inspector h2")),
  }));
  state.shotIndex += 1;
  const shot = await screenshot(page, shotsDir, state.shotIndex, "graph-selection");
  state.steps.push({ control: ".graph-node", action: "keyboard-select", outcome, shot });
  return tabStops === 1 && outcome.tabStops === 1 && outcome.selected === 1 &&
    outcome.inspectorVisible && outcome.hash.includes("view=topology") &&
    outcome.hash.includes("loop=");
}

async function executeFilters(page, shotsDir, state) {
  await activateView(page, "topology");
  const search = page.locator("#loop-search");
  await search.fill("__navigation_judge_no_match__");
  const dimmed = await page.locator(".graph-node.is-dimmed").count();
  const total = await page.locator(".graph-node").count();
  await search.fill("");
  const champion = page.locator("#champion-filter");
  await champion.check();
  const championCount = await page.locator(".graph-node:not(.is-dimmed)").count();
  await champion.uncheck();
  const outcome = { dimmed, total, championCount };
  state.steps.push({ control: "#loop-search,#champion-filter", action: "filter", outcome });
  return total > 0 && dimmed === total && championCount === 1;
}

async function executeTopologyViewport(page, shotsDir, state) {
  await activateView(page, "topology");
  const drawer = page.locator("#loop-inspector");
  if (await drawer.evaluate((element) => element.classList.contains("is-open"))) {
    await page.locator("#topology-inspector-close").click();
  }
  const snapshot = () => page.evaluate(() => {
    const params = new URLSearchParams(location.hash.replace(/^#/, ""));
    const stage = document.querySelector("#graph-stage");
    const drawer = document.querySelector("#loop-inspector");
    const workspace = document.querySelector("#topology-workspace");
    return {
      transform: stage?.style.transform || "",
      x: Number(params.get("x")),
      y: Number(params.get("y")),
      scale: Number(params.get("scale")),
      drawerOpen: drawer?.classList.contains("is-open") || false,
      maximized: workspace?.classList.contains("is-maximized") || false,
    };
  });

  await page.locator("#topology-fit").click();
  const fitted = await snapshot();
  await page.locator("#topology-zoom-in").click();
  const zoomed = await snapshot();
  await page.locator("#topology-zoom-out").click();
  const zoomedOut = await snapshot();
  await page.locator("#topology-reset").click();
  const reset = await snapshot();

  const viewport = page.locator("#graph-viewport");
  const viewportBox = await viewport.boundingBox();
  await page.mouse.move(
    viewportBox.x + viewportBox.width / 2,
    viewportBox.y + viewportBox.height / 2
  );
  await page.mouse.wheel(0, -600);
  const wheelZoomed = await snapshot();
  await page.mouse.move(viewportBox.x + 32, viewportBox.y + 32);
  await page.mouse.down();
  await page.mouse.move(viewportBox.x + 92, viewportBox.y + 72, { steps: 3 });
  await page.mouse.up();
  const panned = await snapshot();

  const beforeMinimap = panned;
  await page.locator("#graph-minimap").click({ position: { x: 170, y: 105 } });
  const afterMinimap = await snapshot();

  await page.locator(".graph-node").first().evaluate((element) => element.click());
  const selected = await snapshot();
  await page.locator("#topology-inspector-close").click();
  const closed = await snapshot();
  await page.locator("#topology-inspector-toggle").click();
  const reopened = await snapshot();

  await page.locator("#topology-maximize").click();
  const maximized = await snapshot();
  await page.locator("#topology-maximize").click();
  const restored = await snapshot();

  const outcome = {
    fitted,
    zoomed,
    zoomedOut,
    reset,
    wheelZoomed,
    panned,
    beforeMinimap,
    afterMinimap,
    selected,
    closed,
    reopened,
    maximized,
    restored,
  };
  state.shotIndex += 1;
  const shot = await screenshot(page, shotsDir, state.shotIndex, "topology-viewport");
  state.steps.push({
    control: "#topology-zoom-in,#topology-zoom-out,#topology-fit,#topology-reset,#topology-inspector-toggle,#topology-inspector-close,#topology-maximize,#graph-minimap",
    action: "operate",
    outcome,
    shot,
  });
  const minimapMoved =
    afterMinimap.x !== beforeMinimap.x || afterMinimap.y !== beforeMinimap.y;
  return fitted.transform.includes("scale(") &&
    zoomed.scale > fitted.scale &&
    zoomedOut.scale < zoomed.scale &&
    reset.scale === 1 &&
    wheelZoomed.scale > reset.scale &&
    (panned.x !== wheelZoomed.x || panned.y !== wheelZoomed.y) &&
    minimapMoved &&
    selected.drawerOpen &&
    !closed.drawerOpen &&
    reopened.drawerOpen &&
    maximized.maximized &&
    !restored.maximized;
}

async function executeLoopLink(page, shotsDir, state) {
  await activateView(page, "overview");
  const link = page.locator("[data-open-loop]").first();
  if (!(await link.count())) return false;
  await link.click();
  const outcome = await page.evaluate(() => ({
    hash: location.hash,
    topology: document.querySelector("#tab-topology")?.getAttribute("aria-selected"),
    selected: document.querySelectorAll('.graph-node[aria-pressed="true"]').length,
  }));
  state.steps.push({ control: "[data-open-loop]", action: "click", outcome });
  return outcome.topology === "true" && outcome.selected === 1 &&
    outcome.hash.includes("view=topology") && outcome.hash.includes("loop=");
}

async function executeTheme(page, state) {
  const select = page.locator("#theme-select");
  let passed = true;
  for (const value of ["dark", "light", "system"]) {
    await select.selectOption(value);
    const outcome = await page.evaluate(() => ({
      selected: document.querySelector("#theme-select")?.value,
      theme: document.documentElement.dataset.theme,
    }));
    passed &&= outcome.selected === value &&
      (outcome.theme === "dark" || outcome.theme === "light");
    state.steps.push({ control: "#theme-select", action: "select", value, outcome });
  }
  return passed;
}

async function executeDialog(page, shotsDir, state) {
  await activateView(page, "topology");
  const invoker = page.locator("#panel-topology .expand-artifact").first();
  if (!(await invoker.count())) return false;
  await invoker.click();
  const opened = await page.locator("#artifact-dialog").evaluate((dialog) => ({
    open: dialog.open,
    focusInside: dialog.contains(document.activeElement),
  }));
  await page.keyboard.press("Tab");
  const contained = await page.locator("#artifact-dialog").evaluate((dialog) =>
    dialog.contains(document.activeElement)
  );
  await page.locator("#dialog-close").click();
  const closed = await page.locator("#artifact-dialog").evaluate((dialog) => ({
    open: dialog.open,
    focusRestored: document.activeElement?.classList.contains("expand-artifact") || false,
  }));
  state.shotIndex += 1;
  const shot = await screenshot(page, shotsDir, state.shotIndex, "artifact-dialog");
  state.steps.push({ control: ".expand-artifact", action: "dialog", outcome: { opened, contained, closed }, shot });
  return opened.open && opened.focusInside && contained && !closed.open && closed.focusRestored;
}

async function executeCompare(page, state) {
  await activateView(page, "compare");
  const a = page.locator("#compare-a");
  const b = page.locator("#compare-b");
  if (!(await a.count()) || !(await b.count())) return false;
  const options = await a.locator("option").evaluateAll((items) => items.map((item) => item.value));
  if (options.length < 2) return false;
  await a.selectOption(options.at(-1));
  await b.selectOption(options[0]);
  const outcome = await page.evaluate(() => ({
    hash: location.hash,
    comparisonVisible: Boolean(document.querySelector("#comparison .compare-artifacts")),
    a: document.querySelector("#compare-a")?.value,
    b: document.querySelector("#compare-b")?.value,
  }));
  state.steps.push({ control: "#compare-a,#compare-b", action: "select", outcome });
  return outcome.comparisonVisible && outcome.a === options.at(-1) &&
    outcome.b === options[0] && outcome.hash.includes("view=compare");
}

async function executeDisclosure(page, state) {
  await activateView(page, "overview");
  const summary = page.locator("details > summary").first();
  if (!(await summary.count())) return false;
  const before = await summary.evaluate((element) => element.parentElement.open);
  await summary.click();
  const after = await summary.evaluate((element) => element.parentElement.open);
  state.steps.push({ control: "details > summary", action: "toggle", outcome: { before, after } });
  return before !== after;
}

async function executeSearch(page, state) {
  await activateView(page, "overview");
  const search = page.locator("#manifest-search");
  await search.evaluate((element) => {
    const disclosure = element.closest("details");
    if (disclosure) disclosure.open = true;
  });
  await search.fill("schema_version");
  const text = await page.locator("#manifest-tree").innerText();
  await search.fill("");
  state.steps.push({ control: "#manifest-search", action: "input", outcome: { matched: text.includes("schema_version") } });
  return text.includes("schema_version");
}

async function executeLinks(page, state) {
  await activateView(page, "topology");
  const links = page.locator("a.button[href]");
  const count = await links.count();
  const unsafe = await links.evaluateAll((items) =>
    items.map((item) => item.getAttribute("href")).filter((href) =>
      !href || href.startsWith("javascript:") || href.startsWith("http:")
    )
  );
  state.steps.push({ control: "a.button[href]", action: "inspect", outcome: { count, unsafe } });
  return unsafe.length === 0;
}

async function executeHumanReview(page, state) {
  const button = page.locator("#human-review-button");
  if (!(await button.count())) return false;
  await button.click();
  await page.locator("#human-general-notes").fill("Navigation judge review");
  await page.locator("#human-verdict").selectOption("approve");
  await page.locator("#human-recommendation").selectOption("keep");
  const firstScore = page.locator('[id^="human-score-"]').first();
  if (await firstScore.count()) await firstScore.fill("4");
  await page.locator("#human-loop-notes").fill("Selected Loop note");
  await page.locator("#human-artifact-notes").fill("Selected Artifact note");
  const downloadPromise = page.waitForEvent("download");
  await page.locator("#human-export").click();
  const download = await downloadPromise;
  const downloadedPath = await download.path();
  const exported = JSON.parse(await readFile(downloadedPath, "utf8"));
  await page.locator("#human-close").click();
  const outcome = {
    filename: download.suggestedFilename(),
    dialogOpen: await page.locator("#human-dialog").evaluate((dialog) => dialog.open),
    focusRestored: await button.evaluate((element) => document.activeElement === element),
    hasIdentity: Object.keys(exported).some((key) => key.toLowerCase().includes("reviewer")),
    experiment: exported.experiment_id,
    manifestHash: exported.manifest_sha256,
    viewerHash: exported.viewer_sha256,
    algorithm: exported.viewer_hash_algorithm,
    criterionCount: exported.criterion_reviews?.length || 0,
    loopNotes: exported.loop_notes?.length || 0,
    artifactNotes: exported.artifact_notes?.length || 0,
  };
  state.steps.push({ control: "#human-review-button,#human-close,#human-export", action: "review_and_export", outcome });
  return !outcome.dialogOpen && outcome.focusRestored && !outcome.hasIdentity &&
    outcome.experiment && /^[a-f0-9]{64}$/.test(outcome.manifestHash) &&
    /^[a-f0-9]{64}$/.test(outcome.viewerHash) &&
    outcome.algorithm === "canonical-html-zeroed-binding-v1" &&
    outcome.criterionCount > 0 && outcome.loopNotes === 1 &&
    outcome.artifactNotes === 1;
}

async function executeContract(page, contract, shotsDir) {
  const state = { shotIndex: 0, steps: [] };
  const results = [];
  for (const control of contract.controls || []) {
    let passed = true;
    for (const action of control.actions || []) {
      if (control.kind === "tab" && action.type === "click") {
        passed &&= await executeTab(page, control, action, shotsDir, state);
      } else if (control.kind === "graph") {
        passed &&= await executeGraph(page, shotsDir, state);
      } else if (control.kind === "filter") {
        passed &&= await executeFilters(page, shotsDir, state);
      } else if (control.kind === "topology_viewport") {
        passed &&= await executeTopologyViewport(page, shotsDir, state);
      } else if (control.kind === "loop_link") {
        passed &&= await executeLoopLink(page, shotsDir, state);
      } else if (control.kind === "select" && control.selector === "#theme-select") {
        passed &&= await executeTheme(page, state);
      } else if (control.kind === "dialog") {
        passed &&= await executeDialog(page, shotsDir, state);
      } else if (control.kind === "select" && control.selector.includes("#compare-a")) {
        passed &&= await executeCompare(page, state);
      } else if (control.kind === "disclosure") {
        passed &&= await executeDisclosure(page, state);
      } else if (control.kind === "search") {
        passed &&= await executeSearch(page, state);
      } else if (control.kind === "dialog_close") {
        passed &&= true;
      } else if (control.kind === "link") {
        passed &&= await executeLinks(page, state);
      } else if (control.kind === "human_review") {
        passed &&= await executeHumanReview(page, state);
      } else {
        passed = false;
        state.steps.push({
          control: control.selector,
          action: action.type,
          error: "unsupported contract action",
        });
      }
    }
    results.push(check(`contract:${control.selector}`, passed ? "pass" : "fail"));
  }
  return { results, steps: state.steps, screenshots: state.shotIndex };
}

async function checkKeyboard(page) {
  const tabs = page.locator('[role="tab"]');
  if ((await tabs.count()) < 2) {
    return check("keyboard", "fail", { error: "at least two tabs are required" });
  }
  await tabs.first().focus();
  const before = await page.evaluate(() => document.activeElement?.id);
  await page.keyboard.press("ArrowRight");
  const after = await page.evaluate(() => document.activeElement?.id);
  await page.keyboard.press("Enter");
  const selected = await page.evaluate(() =>
    document.activeElement?.getAttribute("aria-selected")
  );
  return check(
    "keyboard",
    before !== after && selected === "true" ? "pass" : "fail",
    { before, after, selected }
  );
}

async function checkDeepLinks(page, fileUrl, contract) {
  const failures = [];
  for (const control of (contract.controls || []).filter((item) => item.kind === "tab")) {
    const action = (control.actions || []).find((item) => item.expect_hash);
    if (!action) continue;
    await page.goto(`${fileUrl}${action.expect_hash}`, { waitUntil: "load" });
    const result = await page.locator(control.selector).evaluate((element) => {
      const panelId = element.getAttribute("aria-controls");
      const panel = panelId ? document.getElementById(panelId) : null;
      return {
        hash: location.hash,
        selected: element.getAttribute("aria-selected"),
        panelVisible: Boolean(panel && !panel.hidden),
      };
    });
    if (
      result.hash !== action.expect_hash ||
      result.selected !== "true" ||
      !result.panelVisible
    ) {
      failures.push({ selector: control.selector, ...result });
    }
  }
  await page.goto(`${fileUrl}#view=topology&x=-300&y=-100&scale=2`, { waitUntil: "load" });
  const topologyState = await page.evaluate(() => {
    const params = new URLSearchParams(location.hash.replace(/^#/, ""));
    const stage = document.querySelector("#graph-stage");
    return {
      x: params.get("x"),
      y: params.get("y"),
      scale: params.get("scale"),
      transform: stage?.style.transform || "",
      topology: document.querySelector("#tab-topology")?.getAttribute("aria-selected"),
    };
  });
  if (
    topologyState.x !== "-300" ||
    topologyState.y !== "-100" ||
    topologyState.scale !== "2" ||
    !topologyState.transform.includes("scale(2)") ||
    topologyState.topology !== "true"
  ) {
    failures.push({ selector: "#graph-stage", ...topologyState });
  }
  await page.goto(`${fileUrl}#view=topology&x=bad&y=bad&scale=bad`, { waitUntil: "load" });
  const malformedState = await page.locator("#graph-stage").evaluate((stage) => ({
    transform: stage.style.transform,
    usable: !stage.style.transform.includes("NaN"),
  }));
  if (!malformedState.usable) {
    failures.push({ selector: "#graph-stage", ...malformedState });
  }
  return check("deep_links", failures.length ? "fail" : "pass", { failures });
}

export async function judgeViewer({ viewerPath, evidenceDir }) {
  const resolvedViewer = path.resolve(viewerPath);
  const resolvedOut = path.resolve(evidenceDir);
  const shotsDir = path.join(resolvedOut, "navigation-shots");
  await mkdir(shotsDir, { recursive: true });
  const fileUrl = pathToFileURL(resolvedViewer).href;
  const consoleErrors = [];
  const checks = [];
  let steps = [];
  let screenshots = 0;
  let browser;
  let browserVersion = "unavailable";

  try {
    browser = await chromium.launch({ headless: true });
    browserVersion = browser.version();
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    page.on("console", (message) => {
      if (message.type() === "error") consoleErrors.push(message.text().slice(0, 500));
    });
    page.on("pageerror", (error) =>
      consoleErrors.push(`pageerror: ${String(error).slice(0, 500)}`)
    );
    await page.goto(fileUrl, { waitUntil: "load" });

    let contract;
    try {
      contract = await page.locator("#interaction-contract").evaluate((element) =>
        JSON.parse(element.textContent || "{}")
      );
      checks.push(check("interaction_contract", "pass", { version: contract.version }));
    } catch (error) {
      contract = { controls: [] };
      checks.push(check("interaction_contract", "fail", { error: String(error) }));
    }

    const contractSelectors = (contract.controls || []).map((item) => item.selector);
    const discovered = [];
    for (const tab of (contract.controls || []).filter((item) => item.kind === "tab")) {
      await page.locator(tab.selector).click();
      await page.waitForTimeout(30);
      discovered.push(...await discoverControls(page, contractSelectors));
    }
    const uncovered = discovered.filter((control) => !control.coveredBy);
    checks.push(
      check(
        "control_coverage",
        uncovered.length ? "fail" : "pass",
        { discovered, uncovered }
      )
    );

    const contractRun = await executeContract(page, contract, shotsDir);
    checks.push(...contractRun.results);
    steps = contractRun.steps;
    screenshots = contractRun.screenshots;
    checks.push(await checkKeyboard(page));
    checks.push(await checkDeepLinks(page, fileUrl, contract));
    checks.push(
      check(
        "console_errors",
        consoleErrors.length ? "fail" : "pass",
        { errors: consoleErrors }
      )
    );
  } catch (error) {
    checks.push(check("browser_journey", "fail", { error: String(error) }));
  } finally {
    if (browser) await browser.close();
  }

  const passed = checks.length > 0 && checks.every((item) => item.status === "pass");
  const evidence = {
    schema_version: "1.0",
    status: passed ? "pass" : "fail",
    viewer: path.basename(resolvedViewer),
    viewer_sha256: await viewerHash(resolvedViewer),
    browser: {
      name: "chromium",
      version: browserVersion,
      playwright: playwrightPackage.version,
    },
    checks,
    steps,
    screenshots,
  };
  await writeFile(
    path.join(resolvedOut, "navigation-evidence.json"),
    `${JSON.stringify(evidence, null, 2)}\n`,
    "utf8"
  );
  const report = [
    `# Navigation Evidence`,
    ``,
    `Status: **${evidence.status.toUpperCase()}**`,
    ``,
    `Viewer SHA-256: \`${evidence.viewer_sha256}\``,
    ``,
    ...checks.map((item) => `- **${item.status}** \`${item.name}\``),
  ].join("\n");
  await writeFile(path.join(resolvedOut, "navigation-report.md"), `${report}\n`, "utf8");
  return evidence;
}
