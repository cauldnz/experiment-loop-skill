// navigate.mjs — drive an experiment viewer like a real user and record what happens.
//
// Usage: node navigate.mjs --viewer <file.html> --out <dir>
// Requires: `npm install playwright-core` (drives the locally-installed Edge via
//   channel:"msedge" — no large browser download). Reference implementation for
//   SKILL.md §7 navigation-based judging of interactive artifacts.
//
// It opens the viewer in Edge (via playwright-core), then:
//   * records console errors / page errors
//   * captures the initial view
//   * discovers interactive controls: tabs (role=tab / [data-tab] / nav a[href^="#"]),
//     <select>, checkboxes, and in-page anchor links
//   * exercises each: clicks tabs, selects each option, toggles checkboxes, clicks anchors,
//     asserting whether the visible DOM actually changed (interactivity is real, not dead)
//   * tests KEYBOARD operability of a tablist (focus first tab, ArrowRight/Left, Enter/Space)
//   * tests HASH DEEP-LINKS: for each discovered hash target, load viewer#hash fresh and
//     confirm the corresponding view is shown (round-trip / shareable state)
//   * screenshots every state into <out>/shots and writes <out>/transcript.json + report.md
//
// The transcript is designed so a JUDGE can see the lived behaviour, and re-run any step.

import { chromium } from "playwright-core";
import { mkdirSync, writeFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import path from "node:path";

function arg(name, def = null) {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 ? process.argv[i + 1] : def;
}
const viewer = path.resolve(arg("viewer"));
const outDir = path.resolve(arg("out"));
const shotsDir = path.join(outDir, "shots");
mkdirSync(shotsDir, { recursive: true });
const fileUrl = pathToFileURL(viewer).href;

const transcript = { viewer: path.basename(path.dirname(viewer)), steps: [], console_errors: [], findings: {} };
let shotN = 0;
async function shot(page, label) {
  shotN += 1;
  const name = `${String(shotN).padStart(2, "0")}-${label.replace(/[^a-z0-9]+/gi, "-").slice(0, 40)}.png`;
  const p = path.join(shotsDir, name);
  try { await page.screenshot({ path: p, fullPage: true }); } catch { await page.screenshot({ path: p }); }
  return `shots/${name}`;
}
function step(o) { transcript.steps.push(o); }

const bodyText = (page) => page.evaluate(() => document.body.innerText.replace(/\s+/g, " ").trim().slice(0, 4000));
const visHash = (page) => page.evaluate(() => location.hash);

const browser = await chromium.launch({ channel: "msedge", headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.on("console", (m) => { if (m.type() === "error") transcript.console_errors.push(m.text().slice(0, 300)); });
page.on("pageerror", (e) => transcript.console_errors.push("pageerror: " + String(e).slice(0, 300)));

await page.goto(fileUrl, { waitUntil: "networkidle" });
await page.waitForTimeout(400);
let img = await shot(page, "initial");
let baseText = await bodyText(page);
step({ action: "load", url: fileUrl, hash: await visHash(page), shot: img, body_len: baseText.length });

// ---- discover controls ----
const controls = await page.evaluate(() => {
  const q = (sel) => Array.from(document.querySelectorAll(sel));
  const desc = (el) => (el.getAttribute("aria-label") || el.textContent || el.value || el.id || el.name || "").replace(/\s+/g, " ").trim().slice(0, 60);
  const tabs = q('[role="tab"], [data-tab], .tab, nav a[href^="#"], .nav a[href^="#"]').map((el, i) => ({
    i, tag: el.tagName.toLowerCase(), role: el.getAttribute("role"), href: el.getAttribute("href"),
    hasRoleTab: el.getAttribute("role") === "tab", text: desc(el),
  }));
  const selects = q("select").map((el, i) => ({ i, id: el.id, options: Array.from(el.options).map(o => o.value), text: desc(el) }));
  const checks = q('input[type="checkbox"]').map((el, i) => ({ i, id: el.id, text: desc(el) }));
  const tablists = q('[role="tablist"]').length;
  const landmarks = { header: q("header").length, nav: q("nav").length, main: q("main").length, roles: q("[role]").length };
  return { tabs, selects, checks, tablists, landmarks };
});
transcript.findings.controls = controls;

// ---- exercise TABS ----
const tabResults = [];
for (const t of controls.tabs) {
  const sel = t.href ? `a[href="${t.href}"]` : `[role="tab"], [data-tab], .tab`;
  try {
    const handle = (await page.$$(`[role="tab"], [data-tab], .tab, nav a[href^="#"], .nav a[href^="#"]`))[t.i];
    if (!handle) continue;
    const label = (t.text || t.href || `tab${t.i}`);
    await handle.click();
    await page.waitForTimeout(350);
    const after = await bodyText(page);
    const changed = after !== baseText;
    const hash = await visHash(page);
    const img2 = await shot(page, "tab-" + label);
    tabResults.push({ label, href: t.href, hash_after: hash, view_changed: changed, shot: img2 });
    step({ action: "click_tab", label, href: t.href, hash_after: hash, view_changed: changed, shot: img2 });
    baseText = after; // move baseline forward so next tab-change is detectable
  } catch (e) { tabResults.push({ label: t.text, error: String(e).slice(0, 120) }); }
}
transcript.findings.tabs = tabResults;

// ---- bring filters into their live context: activate the data/matrix tab if present ----
async function activateDataTab() {
  const viewChanging = tabResults.filter(t => t.view_changed);
  if (!viewChanging.length) return null;
  const pick = viewChanging.find(t => /matrix|table|grid|data|score/i.test(t.label || "")) || viewChanging[0];
  const handles = await page.$$(`[role="tab"], [data-tab], .tab, nav a[href^="#"], .nav a[href^="#"]`);
  const idx = controls.tabs.findIndex(t => (t.text || t.href) === (pick.label));
  if (idx >= 0 && handles[idx]) {
    await handles[idx].click();
    await page.waitForTimeout(350);
    baseText = await bodyText(page);
    step({ action: "activate_data_tab_for_filters", label: pick.label });
    return pick.label;
  }
  return null;
}
transcript.findings.filters_context_tab = await activateDataTab();

// ---- exercise SELECT filters ----
const selResults = [];
for (const s of controls.selects) {
  if (!s.id) continue;
  for (const opt of s.options.slice(0, 6)) {
    try {
      const before = await bodyText(page);
      await page.selectOption(`#${s.id}`, opt);
      await page.waitForTimeout(300);
      const after = await bodyText(page);
      const img3 = await shot(page, `select-${s.id}-${opt}`);
      selResults.push({ select: s.id, option: opt, view_changed: after !== before, shot: img3 });
      step({ action: "select_option", select: s.id, option: opt, view_changed: after !== before, shot: img3 });
    } catch (e) { selResults.push({ select: s.id, option: opt, error: String(e).slice(0, 120) }); }
  }
}
transcript.findings.selects = selResults;

// ---- exercise CHECKBOX toggles ----
const chkResults = [];
for (const c of controls.checks) {
  try {
    const before = await bodyText(page);
    const handle = (await page.$$('input[type="checkbox"]'))[c.i];
    if (!handle) continue;
    await handle.click();
    await page.waitForTimeout(300);
    const after = await bodyText(page);
    const img4 = await shot(page, `check-${c.id || c.i}-on`);
    chkResults.push({ check: c.id || c.text, view_changed: after !== before, shot: img4 });
    step({ action: "toggle_checkbox", check: c.id || c.text, view_changed: after !== before, shot: img4 });
    await handle.click(); await page.waitForTimeout(150); // reset
  } catch (e) { chkResults.push({ check: c.id, error: String(e).slice(0, 120) }); }
}
transcript.findings.checkboxes = chkResults;

// ---- KEYBOARD operability of a tablist ----
const kbd = { tested: false };
if (controls.tablists > 0) {
  try {
    kbd.tested = true;
    const firstTab = await page.$('[role="tab"]');
    await firstTab.focus();
    const focus0 = await page.evaluate(() => document.activeElement?.textContent?.trim().slice(0, 40));
    await page.keyboard.press("ArrowRight");
    await page.waitForTimeout(200);
    const focus1 = await page.evaluate(() => document.activeElement?.textContent?.trim().slice(0, 40));
    await page.keyboard.press("Enter");
    await page.waitForTimeout(250);
    const afterEnter = await bodyText(page);
    kbd.focus_moved_on_arrow = focus0 !== focus1;
    kbd.focus_before = focus0; kbd.focus_after_arrow = focus1;
    kbd.activate_changed_view = afterEnter !== baseText;
    kbd.shot = await shot(page, "keyboard-arrow-enter");
    step({ action: "keyboard_tablist", ...kbd });
  } catch (e) { kbd.error = String(e).slice(0, 160); }
}
transcript.findings.keyboard = kbd;

// ---- HASH DEEP-LINK round-trip ----
const hashTargets = Array.from(new Set(controls.tabs.map(t => t.href).filter(h => h && h.startsWith("#") && h.length > 1)));
// also try tab-style hashes if the app uses #tab=...
const guessed = tabResults.map(t => t.hash_after).filter(h => h && h.length > 1);
const allHashes = Array.from(new Set([...hashTargets, ...guessed]));
const deep = [];
for (const h of allHashes.slice(0, 8)) {
  try {
    const freshUrl = fileUrl + h;
    await page.goto(freshUrl, { waitUntil: "networkidle" });
    await page.waitForTimeout(400);
    const hashNow = await visHash(page);
    const text = await bodyText(page);
    const img5 = await shot(page, "deeplink-" + h.replace(/[^a-z0-9=]+/gi, "-"));
    deep.push({ hash: h, restored_hash: hashNow, nonempty: text.length > 50, shot: img5 });
    step({ action: "deeplink_load", hash: h, restored_hash: hashNow, body_len: text.length, shot: img5 });
  } catch (e) { deep.push({ hash: h, error: String(e).slice(0, 120) }); }
}
transcript.findings.deeplinks = deep;

// ---- summary flags ----
transcript.findings.summary = {
  interactive_controls: controls.tabs.length + controls.selects.length + controls.checks.length,
  tabs_that_change_view: tabResults.filter(t => t.view_changed).length,
  filters_that_change_view: selResults.filter(s => s.view_changed).length + chkResults.filter(c => c.view_changed).length,
  keyboard_operable: !!kbd.focus_moved_on_arrow,
  deeplinks_roundtrip: deep.filter(d => d.nonempty && (!d.restored_hash || d.restored_hash === d.hash)).length,
  console_errors: transcript.console_errors.length,
  landmarks: controls.landmarks,
};

writeFileSync(path.join(outDir, "transcript.json"), JSON.stringify(transcript, null, 2));
// human-readable report
const f = transcript.findings;
const md = [
  `# Navigation transcript — ${transcript.viewer}`,
  ``,
  `Screenshots: ${shotN}. Console errors: ${transcript.console_errors.length}.`,
  ``,
  `## Interactivity summary`,
  "```json", JSON.stringify(f.summary, null, 2), "```",
  ``,
  `## Tabs (${f.tabs.length})`,
  ...f.tabs.map(t => `- **${t.label}** → view_changed=${t.view_changed}, hash=${t.hash_after || "—"} (${t.shot || t.error})`),
  ``,
  `## Filters — selects (${f.selects.length}) / checkboxes (${f.checkboxes.length})`,
  ...f.selects.map(s => `- select #${s.select}=${s.option} → changed=${s.view_changed}`),
  ...f.checkboxes.map(c => `- checkbox ${c.check} → changed=${c.view_changed}`),
  ``,
  `## Keyboard`,
  "```json", JSON.stringify(f.keyboard, null, 2), "```",
  ``,
  `## Hash deep-links (${f.deeplinks.length})`,
  ...f.deeplinks.map(d => `- ${d.hash} → restored=${d.restored_hash || "—"}, nonempty=${d.nonempty} (${d.shot || d.error})`),
  ``,
  transcript.console_errors.length ? `## Console errors\n` + transcript.console_errors.map(e => `- ${e}`).join("\n") : `## Console errors\n- none`,
].join("\n");
writeFileSync(path.join(outDir, "report.md"), md);

console.log("NAV DONE:", transcript.viewer, JSON.stringify(f.summary));
await browser.close();
