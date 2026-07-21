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
  await prepareView(page, "overview", { closeInspector: false });
  await page.evaluate(() => {
    history.replaceState(null, "", `${location.pathname}${location.search}`);
  });
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


async function prepareView(page, view, { closeInspector = view === "topology" } = {}) {
  await page.evaluate(() => {
    for (const dialog of document.querySelectorAll("dialog[open]")) dialog.close();
  });
  const workspace = page.locator("#topology-workspace");
  if (
    await workspace.count() &&
    await workspace.evaluate((element) => element.classList.contains("is-maximized"))
  ) {
    await page.locator("#topology-maximize").click();
  }
  await activateView(page, view);
  const drawer = page.locator("#loop-inspector");
  if (
    closeInspector &&
    await drawer.count() &&
    await drawer.evaluate((element) => element.classList.contains("is-open"))
  ) {
    await page.locator("#topology-inspector-close").click();
  }
}


async function resetGraphFilters(page) {
  await page.evaluate(() => {
    for (const id of ["track-filter", "decision-filter", "loop-search"]) {
      const control = document.getElementById(id);
      if (control) control.value = "";
    }
    const champion = document.getElementById("champion-filter");
    if (champion) champion.checked = false;
    document.getElementById("loop-search")?.dispatchEvent(
      new Event("input", { bubbles: true })
    );
  });
}


async function executeGraph(page, shotsDir, state) {
  await prepareView(page, "topology");
  await resetGraphFilters(page);
  const nodes = page.locator(".graph-node");
  const count = await nodes.count();
  if (!count) return false;
  const tabStops = await nodes.evaluateAll((items) =>
    items.filter((item) => item.tabIndex === 0).length
  );
  const selected = nodes.nth(count - 1);
  await selected.click();
  const pointerLoop = await selected.getAttribute("data-loop");
  await selected.focus();
  await page.keyboard.press("ArrowLeft");
  const keyboardLoop = await page.evaluate(() =>
    document.activeElement?.classList.contains("graph-node")
      ? document.activeElement.dataset.loop
      : null
  );
  await page.keyboard.press("Enter");
  const outcome = await page.evaluate(() => ({
    hash: location.hash,
    selected: document.querySelectorAll('.graph-node[aria-pressed="true"]').length,
    tabStops: Array.from(document.querySelectorAll(".graph-node")).filter(
      (node) => node.tabIndex === 0
    ).length,
    inspectorVisible: Boolean(document.querySelector("#loop-inspector h2")),
  }));
  outcome.arrowMoved = Boolean(keyboardLoop && keyboardLoop !== pointerLoop);
  state.shotIndex += 1;
  const shot = await screenshot(page, shotsDir, state.shotIndex, "graph-selection");
  state.steps.push({ control: ".graph-node", action: "keyboard-select", outcome, shot });
  return tabStops === 1 && outcome.arrowMoved && outcome.tabStops === 1 &&
    outcome.selected === 1 &&
    outcome.inspectorVisible && outcome.hash.includes("view=topology") &&
    outcome.hash.includes("loop=");
}

async function executeFilters(page, shotsDir, state) {
  await prepareView(page, "topology");
  await resetGraphFilters(page);
  const total = await page.locator(".graph-node").count();
  const exerciseSelect = async (selector) => {
    const select = page.locator(selector);
    const values = await select.locator("option").evaluateAll((options) =>
      options.map((option) => option.value).filter(Boolean)
    );
    const outcomes = [];
    for (const value of values) {
      await select.selectOption(value);
      outcomes.push({
        value,
        selected: await select.inputValue(),
        visible: await page.locator(".graph-node:not(.is-dimmed)").count(),
        dimmed: await page.locator(".graph-node.is-dimmed").count(),
      });
    }
    await select.selectOption("");
    return outcomes;
  };
  const tracks = await exerciseSelect("#track-filter");
  const decisions = await exerciseSelect("#decision-filter");
  const search = page.locator("#loop-search");
  await search.fill("__navigation_judge_no_match__");
  const dimmed = await page.locator(".graph-node.is-dimmed").count();
  await search.fill("");
  const champion = page.locator("#champion-filter");
  await champion.check();
  const championCount = await page.locator(".graph-node:not(.is-dimmed)").count();
  await champion.uncheck();
  const outcome = { tracks, decisions, dimmed, total, championCount };
  state.shotIndex += 1;
  const shot = await screenshot(page, shotsDir, state.shotIndex, "graph-filters");
  state.steps.push({
    control: "#track-filter,#decision-filter,#loop-search,#champion-filter",
    action: "filter",
    outcome,
    shot,
  });
  const selectionsWorked = (items) => items.every(
    (item) => item.selected === item.value &&
      item.visible + item.dimmed === total &&
      (items.length === 1 || item.visible < total)
  );
  return total > 0 && tracks.length > 0 && decisions.length > 0 &&
    selectionsWorked(tracks) && selectionsWorked(decisions) &&
    dimmed === total && championCount === 1;
}

async function executeTopologyViewport(page, shotsDir, state) {
  await prepareView(page, "topology");
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
  const pointer = {
    x: viewportBox.x + viewportBox.width / 2,
    y: viewportBox.y + viewportBox.height / 2,
  };
  const anchorBefore = {
    x: (viewportBox.width / 2 - reset.x) / reset.scale,
    y: (viewportBox.height / 2 - reset.y) / reset.scale,
  };
  await page.mouse.move(pointer.x, pointer.y);
  await page.mouse.wheel(0, -600);
  const wheelZoomed = await snapshot();
  const anchorAfter = {
    x: (viewportBox.width / 2 - wheelZoomed.x) / wheelZoomed.scale,
    y: (viewportBox.height / 2 - wheelZoomed.y) / wheelZoomed.scale,
  };
  const pointerAnchored =
    Math.abs(anchorBefore.x - anchorAfter.x) < 1 &&
    Math.abs(anchorBefore.y - anchorAfter.y) < 1;
  const panStart = await viewport.evaluate((element) => {
    const rect = element.getBoundingClientRect();
    for (const xRatio of [0.1, 0.25, 0.5, 0.75, 0.9]) {
      for (const yRatio of [0.15, 0.35, 0.55, 0.75]) {
        const x = rect.left + rect.width * xRatio;
        const y = rect.top + rect.height * yRatio;
        const target = document.elementFromPoint(x, y);
        if (
          target &&
          element.contains(target) &&
          !target.closest(".graph-node,.graph-minimap,button,a,input,select")
        ) {
          return { x, y };
        }
      }
    }
    throw new Error("no unobstructed topology background point is available");
  });
  await page.mouse.move(panStart.x, panStart.y);
  await page.mouse.down();
  await page.mouse.move(panStart.x + 60, panStart.y + 40, { steps: 3 });
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
    pointerAnchored,
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
    pointerAnchored &&
    (panned.x !== wheelZoomed.x || panned.y !== wheelZoomed.y) &&
    minimapMoved &&
    selected.drawerOpen &&
    !closed.drawerOpen &&
    reopened.drawerOpen &&
    maximized.maximized &&
    !restored.maximized;
}

async function executeLoopLink(page, shotsDir, state) {
  await prepareView(page, "overview");
  const link = page.locator("[data-open-loop]").first();
  if (!(await link.count())) return false;
  await link.click();
  const outcome = await page.evaluate(() => ({
    hash: location.hash,
    topology: document.querySelector("#tab-topology")?.getAttribute("aria-selected"),
    selected: document.querySelectorAll('.graph-node[aria-pressed="true"]').length,
  }));
  state.shotIndex += 1;
  const shot = await screenshot(page, shotsDir, state.shotIndex, "loop-link");
  state.steps.push({ control: "[data-open-loop]", action: "click", outcome, shot });
  return outcome.topology === "true" && outcome.selected === 1 &&
    outcome.hash.includes("view=topology") && outcome.hash.includes("loop=");
}

async function executeTheme(page, shotsDir, state) {
  await prepareView(page, "overview", { closeInspector: false });
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
    state.shotIndex += 1;
    const shot = await screenshot(
      page, shotsDir, state.shotIndex, `theme-${value}`
    );
    state.steps.push({
      control: "#theme-select",
      action: "select",
      value,
      outcome,
      shot,
    });
  }
  return passed;
}

async function executeDialog(page, shotsDir, state) {
  await prepareView(page, "topology");
  const invoker = page.locator("#panel-topology .expand-artifact").first();
  if (!(await invoker.count())) return false;
  await invoker.click();
  const opened = await page.locator("#artifact-dialog").evaluate((dialog) => ({
    open: dialog.open,
    focusInside: dialog.contains(document.activeElement),
  }));
  state.shotIndex += 1;
  const openedShot = await screenshot(
    page, shotsDir, state.shotIndex, "artifact-dialog-open"
  );
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
  const closedShot = await screenshot(
    page, shotsDir, state.shotIndex, "artifact-dialog-closed"
  );
  state.steps.push({
    control: ".expand-artifact",
    action: "dialog",
    outcome: { opened, contained, closed },
    shots: [openedShot, closedShot],
  });
  return opened.open && opened.focusInside && contained && !closed.open && closed.focusRestored;
}

async function executeDialogClose(page, shotsDir, state) {
  await prepareView(page, "topology");
  const invoker = page.locator("#panel-topology .expand-artifact").first();
  if (!(await invoker.count())) return false;
  await invoker.click();
  const opened = await page.locator("#artifact-dialog").evaluate(
    (dialog) => dialog.open
  );
  await page.locator("#dialog-close").click();
  const outcome = await page.locator("#artifact-dialog").evaluate((dialog) => ({
    open: dialog.open,
    focusRestored: document.activeElement?.classList.contains("expand-artifact") || false,
  }));
  state.shotIndex += 1;
  const shot = await screenshot(
    page, shotsDir, state.shotIndex, "dialog-close-control"
  );
  state.steps.push({
    control: "#dialog-close",
    action: "click",
    outcome: { opened, ...outcome },
    shot,
  });
  return opened && !outcome.open && outcome.focusRestored;
}


async function executeCompare(page, shotsDir, state) {
  await prepareView(page, "compare");
  const a = page.locator("#compare-a");
  const b = page.locator("#compare-b");
  if (!(await a.count()) || !(await b.count())) return false;
  const options = await a.locator("option").evaluateAll((items) => items.map((item) => item.value));
  if (options.length < 2) return false;
  const selections = [];
  for (const [name, select] of [["a", a], ["b", b]]) {
    for (const value of options) {
      await select.selectOption(value);
      const outcome = await page.evaluate(() => ({
        hash: location.hash,
        comparisonVisible: Boolean(
          document.querySelector("#comparison .compare-artifacts")
        ),
        a: document.querySelector("#compare-a")?.value,
        b: document.querySelector("#compare-b")?.value,
      }));
      state.shotIndex += 1;
      const shot = await screenshot(
        page, shotsDir, state.shotIndex, `compare-${name}-${value}`
      );
      selections.push({ control: name, value, outcome, shot });
    }
  }
  const outcome = await page.evaluate(() => ({
    hash: location.hash,
    comparisonVisible: Boolean(document.querySelector("#comparison .compare-artifacts")),
    a: document.querySelector("#compare-a")?.value,
    b: document.querySelector("#compare-b")?.value,
  }));
  state.steps.push({
    control: "#compare-a,#compare-b",
    action: "select",
    outcome: { ...outcome, selections },
    shots: selections.map((selection) => selection.shot),
  });
  return selections.every((selection) =>
    selection.outcome.comparisonVisible &&
    selection.outcome[selection.control] === selection.value &&
    selection.outcome.hash.includes("view=compare")
  );
}

async function executeDisclosure(page, shotsDir, state) {
  await prepareView(page, "overview");
  const summary = page.locator("details > summary").first();
  if (!(await summary.count())) return false;
  const before = await summary.evaluate((element) => element.parentElement.open);
  await summary.click();
  const after = await summary.evaluate((element) => element.parentElement.open);
  state.shotIndex += 1;
  const shot = await screenshot(page, shotsDir, state.shotIndex, "disclosure");
  state.steps.push({
    control: "details > summary",
    action: "toggle",
    outcome: { before, after },
    shot,
  });
  return before !== after;
}

async function executeSearch(page, shotsDir, state) {
  await prepareView(page, "overview");
  const search = page.locator("#manifest-search");
  await search.evaluate((element) => {
    const disclosure = element.closest("details");
    if (disclosure) disclosure.open = true;
  });
  await search.fill("schema_version");
  const text = await page.locator("#manifest-tree").innerText();
  state.shotIndex += 1;
  const shot = await screenshot(page, shotsDir, state.shotIndex, "manifest-search");
  await search.fill("");
  state.steps.push({
    control: "#manifest-search",
    action: "input",
    outcome: { matched: text.includes("schema_version") },
    shot,
  });
  return text.includes("schema_version");
}

async function executeLinks(page, shotsDir, state) {
  await prepareView(page, "topology");
  const links = page.locator("a.button[href]");
  const count = await links.count();
  const unsafe = await links.evaluateAll((items) =>
    items.map((item) => item.getAttribute("href")).filter((href) =>
      !href || href.startsWith("javascript:") || href.startsWith("http:")
    )
  );
  state.shotIndex += 1;
  const shot = await screenshot(page, shotsDir, state.shotIndex, "local-links");
  state.steps.push({
    control: "a.button[href]",
    action: "inspect",
    outcome: { count, unsafe },
    shot,
  });
  return unsafe.length === 0;
}

async function executeHumanReview(page, shotsDir, state) {
  await prepareView(page, "overview", { closeInspector: false });
  const button = page.locator("#human-review-button");
  if (!(await button.count())) return false;
  await button.click();
  await page.locator("#human-general-notes").fill("Navigation judge review");
  await page.locator("#human-verdict").selectOption("approve");
  await page.locator("#human-recommendation").selectOption("keep");
  const firstScore = page.locator('[id^="human-score-"]').first();
  let criterionId = null;
  if (await firstScore.count()) {
    criterionId = await firstScore.evaluate(
      (element) => element.closest("[data-review-criterion]")?.dataset.reviewCriterion
    );
    await firstScore.fill("4");
    await page.locator('[id^="human-rating-"]').first().selectOption("strong");
    await page.locator('[id^="human-criterion-notes-"]').first().fill(
      "Clear and reproducible"
    );
  }
  await page.locator("#human-loop-notes").fill("Selected Loop note");
  await page.locator("#human-artifact-notes").fill("Selected Artifact note");
  state.shotIndex += 1;
  const reviewShot = await screenshot(
    page, shotsDir, state.shotIndex, "human-review-complete"
  );
  const downloadPromise = page.waitForEvent("download");
  await page.locator("#human-export").click();
  const download = await downloadPromise;
  const downloadedPath = await download.path();
  const exported = JSON.parse(await readFile(downloadedPath, "utf8"));
  await page.locator("#human-close").click();
  const entries = exported.human?.entries || [];
  const criterion = entries.find((entry) => entry.feedback_type === "criterion");
  const loop = entries.find((entry) => entry.feedback_type === "loop");
  const artifact = entries.find((entry) => entry.feedback_type === "artifact");
  const identityKeys = [];
  const collectIdentityKeys = (value) => {
    if (!value || typeof value !== "object") return;
    for (const [key, child] of Object.entries(value)) {
      if (/reviewer|email|display.?name/i.test(key)) identityKeys.push(key);
      collectIdentityKeys(child);
    }
  };
  collectIdentityKeys(exported);
  const outcome = {
    filename: download.suggestedFilename(),
    dialogOpen: await page.locator("#human-dialog").evaluate((dialog) => dialog.open),
    focusRestored: await button.evaluate((element) => document.activeElement === element),
    hasIdentity: identityKeys.length > 0,
    schemaVersion: exported.schema_version,
    kind: exported.kind,
    reviewIdValid: /^[A-Za-z0-9][A-Za-z0-9._:-]*$/.test(exported.review_id || ""),
    submittedAtValid: !Number.isNaN(Date.parse(exported.submitted_at)),
    experiment: exported.experiment_id,
    provenanceValid: exported.provenance?.surface === "viewer_native" &&
      exported.provenance?.export_mode === "local_download",
    bindingValid: /^[a-f0-9]{64}$/.test(exported.binding?.manifest_sha256 || "") &&
      /^[a-f0-9]{64}$/.test(exported.binding?.viewer_sha256 || "") &&
      exported.binding?.viewer_hash_algorithm === "canonical-html-zeroed-binding-v1",
    verdict: exported.human?.verdict,
    recommendation: exported.human?.recommendation,
    preferredIteration: exported.human?.preferred_iteration_id,
    feedbackTypes: entries.map((entry) => entry.feedback_type),
    criterionId,
    criterionValid: criterion?.criterion_review?.criterion_id === criterionId &&
      criterion?.criterion_review?.score === 4 &&
      criterion?.criterion_review?.rating === "strong" &&
      criterion?.verbatim === "Clear and reproducible",
    loopValid: loop?.target?.kind === "loop" &&
      Boolean(loop?.target?.id) &&
      loop?.verbatim === "Selected Loop note",
    artifactValid: artifact?.target?.kind === "artifact" &&
      Boolean(artifact?.target?.id) &&
      artifact?.verbatim === "Selected Artifact note",
  };
  state.shotIndex += 1;
  const closedShot = await screenshot(
    page, shotsDir, state.shotIndex, "human-review-closed"
  );
  state.steps.push({
    control: "#human-review-button,#human-close,#human-export",
    action: "review_and_export",
    outcome,
    shots: [reviewShot, closedShot],
  });
  return !outcome.dialogOpen && outcome.focusRestored && !outcome.hasIdentity &&
    outcome.schemaVersion === "1.0" && outcome.kind === "human_feedback_intake" &&
    outcome.reviewIdValid && outcome.filename === `${exported.review_id}.json` &&
    outcome.submittedAtValid && outcome.experiment && outcome.provenanceValid &&
    outcome.bindingValid && outcome.verdict === "approve" &&
    outcome.recommendation === "keep" && outcome.preferredIteration === null &&
    JSON.stringify(outcome.feedbackTypes) ===
      JSON.stringify(["general", "criterion", "loop", "artifact"]) &&
    outcome.criterionValid && outcome.loopValid && outcome.artifactValid;
}


function hasActionTypes(control, expected) {
  const actual = (control.actions || []).map((action) => action.type);
  return actual.length === expected.length &&
    expected.every((type) => actual.includes(type));
}


async function executeContract(page, contract, shotsDir) {
  const state = { shotIndex: 0, steps: [] };
  const results = [];
  for (const control of contract.controls || []) {
    let passed = true;
    if (control.kind === "tab" && hasActionTypes(control, ["click"])) {
      passed = await executeTab(page, control, control.actions[0], shotsDir, state);
    } else if (
      control.kind === "graph" &&
      hasActionTypes(control, ["arrow_navigation", "enter"])
    ) {
      passed = await executeGraph(page, shotsDir, state);
    } else if (control.kind === "filter" && hasActionTypes(control, ["change"])) {
      passed = await executeFilters(page, shotsDir, state);
    } else if (
      control.kind === "topology_viewport" &&
      hasActionTypes(control, ["operate"])
    ) {
      passed = await executeTopologyViewport(page, shotsDir, state);
    } else if (control.kind === "loop_link" && hasActionTypes(control, ["click"])) {
      passed = await executeLoopLink(page, shotsDir, state);
    } else if (
      control.kind === "select" &&
      control.selector === "#theme-select" &&
      hasActionTypes(control, ["each_option"])
    ) {
      passed = await executeTheme(page, shotsDir, state);
    } else if (control.kind === "dialog" && hasActionTypes(control, ["click"])) {
      passed = await executeDialog(page, shotsDir, state);
    } else if (
      control.kind === "select" &&
      control.selector.includes("#compare-a") &&
      hasActionTypes(control, ["each_option"])
    ) {
      passed = await executeCompare(page, shotsDir, state);
    } else if (
      control.kind === "disclosure" &&
      hasActionTypes(control, ["toggle"])
    ) {
      passed = await executeDisclosure(page, shotsDir, state);
    } else if (control.kind === "search" && hasActionTypes(control, ["input"])) {
      passed = await executeSearch(page, shotsDir, state);
    } else if (
      control.kind === "dialog_close" &&
      hasActionTypes(control, ["click"])
    ) {
      passed = await executeDialogClose(page, shotsDir, state);
    } else if (control.kind === "link" && hasActionTypes(control, ["inspect"])) {
      passed = await executeLinks(page, shotsDir, state);
    } else if (
      control.kind === "human_review" &&
      hasActionTypes(control, ["review_and_export"])
    ) {
      passed = await executeHumanReview(page, shotsDir, state);
    } else {
      passed = false;
      state.steps.push({
        control: control.selector,
        actions: (control.actions || []).map((action) => action.type),
        error: "unsupported contract action",
      });
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
    !topologyState.transform.includes("translate(-300px, -100px) scale(2)") ||
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
  await page.goto(`${fileUrl}#view=topology`, { waitUntil: "load" });
  const deepLoopId = await page.locator(".graph-node").last().getAttribute("data-loop");
  await page.goto(
    `${fileUrl}#view=topology&loop=${encodeURIComponent(deepLoopId)}`,
    { waitUntil: "load" }
  );
  await page.waitForTimeout(220);
  const centeredSelection = await page.locator(`.graph-node[data-loop="${deepLoopId}"]`).evaluate((node) => {
    const nodeRect = node.getBoundingClientRect();
    const viewport = document.querySelector("#graph-viewport");
    const viewportRect = viewport.getBoundingClientRect();
    return {
      selected: node.getAttribute("aria-pressed"),
      drawerOpen: document.querySelector("#loop-inspector")?.classList.contains("is-open"),
      deltaX: Math.abs(
        nodeRect.left + nodeRect.width / 2 -
        (viewportRect.left + viewportRect.width / 2)
      ),
      deltaY: Math.abs(
        nodeRect.top + nodeRect.height / 2 -
        (viewportRect.top + viewportRect.height / 2)
      ),
    };
  });
  if (
    centeredSelection.selected !== "true" ||
    !centeredSelection.drawerOpen ||
    centeredSelection.deltaX > 2 ||
    centeredSelection.deltaY > 2
  ) {
    failures.push({ selector: ".graph-node", ...centeredSelection });
  }
  return check("deep_links", failures.length ? "fail" : "pass", { failures });
}

async function checkReducedMotion(page, fileUrl) {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto(`${fileUrl}#view=topology`, { waitUntil: "load" });
  await page.locator(".graph-node").last().evaluate((element) => element.click());
  const result = await page.locator("#graph-stage").evaluate((stage) => ({
    reduced: matchMedia("(prefers-reduced-motion: reduce)").matches,
    transition: stage.style.transition,
  }));
  await page.emulateMedia({ reducedMotion: "no-preference" });
  return check(
    "reduced_motion",
    result.reduced && result.transition === "none" ? "pass" : "fail",
    result
  );
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
    checks.push(await checkReducedMotion(page, fileUrl));
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
